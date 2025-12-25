"""Bridge between raw entries and structured index data."""

from __future__ import annotations

from collections.abc import Iterable
import logging

from xindy.dsl.interpreter import StyleState
from xindy.index.order import apply_merge_rules
from xindy.locref import (
    CategoryAttribute,
    LayeredLocationClass,
    build_location_reference,
    make_category_attribute,
)
from xindy.raw.reader import RawIndexEntry

from .grouping import group_entries_by_letter
from .models import Index, IndexEntry


class IndexBuilderError(RuntimeError):
    """Raised when raw entries cannot be mapped to style constructs."""


logger = logging.getLogger(__name__)


def build_index_entries(
    raw_entries: Iterable[RawIndexEntry],
    style_state: StyleState,
    *,
    default_locclass: str | None = None,
    enable_ranges: bool = True,
) -> Index:
    """Convert raw entries into structured :class:`IndexEntry` objects."""
    locclasses = _resolve_location_classes(style_state, default_locclass)
    entries: list[IndexEntry] = []
    first_display_for_canon: dict[tuple[str, ...], tuple[str, ...]] = {}
    for idx, raw in enumerate(raw_entries):
        target_attrs = _expand_attributes(raw.attr, style_state)
        xref_target = _parse_xref_target(raw.extras.get("xref"))
        if xref_target is not None:
            try:
                xref_attr, xref_verified = _resolve_crossref_class(style_state, raw.attr)
            except IndexBuilderError as exc:
                logger.warning("Skipping crossref entry %s: %s", raw.key, exc)
                continue
            canonical_key = tuple(apply_merge_rules(part, style_state) for part in raw.key)
            if canonical_key not in first_display_for_canon:
                first_display_for_canon[canonical_key] = raw.display_key or raw.key
            entry = IndexEntry(
                key=raw.key,
                display_key=first_display_for_canon[canonical_key],
                canonical_key=canonical_key,
                attribute=xref_attr,
                xref_target=xref_target,
                xref_verified=xref_verified,
                position=idx,
            )
            entries.append(entry)
            continue
        if not target_attrs:
            logger.warning("Skipping entry %s: no target attributes resolved", raw.key)
            continue
        canonical_key = tuple(apply_merge_rules(part, style_state) for part in raw.key)
        if canonical_key not in first_display_for_canon:
            first_display_for_canon[canonical_key] = raw.display_key or raw.key
        entry = IndexEntry(
            key=raw.key,
            display_key=first_display_for_canon[canonical_key],
            canonical_key=canonical_key,
            attribute=target_attrs[0][0],
            position=idx,
        )
        if raw.locref is None:
            logger.warning("Skipping entry %s: missing :locref", raw.key)
            continue
        base_locref = None
        for target_attr, is_merge, drop in target_attrs:
            resolved_attr, catattr = _resolve_attribute(style_state, target_attr)
            if catattr is None:
                logger.warning("Skipping entry %s: no category attribute available", raw.key)
                base_locref = None
                break
            locref = None
            for loccls in locclasses:
                locref = build_location_reference(loccls, raw.locref, catattr, resolved_attr)
                if locref:
                    break
            if not locref:
                logger.warning(
                    "Skipping entry %s: could not build locref for %r", raw.key, raw.locref
                )
                base_locref = None
                break
            if "open-range" in raw.extras:
                locref.state = "open-range"
            if "close-range" in raw.extras:
                locref.state = "close-range"
            locref.attribute = resolved_attr
            if base_locref is None:
                base_locref = locref
            if is_merge:
                locref.virtual = True
                locref.merge_drop = drop
                locref.origin = base_locref
            entry.add_location_reference(locref)
        if base_locref is None and not entry.locrefs:
            logger.warning("Skipping entry %s: no valid location references", raw.key)
            continue
        entries.append(entry)
    grouped = group_entries_by_letter(entries, style_state, enable_ranges=enable_ranges)
    progress = _compute_progress_markers(len(entries))
    return Index(groups=grouped, total_entries=len(entries), progress_markers=progress)


def _resolve_location_class(
    style_state: StyleState,
    provided: str | None,
) -> LayeredLocationClass:
    if provided:
        loccls = style_state.location_classes.get(provided)
        if not loccls:
            raise IndexBuilderError(f"Unknown location class {provided!r}")
        return loccls
    if not style_state.location_classes:
        raise IndexBuilderError("No location classes defined in style")
    ordered = _ordered_locclasses(style_state)
    if not ordered:
        raise IndexBuilderError("No location classes resolved for style")
    return ordered[0]


def _resolve_location_classes(
    style_state: StyleState,
    provided: str | None,
) -> list[LayeredLocationClass]:
    if provided:
        return [_resolve_location_class(style_state, provided)]
    return _ordered_locclasses(style_state)


def _resolve_attribute(
    style_state: StyleState,
    attribute_name: str | None,
) -> tuple[str | None, CategoryAttribute | None]:
    name = attribute_name
    if name is None:
        name = _default_attribute_name(style_state)
    if name is None:
        return None, None
    catattr = style_state.attributes.get(name)
    if catattr is None:
        catattr = make_category_attribute(name)
        style_state.attributes[name] = catattr
        # basic ordering fallback when attribute was not declared explicitly
        catattr.catattr_grp_ordnum = len(style_state.attribute_groups) or 1
        catattr.sort_ordnum = len(style_state.attributes)
        catattr.processing_ordnum = catattr.sort_ordnum
        catattr.last_in_group = name
    return name, catattr


def _default_attribute_name(state: StyleState) -> str | None:
    if "default" in state.attributes:
        return "default"
    if state.attributes:
        return next(iter(state.attributes))
    return None


def _expand_attributes(
    attr_name: str | None,
    style_state: StyleState,
) -> list[tuple[str, bool, bool]]:
    """Return attributes to emit for a raw entry after merge-to rules.

    Each tuple is (attribute name, is_merged, drop_source_if_merged).
    """
    targets: list[tuple[str, bool, bool]] = []
    known_attrs = set(style_state.attributes)
    default_attr = _default_attribute_name(style_state)
    base_attr = attr_name or default_attr
    if base_attr is None:
        base_attr = "default"
    include_base = True
    if base_attr not in known_attrs:
        for source, _, drop in style_state.merge_rules:
            if base_attr == source and drop:
                include_base = False
                break
    if include_base:
        targets.append((base_attr, False, False))
    for source, target, drop in style_state.merge_rules:
        if base_attr == source:
            targets.append((target, True, drop))
    return targets


def _parse_xref_target(value: object | None) -> tuple[str, ...] | None:
    if value is None:
        return None
    if isinstance(value, list):
        if not value:
            return None
        return tuple(str(item) for item in value)
    if isinstance(value, str):
        return (value,)
    raise IndexBuilderError("Unsupported xref format")


def _compute_progress_markers(total_entries: int) -> list[int]:
    if total_entries == 0:
        return []
    markers = []
    for percent in range(10, 110, 10):
        markers.append(max(1, int(total_entries * (percent / 100))))
    return markers


def _resolve_crossref_class(
    style_state: StyleState,
    attr_name: str | None,
) -> tuple[str | None, bool]:
    name = attr_name
    if name is None and style_state.crossref_classes:
        name = next(iter(style_state.crossref_classes))
    if style_state.crossref_classes and name and name not in style_state.crossref_classes:
        raise IndexBuilderError(f"Unknown crossref class {name!r}")
    unverified = False
    if name:
        if style_state.crossref_classes:
            unverified = bool(style_state.crossref_classes.get(name, False))
        elif isinstance(name, str) and name.lower() == "unverified":
            unverified = True
    return name, not unverified


def _ordered_locclasses(style_state: StyleState) -> list[LayeredLocationClass]:
    """Return location classes honoring define-location-class-order if provided."""
    if not style_state.location_classes:
        return []
    ordered: list[LayeredLocationClass] = []
    seen: set[str] = set()
    for name in getattr(style_state, "location_class_order", []) or []:
        loccls = style_state.location_classes.get(name)
        if loccls and name not in seen:
            ordered.append(loccls)
            seen.add(name)
    for name, loccls in style_state.location_classes.items():
        if name in seen:
            continue
        ordered.append(loccls)
        seen.add(name)
    return ordered


__all__ = ["IndexBuilderError", "build_index_entries"]
