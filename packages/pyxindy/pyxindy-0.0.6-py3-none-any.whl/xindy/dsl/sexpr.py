"""Lightweight S-expression parser tailored for xindy's DSL files."""

from __future__ import annotations

from dataclasses import dataclass
from io import TextIOBase
from typing import Union


SExprAtom = Union["Symbol", "Keyword", str, int, float]
SExpr = SExprAtom | list["SExpr"]


class SExprSyntaxError(ValueError):
    """Raised when an S-expression cannot be parsed."""


@dataclass(frozen=True, slots=True)
class Symbol:
    """Representation of a Lisp symbol."""

    name: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.name


@dataclass(frozen=True, slots=True)
class Keyword(Symbol):
    """Representation of a Lisp keyword (prefixed with ':')."""


class _Scanner:
    """Incremental scanner with basic location tracking."""

    def __init__(self, text: str):
        self._text = text
        self._length = len(text)
        self._index = 0
        self._line = 1
        self._column = 1

    def eof(self) -> bool:
        return self._index >= self._length

    def peek(self) -> str | None:
        return None if self.eof() else self._text[self._index]

    def peek_next(self) -> str | None:
        nxt = self._index + 1
        return None if nxt >= self._length else self._text[nxt]

    def advance(self) -> str:
        if self.eof():
            raise SExprSyntaxError("Unexpected EOF")
        ch = self._text[self._index]
        self._index += 1
        if ch == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1
        return ch

    def error(self, message: str) -> SExprSyntaxError:
        location = f"line {self._line}, column {self._column}"
        return SExprSyntaxError(f"{message} at {location}")

    def skip_separators(self) -> None:
        while not self.eof():
            ch = self.peek()
            if ch is None:
                return
            if ch.isspace():
                self.advance()
                continue
            if ch == ";":  # line comment
                self._skip_line_comment()
                continue
            if ch == "#" and self.peek_next() == "|":
                self._skip_block_comment()
                continue
            break

    def _skip_line_comment(self) -> None:
        while not self.eof() and self.advance() != "\n":
            continue

    def _skip_block_comment(self) -> None:
        # consume "#|"
        self.advance()
        self.advance()
        depth = 1
        while depth > 0:
            if self.eof():
                raise self.error("EOF while inside block comment")
            ch = self.advance()
            if ch == "#" and self.peek() == "|":
                self.advance()
                depth += 1
            elif ch == "|" and self.peek() == "#":
                self.advance()
                depth -= 1


def parse_many(source: str | bytes | TextIOBase) -> list[SExpr]:
    """Parse every S-expression present in ``source``."""
    if isinstance(source, TextIOBase):
        text = source.read()
    elif isinstance(source, bytes):
        text = source.decode()
    else:
        text = str(source)
    scanner = _Scanner(text)
    expressions: list[SExpr] = []
    while True:
        scanner.skip_separators()
        if scanner.eof():
            break
        expressions.append(_parse_expression(scanner))
    return expressions


def loads(text: str) -> list[SExpr]:
    """Convenience alias mirroring :func:`json.loads`."""
    return parse_many(text)


def parse_one(source: str | bytes | TextIOBase) -> SExpr:
    """Parse ``source`` expecting exactly one S-expression."""
    exprs = parse_many(source)
    if not exprs:
        raise SExprSyntaxError("Expected one S-expression, found none")
    if len(exprs) > 1:
        raise SExprSyntaxError(f"Expected one S-expression, found {len(exprs)}")
    return exprs[0]


def _parse_expression(scanner: _Scanner) -> SExpr:
    scanner.skip_separators()
    token = scanner.peek()
    if token is None:
        raise scanner.error("Unexpected EOF while reading expression")
    if token == "(":
        return _parse_list(scanner)
    if token == ")":
        raise scanner.error("Unexpected ')'")
    if token == '"':
        return _parse_string(scanner)
    if token == "'":
        scanner.advance()
        return [Symbol("quote"), _parse_expression(scanner)]
    return _parse_atom(scanner)


def _parse_list(scanner: _Scanner) -> list[SExpr]:
    elements: list[SExpr] = []
    scanner.advance()  # consume "("
    while True:
        scanner.skip_separators()
        token = scanner.peek()
        if token is None:
            raise scanner.error("EOF while reading list")
        if token == ")":
            scanner.advance()
            return elements
        elements.append(_parse_expression(scanner))


def _parse_string(scanner: _Scanner) -> str:
    scanner.advance()  # opening quote
    result: list[str] = []
    while True:
        if scanner.eof():
            raise scanner.error("EOF while reading string literal")
        ch = scanner.advance()
        if ch == '"':
            break
        if ch == "\\":
            if scanner.eof():
                raise scanner.error("EOF after escape character")
            escaped = scanner.advance()
            escape_map = {
                '"': '"',
                "\\": "\\",
            }
            if escaped in escape_map:
                result.append(escape_map[escaped])
            else:
                result.append("\\" + escaped)
        else:
            result.append(ch)
    return "".join(result)


def _parse_atom(scanner: _Scanner) -> SExprAtom:
    token_chars: list[str] = []
    while True:
        ch = scanner.peek()
        if ch is None or ch.isspace() or ch in '();"':
            break
        token_chars.append(scanner.advance())
    if not token_chars:
        raise scanner.error("Expected atom")
    token = "".join(token_chars)
    if token.startswith(":"):
        return Keyword(token[1:])
    try:
        return int(token)
    except ValueError:
        pass
    try:
        return float(token)
    except ValueError:
        pass
    return Symbol(token)


__all__ = [
    "Keyword",
    "SExpr",
    "SExprSyntaxError",
    "Symbol",
    "loads",
    "parse_many",
    "parse_one",
]
