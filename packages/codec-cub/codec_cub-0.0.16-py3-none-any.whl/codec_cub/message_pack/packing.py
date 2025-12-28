"""MessagePack packing entry point."""

from __future__ import annotations

from io import BytesIO
from typing import IO, Any

from codec_cub.message_pack._packing import pack_into
from codec_cub.text.bytes_handler import BytesFileHandler
from funcy_bear.typing_stuffs import TypeHint


def pack(obj: Any) -> bytes:
    """Pack an object into MessagePack bytes."""
    buf = BytesFileHandler(buffer=BytesIO, append=True)
    pack_into(obj=obj, buf=buf)
    return buf.read()


class ByteReader:
    """Reusable cursor-based byte reader for MessagePack unpacking."""

    def __init__(self, data: bytes = b"") -> None:
        """Initialize the byte reader."""
        self._buffer: bytes = data
        self._offset: int = 0

    def load(self, data: bytes) -> None:
        """Load new data and reset cursor to start."""
        self._buffer = data
        self._offset = 0

    def read(self, size: int = -1, *, n: int | None = None, tick: int | None = None) -> bytes:
        """Read bytes from current position.

        Args:
            size: Number of bytes to read (-1 for all remaining)
            n: Alias for size (for BytesFileHandler compatibility)
            tick: Advance offset by this amount after reading
        """
        if n is not None:
            size = n
        if size == -1:
            size = len(self._buffer) - self._offset
        data = self._buffer[self._offset : self._offset + size]
        if tick is not None:
            self._offset += tick
        else:
            self._offset += size
        return data

    def read_byte(self) -> int:
        """Read single byte as int, advance cursor."""
        if self._offset >= len(self._buffer):
            return -1
        b = self._buffer[self._offset]
        self._offset += 1
        return b

    def seek(self, pos: int, whence: int = 0) -> int:
        """Move cursor. whence: 0=start, 1=current, 2=end."""
        seek_set, seek_cur, seek_end = 0, 1, 2
        if whence == seek_set:
            self._offset = pos
        elif whence == seek_cur:
            self._offset += pos
        elif whence == seek_end:
            self._offset = len(self._buffer) + pos
        return self._offset

    def tell(self) -> int:
        """Get cursor position."""
        return self._offset

    def get_offset(self) -> int:
        """Alias for tell() - matches BytesFileHandler API."""
        return self._offset

    def remaining(self) -> int:
        """Bytes left to read."""
        return len(self._buffer) - self._offset

    def __len__(self) -> int:
        """Get total buffer length."""
        return len(self._buffer)


class ByteAccumulator(TypeHint(IO[bytes])):
    """Lightweight byte accumulator for MessagePack serialization."""

    def __init__(self) -> None:
        """Initialize the byte accumulator."""
        self._buffer = bytearray()

    def write_byte(self, byte: int) -> None:
        """Write a single byte."""
        self._buffer.append(byte)

    def write(self, data: bytes) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Write bytes."""
        self._buffer.extend(data)

    def getbuffer(self) -> bytearray:
        """Get the internal bytearray buffer."""
        return self._buffer

    def read1(self, n: int = -1) -> bytes:
        """Read up to n bytes from the buffer."""
        if n == -1 or n > len(self._buffer):
            n = len(self._buffer)
        data: bytearray = self._buffer[:n]
        del self._buffer[:n]
        return bytes(data)

    def readlines(self, size: int | None = None) -> list[bytes]:
        """Read all bytes as a single line."""
        if size is None or size > len(self._buffer):
            size = len(self._buffer)
        data: bytearray = self._buffer[:size]
        del self._buffer[:size]
        return [bytes(data)]

    def getvalue(self, clear: bool = False) -> bytes:
        """Get accumulated bytes."""
        values = bytes(self._buffer)
        if clear:
            self._buffer.clear()
        return values

    def length(self) -> int:
        """Get the length of the accumulated bytes."""
        return len(self._buffer)

    def clear(self, **kwargs) -> None:  # noqa: ARG002
        """Clear the buffer."""
        self._buffer.clear()
