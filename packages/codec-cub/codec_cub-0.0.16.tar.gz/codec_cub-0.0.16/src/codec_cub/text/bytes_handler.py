"""A simple bytes file handler with locking and lazy open."""

from __future__ import annotations

from typing import IO, TYPE_CHECKING, Any, Self, TypeGuard, override

from lazy_bear import LazyLoader

from codec_cub.general.base_file_handler import BaseFileHandler
from codec_cub.general.file_lock import ex_lock, sh_lock, unlock
from funcy_bear.constants.binary_types import MAX_VALUE, MIN_VALUE
from funcy_bear.constants.type_constants import StrPath  # noqa: TC001
from funcy_bear.ops.func_stuffs import n_in_range
from funcy_bear.sentinels import EOF

if TYPE_CHECKING:
    from inspect import isclass
else:
    isclass = LazyLoader("inspect").to("isclass")


def is_buffer(buffer: Any) -> TypeGuard[type[IO]]:
    """Check if using an in-memory buffer."""
    return buffer is not None and (callable(buffer) or hasattr(buffer, "read"))


class BytesFileHandler(BaseFileHandler[bytes]):
    """A simple bytes file handler with locking and lazy open.

    - Lazily opens the file on first use
    - Uses fcntl file locks for read/write sections
    - Provides read_bytes(), write_bytes(), clear(), and basic handle helpers
    """

    def __init__(
        self,
        file: StrPath | None = None,
        mode: str = "a+b",
        touch: bool = False,
        buffer: type[IO] | IO | None = None,
        append: bool = False,
    ) -> None:
        """Initialize the bytes file handler.

        Args:
            file: Path to the bytes file
            mode: File open mode (default: "a+b")
            touch: Whether to create the file if it doesn't exist (default: False)
            buffer: Type of in-memory buffer to use (default: BytesIO)
            append: Whether to append to the file (default: False)
        """
        self.buffer: type[IO] | IO | None = buffer
        self.append: int = 0 if not append else 2
        self._offset: int = 0
        super().__init__(file=file, mode=mode, touch=touch)

    @override
    def handle(self, open_file: bool = True) -> IO[Any] | None:
        """Get the file handle, opening it if needed."""
        if is_buffer(self.buffer) and (self._handle is None or self._handle.closed):
            if isclass(self.buffer):
                self._handle = self.buffer()
            else:
                self._handle = self.buffer
            return self._handle
        if not open_file:
            return self._handle
        if self._handle is None or self._handle.closed:
            self._handle = self._open()
        return self._handle

    @override
    def clear(self, offset: int = -1) -> None:
        """Clear the file contents using an exclusive lock.

        Args:
            offset: Offset to navigate to after clearing (default: -1 for no change)
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        not_buffer: bool = not is_buffer(self.buffer)
        try:
            if not_buffer:
                ex_lock(handle)
            handle.seek(0)
            handle.truncate(0)
        finally:
            if not_buffer:
                unlock(handle)
            if offset >= 0:
                self.to_offset(offset)

    def read(
        self,
        size: int = -1,
        *,
        offset: int | None = None,
        tick: int | None = None,
        **kwargs,
    ) -> bytes:
        """Read the entire file (or up to n bytes) as bytes with a shared lock.

        Args:
            size: Number of bytes to read (default: -1 for all)
            offset: Offset to start reading from (default: current offset)
            tick: Number of bytes to advance the offset after reading (default: None)
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        not_buffer: bool = not is_buffer(self.buffer)
        if (n := kwargs.pop("n", None)) is not None:
            size = n
        if offset is None:
            offset = self._offset
        try:
            if not_buffer:
                sh_lock(handle)
            handle.seek(offset)
            data: bytes = handle.read(size)
        finally:
            if not_buffer:
                unlock(handle)
        if tick is not None:
            offset += tick
            self._offset = offset
        return data

    def read_tick(self) -> bytes:
        """Read a single byte and advance the offset by 1."""
        data: bytes = self.read(size=1, tick=1)
        n: int = len(data)
        if n == 0:
            return EOF
        return data

    def read_byte(self, offset: int | None = None) -> bytes:
        """Read a single byte from the file with a shared lock.

        Args:
            offset: Offset to read from (default: current offset)

        Returns:
            The byte read as an integer.
        """
        data: bytes = self.read(size=1, offset=offset)
        n: int = len(data)
        if n == 0:
            return EOF
        return data

    def write(self, data: bytes, **kwargs) -> None:
        """Replace file contents with bytes using an exclusive lock.

        Args:
            data: The bytes to write to the file
            append: Whether to append to the file (default: self.append)
            offset: Offset to navigate to after writing (default: -1 for no change)
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        append: int = kwargs.pop("append", self.append)
        offset: int = kwargs.pop("offset", -1)
        not_buffer: bool = not is_buffer(self.buffer)
        try:
            if not_buffer:
                ex_lock(handle)
            handle.seek(0, append)
            handle.truncate(0) if append == 0 else None
            handle.write(data)
            handle.flush()
        finally:
            if not_buffer:
                unlock(handle)
            if offset >= 0:
                self.to_offset(offset)

    def write_byte(self, b: int, **kwargs) -> None:
        """Write a single byte to the file using an exclusive lock."""
        if n_in_range(b, MIN_VALUE, MAX_VALUE):
            return self.write(bytes([b]), **kwargs)
        raise ValueError(f"Byte value {b} must be in range 0-255.")

    def offset_to_0(self) -> Self:
        """Reset the file read/write offset to 0."""
        self._offset = 0
        return self

    def to_offset(self, o: int) -> Self:
        """Navigate to a specific file read/write offset.

        Args:
            o: The offset to navigate to
        """
        self._offset = o
        return self

    def get_offset(self) -> int:
        """Get the current file read/write offset."""
        return self._offset
