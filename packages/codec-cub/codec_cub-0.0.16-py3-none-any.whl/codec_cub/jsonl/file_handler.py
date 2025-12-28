"""A module for handling JSON Lines (JSONL) files with caching and file locking."""

from __future__ import annotations

from collections.abc import Iterable
import json
from typing import IO, Any

from codec_cub.general.base_file_handler import BaseFileHandler
from codec_cub.general.file_lock import LockExclusive
from funcy_bear.constants.type_constants import StrPath  # noqa: TC001

from .utils import deserialize, filter_items, jsonl_serialize


class JSONLFileHandler[File_T](BaseFileHandler[list[File_T]]):
    """A simple JSONL file handler for reading and writing JSON Lines files."""

    def __init__(
        self,
        file: StrPath,
        mode: str = "a+",
        encoding: str = "utf-8",
        touch: bool = False,
    ) -> None:
        """Initialize the handler with the path to the JSONL file.

        Args:
            file: Path to the JSONL file
            mode: File open mode (default: "a+")
            encoding: File encoding (default: "utf-8")
            touch: Whether to create the file if it doesn't exist (default: False)
        """
        super().__init__(file, mode=mode, encoding=encoding, touch=touch)

    def prepare(self, data: list[dict | str] | Iterable) -> list[str]:
        """Prepare data for writing to the JSONL file.

        Args:
            data: A list of dictionaries or strings to be written to the file.

        Returns:
            A list of strings, each representing a line in the JSONL file.
        """
        if isinstance(data, Iterable) and not isinstance(data, list):
            data = list(data)
        return [ln if isinstance(ln, str) else json.dumps(ln, ensure_ascii=False) for ln in filter_items(data)]

    def splitlines(self) -> list[str]:
        """Return all lines in the file as strings.

        Returns:
            A list of strings, each representing a line in the JSONL file.
        """
        lines: list[File_T] = self.readlines()
        if all(isinstance(ln, dict) for ln in lines):
            return [json.dumps(ln, ensure_ascii=False) for ln in lines]
        return [str(ln) for ln in lines]

    def read(self, **kwargs) -> list[File_T] | None:
        """Read data from the JSON file.

        Returns:
            A list of dictionaries or strings read from the file.
        """
        handle: IO | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        data: list[File_T] = deserialize(handle, **kwargs)
        if not data:
            return None
        return data

    def readlines(self, start: int = 0, stop: int | None = None) -> list[File_T]:
        """Read all lines from the JSONL file.

        Args:
            start: The starting index of lines to read. Default is 0.
            stop: The ending index of lines to read. Default is -1 (read all).

        Returns:
            A list of dictionaries or strings read from the file.
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            return []
        data: list[File_T] | None = self.read()
        if data is None:
            return []
        return data[start:stop] if stop is not None else data[start:]

    def readline(self, size: int = -1) -> File_T | str:
        """Read a single line from the JSONL file.

        Args:
            size: The index of the line to read. Default is -1 (read the last line).

        Returns:
            A single dictionary or string read from the file, or an empty string if the file is empty.
        """
        lines = self.readlines()
        start: int = 0 if size >= 0 else max(0, len(lines) + size)
        stop: int | None = size + 1 if size >= 0 else None
        lines: list[File_T] = lines[start:stop] if stop is not None else lines[start:]
        return lines[0] if lines else ""

    def write(self, data: list[File_T], **_) -> None:
        """Write data to the JSON file, replacing existing content.

        Args:
            data: A list of dictionaries or strings to be written to the file.
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        with LockExclusive(handle):
            handle.seek(0)
            handle.truncate(0)
            handle.flush()
            lines: list[str] = jsonl_serialize(data)
            handle.writelines(f"{line}\n" for line in lines)
            handle.flush()

    def writelines(self, lines: Iterable, offset: int = 0, whence: int = 2) -> None:
        """Append multiple lines to the JSONL file.

        Args:
            lines: An iterable of dictionaries or strings to be written to the file.
            offset: The offset to seek to before writing. Default is 0.
            whence: The reference point for the offset. Default is 2 (end of file

        Raises:
            TypeError: If the row is not a string or dictionary.
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        with LockExclusive(handle):
            handle.seek(offset, whence)
            for ln in self.prepare(lines):
                handle.write(f"{ln}\n")
            handle.flush()  # Force write to disk
