"""A set of common utilities for MessagePack handling."""

from typing import Protocol


class ByteFileProtocol(Protocol):
    """Protocol for a byte file handler (writing)."""

    def write_byte(self, byte: int) -> None:
        """Write a single byte to the handler."""

    def write(self, data: bytes) -> None:
        """Write bytes data to the handler."""


class ByteReaderProtocol(Protocol):
    """Protocol for a byte reader (reading with cursor)."""

    def read(self, size: int = -1, *, n: int | None = None, tick: int | None = None) -> bytes:
        """Read bytes from current position."""
        ...

    def get_offset(self) -> int:
        """Get current read position."""
        ...


class EnumWithBounds(Protocol):
    """Protocol for enums with low and high bounds."""

    low: int
    high: int


def in_range(n: int, enum: EnumWithBounds) -> bool:
    """Check if n is within the bounds of the given enum.

    Args:
        n: The value to check.
        enum: An enum with 'low' and 'high' attributes.

    Returns:
        bool: True if n is within the bounds, False otherwise.
    """
    return enum.low <= n <= enum.high
