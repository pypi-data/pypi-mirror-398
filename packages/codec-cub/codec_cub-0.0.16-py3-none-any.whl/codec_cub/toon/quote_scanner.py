"""Quote-aware string scanning utilities for TOON decoder."""

from __future__ import annotations

from codec_cub.toon.constants import BACKSLASH, DOUBLE_QUOTE
from funcy_bear.tools.string_cursor import StringCursor


class QuoteAwareScanner:
    """Scanner that respects quoted regions when finding delimiters."""

    def __init__(self, text: str) -> None:
        """Initialize scanner with text to scan."""
        self._text: str = text
        self.tokens: list[str] = []
        self.current: list[str] = []
        self.in_quotes = False
        self.cursor = StringCursor(text)

    def find_unquoted(self, target: str) -> int:
        """Find first unquoted occurrence of target character/string.

        Args:
            target: Character or string to find

        Returns:
            Index of first unquoted occurrence, or -1 if not found
        """
        cursor: StringCursor = self.cursor
        while cursor.within_bounds:
            if cursor.is_char(DOUBLE_QUOTE) and (cursor.index == 0 or not cursor.tail_equals(BACKSLASH)):
                self.in_quotes: bool = not self.in_quotes
                self.cursor.tick()
                continue

            if not self.in_quotes and cursor.matches_ahead(target):
                return cursor.index
            self.cursor.tick()
        return -1

    def split_by(self, delimiter: str) -> list[str]:
        """Split text by delimiter, respecting quoted regions.

        Args:
            delimiter: Delimiter to split by (comma, tab, pipe)

        Returns:
            List of tokens with leading/trailing whitespace stripped
        """
        cursor: StringCursor = self.cursor
        while cursor.within_bounds:
            if cursor.is_char(DOUBLE_QUOTE):
                if not cursor.tail_equals(BACKSLASH):
                    self.in_quotes: bool = not self.in_quotes
                self.current.append(cursor.current)
            elif cursor.is_char(delimiter) and not self.in_quotes:
                self.tokens.append("".join(self.current).strip())
                self.current = []
            else:
                self.current.append(cursor.current)
            cursor.tick()
        if self.current or cursor.tail_equals(delimiter):
            self.tokens.append("".join(self.current).strip())
        return self.tokens

    def has_unquoted(self, target: str) -> bool:
        """Check if target exists outside quoted regions.

        Args:
            target: Character or string to check for

        Returns:
            True if target appears unquoted
        """
        return self.find_unquoted(target) != -1
