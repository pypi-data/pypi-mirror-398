"""Lark-based parser for TOON array headers."""

from __future__ import annotations

from typing import Any

from lark import Lark, ParseTree, Transformer

from codec_cub.toon.constants import COMMA, PIPE, TAB

HEADER_GRAMMAR = r"""
    start: "[" length delimiter? "]" fields? ":" REST?

    length: INT
    delimiter: TAB | PIPE
    fields: "{" field_list "}"
    field_list: field ("," field)*

    ?field: ESCAPED_STRING | IDENT

    REST: /.+/s
    TAB: "\t"
    PIPE: "|"
    IDENT: /[a-zA-Z0-9_]+/
    INT: /\d+/

    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
"""


class ArrayHeader:
    """Parsed representation of a TOON array header."""

    def __init__(
        self,
        length: int,
        delimiter: str,
        field_names: list[str],
    ) -> None:
        """Initialize parsed header.

        Args:
            length: Declared array length
            delimiter: Delimiter character (comma, tab, or pipe)
            field_names: Field names for tabular format (empty if not tabular)
        """
        self.length: int = length
        self.delimiter: str = delimiter
        self.field_names: list[str] = field_names

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ArrayHeader(length={self.length}, delimiter={self.delimiter!r}, fields={self.field_names})"


class HeaderTransformer(Transformer):
    """Transform parsed header into ArrayHeader."""

    def length(self, children: list[Any]) -> int:
        """Extract length as int."""
        return int(str(children[0]))

    def delimiter(self, children: list[Any]) -> str:
        """Extract delimiter character."""
        return str(children[0])

    def field_list(self, children: list[Any]) -> list[str]:
        """Extract field names."""
        return [str(child)[1:-1] if str(child).startswith('"') else str(child) for child in children]

    def fields(self, children: list[Any]) -> list[str]:
        """Return field list."""
        return children[0] if children else []


class ArrayHeaderParser:
    r"""Parse TOON array headers using Lark.

    Parses headers like:
        [N<delim?>]{field1,field2,...}:

    Where:
        - N is the array length (integer)
        - Optional delimiter marker (\t or |) after length
        - Optional {field_names} for tabular format
        - Followed by colon
    """

    def __init__(self) -> None:
        """Initialize parser with Lark grammar."""
        self._parser = Lark(
            HEADER_GRAMMAR,
            parser="lalr",
            transformer=HeaderTransformer(),
            cache=True,
            cache_grammar=True,
            lexer="contextual",
        )

    def parse(self, header_line: str) -> ArrayHeader:
        """Parse array header line.

        Args:
            header_line: Line containing array header (e.g., "tags[3]: ..." or "users[2]{id,name}:")

        Returns:
            ArrayHeader with length, delimiter, and field names

        Raises:
            ValueError: If header is malformed
        """
        try:
            tree: ParseTree = self._parser.parse(header_line)
            length = 0
            delimiter = COMMA
            field_names: list[str] = []

            for child in tree.children:
                if isinstance(child, int):
                    length = child
                elif isinstance(child, str) and child in (TAB, PIPE):
                    delimiter = child
                elif isinstance(child, list):
                    field_names = child

            return ArrayHeader(length, delimiter, field_names)

        except Exception as e:
            raise ValueError(f"Malformed array header: {header_line}") from e


_header_parser = ArrayHeaderParser()


def parse_array_header(header_line: str) -> tuple[int, str, list[str]]:
    """Parse array header line using Lark parser.

    This replaces the manual string slicing in ToonDecoder._parse_array_header.

    Args:
        header_line: Header line like "[3]:", "[2]{id,name}:", "items[3|]:"

    Returns:
        (length, delimiter, field_names)
    """
    header: ArrayHeader = _header_parser.parse(header_line)
    return (header.length, header.delimiter, header.field_names)
