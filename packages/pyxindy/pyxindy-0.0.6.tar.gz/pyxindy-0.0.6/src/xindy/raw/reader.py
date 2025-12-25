"""Facilities to parse xindy .raw files into Python data structures."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path

from xindy.dsl.sexpr import Keyword, Symbol, loads


class RawIndexSyntaxError(ValueError):
    """Raised when a .raw file contains malformed data."""


@dataclass(slots=True)
class RawIndexEntry:
    """Representation of one ``(indexentry ...)`` S-expression."""

    key: tuple[str, ...]
    locref: str | None = None
    display_key: tuple[str, ...] | None = None
    attr: str | None = None
    extras: Mapping[str, object] = field(default_factory=dict)


def parse_raw_index(text: str) -> list[RawIndexEntry]:
    """Parse the contents of a raw index file provided as a string."""
    forms = loads(text)
    return [_entry_from_form(form) for form in forms]


def load_raw_index(path: str | PathLike[str]) -> list[RawIndexEntry]:
    """Read ``path`` and parse every index entry."""
    try:
        content = Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = Path(path).read_text(encoding="latin-1")
    return parse_raw_index(content)


def _entry_from_form(form: object) -> RawIndexEntry:
    if not isinstance(form, list) or not form:
        raise RawIndexSyntaxError("indexentry must be a non-empty list")
    head, *rest = form
    if not isinstance(head, Symbol) or head.name != "indexentry":
        raise RawIndexSyntaxError("Unsupported form; only indexentry is allowed")

    properties: dict[str, object] = {}
    idx = 0
    while idx < len(rest):
        key = rest[idx]
        if not isinstance(key, Keyword):
            raise RawIndexSyntaxError("indexentry properties must start with keywords")
        value: object = True
        if idx + 1 < len(rest) and not isinstance(rest[idx + 1], Keyword):
            value = rest[idx + 1]
            idx += 2
        else:
            idx += 1
        properties[key.name] = value

    key_prop = properties.get("key")
    display_key: tuple[str, ...] | None = None
    if key_prop is None and "tkey" in properties:
        key_prop = properties.get("tkey")
    key, display_key = _coerce_key(key_prop)
    locref = _coerce_optional_string(properties.get("locref"))
    attr = _coerce_optional_string(properties.get("attr"))
    extras = {
        name: value
        for name, value in properties.items()
        if name not in {"key", "tkey", "locref", "attr"}
    }
    return RawIndexEntry(
        key=key,
        display_key=display_key,
        locref=locref,
        attr=attr,
        extras=extras,
    )


def _coerce_key(value: object) -> tuple[tuple[str, ...], tuple[str, ...] | None]:
    if not isinstance(value, list) or not value:
        raise RawIndexSyntaxError(":key must be a non-empty list")
    coerced: list[str] = []
    display_parts: list[str] = []
    for part in value:
        if isinstance(part, list):
            if not part or not isinstance(part[0], str):
                raise RawIndexSyntaxError(":tkey entries must be string lists")
            coerced.append(part[0])
            display_parts.append(part[1] if len(part) > 1 and isinstance(part[1], str) else part[0])
        else:
            if not isinstance(part, str):
                raise RawIndexSyntaxError(":key entries must be strings")
            coerced.append(part)
            display_parts.append(part)
    display_key = (
        tuple(display_parts)
        if any((isinstance(part, list) and len(part) > 1) for part in value)
        else None
    )
    return tuple(coerced), display_key


def _coerce_optional_string(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise RawIndexSyntaxError("attribute values must be strings if provided")
    return value


__all__ = ["RawIndexEntry", "RawIndexSyntaxError", "load_raw_index", "parse_raw_index"]
