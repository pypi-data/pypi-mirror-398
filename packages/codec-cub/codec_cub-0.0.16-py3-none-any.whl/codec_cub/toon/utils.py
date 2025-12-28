"""Utility functions for TOON codec."""

from __future__ import annotations

from decimal import Decimal
import math
import re
from typing import Any, Final

from funcy_bear.constants import characters as char
from funcy_bear.constants.escaping import E_LITERAL, ZERO_QUOTE
from funcy_bear.ops.strings.escaping import return_escaped

from .constants import LIST_ITEM_MARKER

BRACKETS: Final[set[str]] = {char.LEFT_BRACE, char.RIGHT_BRACE, char.LEFT_BRACKET, char.RIGHT_BRACKET}
LITERALS: Final[set[str]] = {char.TRUE_LITERAL, char.FALSE_LITERAL, char.NULL_LITERAL}
WHITESPACES: Final[set[str]] = {char.SPACE, char.TAB, char.NEWLINE, char.CARRIAGE}
MISC: Final[set[str]] = {char.COLON, char.DOUBLE_QUOTE, char.BACKSLASH}
DELIMITER_MAP: dict[str, str] = {char.COMMA: "", char.TAB: char.TAB, char.PIPE: char.PIPE}


def is_identifier_segment(s: str) -> bool:
    """Check if string is a valid identifier segment for safe folding/expansion.

    Must match: ^[A-Za-z_][A-Za-z0-9_]*$ (no dots allowed).
    """
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", s))


def is_valid_unquoted_key(s: str) -> bool:
    """Check if string can be used as an unquoted key.

    Must match: ^[A-Za-z_][A-Za-z0-9_.]*$
    """
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_.]*$", s))


def is_numeric_like(s: str) -> bool:
    """Check if string looks like a number."""
    if re.match(r"^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$", s):
        return True
    return bool(re.match(r"^0\d+$", s))


def needs_quoting(value: str, delimiter: str) -> bool:
    """Determine if a string value needs quoting per TOON spec §7.2.

    Args:
        value: The string value to check
        delimiter: The active delimiter (comma, tab, or pipe)

    Returns:
        True if the value must be quoted
    """
    return (
        not value
        or value != value.strip()
        or value in LITERALS
        or is_numeric_like(value)
        or any(char in value for char in BRACKETS)
        or any(char in value for char in WHITESPACES)
        or any(char in value for char in MISC)
        or delimiter in value
        or value.startswith(LIST_ITEM_MARKER)
        or value == LIST_ITEM_MARKER
    )


def escape_string(s: str) -> str:
    r"""Escape a string for TOON format per §7.1.

    Only escapes: \\, ", \n, \r, \t
    """
    result: list[str] = []
    for ch in s:
        result.append(return_escaped(ch))
    return "".join(result)


def quote_string(value: str, delimiter: str) -> str:
    """Quote and escape a string if needed.

    Args:
        value: The string value
        delimiter: The active delimiter

    Returns:
        Quoted and escaped string, or unquoted if safe
    """
    if needs_quoting(value, delimiter):
        return f'"{escape_string(value)}"'
    return value


def encode_key(key: str) -> str:
    """Encode an object key per §7.3.

    Keys must be quoted unless they match: ^[A-Za-z_][A-Za-z0-9_.]*$
    """
    if is_valid_unquoted_key(key):
        return key
    return f'"{escape_string(key)}"'


def normalize_number(value: float) -> str | None:
    """Normalize a number to canonical TOON form per §2.

    Returns:
        Canonical string representation, or None for non-finite values
    """
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        if value == 0.0:
            return ZERO_QUOTE
    if isinstance(value, int):
        return str(value)
    text = str(value)
    if E_LITERAL in text.lower():
        dec = Decimal(text)
        text: str = format(dec, "f")
    if char.DOT in text:
        text = text.rstrip(ZERO_QUOTE).rstrip(char.DOT)
    return text or ZERO_QUOTE


def get_delimiter_char(delimiter: str) -> str:
    """Get the delimiter character for array headers.

    Returns empty string for comma (default), TAB for tab, "|" for pipe.
    """
    return DELIMITER_MAP.get(delimiter, "")


def encode_primitive(value: Any, delimiter: str) -> str:
    """Encode a primitive value to TOON string representation.

    Args:
        value: Python value (None, bool, int, float, or str)
        delimiter: Active delimiter for quoting decisions

    Returns:
        TOON string representation of the value
    """
    if value is None:
        return char.NULL_LITERAL
    if isinstance(value, bool):
        return char.TRUE_LITERAL if value else char.FALSE_LITERAL
    if isinstance(value, (int, float)):
        normalized: str | None = normalize_number(value)
        return normalized if normalized is not None else char.NULL_LITERAL
    if isinstance(value, str):
        return quote_string(value, delimiter)
    return char.NULL_LITERAL


def is_primitive_array(items: list[Any]) -> bool:
    """Check if all items are primitives (not dict/list)."""
    return all(not isinstance(item, (dict, list)) for item in items)


def build_array_header(
    key: str | None,
    length: int,
    fields: list[str],
    delimiter: str,
    delim_char: str,
) -> str:
    """Build array header string: key[N<delim>]{fields}: or [N<delim>]{fields}:

    Args:
        key: Optional key prefix (None for root arrays)
        length: Number of items in array
        fields: Field names for tabular format (empty for non-tabular)
        delimiter: Delimiter for joining fields
        delim_char: Delimiter indicator in header (empty for comma)

    Returns:
        Formatted array header string
    """
    if fields:
        encoded_fields: str = delimiter.join(encode_key(f) for f in fields)
        header: str = f"[{length}{delim_char}]{{{encoded_fields}}}:"
    else:
        header = f"[{length}{delim_char}]:"

    return f"{key}{header}" if key else header
