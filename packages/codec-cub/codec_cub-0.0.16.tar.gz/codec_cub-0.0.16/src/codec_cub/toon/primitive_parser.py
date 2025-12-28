"""Lark-based parser for TOON primitive values."""

from __future__ import annotations

from typing import Any

from lark import Lark, Transformer, exceptions

PRIMITIVE_GRAMMAR = r"""
    ?start: quoted
          | null
          | bool
          | leading_zero
          | float_num
          | integer
          | unquoted

    null: NULL
    bool: TRUE | FALSE

    quoted: ESCAPED_STRING
    leading_zero: /0\d+/
    float_num: SIGNED_NUMBER
    integer: SIGNED_INT
    unquoted: /[^\s:,\|\t]+/

    NULL: "null"
    TRUE: "true"
    FALSE: "false"

    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.SIGNED_INT
    %import common.WS
    %ignore WS
"""


class PrimitiveTransformer(Transformer):
    """Transform parsed primitives."""

    def null(self, children: list[Any]) -> None:  # noqa: ARG002
        """Return None for null."""
        return None  # noqa: RET501

    def bool(self, children: list[Any]) -> bool:
        """Return bool value."""
        return str(children[0]) == "true"

    def quoted(self, children: list[Any]) -> str:
        """Unescape quoted string."""
        s: str = str(children[0])[1:-1]
        return s.encode("utf-8").decode("unicode_escape")

    def leading_zero(self, children: list[Any]) -> str:
        """Keep leading zero string as is."""
        return str(children[0])

    def float_num(self, children: list[Any]) -> float:
        """Parse float."""
        return float(str(children[0]))

    def integer(self, children: list[Any]) -> int:
        """Parse integer."""
        return int(str(children[0]))

    def unquoted(self, children: list[Any]) -> str:
        """Return unquoted string."""
        return str(children[0])


class PrimitiveParser:
    """Parse TOON primitive values using Lark."""

    def __init__(self) -> None:
        """Initialize parser with Lark grammar for primitives."""
        self._parser = Lark(
            PRIMITIVE_GRAMMAR,
            parser="lalr",
            transformer=PrimitiveTransformer(),
            cache=True,
            lexer="contextual",
        )

    def parse(self, token: str) -> Any:
        """Parse a primitive token.

        Args:
            token: Token string to parse

        Returns:
            Parsed primitive value (str, int, float, bool, None)
        """
        token = token.strip()
        if not token:
            return ""

        try:
            return self._parser.parse(token)
        except exceptions.LarkError:
            return token


_primitive_parser = PrimitiveParser()


def parse_primitive(token: str) -> Any:
    """Parse a TOON primitive value.

    Args:
        token: Token string to parse

    Returns:
        Parsed primitive value
    """
    return _primitive_parser.parse(token)
