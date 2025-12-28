"""Constants for TOON encoders."""

from __future__ import annotations

from enum import StrEnum
from typing import Final, Literal

from funcy_bear.constants.characters import COLON, COMMA, FALSE_LITERAL, NULL_LITERAL, PIPE, SPACE, TAB, TRUE_LITERAL

type DelimiterKey = Literal["comma", "tab", "pipe"]
Delimiter = Literal[COMMA, TAB, PIPE]

LIST_ITEM_MARKER: Final[str] = "-"
LIST_ITEM_PREFIX: Final[str] = "- "


class ListMarkers(StrEnum):
    """Markers used for list items in TOON format."""

    ITEM = LIST_ITEM_MARKER
    PREFIX = LIST_ITEM_PREFIX


class StructuralChars(StrEnum):
    """Structural characters used in TOON format."""

    COMMA = COMMA
    TAB = TAB
    COLON = COLON
    SPACE = SPACE
    PIPE = PIPE


OPEN_BRACKET: Final[str] = "["
CLOSE_BRACKET: Final[str] = "]"
OPEN_BRACE: Final[str] = "{"
CLOSE_BRACE: Final[str] = "}"


class FormattingChars(StrEnum):
    """Formatting characters used in TOON format."""

    OPEN_BRACKET = OPEN_BRACKET
    CLOSE_BRACKET = CLOSE_BRACKET

    OPEN_BRACE = OPEN_BRACE
    CLOSE_BRACE = CLOSE_BRACE


class LiteralValues(StrEnum):
    """Literal values used in TOON format."""

    NULL = NULL_LITERAL
    TRUE = TRUE_LITERAL
    FALSE = FALSE_LITERAL


BACKSLASH: Final[str] = "\\"
DOUBLE_QUOTE: Final[str] = '"'
NEWLINE: Final[str] = "\n"
CARRIAGE_RETURN: Final[str] = "\r"


class EscapeChars(StrEnum):
    """Escape characters used in TOON format."""

    BACKSLASH = BACKSLASH
    DOUBLE_QUOTE = DOUBLE_QUOTE
    NEWLINE = NEWLINE
    CARRIAGE_RETURN = CARRIAGE_RETURN
    TAB = TAB


class Delimiters(StrEnum):
    """Supported delimiters for array value separation."""

    COMMA = COMMA
    TAB = TAB
    PIPE = PIPE


DEFAULT_DELIMITER: Final[Delimiters] = Delimiters.COMMA
