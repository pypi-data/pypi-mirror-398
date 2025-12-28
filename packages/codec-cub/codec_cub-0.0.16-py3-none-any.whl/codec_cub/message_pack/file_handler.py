"""MessagePack file handler using MsgPackHandler for caching and serialization.

This handler provides MessagePack serialization/deserialization for file-based storage,
leveraging MsgPackHandler's buffer management and caching capabilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from codec_cub.text.bytes_handler import BytesFileHandler

from .msg_pack_handler import MsgPackHandler

if TYPE_CHECKING:
    from pathlib import Path


class MsgPackFileHandler(BytesFileHandler):
    """File handler for MessagePack binary format.

    Uses MsgPackHandler internally for efficient buffer management and
    automatic pack/unpack operations.
    """

    def __init__(
        self,
        file: str | Path,
        mode: str = "r+b",
        touch: bool = False,
    ) -> None:
        """Initialize the MessagePack file handler.

        Args:
            file: Path to the MessagePack file
            buffer: In-memory buffer or buffer type (default: None)
            mode: File open mode (default: "r+b" for binary read/write)
            touch: Whether to create the file if it doesn't exist (default: False)
        """
        super().__init__(file=file, mode=mode, touch=touch)
        self._msgpack: MsgPackHandler | None = None

    @property
    def msgpack_handler(self) -> MsgPackHandler:
        """Get the MsgPackHandler instance (lazy initialization)."""
        if self._msgpack is None:
            self._msgpack = MsgPackHandler()
        return self._msgpack

    def read(self, **kwargs) -> Any | None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Read and unpack MessagePack data from the file.

        Returns:
            Unpacked Python object or None if file is empty
        """
        data: bytes = super().read(**kwargs)
        if not data:
            return None
        return self.msgpack_handler.unpack_one(data)

    def write(self, data: Any, **kwargs) -> None:
        """Write a Python object as MessagePack to the file.

        Args:
            data: Python object to serialize and write
        """
        packed_data: bytes = self.msgpack_handler.pack_one(data)
        super().write(packed_data, **kwargs)

    def close(self) -> None:
        """Close the file handler and clear the MsgPackHandler cache."""
        if self._msgpack is not None:
            self._msgpack.clear()
        super().close()


__all__ = ["MsgPackFileHandler"]
