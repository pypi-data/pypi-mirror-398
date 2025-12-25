"""Simple textual renderer for the Python xindy index."""

from __future__ import annotations

from dataclasses import dataclass, field

from xindy.dsl.interpreter import StyleState
from xindy.index.models import Index, IndexNode


@dataclass(slots=True)
class LocrefFormat:
    prefix: str = ""
    open: str = ""
    close: str = ""
    separator: str = ", "


@dataclass(slots=True)
class LocrefListFormat:
    open: str = ""
    sep: str = ", "


@dataclass(slots=True)
class LocrefLayerFormat:
    open: str = ""
    close: str = ""


@dataclass(slots=True)
class RangeFormat:
    sep: str | None = None
    open: str = ""
    close: str = ""
    length: int | None = None
    ignore_end: bool = False


@dataclass(slots=True)
class MarkupConfig:
    show_letter_headers: bool = True
    letter_header_template: str = "{label}"
    letter_header_prefix: str = ""
    letter_header_suffix: str = ""
    letter_header_capitalize: bool = False
    index_open: str = ""
    index_close: str = ""
    letter_group_open: str = ""
    letter_group_close: str = ""
    letter_group_separator: str = ""
    attr_group_open: str = ""
    attr_group_sep: str = ""
    attribute_order: list[str] = field(default_factory=list)
    entry_indent: str = "  "
    entry_template: str = "{indent}{term}{locrefs}"
    entry_templates_by_depth: dict[int, str] = field(default_factory=dict)
    entry_list_open_templates: dict[int, str] = field(default_factory=dict)
    entry_list_close_templates: dict[int, str] = field(default_factory=dict)
    entry_open_templates: dict[int, str] = field(default_factory=dict)
    entry_close_templates: dict[int, str] = field(default_factory=dict)
    entry_separator: str = ""
    verbose: bool = False
    locref_formats: dict[str, LocrefFormat] = field(default_factory=dict)
    locref_list_formats: dict[str, dict[int, LocrefListFormat]] = field(default_factory=dict)
    locref_layer_formats: dict[str, dict[int, dict[int, LocrefLayerFormat]]] = field(
        default_factory=dict
    )
    default_locref_format: LocrefFormat = field(default_factory=LocrefFormat)
    locref_list_close: str = ""
    range_separator: str = "-"
    crossref_prefix: str = "see "
    crossref_suffix: str = ""
    crossref_separator: str = ", "
    crossref_layer_separator: str = ", "
    crossref_label_template: str | None = None
    crossref_unverified_suffix: str = ""
    enable_crossrefs: bool = True
    max_depth: int | None = None
    backend: str = "text"  # "text" or "tex"
    range_formats: dict[str, list[RangeFormat]] = field(default_factory=dict)


def render_index(
    index: Index,
    config: MarkupConfig | None = None,
    style_state: StyleState | None = None,
) -> str:
    cfg = config or (_config_from_style(style_state) if style_state else MarkupConfig())
    if style_state and "max_depth" in style_state.markup_options:
        cfg.max_depth = style_state.markup_options.get("max_depth")
    if cfg.backend == "tex" and cfg.entry_template == "{indent}{term}{locrefs}":
        cfg.entry_template = "{term}{locrefs}"
    lines: list[str] = []
    if cfg.index_open:
        open_str = cfg.index_open
        open_lines = open_str.splitlines()
        lines.extend(open_lines)
        if open_str.endswith("\n") and (not open_lines or open_lines[-1] != ""):
            lines.append("")
    for idx, group in enumerate(index.groups):
        label_text = (
            group.label.capitalize() if cfg.letter_header_capitalize else group.label.upper()
        )
        if (
            cfg.backend == "text"
            and cfg.letter_header_prefix
            and style_state
            and not style_state.letter_groups
            and idx == 0
        ):
            lines.append(f"{cfg.letter_header_prefix}A{cfg.letter_header_suffix}")
        if cfg.letter_group_open:
            lines.append(cfg.letter_group_open.format(label=group.label.upper()))
        if cfg.show_letter_headers:
            header = cfg.letter_header_template.format(label=label_text)
            prefix = cfg.letter_header_prefix
            if prefix.startswith("\n"):
                if not lines or lines[-1] != "":
                    lines.append("")
                prefix = prefix.lstrip("\n")
            lines.append(f"{prefix}{header}{cfg.letter_header_suffix}")
        _render_nodes(group.nodes, lines, cfg, depth=0, style_state=style_state)
        if cfg.letter_group_separator and idx != len(index.groups) - 1:
            sep_str = cfg.letter_group_separator
            lines.extend(sep_str.splitlines())
            if sep_str.endswith("\n"):
                lines.append("")
        if cfg.letter_group_close:
            lines.append(cfg.letter_group_close.format(label=group.label.upper()))
    if cfg.index_close:
        lines.extend(cfg.index_close.splitlines())
    output = "\n".join(lines).rstrip()
    return output + ("\n" if output else "")


def _render_node(
    node: IndexNode,
    lines: list[str],
    cfg: MarkupConfig,
    depth: int,
    style_state: StyleState | None,
) -> None:
    indent = cfg.entry_indent * depth
    locfmt = cfg.default_locref_format

    locref_part = _render_locref_part(node, cfg, locfmt, depth, style_state)
    crossref_parts: list[str] = []
    if cfg.enable_crossrefs:
        for crossref in node.crossrefs:
            refs = cfg.crossref_layer_separator.join(crossref.target)
            if cfg.crossref_label_template:
                template = cfg.crossref_label_template
                if "{target}" in template:
                    body = template.replace("{target}", refs)
                else:
                    body = f"{template}{refs}"
            else:
                body = f"{cfg.crossref_prefix}{refs}{cfg.crossref_suffix}"
            suffix = ""
            if not getattr(crossref, "verified", True):
                suffix = cfg.crossref_unverified_suffix
            crossref_parts.append(f"{body}{suffix}")
    template = cfg.entry_templates_by_depth.get(depth, cfg.entry_template)
    line = template.format(
        indent="" if cfg.entry_open_templates.get(depth) else indent,
        term=node.term,
        locrefs=locref_part,
        depth=depth,
    )
    if crossref_parts:
        sep = cfg.crossref_separator or " "
        if not locref_part and sep.lstrip().startswith(";"):
            sep = " "
        tail = (sep if sep.endswith(" ") else sep).join(crossref_parts)
        line = f"{line}{sep}{tail}"
    open_template = cfg.entry_open_templates.get(depth)
    close_template = cfg.entry_close_templates.get(depth)
    if open_template:
        if "{content}" in open_template:
            line = open_template.format(content=line, depth=depth)
        else:
            line = _normalize_markup_string(open_template) + line
    if close_template:
        if "{content}" in close_template:
            line = close_template.format(content=line, depth=depth)
        else:
            line = line + _normalize_markup_string(close_template)
    if cfg.verbose:
        line = f"[d={depth}] {line}"
    lines.append(line)
    next_depth = depth + 1
    if cfg.max_depth is not None and next_depth > cfg.max_depth:
        return
    _render_nodes(node.children, lines, cfg, depth=next_depth, style_state=style_state)


def _render_nodes(
    nodes: list[IndexNode],
    lines: list[str],
    cfg: MarkupConfig,
    depth: int,
    style_state: StyleState | None,
) -> None:
    if not nodes:
        return
    open_template = cfg.entry_list_open_templates.get(depth)
    if open_template:
        lines.append(open_template.format(depth=depth))
    for n_idx, node in enumerate(nodes):
        _render_node(node, lines, cfg, depth=depth, style_state=style_state)
        if cfg.entry_separator and n_idx != len(nodes) - 1:
            lines.append(cfg.entry_separator)
    close_template = cfg.entry_list_close_templates.get(depth)
    if close_template:
        lines.append(close_template.format(depth=depth))


def _render_locref_part(
    node: IndexNode,
    cfg: MarkupConfig,
    locfmt: LocrefFormat,
    depth: int,
    style_state: StyleState | None,
) -> str:
    if not node.locrefs and not node.ranges:
        return ""
    locrefs_by_key: dict[tuple[str, str | None], list[object]] = {}
    locclass_map: dict[str, object] = {}
    for ref in node.locrefs:
        class_name = getattr(ref.locclass, "name", "")
        locclass_map[class_name] = ref.locclass
        locrefs_by_key.setdefault((class_name, ref.attribute), []).append(ref)
    ranges_by_key: dict[tuple[str, str | None], list[tuple[object, object]]] = {}
    for start, end in node.ranges:
        class_name = getattr(start.locclass, "name", "")
        ranges_by_key.setdefault((class_name, start.attribute), []).append((start, end))

    # attribute order preference
    attr_order: list[str] = list(cfg.attribute_order)
    if style_state:
        if style_state.attribute_groups:
            attr_order = []
            for group in style_state.attribute_groups:
                attr_order.extend(group)
        elif style_state.attributes:
            ordered_attrs = sorted(
                style_state.attributes.values(),
                key=lambda cat: getattr(cat, "sort_ordnum", float("inf")),
            )
            attr_order = [cat.name for cat in ordered_attrs]

    parts: list[
        tuple[str | None, LocrefFormat, list[object], list[tuple[object, object]], object]
    ] = []
    for (class_name, attr), refs in locrefs_by_key.items():
        class_ranges = ranges_by_key.get((class_name, attr), [])
        locclass = locclass_map.get(class_name)
        override_fmt = cfg.locref_formats.get(attr) if attr else None
        fmt_base = _merge_locfmt(locfmt, override_fmt)
        parts.append((attr, fmt_base, refs, class_ranges, locclass))
    if not parts and node.ranges:
        for (class_name, attr), class_ranges in ranges_by_key.items():
            locclass = locclass_map.get(class_name)
            override_fmt = cfg.locref_formats.get(attr) if attr else None
            fmt_base = _merge_locfmt(locfmt, override_fmt)
            parts.append((attr, fmt_base, [], class_ranges, locclass))

    if not parts:
        return ""

    # order attributes if possible
    def sort_key(
        item: tuple[str | None, LocrefFormat, list[object], list[tuple[object, object]], object],
    ) -> tuple[float, int]:
        attr, _, refs, class_ranges, _ = item
        ordnums: list[float] = []
        for ref in refs:
            try:
                ordnums.append(float(ref.ordnums[0]))
            except Exception:
                continue
        for start, _end in class_ranges:
            try:
                ordnums.append(float(start.ordnums[0]))
            except Exception:
                continue
        min_ord = min(ordnums) if ordnums else float("inf")
        if attr is None:
            attr_index = len(attr_order) + 1
        elif attr in attr_order:
            attr_index = attr_order.index(attr)
        else:
            attr_index = len(attr_order)
        return (min_ord, attr_index)

    parts.sort(key=sort_key)
    # map attributes to groups
    attr_group_map: dict[str | None, int] = {}
    if style_state:
        for idx, group in enumerate(style_state.attribute_groups):
            for attr in group:
                attr_group_map[attr] = idx

    suppress_covered = bool(style_state and style_state.markup_options)
    per_item_format = bool(style_state and "range" in style_state.markup_options)
    dropped_claims = getattr(node, "dropped_ordnums", {}) or {}
    priority = list(attr_order)
    for attr, *_ in parts:
        if attr not in priority:
            priority.append(attr)
    allowed_by_attr: dict[
        str | None, tuple[list[object], list[tuple[object, object]], set[int]]
    ] = {}
    claimed_by_group: dict[int, set[str]] = {}
    for attr in priority:
        segment = next((p for p in parts if p[0] == attr), None)
        group_id = attr_group_map.get(attr, -1)
        claimed = claimed_by_group.setdefault(group_id, set())
        extra_claims = dropped_claims.get(attr)
        if extra_claims:
            claimed.update(extra_claims)
        if not segment:
            claimed_by_group[group_id] = claimed
            continue
        _, _, refs, class_ranges, _ = segment
        filtered_refs = [r for r in refs if r.locref_string not in claimed]
        unique_refs: list[object] = []
        seen_strings: set[str] = set()
        for r in filtered_refs:
            if r.locref_string in seen_strings:
                continue
            seen_strings.add(r.locref_string)
            unique_refs.append(r)
        filtered_refs = unique_refs
        filtered_ranges = []
        covered: set[int] = set()
        for start, end in class_ranges:
            if start.locref_string in claimed or end.locref_string in claimed:
                continue
            filtered_ranges.append((start, end))
            # claim all ordnums in range
            try:
                s_ord = int(getattr(start, "ordnums", [None])[0])
                e_ord = int(getattr(end, "ordnums", [None])[0])
                if s_ord > e_ord:
                    s_ord, e_ord = e_ord, s_ord
                for val in range(s_ord, e_ord + 1):
                    claimed.add(str(val))
                    covered.add(val)
            except (TypeError, ValueError):
                pass
        for r in filtered_refs:
            claimed.add(r.locref_string)
        claimed_by_group[group_id] = claimed
        allowed_by_attr[attr] = (filtered_refs, filtered_ranges, covered)

    dropped_claims = getattr(node, "dropped_ordnums", {}) if node else {}
    attr_order_map = {attr: idx for idx, attr in enumerate(priority)}
    part_lookup = {
        attr: (fmt_base, class_ranges, locclass)
        for attr, fmt_base, _, class_ranges, locclass in parts
    }
    if style_state and style_state.attribute_groups:
        group_list = style_state.attribute_groups
    else:
        group_list = [[attr] for attr in priority]

    all_items: list[str] = []
    global_separator: str | None = None
    for group_attrs in group_list:
        items: list[tuple[tuple[float, int], str]] = []
        separator: str | None = None
        for attr in group_attrs:
            segment = part_lookup.get(attr)
            if not segment:
                continue
            fmt_base, class_ranges, locclass = segment
            refs_filtered, ranges_filtered, covered = allowed_by_attr.get(attr, ([], [], set()))
            if separator is None:
                separator = cfg.attr_group_sep or fmt_base.separator
            attr_idx = attr_order_map.get(attr, len(attr_order_map))
            hierdepth = getattr(locclass, "hierdepth", 0) or 0
            if hierdepth > 1:
                content = _format_locrefs_for_class(
                    refs_filtered,
                    ranges_filtered,
                    locclass,
                    cfg,
                    depth,
                    fmt_base,
                    per_item_format,
                )
                if content:
                    ord_candidates = [_loc_ordnum(ref) for ref in refs_filtered] + [
                        _loc_ordnum(start) for start, _ in ranges_filtered
                    ]
                    ord_candidates = [o for o in ord_candidates if o is not None]
                    ordnum = min(ord_candidates) if ord_candidates else float("inf")
                    items.append(((ordnum, attr_idx, 0), content))
                continue
            attr_items: list[tuple[tuple[float, int], str]] = []
            for start, end in ranges_filtered:
                ordnum_raw = _loc_ordnum(start)
                ordnum = ordnum_raw if suppress_covered else float("inf")
                key = (ordnum if ordnum is not None else float("inf"), attr_idx, 1)
                class_name = getattr(locclass, "name", "__default__")
                range_fmt = _select_range_format(cfg, class_name, start, end)
                text = _format_range_value(start, end, fmt_base, cfg, per_item_format, range_fmt)
                attr_items.append((key, text))
            for ref in refs_filtered:
                ordnum = _loc_ordnum(ref)
                if suppress_covered and covered and ordnum is not None and ordnum in covered:
                    continue
                key = (ordnum if ordnum is not None else float("inf"), attr_idx, 0)
                if per_item_format:
                    text = f"{fmt_base.open}{ref.locref_string}{fmt_base.close}"
                else:
                    text = ref.locref_string
                attr_items.append((key, text))
            if not attr_items:
                continue
            attr_items.sort(key=lambda item: item[0])
            if not suppress_covered:
                ref_items = [it for it in attr_items if it[0][2] == 0]
                range_items = [it for it in attr_items if it[0][2] == 1]
                attr_items = ref_items + range_items
            if per_item_format:
                # prefix applied after global sort
                pass
            else:
                open_token = fmt_base.open or ""
                close_token = fmt_base.close or ""
                if cfg.backend == "tex":
                    if open_token or close_token:
                        attr_items = [
                            (key, f"{open_token}{text}{close_token}") for key, text in attr_items
                        ]
                else:
                    if open_token or close_token:
                        key_first, text_first = attr_items[0]
                        attr_items[0] = (key_first, f"{open_token}{text_first}")
                        key_last, text_last = attr_items[-1]
                        attr_items[-1] = (key_last, f"{text_last}{close_token}")
            items.extend(attr_items)
        if not items:
            continue
        items.sort(key=lambda item: item[0])
        if separator is None:
            separator = cfg.attr_group_sep or cfg.default_locref_format.separator
        if global_separator is None:
            global_separator = separator
        all_items.extend(text for _, text in items)
    if not all_items:
        return ""
    prefix_token = locfmt.prefix or cfg.default_locref_format.prefix
    if prefix_token and not all_items[0].startswith(prefix_token):
        all_items[0] = prefix_token + all_items[0]
    spacer = ""
    if cfg.backend == "text" and not cfg.attr_group_open:
        spacer = "" if all_items and all_items[0].startswith(" ") else " "
    sep = cfg.attr_group_sep or global_separator or locfmt.separator
    body = sep.join(all_items)
    if cfg.attr_group_open:
        body = cfg.attr_group_open + body
    if cfg.locref_list_close and not body.endswith(cfg.locref_list_close):
        body = body + cfg.locref_list_close
    return spacer + body


def _format_locrefs_for_class(
    refs: list[object],
    ranges: list[tuple[object, object]],
    locclass: object,
    cfg: MarkupConfig,
    depth: int,
    fmt: LocrefFormat,
    per_item_format: bool,
) -> str:
    orig_refs = list(refs)
    hierdepth = getattr(locclass, "hierdepth", 0) or 0
    class_name = getattr(locclass, "name", "__default__")

    # stable sort by ordnum if available, otherwise by locref string
    def ref_key(ref: object) -> tuple[int, str]:
        ordnum = None
        try:
            ordnum = int(getattr(ref, "ordnums", [None])[0])
        except (TypeError, ValueError):
            ordnum = None
        return (ordnum if ordnum is not None else float("inf"), getattr(ref, "locref_string", ""))

    refs = sorted(refs, key=ref_key)
    ranges = sorted(ranges, key=lambda pair: ref_key(pair[0]))
    if ranges and cfg.backend == "tex":
        covered_ordnums: set[int] = set()
        for start, end in ranges:
            try:
                start_num = int(getattr(start, "ordnums", [None])[0])
                end_num = int(getattr(end, "ordnums", [None])[0])
            except (TypeError, ValueError):
                continue
            if start_num is None or end_num is None:
                continue
            if start_num > end_num:
                start_num, end_num = end_num, start_num
            covered_ordnums.update(range(start_num, end_num + 1))
        if covered_ordnums:
            refs = [
                ref
                for ref in refs
                if int(getattr(ref, "ordnums", [None])[0] or -1) not in covered_ordnums
            ]
    if hierdepth > 1:
        body = _format_hierarchical_locrefs(
            refs,
            ranges,
            locclass,
            cfg,
            depth,
        )
        if fmt.prefix or fmt.open or fmt.close:
            return f"{fmt.prefix}{fmt.open}{body}{fmt.close}"
        return body
    separator = fmt.separator
    wrap = (
        (lambda val: f"{fmt.open}{val}{fmt.close}")
        if (fmt.open or fmt.close)
        else (lambda val: val)
    )
    if cfg.backend == "text":

        def ord_or_inf(ref: object) -> int | float:
            try:
                return int(getattr(ref, "ordnums", [None])[0])
            except (TypeError, ValueError):
                return float("inf")

        covered: set[int] = set()
        items: list[tuple[int | float, str]] = []
        for start, end in ranges:
            s = ord_or_inf(start)
            e = ord_or_inf(end)
            if s == float("inf") or e == float("inf"):
                continue
            if s > e:
                s, e = e, s
            covered.update(range(int(s), int(e) + 1))
            range_fmt = _select_range_format(cfg, class_name, start, end)
            items.append(
                (
                    s,
                    _format_range_value(
                        start,
                        end,
                        fmt,
                        cfg,
                        per_item_format,
                        range_fmt,
                    ),
                )
            )
        for ref in orig_refs:
            ordnum = ord_or_inf(ref)
            if covered and isinstance(ordnum, int) and ordnum in covered:
                continue
            items.append((ordnum, wrap(ref.locref_string)))
        items.sort(key=lambda item: item[0])
        joined = separator.join(val for _, val in items)
        return f"{fmt.prefix}{joined}"
    items: list[tuple[int | float, str]] = []
    covered: set[int] = set()
    for start, end in ranges:
        try:
            s = int(start.ordnums[0]) if start.ordnums else None
            e = int(end.ordnums[0]) if end.ordnums else None
        except (TypeError, ValueError):
            s = e = None
        if s is not None and e is not None:
            if s > e:
                s, e = e, s
            covered.update(range(s, e + 1))
            range_fmt = _select_range_format(cfg, class_name, start, end)
            items.append(
                (
                    s,
                    _format_range_value(
                        start,
                        end,
                        fmt,
                        cfg,
                        per_item_format,
                        range_fmt,
                    ),
                )
            )
    for ref in orig_refs:
        try:
            ordnum = int(ref.ordnums[0]) if ref.ordnums else None
        except (TypeError, ValueError):
            ordnum = None
        if cfg.backend == "tex" and covered and ordnum is not None and ordnum in covered:
            continue
        items.append((ordnum if ordnum is not None else float("inf"), wrap(ref.locref_string)))
    items.sort(key=lambda item: item[0] if item[0] is not None else float("inf"))
    joined = separator.join(val for _, val in items)
    return f"{fmt.prefix}{joined}"


def _format_range_value(
    start: object,
    end: object,
    fmt: LocrefFormat,
    cfg: MarkupConfig,
    per_item_format: bool,
    range_fmt: RangeFormat | None,
) -> str:
    if range_fmt:
        sep = range_fmt.sep or cfg.range_separator
        start_val = start.locref_string
        end_val = end.locref_string
        if per_item_format and not (range_fmt.open or range_fmt.close) and (fmt.open or fmt.close):
            start_val = f"{fmt.open}{start_val}{fmt.close}"
            end_val = f"{fmt.open}{end_val}{fmt.close}"
        core = start_val if range_fmt.ignore_end else f"{start_val}{sep}{end_val}"
        if range_fmt.open or range_fmt.close:
            return f"{range_fmt.open or ''}{core}{range_fmt.close or ''}"
        return core

    sep = cfg.range_separator
    open_token = ""
    close_token = ""
    if per_item_format:
        open_token = fmt.open
        close_token = fmt.close
    if open_token or close_token:
        start_val = f"{open_token}{start.locref_string}{close_token}"
        end_val = f"{open_token}{end.locref_string}{close_token}"
    else:
        start_val = start.locref_string
        end_val = end.locref_string
    return f"{start_val}{sep}{end_val}"


def _range_length(start: object, end: object) -> int | None:
    start_ord = _loc_ordnum(start)
    end_ord = _loc_ordnum(end)
    if start_ord is None or end_ord is None:
        return None
    return abs(end_ord - start_ord)


def _select_range_format(
    cfg: MarkupConfig, class_name: str, start: object, end: object
) -> RangeFormat | None:
    formats = cfg.range_formats.get(class_name) or cfg.range_formats.get("__default__")
    if not formats:
        return None
    length = _range_length(start, end)
    fallback: RangeFormat | None = None
    for fmt in formats:
        if fmt.length is None:
            fallback = fallback or fmt
            continue
        if length is not None and length == fmt.length:
            return fmt
    return fallback


def _loc_ordnum(ref: object) -> int | None:
    try:
        ordnums = getattr(ref, "ordnums", None)
        if ordnums:
            return int(ordnums[-1])
    except (TypeError, ValueError):
        return None
    try:
        return int(getattr(ref, "locref_string", None))
    except (TypeError, ValueError):
        return None


def _format_hierarchical_locrefs(
    refs: list[object],
    ranges: list[tuple[object, object]],
    locclass: object,
    cfg: MarkupConfig,
    depth: int,
) -> str:
    class_name = getattr(locclass, "name", "__default__")
    hierdepth = getattr(locclass, "hierdepth", 0) or 0
    if hierdepth < 2:
        return cfg.default_locref_format.separator.join(ref.locref_string for ref in refs)
    groups: dict[tuple[str, ...], list[str]] = {}
    for ref in refs:
        layers = ref.layers or (ref.locref_string,)
        if len(layers) < hierdepth:
            prefix = tuple(layers[:-1])
            value = layers[-1]
        else:
            prefix = tuple(layers[: hierdepth - 1])
            value = layers[hierdepth - 1]
        groups.setdefault(prefix, []).append(value)
    for start, end in ranges:
        layers = start.layers or (start.locref_string,)
        if len(layers) < hierdepth:
            prefix = tuple(layers[:-1])
            start_val = layers[-1]
            end_val = start_val
        else:
            prefix = tuple(layers[: hierdepth - 1])
            start_val = layers[hierdepth - 1]
            end_layers = end.layers or (end.locref_string,)
            end_val = end_layers[hierdepth - 1] if len(end_layers) >= hierdepth else end_layers[-1]
        groups.setdefault(prefix, []).append(f"{start_val}{cfg.range_separator}{end_val}")

    rendered_groups: list[str] = []
    for prefix_layers in sorted(groups):
        values = groups[prefix_layers]
        min_len = getattr(locclass, "join_length", 2)
        collapsed = _collapse_layer_values(values, cfg.range_separator, min_len)
        value_fmt = _get_locref_list_format(cfg, class_name, 1)
        sep = value_fmt.sep if value_fmt else cfg.default_locref_format.separator
        formatted_values = [
            _apply_layer_format(
                val,
                cfg,
                class_name,
                depth,
                hierdepth - 1,
            )
            for val in collapsed
        ]
        tail = sep.join(formatted_values)
        if value_fmt and value_fmt.open:
            tail = f"{value_fmt.open}{tail}"
        prefix_rendered = "-".join(
            _apply_layer_format(
                layer_val,
                cfg,
                class_name,
                depth,
                idx,
            )
            for idx, layer_val in enumerate(prefix_layers)
        )
        group_str = f"{prefix_rendered}{tail}"
        rendered_groups.append(group_str)
    list_fmt = _get_locref_list_format(cfg, class_name, 0)
    outer_sep = list_fmt.sep if list_fmt else cfg.default_locref_format.separator
    body = outer_sep.join(rendered_groups)
    if list_fmt and list_fmt.open:
        body = f"{list_fmt.open}{body}"
    return body


def _collapse_layer_values(
    values: list[str],
    range_sep: str,
    min_length: int,
) -> list[str]:
    ints: list[int] = []
    try:
        ints = sorted({int(val) for val in values})
    except ValueError:
        return values
    if not ints:
        return values
    collapsed: list[str] = []
    start = prev = ints[0]
    run_length = 1
    for num in ints[1:]:
        if num == prev + 1:
            prev = num
            run_length += 1
            continue
        if run_length >= min_length:
            collapsed.append(f"{start}{range_sep}{prev}")
        else:
            collapsed.extend(str(n) for n in range(start, prev + 1))
        start = prev = num
        run_length = 1
    if run_length >= min_length:
        collapsed.append(f"{start}{range_sep}{prev}")
    else:
        collapsed.extend(str(n) for n in range(start, prev + 1))
    return collapsed


def _apply_layer_format(
    value: str,
    cfg: MarkupConfig,
    class_name: str,
    depth: int,
    layer_idx: int,
) -> str:
    fmt = _get_locref_layer_format(cfg, class_name, depth, layer_idx)
    if not fmt:
        return value
    return f"{fmt.open}{value}{fmt.close}"


def _get_locref_list_format(
    cfg: MarkupConfig,
    class_name: str,
    depth: int,
) -> LocrefListFormat | None:
    # locref_class markup overrides list formatting for a specific class
    class_fmt = cfg.locref_list_formats.get(class_name)
    if class_fmt and depth in class_fmt:
        return class_fmt[depth]
    class_fmt = cfg.locref_list_formats.get("__default__")
    if class_fmt and depth in class_fmt:
        return class_fmt[depth]
    return cfg.locref_list_formats.get(class_name, {}).get(depth) or cfg.locref_list_formats.get(
        "__default__", {}
    ).get(depth)


def _get_locref_layer_format(
    cfg: MarkupConfig,
    class_name: str,
    depth: int,
    layer_idx: int,
) -> LocrefLayerFormat | None:
    depth_map = cfg.locref_layer_formats.get(class_name) or cfg.locref_layer_formats.get(
        "__default__"
    )
    if not depth_map:
        return None
    return depth_map.get(depth, {}).get(layer_idx)


def _merge_locfmt(base: LocrefFormat, override: LocrefFormat | None) -> LocrefFormat:
    if override is None:
        return base
    return LocrefFormat(
        prefix=override.prefix or base.prefix,
        open=override.open or base.open,
        close=override.close or base.close,
        separator=override.separator or base.separator,
    )


def _config_from_style(style_state: StyleState) -> MarkupConfig:
    cfg = MarkupConfig()
    cfg.show_letter_headers = bool(style_state.letter_groups)
    opts = style_state.markup_options
    if style_state.attribute_groups:
        for group in style_state.attribute_groups:
            cfg.attribute_order.extend(group)
    elif style_state.attributes:
        cfg.attribute_order.extend(style_state.attributes.keys())

    index_opts = opts.get("index", {})
    cfg.index_open = _normalize_markup_string(index_opts.get("open", cfg.index_open))
    close_val = _normalize_markup_string(index_opts.get("close", cfg.index_close))
    if close_val:
        close_val = "\n" + close_val.lstrip("\n")
        close_val = close_val.rstrip("\n")
    cfg.index_close = close_val
    if "\\begin{theindex}" in cfg.index_open:
        cfg.backend = "tex"

    letter_group_opts = opts.get("letter_group", {})
    lg_opts = opts.get("letter_group_list", {})
    separator = _normalize_markup_string(lg_opts.get("sep", cfg.letter_group_separator))
    if separator:
        separator = "\n" + separator.lstrip("\n")
        separator = separator.rstrip("\n") + "\n"
    cfg.letter_group_separator = separator
    cfg.letter_group_open = _normalize_markup_string(lg_opts.get("open", cfg.letter_group_open))
    cfg.letter_group_close = _normalize_markup_string(lg_opts.get("close", cfg.letter_group_close))
    if letter_group_opts:
        cfg.show_letter_headers = True
        group_open = _normalize_markup_string(letter_group_opts.get("open", ""))
        cfg.letter_header_prefix = _normalize_markup_string(
            letter_group_opts.get("open_head", cfg.letter_header_prefix)
        )
        cfg.letter_header_suffix = _normalize_markup_string(
            letter_group_opts.get("close_head", cfg.letter_header_suffix)
        )
        if group_open:
            cfg.letter_header_prefix = group_open + cfg.letter_header_prefix
        group_close = _normalize_markup_string(letter_group_opts.get("close", ""))
        if group_close:
            cfg.letter_header_suffix = cfg.letter_header_suffix + group_close
        if letter_group_opts.get("capitalize"):
            cfg.letter_header_capitalize = True
    elif lg_opts:
        # if no explicit header, do not emit headers
        cfg.show_letter_headers = False
    attr_group_opts = opts.get("attribute_group_list", {})
    if attr_group_opts:
        cfg.attr_group_open = _normalize_markup_string(
            attr_group_opts.get("open", cfg.attr_group_open)
        )
        cfg.attr_group_sep = _normalize_markup_string(
            attr_group_opts.get("sep", cfg.attr_group_sep)
        )

    entry_list_opts = opts.get("indexentry_list", {})
    if "sep" in entry_list_opts:
        cfg.entry_separator = _normalize_markup_string(entry_list_opts["sep"])
        if cfg.entry_separator == "\n":
            cfg.entry_separator = ""
    if "open" in entry_list_opts:
        cfg.entry_list_open_templates[0] = _normalize_markup_string(entry_list_opts["open"])
    if "close" in entry_list_opts:
        cfg.entry_list_close_templates[0] = _normalize_markup_string(entry_list_opts["close"])

    entries = opts.get("indexentries", {})
    for depth, entry_cfg in entries.items():
        if "open" in entry_cfg:
            open_val = _normalize_markup_string(entry_cfg["open"]).lstrip("\n")
            cfg.entry_open_templates[depth] = open_val
        if "close" in entry_cfg:
            close_val = _normalize_markup_string(entry_cfg["close"]).rstrip("\n")
            cfg.entry_close_templates[depth] = close_val
        if "template" in entry_cfg:
            cfg.entry_templates_by_depth[depth] = entry_cfg["template"]
        elif cfg.backend == "tex":
            cfg.entry_templates_by_depth[depth] = "{term}{locrefs}"

    locref_opts = opts.get("locref", {})
    default_locref = locref_opts.get("__default__", {})
    cfg.default_locref_format = _update_locfmt(
        cfg.default_locref_format,
        default_locref,
    )
    for attr, raw_cfg in locref_opts.items():
        if attr == "__default__":
            continue
        cfg.locref_formats[attr] = _update_locfmt(LocrefFormat(), raw_cfg)

    locref_lists = opts.get("locref_lists", {})
    for class_name, depth_map in locref_lists.items():
        for depth, raw_cfg in depth_map.items():
            fmt = LocrefListFormat()
            if "open" in raw_cfg:
                fmt.open = _normalize_markup_string(raw_cfg["open"])
            if "sep" in raw_cfg:
                fmt.sep = _normalize_markup_string(raw_cfg["sep"])
            cfg.locref_list_formats.setdefault(class_name, {})[int(depth)] = fmt
    default_list_fmt = cfg.locref_list_formats.get("__default__", {}).get(0)
    if default_list_fmt and default_list_fmt.sep:
        cfg.default_locref_format.separator = default_list_fmt.sep

    locref_list = opts.get("locref_list", {})
    if locref_list.get("sep"):
        cfg.default_locref_format.separator = locref_list["sep"]
    locclass_list = opts.get("locclass_list", {})
    if locclass_list.get("open"):
        cfg.default_locref_format.prefix = _normalize_markup_string(locclass_list["open"])
    if locclass_list.get("close"):
        cfg.locref_list_close = _normalize_markup_string(locclass_list["close"])
    locref_class_opts = opts.get("locref_class", {})
    for class_name, raw_cfg in locref_class_opts.items():
        fmt = LocrefListFormat()
        if "open" in raw_cfg:
            fmt.open = _normalize_markup_string(raw_cfg["open"])
        if "sep" in raw_cfg:
            fmt.sep = _normalize_markup_string(raw_cfg["sep"])
        cfg.locref_list_formats.setdefault(class_name, {})[0] = fmt

    locref_layers = opts.get("locref_layers", {})
    for class_name, depth_map in locref_layers.items():
        for depth, layer_map in depth_map.items():
            depth_fmt = cfg.locref_layer_formats.setdefault(class_name, {})
            layer_fmt = depth_fmt.setdefault(int(depth), {})
            for layer_idx, raw_cfg in layer_map.items():
                layer_fmt[int(layer_idx)] = LocrefLayerFormat(
                    open=_normalize_markup_string(raw_cfg.get("open", "")),
                    close=_normalize_markup_string(raw_cfg.get("close", "")),
                )

    crossref_opts = opts.get("crossref_list", {})
    if "open" in crossref_opts:
        cfg.crossref_prefix = crossref_opts["open"]
    if "sep" in crossref_opts:
        cfg.crossref_separator = crossref_opts["sep"]
    if "close" in crossref_opts:
        cfg.crossref_suffix = crossref_opts["close"]
    if "open" in crossref_opts or "close" in crossref_opts:
        cfg.crossref_label_template = None
    layer_opts = opts.get("crossref_layer_list", {})
    if "sep" in layer_opts:
        cfg.crossref_layer_separator = layer_opts["sep"]

    range_opts_raw = opts.get("range", {})
    range_map: dict[str, list[dict[str, object]]] = {}
    if range_opts_raw:
        # Newer handler stores ranges per class; older styles may provide a flat dict
        if isinstance(range_opts_raw, dict) and any(
            isinstance(val, list) for val in range_opts_raw.values()
        ):
            range_map = {key: list(val) for key, val in range_opts_raw.items()}
        else:
            range_map = {"__default__": [range_opts_raw]}

    for class_name, formats in range_map.items():
        parsed: list[RangeFormat] = []
        for raw_cfg in formats:
            sep_val = raw_cfg.get("sep") if isinstance(raw_cfg, dict) else None
            sep_norm = _normalize_markup_string(sep_val) if sep_val is not None else None
            open_val = (
                _normalize_markup_string(raw_cfg.get("open", ""))
                if isinstance(raw_cfg, dict)
                else ""
            )
            close_val = (
                _normalize_markup_string(raw_cfg.get("close", ""))
                if isinstance(raw_cfg, dict)
                else ""
            )
            length_val = raw_cfg.get("length") if isinstance(raw_cfg, dict) else None
            try:
                length_int = int(length_val) if length_val is not None else None
            except (ValueError, TypeError):
                length_int = None
            parsed.append(
                RangeFormat(
                    sep=sep_norm or None,
                    open=open_val,
                    close=close_val,
                    length=length_int,
                    ignore_end=bool(raw_cfg.get("ignore_end"))
                    if isinstance(raw_cfg, dict)
                    else False,
                )
            )
        cfg.range_formats[class_name] = parsed
    if "__default__" in cfg.range_formats:
        for fmt in cfg.range_formats["__default__"]:
            if fmt.sep:
                cfg.range_separator = fmt.sep
                break

    return cfg


def _update_locfmt(locfmt: LocrefFormat, data: dict[str, object]) -> LocrefFormat:
    if "sep" in data:
        locfmt.separator = data["sep"]
    if "open" in data:
        locfmt.open = data["open"]
    if "close" in data:
        locfmt.close = data["close"]
    if "prefix" in data:
        locfmt.prefix = data["prefix"]
    return locfmt


def _normalize_markup_string(value: object | None) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        result = value.replace("~n", "\n")
        while "~~" in result:
            result = result.replace("~~", "~")
        return result
    return str(value)


def _wrap_tex(body: str) -> str:
    return "\\begin{theindex}\n\n" + body + "\n\n\\end{theindex}"


__all__ = ["MarkupConfig", "render_index"]
