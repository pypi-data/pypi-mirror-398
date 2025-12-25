"""Command-line entry point for the Python xindy port."""

from __future__ import annotations

from collections.abc import Sequence
import os
from pathlib import Path
import subprocess
import sys

import click

from . import __version__
from .dsl.interpreter import StyleError, StyleInterpreter
from .dsl.sexpr import SExprSyntaxError
from .index import build_index_entries
from .markup import render_index
from .raw.reader import load_raw_index, parse_raw_index


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Experimental Python port of the xindy index processor.",
)
@click.version_option(__version__, message="%(prog)s %(version)s")
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, resolve_path=True, path_type=Path),
    help="Write output to FILE instead of stdout.",
)
@click.option(
    "-M",
    "--module",
    "--style",
    "style",
    type=click.Path(dir_okay=False, resolve_path=True, path_type=Path),
    help="Style file (.xdy). Defaults to <raw>.xdy if omitted.",
)
@click.option(
    "-f",
    "--filter",
    "filter_cmd",
    help="Filter program to preprocess raw input (read from stdin, emit raw).",
)
@click.option(
    "-L",
    "--searchpath",
    "searchpath",
    multiple=True,
    type=click.Path(resolve_path=True, path_type=Path),
    help="Additional style search path (can be given multiple times).",
)
@click.option(
    "--log-level",
    "-V",
    "loglevel",
    type=int,
    default=None,
    help="Logging verbosity level (compat xindy.in -L).",
)
@click.option(
    "-C",
    "--codepage",
    default="utf-8",
    show_default=True,
    help="Encoding used to write the output.",
)
@click.option(
    "-l",
    "--log",
    "logfile",
    type=click.Path(dir_okay=False, resolve_path=True, path_type=Path),
    help="Write a brief log to FILE (best-effort).",
)
@click.option(
    "-t",
    "--trace",
    is_flag=True,
    help="Print tracebacks on errors.",
)
@click.option(
    "--markup-trace",
    is_flag=True,
    help="Enable markup tracing (compat -t from xindy.in; best-effort).",
)
@click.option(
    "-i",
    "--interactive",
    is_flag=True,
    help="Compatibility flag (interactive mode not supported; ignored with warning).",
)
@click.option(
    "-n",
    "--try-run",
    is_flag=True,
    help="Compatibility flag (try-run/skip checks; ignored with warning).",
)
@click.argument("raw")
@click.pass_context
def cli(
    ctx: click.Context,
    raw: str,
    output: Path | None,
    style: Path | None,
    filter_cmd: str | None,
    searchpath: tuple[Path, ...],
    loglevel: int | None,
    codepage: str,
    logfile: Path | None,
    trace: bool,
    markup_trace: bool,
    interactive: bool,
    try_run: bool,
) -> int:
    """Click entrypoint for the xindy CLI."""
    return _run_cli(
        ctx=ctx,
        raw=raw,
        output=output,
        style=style,
        filter_cmd=filter_cmd,
        searchpath=list(searchpath),
        loglevel=loglevel,
        codepage=codepage,
        logfile=logfile,
        trace=trace,
        markup_trace=markup_trace,
        interactive=interactive,
        try_run=try_run,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point used by both python -m xindy and console scripts."""
    try:
        result = cli.main(args=list(argv) if argv is not None else None, standalone_mode=False)
    except SystemExit as exc:
        return int(exc.code)
    except click.ClickException as exc:
        exc.show()
        return exc.exit_code
    return int(result) if isinstance(result, int) else 0


def _run_cli(
    *,
    ctx: click.Context,
    raw: str,
    output: Path | None,
    style: Path | None,
    filter_cmd: str | None,
    searchpath: list[Path],
    loglevel: int | None,
    codepage: str,
    logfile: Path | None,
    trace: bool,
    markup_trace: bool,
    interactive: bool,
    try_run: bool,
) -> int:
    raw_path = None if raw == "-" else Path(raw).resolve()
    if raw_path is not None and not raw_path.exists():
        raise click.UsageError(f"raw file not found: {raw_path}", ctx=ctx)

    style_path = style if style else (raw_path.with_suffix(".xdy") if raw_path else None)
    if style_path is None or not style_path.exists():
        raise click.UsageError(f"style file not found: {style_path}", ctx=ctx)

    search_paths: list[Path] = []
    env_search = os.environ.get("XINDY_SEARCHPATH")
    if env_search:
        search_paths.extend(Path(p).resolve() for p in env_search.split(os.pathsep) if p.strip())
    search_paths.extend(searchpath)
    search_paths.append(style_path.parent)

    def _log(message: str) -> None:
        if logfile:
            logfile.parent.mkdir(parents=True, exist_ok=True)
            with logfile.open("a", encoding="utf-8") as fh:
                fh.write(message + "\n")
        elif loglevel:
            sys.stderr.write(message + "\n")

    try:
        interpreter = StyleInterpreter()
        state = interpreter.load(style_path, extra_search_paths=search_paths)
        if markup_trace:
            state.markup_options.setdefault("trace", {})["enabled"] = True
        if interactive:
            print(
                "warning: interactive mode (-i) not supported in Python port; ignoring",
                file=sys.stderr,
            )
        if try_run:
            print("note: try-run (-n) has no effect in Python port", file=sys.stderr)
        if loglevel is not None:
            _log(f"log level set to {loglevel}")

        if filter_cmd:
            raw_text = _read_raw_text(raw_path, codepage)
            filtered = subprocess.run(
                filter_cmd,
                input=raw_text.encode(codepage),
                capture_output=True,
                shell=True,
            )
            if filtered.returncode != 0:
                raise RuntimeError(
                    f"filter command failed ({filtered.returncode}): {filtered.stderr.decode(errors='ignore')}"
                ) from None
            raw_entries = parse_raw_index(filtered.stdout.decode(codepage))
        elif raw_path is None:
            raw_text = sys.stdin.buffer.read().decode(codepage)
            raw_entries = parse_raw_index(raw_text)
        else:
            raw_entries = load_raw_index(raw_path)
        index = build_index_entries(raw_entries, state)
        output_text = render_index(index, style_state=state)
    except (FileNotFoundError, StyleError, SExprSyntaxError) as exc:
        print(f"xindy error: {exc}", file=sys.stderr)
        _log(f"error: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - defensive path
        if trace:
            raise
        print(f"xindy error: {exc}", file=sys.stderr)
        _log(f"error: {exc}")
        return 1

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(output_text, encoding=codepage)
        _log(f"wrote {output}")
    else:
        sys.stdout.write(output_text)
    return 0


def _read_raw_text(raw_path: Path | None, encoding: str) -> str:
    if raw_path is None:
        return sys.stdin.buffer.read().decode(encoding)
    try:
        return raw_path.read_text(encoding=encoding)
    except UnicodeDecodeError:
        return raw_path.read_text(encoding="latin-1")


if __name__ == "__main__":
    raise SystemExit(main())
