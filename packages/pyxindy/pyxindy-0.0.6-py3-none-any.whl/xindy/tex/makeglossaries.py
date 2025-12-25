"""Python port of the makeglossaries helper."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import os
from pathlib import Path
import re
import sys

from xindy.cli import main as xindy_main
from xindy.tex import makeindex4


VERSION = "4.53-py"


@dataclass
class GlossaryType:
    """Glossary file extensions collected from the .aux."""

    name: str
    log_ext: str
    out_ext: str
    in_ext: str


@dataclass
class AuxData:
    """Information scraped from the LaTeX .aux file(s)."""

    style: Path | None
    types: dict[str, GlossaryType]
    glslist: list[str] | None
    letter_ordering: bool | None
    languages: dict[str, str]
    codepages: dict[str, str]
    extramkidxopts: str
    found_bib2gls_resource: bool


@dataclass
class GlossaryJob:
    """Single glossary processing job."""

    type_name: str
    input_path: Path
    output_path: Path
    log_path: Path
    language: str | None
    codepage: str | None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="makeglossaries",
        description="Best-effort Python port of the glossaries helper.",
    )
    parser.add_argument("basename", help="Document base name (with or without extension).")
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Reduce chatter (warnings may still appear from subcommands).",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Print the commands that would run but do not execute them.",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=Path,
        help="Directory containing the .aux/.glo/etc files (changes cwd).",
    )
    parser.add_argument("-s", "--style", type=Path, help="Style file (.ist or .xdy).")
    parser.add_argument(
        "-o",
        "--output",
        help="Override output file (only sensible when a single glossary is processed).",
    )
    parser.add_argument(
        "-t",
        "--transcript",
        dest="logfile",
        help="Override transcript/log file (single glossary only).",
    )
    parser.add_argument("-L", "--language", help="Xindy language override (xindy only).")
    parser.add_argument("-C", "--codepage", help="Xindy codepage override (xindy only).")
    parser.add_argument(
        "-i",
        dest="stdin",
        action="store_true",
        help="Ignored for compatibility with the Perl script.",
    )
    parser.add_argument(
        "-l",
        dest="letter_ordering",
        action="store_true",
        default=None,
        help="Force letter ordering; defaults to the ordering stored in the .aux file.",
    )
    parser.add_argument("-c", "--compress", action="store_true", help="makeindex -c")
    parser.add_argument("-g", "--german", action="store_true", help="makeindex -g")
    parser.add_argument("-p", "--start-page", dest="start_page", help="makeindex -p")
    parser.add_argument("-r", "--no-range", action="store_true", help="makeindex -r")
    parser.add_argument(
        "-e",
        "--no-encap-fix",
        action="store_true",
        help="Compatibility flag; encap repair not yet implemented in the Python port.",
    )
    parser.add_argument(
        "-Q",
        dest="suppress_fork_warning",
        action="store_true",
        help="Ignored for compatibility with the Perl script.",
    )
    parser.add_argument(
        "-k",
        dest="no_pipe",
        action="store_true",
        help="Ignored for compatibility with the Perl script.",
    )
    parser.add_argument(
        "-m",
        dest="makeindex_path",
        help="Ignored: the built-in makeindex4 implementation is always used.",
    )
    parser.add_argument(
        "-x",
        dest="xindy_path",
        help="Ignored: the built-in xindy implementation is always used.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    args = parser.parse_args(argv)

    if args.directory:
        os.chdir(args.directory)

    base_path = Path(args.basename)
    base_stem = base_path.with_suffix("")
    ext = base_path.suffix[1:] if base_path.suffix else ""

    if ext.lower() == "tex":
        parser.error(
            "Don't pass the .tex file. Use the document base name or a glossary file instead."
        )

    aux_path = base_stem.with_suffix(".aux")
    if not aux_path.exists():
        parser.error(f"Auxiliary file '{aux_path}' does not exist. Did LaTeX run succeed?")

    if not args.quiet:
        print(f"makeglossaries (python) version {VERSION}")

    aux_data = parse_aux(aux_path, quiet=args.quiet)

    style_path = Path(args.style) if args.style else aux_data.style
    if style_path is None:
        if aux_data.found_bib2gls_resource:
            parser.error(
                "Found \\glsxtr@resource but no \\@istfilename. Run bib2gls instead of "
                "makeglossaries or add \\makeglossaries for hybrid mode."
            )
        parser.error("No \\@istfilename found in the .aux file.")

    letter_ordering = (
        args.letter_ordering if args.letter_ordering is not None else aux_data.letter_ordering
    )
    use_xindy = style_path.suffix.lower() == ".xdy"

    jobs = build_jobs(
        base_stem,
        ext=ext,
        aux=aux_data,
        output_override=args.output,
        log_override=args.logfile,
        quiet=args.quiet,
    )
    if not jobs:
        if not args.quiet:
            print("No glossary types to process.")
        return 0

    exit_code = 0
    for job in jobs:
        try:
            if use_xindy:
                run_xindy_job(
                    job,
                    style_path=style_path,
                    language=args.language or job.language,
                    codepage=args.codepage or job.codepage,
                    dry_run=args.dry_run,
                    quiet=args.quiet,
                )
            else:
                run_makeindex_job(
                    job,
                    style_path=style_path,
                    letter_ordering=bool(letter_ordering),
                    compress=args.compress,
                    german=args.german,
                    start_page=args.start_page,
                    no_range=args.no_range,
                    dry_run=args.dry_run,
                    quiet=args.quiet,
                )
        except Exception as exc:  # pragma: no cover - defensive path
            exit_code = 1
            print(f"makeglossaries error ({job.type_name}): {exc}", file=sys.stderr)

    return exit_code


def parse_aux(path: Path, *, quiet: bool) -> AuxData:
    """Parse the .aux file to discover glossary definitions and style/language hints."""

    data = AuxData(
        style=None,
        types={},
        glslist=None,
        letter_ordering=None,
        languages={},
        codepages={},
        extramkidxopts="",
        found_bib2gls_resource=False,
    )
    seen: set[Path] = set()

    def _parse_one(aux_path: Path) -> None:
        if aux_path in seen:
            return
        seen.add(aux_path)
        try:
            text = aux_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            print(f"Warning: unable to read {aux_path}: {exc}", file=sys.stderr)
            return

        for line in text.splitlines():
            if "\\@gls@reference" in line and not data.glslist:
                raise SystemExit(
                    "Your document used \\makenoidxglossaries; makeglossaries is not required."
                )
            match = re.search(r"\\glsxtr@makeglossaries\{([^}]*)\}", line)
            if match:
                data.glslist = [part for part in match.group(1).split(",") if part]
                if not quiet:
                    print(f"only processing subset '{','.join(data.glslist)}'")
                continue

            match = re.search(r"\\@input\{(.+)\.aux\}", line)
            if match:
                _parse_one(aux_path.parent / f"{match.group(1)}.aux")
                continue

            match = re.search(
                r"\\@newglossary\s*\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}", line
            )
            if match:
                gloss = GlossaryType(
                    name=match.group(1),
                    log_ext=match.group(2),
                    out_ext=match.group(3),
                    in_ext=match.group(4),
                )
                data.types[gloss.name] = gloss
                if not quiet:
                    print(
                        "added glossary type "
                        f"'{gloss.name}' ({gloss.log_ext},{gloss.out_ext},{gloss.in_ext})"
                    )
                continue

            match = re.search(r"\\@istfilename\s*\{([^}]*)\}", line)
            if match:
                ist = match.group(1).strip()
                ist = re.sub(r'^"(.*)"\.(ist|xdy)$', r"\1.\2", ist)
                data.style = Path(ist)
                continue

            match = re.search(r"\\@xdylanguage\s*\{([^}]+)\}\{([^}]*)\}", line)
            if match:
                data.languages[match.group(1)] = match.group(2)
                continue

            match = re.search(r"\\@gls@codepage\s*\{([^}]+)\}\{([^}]*)\}", line)
            if match:
                data.codepages[match.group(1)] = match.group(2)
                continue

            match = re.search(r"\\@gls@extramakeindexopts\{(.*)\}", line)
            if match:
                data.extramkidxopts += match.group(1)
                continue

            if "\\glsxtr@resource" in line:
                data.found_bib2gls_resource = True

            if data.letter_ordering is None:
                match = re.search(r"\\@glsorder\s*\{([^}]+)\}", line)
                if match:
                    if match.group(1) == "letter":
                        data.letter_ordering = True
                    elif match.group(1) == "word":
                        data.letter_ordering = False
                    else:
                        if not quiet:
                            print(
                                f"Unknown ordering '{match.group(1)}'; assuming word ordering.",
                                file=sys.stderr,
                            )
                        data.letter_ordering = False

    _parse_one(path)
    return data


def build_jobs(
    base: Path,
    *,
    ext: str,
    aux: AuxData,
    output_override: str | None,
    log_override: str | None,
    quiet: bool,
) -> list[GlossaryJob]:
    """Translate aux metadata into concrete jobs."""

    def _iter_types() -> Iterable[GlossaryType]:
        if ext:
            for gloss in aux.types.values():
                if gloss.in_ext == ext:
                    yield gloss
            return
        if aux.glslist:
            for name in aux.glslist:
                if name in aux.types:
                    yield aux.types[name]
            return
        yield from aux.types.values()

    jobs: list[GlossaryJob] = []
    for gloss in _iter_types():
        input_path = base.with_suffix(f".{gloss.in_ext}")
        output_path = (
            Path(output_override) if output_override else base.with_suffix(f".{gloss.out_ext}")
        )
        log_path = Path(log_override) if log_override else base.with_suffix(f".{gloss.log_ext}")
        jobs.append(
            GlossaryJob(
                type_name=gloss.name,
                input_path=input_path,
                output_path=output_path,
                log_path=log_path,
                language=aux.languages.get(gloss.name),
                codepage=aux.codepages.get(gloss.name),
            )
        )

    if ext and not jobs:
        raise SystemExit(
            f"The file extension '.{ext}' does not correspond to any known glossary type. "
            "Run makeglossaries without an extension to process all glossaries."
        )

    if not jobs and not quiet:
        print("Warning: no glossary types declared in the .aux file.", file=sys.stderr)

    return jobs


def run_makeindex_job(
    job: GlossaryJob,
    *,
    style_path: Path,
    letter_ordering: bool,
    compress: bool,
    german: bool,
    start_page: str | None,
    no_range: bool,
    dry_run: bool,
    quiet: bool,
) -> None:
    """Execute a single makeindex-style job using the built-in makeindex4 wrapper."""

    if not job.input_path.exists():
        if not quiet:
            print(f"Warning: file '{job.input_path}' not found; skipping '{job.type_name}'.")
        return

    if job.input_path.stat().st_size == 0:
        if not quiet:
            print(
                "Warning: file "
                f"'{job.input_path}' is empty. Writing placeholder to '{job.output_path}'."
            )
        job.output_path.parent.mkdir(parents=True, exist_ok=True)
        job.output_path.write_text("\\null\n", encoding="utf-8")
        return

    cli_args = [str(job.input_path), "-o", str(job.output_path), "-t", str(job.log_path)]
    if letter_ordering:
        cli_args.append("-l")
    if compress:
        cli_args.append("-c")
    if german:
        cli_args.append("-g")
    if start_page:
        cli_args.extend(["-p", start_page])
    if no_range:
        cli_args.append("-r")
    # makeindex4 currently ignores -s but we pass it along for transparency.
    if style_path:
        cli_args.extend(["-s", str(style_path)])

    cmd_display = "makeindex4 " + " ".join(cli_args)
    if not quiet:
        print(cmd_display)
    if dry_run:
        return

    job.log_path.unlink(missing_ok=True)
    job.output_path.parent.mkdir(parents=True, exist_ok=True)
    rc = makeindex4.main(cli_args)
    if rc != 0:
        raise RuntimeError(
            f"makeindex4 failed with exit code {rc}. See {job.log_path} for details."
        )


def run_xindy_job(
    job: GlossaryJob,
    *,
    style_path: Path,
    language: str | None,
    codepage: str | None,
    dry_run: bool,
    quiet: bool,
) -> None:
    """Execute a single xindy-style job using the Python port."""

    if not job.input_path.exists():
        if not quiet:
            print(f"Warning: file '{job.input_path}' not found; skipping '{job.type_name}'.")
        return

    if job.input_path.stat().st_size == 0:
        if not quiet:
            print(
                "Warning: file "
                f"'{job.input_path}' is empty. Writing placeholder to '{job.output_path}'."
            )
        job.output_path.parent.mkdir(parents=True, exist_ok=True)
        job.output_path.write_text("\\null\n", encoding="utf-8")
        return

    cli_args = ["-M", str(style_path), "-o", str(job.output_path), "-l", str(job.log_path)]
    if codepage:
        cli_args.extend(["-C", codepage])
    cli_args.append(str(job.input_path))

    if language and not quiet:
        print(
            f"Note: language '{language}' recorded in .aux; current xindy port uses style modules."
        )

    cmd_display = "xindy " + " ".join(cli_args)
    if not quiet:
        print(cmd_display)
    if dry_run:
        return

    job.log_path.unlink(missing_ok=True)
    job.output_path.parent.mkdir(parents=True, exist_ok=True)
    rc = xindy_main(cli_args)
    if rc != 0:
        raise RuntimeError(f"xindy failed with exit code {rc}. See {job.log_path} for details.")


if __name__ == "__main__":
    raise SystemExit(main())
