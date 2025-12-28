from collections.abc import Generator
from contextlib import contextmanager
from io import StringIO
from typing import Any, Self

from funcy_bear.constants.characters import INDENT, NEWLINE
from funcy_bear.ops.math import clamp
from funcy_bear.ops.strings.manipulation import join


class StringBuilder:
    """Simple string builder using an internal StringIO buffer."""

    def __init__(self, *s: str) -> None:
        """Initialize a StringBuilder.

        Args:
            s: Initial string content.
        """
        self._data: StringIO = StringIO()
        self._data.write("".join(s)) if s else None

    def add(self, content: str) -> Self:
        """Add content to the string builder."""
        self._data.write(content)
        return self

    def join(self, *segments: str, sep: str = "") -> Self:
        """Join segments with a separator and add to the string builder."""
        self._data.write(sep.join(segments))
        return self

    def consume(self) -> str:
        """Get the current content of the string builder."""
        value: str = self._data.getvalue()
        self._data.close()
        return value


class BufferHelper:
    """Dataclass representing a section of a code buffer."""

    def __init__(self, buffer: StringIO | None = None, indent: int = 0, content: str = "") -> None:
        """Initialize a BufferSection.

        Args:
            indent: The initial indentation level.
        """
        self.indent: int = indent
        self._data: StringIO = buffer or StringIO()
        if content:
            self._data.write(content)

    def write(self, line: str, prefix: str = "", suffix: str = "") -> Self:
        """Add a line to the buffer with the current indentation.

        Args:
            line: The line to add to the buffer.
            prefix: Optional prefix to add before the line.
            suffix: Optional suffix to add after the line.
        """
        indented_line: str = join(INDENT * self.indent, line)
        self._data.write(join(prefix, indented_line, suffix))
        return self

    def newline(self) -> Self:
        """Add a newline to the buffer."""
        self.write(NEWLINE)
        return self

    @contextmanager
    def indented(self, n: int = 1) -> Generator[Self, Any]:
        """Context manager to temporarily increase indentation."""
        self.tick(n)
        try:
            yield self
        finally:
            self.tock(n)

    def tick(self, n: int = 1) -> Self:
        """Increase the indentation level by one."""
        self.indent += n
        return self

    def tock(self, n: int = 1) -> Self:
        """Decrease the indentation level by one, not going below zero."""
        self.indent = clamp(self.indent - n, 0, self.indent)
        return self

    def clear(self) -> Self:
        """Clear the buffer content."""
        self._data.seek(0)
        self._data.truncate(0)
        return self

    def getvalue(self, close: bool = False) -> str:
        """Get the current content of the buffer.

        Returns:
            The content of the buffer as a string.
        """
        value: str = self._data.getvalue()
        if close:
            self.close()
        return value

    @property
    def empty(self) -> bool:
        """Check if the buffer is empty.

        Returns:
            True if the buffer is empty, False otherwise.
        """
        return not bool(self._data.getvalue())

    @property
    def not_empty(self) -> bool:
        """Check if the buffer has any content.

        Returns:
            True if the buffer is not empty, False otherwise.
        """
        return bool(self._data.getvalue())

    def close(self) -> None:
        """Close the underlying buffer."""
        self._data.close()

    def __str__(self) -> str:
        """Return the string representation of the buffer content.

        Returns:
            The content of the buffer as a string.
        """
        return self.getvalue()

    def __repr__(self) -> str:
        """Return the official string representation of the BufferHelper.

        Returns:
            A string representation of the BufferHelper.
        """
        return f"BufferHelper(indent={self.indent}, content={self.getvalue()!r})"

    def __enter__(self) -> Self:
        """Enter the runtime context related to this object.

        Returns:
            The BufferHelper instance.
        """
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Exit the runtime context related to this object.

        Args:
            exc_type: The exception type.
            exc_value: The exception value.
            traceback: The traceback object.
        """
        self.close()
