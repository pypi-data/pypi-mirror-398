"""MessagePack packing and unpacking handler with reusable buffer."""

from __future__ import annotations

from contextlib import suppress
from typing import Any, Self

from codec_cub.message_pack.packing import ByteAccumulator, ByteReader

from ._packing import pack_into
from .unpacking import unpack_one


class MsgPackHandler:
    """In-memory cache for packing and unpacking MessagePack data.

    Maintains a reusable buffer for efficient serialization/deserialization.
    """

    def __init__(self, data: Any | None = None) -> None:
        """Initialize the MsgPackHandler.

        Args:
            data: Initial data to load into the buffer (optional)
        """
        self.buffer = ByteAccumulator()
        self._reader = ByteReader()
        if data is not None:
            self.pack(data)

        # used for single-object operations, so they don't interfere with main buffer
        self._temp = ByteAccumulator()

    def pack(self, x: object) -> None:
        """Pack an object into the buffer (accumulates data).

        Args:
            x: The object to pack into MessagePack format
        """
        pack_into(obj=x, buf=self.buffer)

    def pack_one(self, x: Any) -> bytes:
        """Pack a single object and return it (clears temp buffer first).

        Args:
            x: The object to pack into MessagePack format
        Returns:
            The packed MessagePack bytes
        """
        pack_into(obj=x, buf=self._temp)
        return self._temp.getvalue(clear=True)

    def unpack_one(self, data: bytes) -> Any:
        """Unpack MessagePack bytes into a Python object (from start of buffer).

        Args:
            data: The MessagePack bytes to unpack
        Returns:
            The unpacked Python object
        """
        self._reader.load(data)
        return unpack_one(self._reader)

    def unpack(self) -> Any:
        """Unpack the next MessagePack object from the internal buffer.

        Returns:
            The unpacked Python object
        """
        return unpack_one(self._reader)

    def unpack_stream(self, data: bytes) -> list[Any]:
        """Unpack all MessagePack objects from the data."""
        self._reader.load(data)
        results: list[Any] = []
        with suppress(Exception):
            while self._reader.get_offset() < len(self._reader):
                result: Any = unpack_one(self._reader)
                results.append(result)
        return results

    def clear(self) -> None:
        """Clear the internal buffer."""
        self.buffer.clear(offset=0)

    def get_buffer(self, clear: bool = False) -> bytes:
        """Get the current content of the internal buffer."""
        return self.buffer.getvalue(clear=clear)

    @property
    def size(self) -> int:
        """Get the current size of the internal buffer."""
        return self.buffer.length()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.clear()
