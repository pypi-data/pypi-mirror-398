"""Lark-based Nix parser implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lark import Lark, Transformer

from codec_cub.config import NixCodecConfig

if TYPE_CHECKING:
    from codec_cub.config import NixCodecConfig

NIX_GRAMMAR = r"""
    ?start: value

    ?value: null
          | bool
          | number
          | string
          | list
          | attrset

    null: "null"

    bool.2: TRUE | FALSE
    TRUE: "true"
    FALSE: "false"

    number: SIGNED_NUMBER

    string: ESCAPED_STRING

    list: "[" value* "]"

    attrset: "{" [attr_pair (SEMICOLON? attr_pair)* SEMICOLON?] "}"
    attr_pair: key "=" value

    SEMICOLON: ";"

    ?key: IDENT | string

    IDENT: /[a-zA-Z_][a-zA-Z0-9_-]*/
    COMMENT: /#[^\n]*/

    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.WS

    %ignore WS
    %ignore COMMENT
"""


class NixTransformer(Transformer):
    """Transform Lark parse tree into Python objects."""

    def null(self, children: list[Any]) -> None:  # noqa: ARG002
        """Convert Nix null to Python None."""
        return None  # noqa: RET501

    def bool(self, children: list[Any]) -> bool:
        """Convert 'true'/'false' to boolean."""
        return str(children[0]) == "true"

    def number(self, children: list[Any]) -> int | float:
        """Convert number string to int or float."""
        value = str(children[0])
        if "." in value or "e" in value.lower():
            return float(value)
        return int(value)

    def string(self, children: list[Any]) -> str:
        """Convert escaped string to Python string.

        Lark's ESCAPED_STRING includes the quotes, strip and unescape them.
        """
        return str(children[0])[1:-1].encode().decode("unicode_escape")

    def list(self, children: list[Any]) -> list[Any]:
        """Convert list of items to Python list."""
        return children

    def attrset(self, children: list[Any]) -> dict[str, Any]:
        """Convert attribute pairs to dictionary."""
        if not children:
            return {}
        key_value = 2
        result: dict[str, Any] = {}
        for item in children:
            if isinstance(item, tuple) and len(item) == key_value:
                key_str: str = str(item[0]) if not isinstance(item[0], str) else item[0]
                result[key_str] = item[1]
        return result

    def attr_pair(self, children: list[Any]) -> tuple[str, Any]:
        """Return key-value pair as tuple."""
        key: Any = children[0]
        value: Any = children[1]
        key_str: str = str(key) if not isinstance(key, str) else key
        return (key_str, value)

    def key(self, children: list[Any]) -> str:
        """Convert key to string.

        Handle both IDENT (bare identifiers) and quoted strings
        """
        name: str = str(children[0]) if children else ""
        if name.startswith('"'):
            return name[1:-1]
        return name


class _NixParser:
    """Lark-based Nix parser."""

    def __init__(self, cfg: NixCodecConfig) -> None:
        """Initialize the Lark Nix parser."""
        self._cfg: NixCodecConfig = cfg
        self.parser = Lark(
            NIX_GRAMMAR,
            parser="lalr",
            transformer=NixTransformer(),
            cache=True,
            cache_grammar=True,
            lexer="contextual",
        )

    def parse_string(self, text: str) -> Any:
        """Parse Nix syntax string into Python object."""
        return self.parser.parse(text)


__all__ = ["_NixParser"]
