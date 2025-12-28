"""Indentation state machine for TOON decoder."""

from __future__ import annotations

from typing import NamedTuple


class LineInfo(NamedTuple):
    """Information about a line's text and indentation depth."""

    text: str = ""
    depth: int = 0
    end: bool = False


class IndentationTracker:
    """State machine for tracking line-based indentation during parsing.

    Centralizes the concerns of:
    - Current line position
    - Indentation depth per line
    - Lookahead without consuming
    - Skipping blank lines in appropriate contexts
    """

    def __init__(self, lines: list[str], depths: list[int]) -> None:
        """Initialize tracker with pre-computed line depths."""
        self._lines: list[str] = lines
        self._depths: list[int] = depths
        self._index = 0

    @property
    def current_index(self) -> int:
        """Get current line index."""
        return self._index

    @current_index.setter
    def current_index(self, value: int) -> None:
        """Set current line index."""
        self._index: int = value

    def reset(self) -> None:
        """Reset index to start."""
        self._index = 0

    def peek(self) -> LineInfo:
        """Peek at current line without consuming.

        Returns:
            LineInfo of current line, or end=True if at end
        """
        if self._index >= len(self._lines):
            return LineInfo(end=True)
        return LineInfo(self._lines[self._index], self._depths[self._index])

    def consume(self) -> LineInfo:
        """Consume and return current line, advancing index.

        Returns:
            (line_text, depth)

        Raises:
            IndexError: If no more lines available
        """
        if self._index >= len(self._lines):
            raise IndexError("No more lines to consume")
        result: LineInfo = LineInfo(self._lines[self._index], self._depths[self._index])
        self._index += 1
        return result

    def peek_depth(self) -> int | None:
        """Peek at current line's depth without consuming.

        Returns:
            Depth or None if at end
        """
        if self._index >= len(self._lines):
            return None
        return self._depths[self._index]

    def has_more(self) -> bool:
        """Check if more lines are available."""
        return self._index < len(self._lines)

    def has_more_at_depth(self, depth: int, skip_blank: bool = False) -> bool:
        """Check if more lines exist at or deeper than specified depth.

        Args:
            depth: Target depth to check for
            skip_blank: Whether to skip blank lines during check

        Returns:
            True if lines at >= depth exist ahead
        """
        idx: int = self._index
        while idx < len(self._lines):
            line: str = self._lines[idx]
            if not line.strip():
                if skip_blank:
                    idx += 1
                    continue
                return False
            return self._depths[idx] >= depth
        return False

    def skip_blank_lines(self) -> None:
        """Skip consecutive blank lines from current position."""
        while self._index < len(self._lines) and not self._lines[self._index].strip():
            self._index += 1

    def peek_next_at_depth(self, target_depth: int) -> LineInfo:
        """Look ahead for next line at exact target depth.

        Args:
            target_depth: Exact depth to find

        Returns:
            LineInfo of next line at target depth, or end=True if none found
        """
        idx: int = self._index
        while idx < len(self._lines):
            if self._depths[idx] < target_depth:
                return LineInfo(end=True)
            if self._depths[idx] == target_depth and self._lines[idx].strip():
                return LineInfo(self._lines[idx], self._depths[idx])
            idx += 1
        return LineInfo(end=True)
