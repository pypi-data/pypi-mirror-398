"""Base types (alphabets, enumerations) used by location classes."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import re


@dataclass(slots=True)
class MatchResult:
    """Represents the outcome of matching a prefix."""

    matched: str
    rest: str
    ordnum: int | bool


@dataclass(slots=True)
class BaseType:
    """Common data shared by alphabets/enumerations."""

    name: str
    base_alphabet: tuple[str, ...] = ()

    def prefix_match(self, text: str) -> MatchResult | None:
        raise NotImplementedError


def calculate_base_alphabet(symbols: Sequence[str]) -> tuple[str, ...]:
    """Compute the sorted list of distinct characters found in ``symbols``."""
    chars = {char for symbol in symbols for char in symbol}
    return tuple(sorted(chars))


@dataclass(slots=True)
class Alphabet(BaseType):
    """Concrete alphabet consisting of ordered string symbols."""

    symbols: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.symbols:
            raise ValueError("alphabet requires at least one symbol")
        self.base_alphabet = calculate_base_alphabet(self.symbols)

    def prefix_match(self, text: str) -> MatchResult | None:
        best: MatchResult | None = None
        for ordinal, symbol in enumerate(self.symbols):
            length = _common_prefix_length(text, symbol)
            if length == 0:
                continue
            if not best or length > len(best.matched):
                matched = text[:length]
                rest = text[length:]
                best = MatchResult(matched=matched, rest=rest, ordnum=ordinal)
        return best


@dataclass(slots=True)
class Enumeration(BaseType):
    """Enumeration uses a callable matcher (e.g. numeric parsing)."""

    match_func: Callable[[str], tuple[str, str, int | None]] | None = None

    def prefix_match(self, text: str) -> MatchResult | None:
        if not self.match_func:
            return None
        matched, rest, ordnum = self.match_func(text)
        if not matched:
            return None
        return MatchResult(
            matched=matched,
            rest=rest,
            ordnum=ordnum if ordnum is not None else 0,
        )


@dataclass(slots=True)
class LocClassLayer:
    """Wraps a basetype for use inside layered location classes."""

    basetype: BaseType

    def prefix_match(self, text: str) -> MatchResult | None:
        return self.basetype.prefix_match(text)


@dataclass(slots=True)
class LocClassSeparator:
    """Separator token inside layered location classes."""

    separator: str

    def prefix_match(self, text: str) -> MatchResult | None:
        if not text.startswith(self.separator):
            return None
        rest = text[len(self.separator) :]
        return MatchResult(matched=self.separator, rest=rest, ordnum=True)


LayerElement = LocClassLayer | LocClassSeparator


def _common_prefix_length(text: str, candidate: str) -> int:
    max_len = min(len(text), len(candidate))
    idx = 0
    while idx < max_len and text[idx] == candidate[idx]:
        idx += 1
    # allow complete candidate match even if text has more chars
    if idx == len(candidate):
        return idx
    if idx == len(text):
        return idx
    return idx


def prefix_match_for_radix_numbers(
    text: str,
    radix: int,
) -> tuple[str, str, int | None]:
    """Return (matched, rest, numeric value) for the given radix."""
    digits = []
    value: int | None = None
    for char in text:
        try:
            digit = int(char, radix)
        except ValueError:
            break
        digits.append(char)
        value = (value or 0) * radix + digit
    matched = "".join(digits)
    rest = text[len(matched) :]
    return matched, rest, value


def _roman_to_int(roman: str) -> int | None:
    mapping = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    prev = 0
    for char in roman:
        value = mapping.get(char)
        if value is None:
            return None
        if value > prev:
            total += value - 2 * prev
        else:
            total += value
        prev = value
    return total if total > 0 else None


def prefix_match_for_roman_numbers(
    text: str,
    lowercase: bool = False,
) -> tuple[str, str, int | None]:
    """Return (matched, rest, numeric value) for roman numerals."""
    pattern = r"^(m{0,4}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))"
    if not lowercase:
        match = re.match(pattern, text.upper())
        matched = match.group(0) if match else ""
        matched_original = text[: len(matched)]
    else:
        match = re.match(pattern, text.lower())
        matched = match.group(0) if match else ""
        matched_original = text[: len(matched)]
    value = _roman_to_int(matched.upper()) if matched else None
    rest = text[len(matched_original) :]
    return matched_original, rest, value


__all__ = [
    "Alphabet",
    "BaseType",
    "Enumeration",
    "LayerElement",
    "LocClassLayer",
    "LocClassSeparator",
    "MatchResult",
    "calculate_base_alphabet",
    "prefix_match_for_radix_numbers",
    "prefix_match_for_roman_numbers",
]
