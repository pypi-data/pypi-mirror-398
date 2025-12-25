"""Utilities to build hierarchical index nodes from flat entries."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from xindy.locref import LayeredLocationReference

from .models import IndexEntry, IndexNode


def build_hierarchy(
    entries: Iterable[IndexEntry],
    allowed_range_attrs: Sequence[str] | None = None,
    suppress_covered_ranges: bool = False,
    enable_ranges: bool = True,
) -> list[IndexNode]:
    roots: list[IndexNode] = []
    range_allowed = set(allowed_range_attrs or [])
    allow_all_ranges = not range_allowed
    for entry in entries:
        if not entry.key:
            continue
        current_level = roots
        prefix: list[str] = []
        canon_prefix: list[str] = []
        node: IndexNode | None = None
        for token, canon_token in zip(entry.display_key, entry.canonical_key, strict=False):
            prefix.append(token)
            canon_prefix.append(canon_token)
            node = _find_or_create_node(current_level, token, tuple(canon_prefix))
            current_level = node.children
        if node:
            if entry.attribute and node.attribute is None:
                node.attribute = entry.attribute
            if entry.xref_target:
                node.add_crossref(
                    entry.xref_target,
                    entry.attribute,
                    getattr(entry, "xref_verified", True),
                )
                continue
            node.add_locrefs(entry.locrefs)
            # defer range detection to final sweep
    if enable_ranges:
        for node in roots:
            _finalize_ranges(node, range_allowed, allow_all_ranges, suppress_covered_ranges)
    return roots


def _find_or_create_node(
    nodes: list[IndexNode],
    term: str,
    key: tuple[str, ...],
) -> IndexNode:
    for node in nodes:
        if node.key == key:
            return node
    new_node = IndexNode(term=term, key=key)
    nodes.append(new_node)
    return new_node


def _detect_numeric_ranges(
    node: IndexNode,
    allowed_range_attrs: set[str],
    allow_all: bool,
    suppress_covered: bool,
) -> set[LayeredLocationReference]:
    node.ranges.clear()
    range_refs: set[LayeredLocationReference] = set()

    grouped: dict[
        tuple[str | None, str, tuple[str, ...]],
        list[LayeredLocationReference],
    ] = {}
    class_lookup: dict[tuple[str | None, str, tuple[str, ...]], LayeredLocationReference] = {}
    for ref in node.locrefs:
        prefix_layers: tuple[str, ...] = tuple(getattr(ref, "layers", ())[:-1])
        key = (ref.attribute, getattr(ref.locclass, "name", ""), prefix_layers)
        grouped.setdefault(key, []).append(ref)
        class_lookup[key] = ref.locclass

    for key, refs in grouped.items():
        attr, _, _ = key
        locclass = class_lookup[key]
        join_length = getattr(locclass, "join_length", 2)
        local_ranges: list[tuple[LayeredLocationReference, LayeredLocationReference]] = []
        refs_sorted = sorted(
            refs,
            key=lambda r: (
                _to_ordnum(r) if _to_ordnum(r) is not None else float("inf"),
                r.locref_string,
            ),
        )
        stack: list[LayeredLocationReference] = []
        covered: set[int] = set()
        remaining: list[LayeredLocationReference] = []
        for ref in refs_sorted:
            state = getattr(ref, "state", "normal")
            if state == "open-range":
                stack.append(ref)
                continue
            if state == "close-range":
                if stack:
                    start = stack.pop()
                    start_num = _to_ordnum(start)
                    end_num = _to_ordnum(ref)
                    if (
                        start_num is not None
                        and end_num is not None
                        and (allow_all or attr in allowed_range_attrs)
                        and abs(end_num - start_num) >= join_length
                    ):
                        local_ranges.append((start, ref))
                        range_refs.update({start, ref})
                        lower, upper = sorted((start_num, end_num))
                        covered.update(range(lower, upper + 1))
                        continue
                    start.state = "normal"
                    ref.state = "normal"
                    remaining.append(start)
                remaining.append(ref)
                continue
            remaining.append(ref)
        # unmatched opens are treated as normal references
        for leftover in stack:
            leftover.state = "normal"
        remaining.extend(stack)

        filtered: list[LayeredLocationReference] = []
        for ref in remaining:
            ordnum = _to_ordnum(ref)
            if ordnum is not None and ordnum in covered:
                continue
            filtered.append(ref)

        numeric = [
            (ref, _to_ordnum(ref))
            for ref in filtered
            if _to_ordnum(ref) is not None
            and getattr(ref, "state", "normal") not in ("open-range", "close-range")
            and (suppress_covered or not getattr(ref, "virtual", False))
        ]
        if numeric and (allow_all or attr in allowed_range_attrs):
            numeric.sort(key=lambda item: item[1])
            start_ref, start_val = numeric[0]
            prev_val = start_val
            run_refs: list[tuple[LayeredLocationReference, int | None]] = [(start_ref, start_val)]
            for ref, value in numeric[1:]:
                if value == prev_val:
                    run_refs.append((ref, value))
                    continue
                if value == prev_val + 1:
                    run_refs.append((ref, value))
                    prev_val = value
                    continue
                _emit_range_if_needed(run_refs, join_length, local_ranges, suppress_covered)
                run_refs = [(ref, value)]
                prev_val = value
            _emit_range_if_needed(run_refs, join_length, local_ranges, suppress_covered)

        merged = _merge_overlapping_ranges(local_ranges)
        node.ranges.extend(merged)
        range_refs.update({start for start, _ in merged})
        range_refs.update({end for _, end in merged})
    return range_refs


def _emit_range_if_needed(
    run_refs: list[tuple[LayeredLocationReference, int | None]],
    join_length: int,
    local_ranges: list[tuple[LayeredLocationReference, LayeredLocationReference]],
    suppress_covered: bool,
) -> None:
    run_len = len(run_refs)
    if run_len < 2:
        return
    start_ref, start_val = run_refs[0]
    end_ref, end_val = run_refs[-1]
    if start_val is None or end_val is None:
        return
    span = abs(end_val - start_val)
    if suppress_covered:
        if run_len >= join_length:
            if join_length <= 2 and span < join_length:
                return
            local_ranges.append((start_ref, end_ref))
    else:
        if run_len >= max(2, join_length):
            local_ranges.append((start_ref, end_ref))


def _merge_overlapping_ranges(
    ranges: list[tuple[LayeredLocationReference, LayeredLocationReference]],
) -> list[tuple[LayeredLocationReference, LayeredLocationReference]]:
    if len(ranges) < 2:
        return ranges
    numeric: list[tuple[int, int, LayeredLocationReference, LayeredLocationReference]] = []
    misc: list[tuple[LayeredLocationReference, LayeredLocationReference]] = []
    for start, end in ranges:
        start_num = _to_ordnum(start)
        end_num = _to_ordnum(end)
        if start_num is None or end_num is None:
            misc.append((start, end))
            continue
        if start_num > end_num:
            start_num, end_num, start, end = end_num, start_num, end, start
        numeric.append((start_num, end_num, start, end))
    numeric.sort(key=lambda item: item[0])
    merged: list[tuple[LayeredLocationReference, LayeredLocationReference]] = []
    current: tuple[int, int, LayeredLocationReference, LayeredLocationReference] | None = None
    for start_num, end_num, start_ref, end_ref in numeric:
        if current is None:
            current = (start_num, end_num, start_ref, end_ref)
            continue
        cur_start, cur_end, cur_start_ref, cur_end_ref = current
        if start_num <= cur_end + 1:
            if end_num > cur_end:
                current = (cur_start, end_num, cur_start_ref, end_ref)
            else:
                current = (cur_start, cur_end, cur_start_ref, cur_end_ref)
        else:
            merged.append((cur_start_ref, cur_end_ref))
            current = (start_num, end_num, start_ref, end_ref)
    if current:
        merged.append((current[2], current[3]))
    merged.extend(misc)
    return merged


def _apply_merge_filters(
    node: IndexNode,
    range_refs: set[LayeredLocationReference],
) -> None:
    sources_to_drop: set[LayeredLocationReference] = set()
    dropped_claims: dict[str | None, set[str]] = {}
    for start, end in node.ranges:
        for ref in (start, end):
            if getattr(ref, "virtual", False) and getattr(ref, "merge_drop", False):
                origin = getattr(ref, "origin", None)
                if origin is None:
                    continue
                span = _range_ordnum_span(start, end)
                if span:
                    low, high = span
                    attr_source = getattr(origin, "attribute", None)
                    for candidate in node.locrefs:
                        if candidate.attribute != attr_source:
                            continue
                        ordnum = _to_ordnum(candidate)
                        if ordnum is not None and low <= ordnum <= high:
                            sources_to_drop.add(candidate)
                            dropped_claims.setdefault(attr_source, set()).add(str(ordnum))
                sources_to_drop.add(origin)
                ord_origin = _to_ordnum(origin)
                if ord_origin is not None:
                    dropped_claims.setdefault(getattr(origin, "attribute", None), set()).add(
                        str(ord_origin)
                    )

    filtered_locrefs: list[LayeredLocationReference] = []
    for ref in node.locrefs:
        if getattr(ref, "virtual", False) and ref not in range_refs:
            continue
        if ref in sources_to_drop:
            continue
        filtered_locrefs.append(ref)
    node.locrefs = filtered_locrefs

    node.ranges = [
        (start, end)
        for start, end in node.ranges
        if start not in sources_to_drop and end not in sources_to_drop
    ]
    if dropped_claims:
        node.dropped_ordnums = dropped_claims


def _range_ordnum_span(
    start: LayeredLocationReference,
    end: LayeredLocationReference,
) -> tuple[int, int] | None:
    s_num = _to_ordnum(start)
    e_num = _to_ordnum(end)
    if s_num is None or e_num is None:
        return None
    low, high = sorted((s_num, e_num))
    return low, high


def _to_ordnum(ref: LayeredLocationReference) -> int | None:
    if ref.ordnums:
        try:
            return int(ref.ordnums[-1])
        except (TypeError, ValueError):
            return None
    try:
        return int(ref.locref_string)
    except (TypeError, ValueError):
        return None


def _finalize_ranges(
    node: IndexNode,
    allowed_range_attrs: set[str],
    allow_all: bool,
    suppress_covered_ranges: bool,
) -> None:
    range_refs = _detect_numeric_ranges(
        node, allowed_range_attrs, allow_all, suppress_covered_ranges
    )
    _apply_merge_filters(node, range_refs)
    for child in node.children:
        _finalize_ranges(child, allowed_range_attrs, allow_all, suppress_covered_ranges)


__all__ = ["build_hierarchy"]
