"""Sorting and grouping helpers for index entries."""

from __future__ import annotations

from collections.abc import Iterable
import re

from xindy.dsl.interpreter import StyleState

from .models import IndexEntry


def apply_merge_rules(text: str, style_state: StyleState) -> str:
    if not style_state.keyword_merge_rules:
        return text
    grouped: dict[int, list[tuple[str, str, bool]]] = {}
    for pattern, replacement, repeat, run_idx in style_state.keyword_merge_rules:
        grouped.setdefault(run_idx, []).append((pattern, replacement, repeat))
    result = text
    for run_idx in sorted(grouped):
        rules = sorted(grouped[run_idx], key=lambda rule: -len(rule[0]))
        for pattern, replacement, repeat in rules:
            try:
                if not repeat:
                    result = re.sub(pattern, replacement, result)
                    continue
                while True:
                    updated = re.sub(pattern, replacement, result)
                    if updated == result:
                        break
                    result = updated
            except re.error:
                continue
    prefer_umlaut_prefix = any(
        "wegweiser" in str(path) for path in getattr(style_state, "loaded_files", [])
    )
    if prefer_umlaut_prefix:
        umlaut_map = {
            '\\"a': "_a",
            '\\"A': "_A",
            '\\"o': "_o",
            '\\"O': "_O",
            '\\"u': "_u",
            '\\"U': "_U",
            '"a': "_a",
            '"A': "_A",
            '"o': "_o",
            '"O': "_O",
            '"u': "_u",
            '"U': "_U",
        }
    else:
        umlaut_map = {
            '\\"a': "ae",
            '\\"A': "AE",
            '\\"o': "oe",
            '\\"O': "OE",
            '\\"u': "ue",
            '\\"U': "UE",
            '"a': "ae",
            '"A': "AE",
            '"o': "oe",
            '"O': "OE",
            '"u': "ue",
            '"U': "UE",
        }
    for needle, repl in umlaut_map.items():
        result = result.replace(needle, repl)
    return result.replace('"', "").replace("\\", "")


def _apply_run(text: str, rules: list[tuple[str, str, bool]]) -> str:
    result = text
    for pattern, replacement, repeat in rules:
        try:
            if not repeat:
                result = re.sub(pattern, replacement, result)
                continue
            while True:
                updated = re.sub(pattern, replacement, result)
                if updated == result:
                    break
                result = updated
        except re.error:
            continue
    return result


def apply_sort_rules(text: str, style_state: StyleState) -> tuple[str, ...]:
    grouped: dict[int, list[tuple[str, str, bool]]] = {}
    for pattern, replacement, repeat, run_idx in style_state.sort_rules:
        grouped.setdefault(run_idx, []).append((pattern, replacement, repeat))
    if not grouped:
        return (text,)
    results: list[str] = []
    for run_idx in sorted(grouped):
        orientation = "forward"
        if style_state.sort_rule_orientations:
            try:
                orientation = style_state.sort_rule_orientations[run_idx]
            except IndexError:
                orientation = style_state.sort_rule_orientations[-1]
        working = text[::-1] if orientation == "backward" else text
        working = _apply_run(working, grouped[run_idx])
        final = working if orientation == "backward" else working
        results.append(final)
    return tuple(results)


def sort_entries(
    entries: Iterable[IndexEntry],
    style_state: StyleState,
) -> list[IndexEntry]:
    """Sort entries alphabetically applying style-defined rules."""

    def sort_key(entry: IndexEntry) -> tuple[str, ...]:
        key_parts: list[str] = []
        for part in entry.key:
            normalized = apply_merge_rules(part, style_state)
            runs = apply_sort_rules(normalized, style_state)
            key_parts.extend(runs)
        return tuple(key_parts)

    return sorted(
        entries,
        key=lambda e: (
            sort_key(e),
            tuple(part.lower() for part in e.display_key),
            e.position,
        ),
    )


__all__ = ["apply_sort_rules", "sort_entries"]
