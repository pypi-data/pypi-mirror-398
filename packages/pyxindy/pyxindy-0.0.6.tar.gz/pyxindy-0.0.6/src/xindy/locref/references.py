"""Location reference dataclasses and helpers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from .classes import LayeredLocationClass, LocationMatchError, perform_match


@dataclass(slots=True)
class CategoryAttribute:
    name: str
    catattr_grp_ordnum: int = 0
    sort_ordnum: int = 0
    processing_ordnum: int = 0
    last_in_group: str | None = None
    type: str | None = None
    markup: str | None = None


@dataclass(slots=True)
class LocationReference:
    locclass: LayeredLocationClass
    attribute: str | None


@dataclass(slots=True, eq=False)
class LayeredLocationReference(LocationReference):
    layers: tuple[str, ...]
    locref_string: str
    ordnums: tuple[int, ...]
    catattr: CategoryAttribute
    state: str = "normal"
    rangeattr: str | None = None
    origin: LayeredLocationReference | None = None
    virtual: bool = False
    merge_drop: bool = False
    subrefs: list[LayeredLocationReference] = field(default_factory=list)

    def __hash__(self) -> int:
        return id(self)


@dataclass(slots=True)
class CrossrefLocationReference(LocationReference):
    target: str


def make_category_attribute(name: str) -> CategoryAttribute:
    return CategoryAttribute(name=name)


def build_location_reference(
    locclass: LayeredLocationClass,
    locref_str: str,
    category: CategoryAttribute,
    attribute: str | None,
) -> LayeredLocationReference | None:
    try:
        layers, ordnums = perform_match(locref_str, locclass)
    except LocationMatchError:
        return None
    return LayeredLocationReference(
        locclass=locclass,
        layers=tuple(layers),
        locref_string=locref_str,
        ordnums=tuple(ordnums),
        catattr=category,
        attribute=attribute,
    )


def create_cross_reference(
    locclass: LayeredLocationClass,
    target: str,
    attribute: str | None,
) -> CrossrefLocationReference:
    return CrossrefLocationReference(
        locclass=locclass,
        target=target,
        attribute=attribute,
    )


def locref_class_lt(locref_a: LocationReference, locref_b: LocationReference) -> bool:
    return locref_a.locclass.ordnum < locref_b.locclass.ordnum


def locref_class_eq(locref_a: LocationReference, locref_b: LocationReference) -> bool:
    return locref_a.locclass is locref_b.locclass


def locref_ordnum_lt(list_a: Sequence[int], list_b: Sequence[int]) -> bool:
    if list_a == list_b:
        return False
    for a, b in zip(list_a, list_b, strict=False):
        if a == b:
            continue
        return a < b
    return len(list_a) < len(list_b)


def locref_ordnum_eq(list_a: Sequence[int], list_b: Sequence[int]) -> bool:
    return tuple(list_a) == tuple(list_b)


__all__ = [
    "CategoryAttribute",
    "CrossrefLocationReference",
    "LayeredLocationReference",
    "LocationReference",
    "build_location_reference",
    "create_cross_reference",
    "locref_class_eq",
    "locref_class_lt",
    "locref_ordnum_eq",
    "locref_ordnum_lt",
    "make_category_attribute",
]
