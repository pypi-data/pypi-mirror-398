"""TOON file handler for codec-cub."""

from __future__ import annotations

from typing import IO, TYPE_CHECKING, Any

from codec_cub.general.base_file_handler import BaseFileHandler
from codec_cub.general.file_lock import LockShared
from codec_cub.text.file_handler import TextFileHandler
from codec_cub.toon.codec import ToonCodec

if TYPE_CHECKING:
    from pathlib import Path

    from codec_cub.config import ToonCodecConfig


type ToonData = dict[str, Any] | list[Any]


class ToonFileHandler(BaseFileHandler[ToonData]):
    """TOON file handler with encoding/decoding and file I/O."""

    def __init__(
        self,
        file: Path | str,
        touch: bool = False,
        config: ToonCodecConfig | None = None,
    ) -> None:
        """Initialize the handler with a file path.

        Args:
            file: Path to the TOON file
            touch: Whether to create the file if it doesn't exist (default: False)
            config: ToonCodecConfig for customizing encoding/decoding behavior
        """
        super().__init__(file, mode="r", touch=touch)
        self._txt_handler: TextFileHandler | None = None
        self._codec: ToonCodec | None = None
        self._config: ToonCodecConfig | None = config

    @property
    def txt_handler(self) -> TextFileHandler:
        """Get a text file handler for reading/writing TOON data."""
        if self._txt_handler is None:
            self._txt_handler = TextFileHandler(self.file, mode="r+", encoding="utf-8")
        return self._txt_handler

    @property
    def codec(self) -> ToonCodec:
        """Get the ToonCodec instance (lazy initialization)."""
        if self._codec is None:
            self._codec = ToonCodec(self._config) if self._config else ToonCodec()
        return self._codec

    def read(self, **_) -> ToonData | None:
        """Read and parse TOON file.

        Returns:
            Parsed TOON data (dict or list) or None if file is empty

        Raises:
            ValueError: If file cannot be read or contains invalid TOON
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")

        with LockShared(handle=handle):
            try:
                handle.seek(0)
                content: str = handle.read()
                if not content.strip():
                    return None
                return self.codec.decode(content)
            except Exception as e:
                raise ValueError(f"Error reading TOON file {self.file}: {e}") from e

    def write(self, data: ToonData, **_) -> None:
        """Write data as TOON to file.

        Args:
            data: Data to serialize as TOON (dict or list)

        Raises:
            ValueError: If file cannot be written or data cannot be encoded
        """
        if self.handle() is None:
            raise ValueError("File handle is not available.")

        try:
            toon_str: str = self.to_string(data)
            txt_handle: IO[Any] | None = self.txt_handler.handle()
            if txt_handle is not None:
                txt_handle.seek(0)
                txt_handle.truncate()
            self.txt_handler.write(toon_str)
            if txt_handle is not None:
                txt_handle.flush()
        except Exception as e:
            raise ValueError(f"Error writing TOON file {self.file}: {e}") from e

    def to_string(self, data: ToonData) -> str:
        """Convert data to TOON string.

        Args:
            data: Data to serialize (dict or list)

        Returns:
            TOON formatted string

        Raises:
            ValueError: If data cannot be serialized
        """
        try:
            return self.codec.encode(data)
        except Exception as e:
            raise ValueError(f"Cannot serialize data to TOON: {e}") from e

    def close(self) -> None:
        """Close the TOON file handler and associated text handler."""
        super().close()
        if self._txt_handler is not None:
            self._txt_handler.close()


__all__ = ["ToonData", "ToonFileHandler"]
