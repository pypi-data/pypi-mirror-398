"""Location classes (standard, variable, cross references)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from .basetypes import LayerElement


class LocationMatchError(ValueError):
    """Raised when a location string cannot be matched."""


class _OrdnumGenerator:
    def __init__(self) -> None:
        self._value = 0

    def next(self) -> int:
        self._value += 1
        return self._value


_ORDNUM = _OrdnumGenerator()


@dataclass(slots=True)
class LocationClass:
    name: str
    ordnum: int = field(default_factory=_ORDNUM.next, init=False)


@dataclass(slots=True)
class LayeredLocationClass(LocationClass):
    layers: tuple[LayerElement, ...]
    hierdepth: int = 0


@dataclass(slots=True)
class StandardLocationClass(LayeredLocationClass):
    join_length: int = 0


@dataclass(slots=True)
class VarLocationClass(LayeredLocationClass):
    pass


@dataclass(slots=True)
class CrossrefLocationClass(LocationClass):
    target: str | None = None
    verified: bool = False


def checked_make_standard_location_class(
    name: str,
    layers: Sequence[LayerElement],
    join_length: int,
    hierdepth: int = 0,
) -> StandardLocationClass:
    return StandardLocationClass(
        name=name,
        layers=tuple(layers),
        join_length=join_length,
        hierdepth=hierdepth,
    )


def checked_make_var_location_class(
    name: str,
    layers: Sequence[LayerElement],
    hierdepth: int = 0,
) -> VarLocationClass:
    return VarLocationClass(name=name, layers=tuple(layers), hierdepth=hierdepth)


def perform_match(
    locstring: str,
    locclass: LayeredLocationClass,
) -> tuple[list[str], list[int]]:
    """Mimic LOCREF:perform-match returning matched layers and ordnums."""
    layer_matches: list[str] = []
    ordnums: list[int] = []
    rest = locstring
    for element in locclass.layers:
        result = element.prefix_match(rest)
        if not result:
            raise LocationMatchError(f"could not match {element!r} against {rest!r}")
        rest = result.rest
        if isinstance(result.ordnum, bool):
            continue
        layer_matches.append(result.matched)
        ordnums.append(int(result.ordnum))
    if rest:
        raise LocationMatchError(f"unparsed remainder {rest!r} for {locclass.name}")
    return layer_matches, ordnums


__all__ = [
    "CrossrefLocationClass",
    "LayeredLocationClass",
    "LocationClass",
    "LocationMatchError",
    "StandardLocationClass",
    "VarLocationClass",
    "checked_make_standard_location_class",
    "checked_make_var_location_class",
    "perform_match",
]
