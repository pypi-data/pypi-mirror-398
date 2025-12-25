"""TeX ``.idx`` to xindy ``.raw`` converter with basic makeindex4 compatibility."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
import sys

from xindy.raw.reader import RawIndexEntry


@dataclass(slots=True)
class IdxEntry:
    key: tuple[str, ...]
    display_key: tuple[str, ...] | None
    attr: str | None
    loc: str | None
    xref_target: tuple[str, ...] | None = None

    def to_raw(self) -> RawIndexEntry:
        extras: dict[str, object] = {}
        if self.xref_target:
            extras["xref"] = list(self.xref_target)
        return RawIndexEntry(
            key=self.key,
            display_key=self.display_key,
            locref=None if self.xref_target else self.loc,
            attr=self.attr,
            extras=extras,
        )


def parse_idx_line(line: str) -> IdxEntry | None:
    """Parse a single ``\\indexentry{...}{...}`` occurrence (used for unit tests)."""
    text = line.strip()
    try:
        body, loc, _ = _extract_arguments(text)
    except ValueError:
        return None
    return _parse_entry(body, loc)


def parse_idx(text: str) -> list[IdxEntry]:
    """Parse an entire .idx file text into IdxEntry objects."""
    results: list[IdxEntry] = []
    idx = 0
    length = len(text)
    while idx < length:
        start = text.find("\\indexentry", idx)
        if start == -1:
            break
        idx = start + len("\\indexentry")
        try:
            body, loc, end_pos = _extract_arguments(text, text.find("{", idx))
        except ValueError:
            break
        entry = _parse_entry(body, loc)
        if entry:
            results.append(entry)
        idx = end_pos
    return results


def convert_idx_to_raw_entries(
    path: str | Path,
    *,
    encoding: str = "latin-1",
) -> list[RawIndexEntry]:
    """Read an .idx file and return corresponding RawIndexEntry objects."""
    if str(path) == "-":
        text = sys.stdin.buffer.read().decode(encoding)
    else:
        text = Path(path).read_text(encoding=encoding)
    idx_entries = parse_idx(text)
    return [entry.to_raw() for entry in idx_entries]


def write_raw(
    entries: Iterable[RawIndexEntry],
    dest: str | Path,
    *,
    encoding: str = "utf-8",
) -> None:
    """Serialize raw entries to ``dest`` as xindy ``.raw`` S-expressions."""
    lines = []
    for entry in entries:
        key_prop = _serialize_key(entry)
        props = [key_prop]
        if entry.attr:
            props.append(f':attr "{_escape(entry.attr)}"')
        if entry.locref:
            props.append(f':locref "{_escape(entry.locref)}"')
        xref_target = entry.extras.get("xref") if entry.extras else None
        if xref_target:
            if isinstance(xref_target, list):
                formatted = " ".join(f'"{_escape(str(x))}"' for x in xref_target)
                props.append(f":xref ({formatted})")
            else:
                props.append(f':xref "{_escape(str(xref_target))}"')
        # extras ignored for now
        props_str = " ".join(props)
        lines.append(f"(indexentry {props_str})")
    Path(dest).write_text("\n".join(lines) + "\n", encoding=encoding)


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="tex2xindy",
        description="Minimal TeX .idx to xindy .raw converter (Python port).",
    )
    parser.add_argument("idx", help="Input .idx file")
    parser.add_argument("-o", "--output", help="Output .raw file (default: stdout)")
    parser.add_argument(
        "--input-encoding",
        default="latin-1",
        help="Encoding of the .idx file (default: latin-1)",
    )
    parser.add_argument(
        "--output-encoding",
        default="utf-8",
        help="Encoding of the .raw output (default: utf-8)",
    )
    parser.add_argument("--log", help="Optional log file.")
    args = parser.parse_args(argv)

    entries = convert_idx_to_raw_entries(args.idx, encoding=args.input_encoding)
    if args.log:
        Path(args.log).write_text(f"converted {len(entries)} entries\n", encoding="utf-8")
    if args.output:
        write_raw(entries, args.output, encoding=args.output_encoding)
    else:
        for entry in entries:
            props = [_serialize_key(entry)]
            if entry.attr:
                props.append(f':attr "{_escape(entry.attr)}"')
            if entry.locref:
                props.append(f':locref "{_escape(entry.locref)}"')
            xref_target = entry.extras.get("xref") if entry.extras else None
            if xref_target:
                if isinstance(xref_target, list):
                    formatted = " ".join(f'"{_escape(str(x))}"' for x in xref_target)
                    props.append(f":xref ({formatted})")
                else:
                    props.append(f':xref "{_escape(str(xref_target))}"')
            print(f"(indexentry {' '.join(props)})")
    return 0


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


# ------------------------------- parsing helpers -------------------------------


def _extract_arguments(text: str, start: int | None = None) -> tuple[str, str, int]:
    """Return (body, locref, end_pos) for one \\indexentry occurrence starting at ``start``."""
    idx = start if start is not None else text.find("{")
    if idx == -1:
        raise ValueError("missing opening brace")
    body, next_pos = _read_braced(text, idx)
    loc, end_pos = _read_braced(text, next_pos)
    return body, loc, end_pos


def _read_braced(text: str, start: int) -> tuple[str, int]:
    """Read the braced content starting at ``start`` (which must be '{')."""
    if start >= len(text) or text[start] != "{":
        raise ValueError("expected '{'")
    depth = 0
    buf: list[str] = []
    idx = start
    while idx < len(text):
        ch = text[idx]
        idx += 1
        if ch == "\\":
            if idx < len(text):
                buf.append(ch)
                buf.append(text[idx])
                idx += 1
            continue
        if ch == "{":
            depth += 1
            if depth > 1:
                buf.append(ch)
            continue
        if ch == "}":
            if depth == 1:
                return "".join(buf), idx
            if depth == 0:
                return "".join(buf), idx
            depth -= 1
            if depth > 0:
                buf.append(ch)
            continue
        buf.append(ch)
    raise ValueError("unterminated brace group")


def _parse_entry(body: str, loc: str) -> IdxEntry:
    term_part, attr_part = _split_attr(body)
    key, display = _split_levels(term_part)
    attr, xref_target = _parse_attr(attr_part)
    loc_clean = None if xref_target else (_normalize_token(loc) if loc is not None else None)
    return IdxEntry(
        key=key,
        display_key=display,
        attr=attr,
        loc=loc_clean,
        xref_target=xref_target,
    )


def _split_attr(body: str) -> tuple[str, str | None]:
    """Split ``body`` into term and optional attribute after an unescaped ``|``."""
    depth = 0
    escape = False
    for idx, ch in enumerate(body):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == "{":
            depth += 1
            continue
        if ch == "}":
            depth = max(0, depth - 1)
            continue
        if ch == "|" and depth == 0:
            return body[:idx], body[idx + 1 :]
    return body, None


def _split_levels(term: str) -> tuple[tuple[str, ...], tuple[str, ...] | None]:
    """Split ``term`` into hierarchy levels and display overrides."""
    parts: list[str] = []
    depth = 0
    escape = False
    buf: list[str] = []
    for ch in term:
        if escape:
            buf.append(ch)
            escape = False
            continue
        if ch == "\\":
            escape = True
            buf.append(ch)
            continue
        if ch == "{":
            depth += 1
            buf.append(ch)
            continue
        if ch == "}":
            depth = max(0, depth - 1)
            buf.append(ch)
            continue
        if ch == "!" and depth == 0:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    if buf:
        parts.append("".join(buf))

    key_parts: list[str] = []
    display_parts: list[str] = []
    display_differs = False

    for part in parts:
        sort_text, display_text = _split_actual(part)
        sort_norm = _normalize_token(sort_text)
        display_norm = _normalize_token(display_text)
        key_parts.append(sort_norm)
        display_parts.append(display_norm)
        if sort_norm != display_norm:
            display_differs = True

    display_tuple = tuple(display_parts) if display_differs else None
    return tuple(key_parts), display_tuple


def _split_actual(part: str) -> tuple[str, str]:
    """Split one level into (sort, display) on the first unescaped '@'."""
    depth = 0
    escape = False
    for idx, ch in enumerate(part):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == "{":
            depth += 1
            continue
        if ch == "}":
            depth = max(0, depth - 1)
            continue
        if ch == "@" and depth == 0:
            return part[:idx], part[idx + 1 :]
    return part, part


def _parse_attr(attr: str | None) -> tuple[str | None, tuple[str, ...] | None]:
    if attr is None:
        return None, None
    attr = attr.strip()
    if not attr:
        return None, None
    # cross-reference like see{target}
    if "{" in attr and attr.endswith("}"):
        name, target = _split_command(attr)
        if target is not None:
            key, _display = _split_levels(target)
            return name, key
    return _normalize_token(attr), None


def _split_command(attr: str) -> tuple[str, str | None]:
    """Split ``cmd{arg}`` into (cmd, arg) handling escaped braces."""
    name: list[str] = []
    idx = 0
    while idx < len(attr) and (attr[idx].isalpha() or (attr[idx] in {"\\", ":"} and idx == 0)):
        name.append(attr[idx])
        idx += 1
    remaining = attr[idx:].lstrip()
    if not remaining.startswith("{"):
        return _normalize_token(attr), None
    try:
        body, _ = _read_braced(remaining, 0)
    except ValueError:
        return _normalize_token(attr), None
    cmd = "".join(name).lstrip("\\")
    return (cmd or _normalize_token(attr), body)


def _normalize_token(text: str) -> str:
    """Trim whitespace and unescape a handful of TeX separators."""
    if text is None:
        return ""
    text = text.strip()
    if text.startswith("\\relax"):
        text = text[len("\\relax") :].strip()
    # unescape makeindex separators
    text = (
        text.replace("\\!", "!")
        .replace("\\@", "@")
        .replace("\\|", "|")
        .replace("\\{", "{")
        .replace("\\}", "}")
    )
    text = text.replace("\\\\", "\\")
    return text


def _serialize_key(entry: RawIndexEntry) -> str:
    if entry.display_key and entry.display_key != entry.key:
        parts = []
        for sort, disp in zip(entry.key, entry.display_key, strict=False):
            parts.append(f'("{_escape(sort)}" "{_escape(disp)}")')
        return f":tkey ({' '.join(parts)})"
    return ':key ("' + '" "'.join(_escape(s) for s in entry.key) + '")'


if __name__ == "__main__":
    raise SystemExit(main())
