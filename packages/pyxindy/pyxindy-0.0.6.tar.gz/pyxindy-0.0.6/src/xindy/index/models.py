"""Data structures describing processed index entries."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from xindy.locref import LayeredLocationReference


@dataclass(slots=True)
class IndexEntry:
    """Represents a single index entry after applying style semantics."""

    key: tuple[str, ...]
    display_key: tuple[str, ...]
    canonical_key: tuple[str, ...]
    attribute: str | None
    position: int = 0
    locrefs: list[LayeredLocationReference] = field(default_factory=list)
    xref_target: tuple[str, ...] | None = None
    xref_verified: bool = True

    def add_location_reference(self, locref: LayeredLocationReference) -> None:
        self.locrefs.append(locref)


@dataclass(slots=True)
class IndexCrossReference:
    target: tuple[str, ...]
    attribute: str | None
    verified: bool = True


@dataclass(slots=True)
class IndexNode:
    """Node in the hierarchical index tree."""

    term: str
    key: tuple[str, ...]
    attribute: str | None = None
    locrefs: list[LayeredLocationReference] = field(default_factory=list)
    ranges: list[tuple[LayeredLocationReference, LayeredLocationReference]] = field(
        default_factory=list
    )
    children: list[IndexNode] = field(default_factory=list)
    crossrefs: list[IndexCrossReference] = field(default_factory=list)
    dropped_ordnums: dict[str | None, set[str]] = field(default_factory=dict)

    def add_child(self, node: IndexNode) -> None:
        self.children.append(node)

    def extend_locrefs(self, refs: list[LayeredLocationReference]) -> None:
        self.locrefs.extend(refs)

    def add_locrefs(self, refs: Iterable[LayeredLocationReference]) -> bool:
        added = False
        existing = {
            (ref.locref_string, ref.attribute, getattr(ref, "state", None)) for ref in self.locrefs
        }
        for ref in refs:
            signature = (ref.locref_string, ref.attribute, getattr(ref, "state", None))
            if signature in existing:
                continue
            self.locrefs.append(ref)
            existing.add(signature)
            added = True
        return added

    def add_crossref(
        self, target: tuple[str, ...], attribute: str | None, verified: bool = True
    ) -> None:
        self.crossrefs.append(
            IndexCrossReference(target=target, attribute=attribute, verified=verified)
        )


@dataclass(slots=True)
class IndexLetterGroup:
    label: str
    nodes: list[IndexNode]
    entry_count: int


@dataclass(slots=True)
class Index:
    groups: list[IndexLetterGroup]
    total_entries: int
    progress_markers: list[int]


__all__ = [
    "Index",
    "IndexCrossReference",
    "IndexEntry",
    "IndexLetterGroup",
    "IndexNode",
]
