"""Letter grouping utilities."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
import re

from xindy.dsl.interpreter import StyleState

from .hierarchy import build_hierarchy
from .models import IndexEntry, IndexLetterGroup
from .order import apply_sort_rules, sort_entries


def group_entries_by_letter(
    entries: Iterable[IndexEntry],
    style_state: StyleState,
    *,
    enable_ranges: bool = True,
) -> list[IndexLetterGroup]:
    sorted_entries = sort_entries(entries, style_state)
    groups = _resolve_letter_groups(style_state)
    buckets: dict[str, list[IndexEntry]] = {label: [] for label in groups}
    extra_labels: list[str] = []
    fallback_label = groups[0] if groups else "#"
    for entry in sorted_entries:
        label = _letter_label_for_entry(entry, groups, style_state)
        if label not in buckets:
            buckets[label] = []
            extra_labels.append(label)
        buckets[label].append(entry)
    result: list[IndexLetterGroup] = []
    ordered_labels = list(groups) + extra_labels
    for label in ordered_labels:
        entries = buckets.get(label, [])
        nodes = build_hierarchy(
            entries,
            allowed_range_attrs=_range_attrs(style_state),
            suppress_covered_ranges=bool(style_state.markup_options),
            enable_ranges=enable_ranges,
        )
        if nodes:
            result.append(
                IndexLetterGroup(
                    label=label,
                    nodes=nodes,
                    entry_count=len(entries),
                )
            )
    if not result and sorted_entries:
        nodes = build_hierarchy(
            sorted_entries,
            allowed_range_attrs=_range_attrs(style_state),
            enable_ranges=enable_ranges,
        )
        result.append(
            IndexLetterGroup(
                label=fallback_label,
                nodes=nodes,
                entry_count=len(sorted_entries),
            )
        )
    return result


def _range_attrs(style_state: StyleState) -> list[str]:
    if style_state.attributes:
        return list(style_state.attributes.keys())
    return []


def _resolve_letter_groups(state: StyleState) -> list[str]:
    if state.letter_groups:
        return state.letter_groups
    # fallback to base alphabet of first basetype
    if state.basetypes:
        first = next(iter(state.basetypes.values()))
        return list(first.base_alphabet)
    return []


def _letter_label_for_entry(
    entry: IndexEntry,
    groups: Sequence[str],
    style_state: StyleState,
) -> str:
    text = ""
    if getattr(entry, "canonical_key", None):
        text = entry.canonical_key[0] if entry.canonical_key else ""
    elif entry.key:
        text = entry.key[0]
    if style_state and text:
        runs = apply_sort_rules(text, style_state)
        if runs:
            text = runs[0]
    normalized = re.sub(r"^[^0-9a-zA-Z]+", "", text.lower())
    if not normalized:
        normalized = text.lower()
    # prefer longest matching group prefix
    sorted_groups = sorted(groups, key=lambda g: (-len(g), groups.index(g)))
    for label in sorted_groups:
        if normalized.startswith(label.lower()):
            return label
    return groups[0] if groups else "#"


__all__ = ["group_entries_by_letter"]
