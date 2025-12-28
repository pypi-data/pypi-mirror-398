"""Simple text file handler for line-agnostic IO with locking.

This is a minimal, reusable file handler intended for formats like
JSON (full-text) or general text. It provides safe read_text and
write_text operations with file locking and lazy handle management.

Note: For JSONL (line-oriented) use JSONLFileHandler, which provides
specialized iter/line APIs.
"""

from __future__ import annotations

import json
import os
from typing import IO, TYPE_CHECKING, Any

from codec_cub.general.base_file_handler import BaseFileHandler
from codec_cub.general.file_lock import LockExclusive, LockShared

if TYPE_CHECKING:
    from funcy_bear.constants.type_constants import StrPath


class TextFileHandler(BaseFileHandler[str]):
    """A simple text file handler with locking and lazy open.

    - Lazily opens the file on first use
    - Uses fcntl file locks for read/write sections
    - Provides read_text(), write_text(), clear(), and basic handle helpers
    """

    def __init__(
        self,
        file: StrPath,
        mode: str = "a+",
        encoding: str = "utf-8",
        touch: bool = False,
    ) -> None:
        """Initialize the text file handler.

        Args:
            file: Path to the text file
            mode: File open mode (default: "a+")
            encoding: File encoding (default: "utf-8")
            touch: Whether to create the file if it doesn't exist (default: False)
        """
        super().__init__(file=file, mode=mode, encoding=encoding, touch=touch)

    def read(self, **kwargs) -> str:
        """Read the entire file (or up to n chars) as text with a shared lock.

        Args:
            n: Number of characters to read (default: -1, read all)

        Returns:
            The file contents as a string, or empty string if file is empty.
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        with LockShared(handle):
            handle.seek(0)
            data: str = handle.read(kwargs.pop("n", -1))
            return data

    def write(self, data: str, **kwargs) -> None:
        """Replace file contents with text using an exclusive lock.

        Args:
            data: The text data to write to the file
            append: Whether to append to the file (default: False)
            end: String to append at the end (default: newline if appending, else empty)
            force: Whether to force flush to disk (default: False)
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        with LockExclusive(handle):
            handle.seek(0)
            append: bool = kwargs.pop("append", False)
            end: str = kwargs.get("end", "\n" if append else "")
            if append:
                handle.seek(0, 2)
            else:
                handle.truncate(0)
            handle.write(data + end)
            handle.flush()
            if kwargs.get("force", False):
                os.fsync(handle.fileno())

    def append(self, data: str | dict, *, end: str = "\n", force: bool = False) -> None:
        """Append a new entry to the WAL with an exclusive lock.

        Args:
            data: The text or dict entry to append
            end: The string to append at the end (default: newline)
            force: Whether to force flush to disk (default: False)
        """
        entry: str = json.dumps(data) if isinstance(data, dict) else data
        self.write(data=entry, append=True, end=end, force=force)
