"""TOML file handler for Bear Dereth."""

from __future__ import annotations

from enum import IntFlag, auto
import tomllib
from typing import IO, TYPE_CHECKING, Any, Self

from frozen_cub.utils import filter_out_nones, none_to_null as _none_to_null, null_to_none as _null_to_none
import tomli_w

from codec_cub.general.base_file_handler import BaseFileHandler
from codec_cub.general.file_lock import LockExclusive, LockShared

if TYPE_CHECKING:
    from pathlib import Path

TomlData = dict[str, Any]


class TomlWriteOpts(IntFlag):
    """Options for writing TOML files."""

    NONE = auto()
    SORT_KEYS = auto()
    EXCLUDE_NONE = auto()
    CONVERT_NONE = auto()


class TomlFileHandler(BaseFileHandler[TomlData]):
    """TOML file handler with caching and utilities."""

    def __init__(self, file: Path | str, touch: bool = False) -> None:
        """Initialize the handler with a file path.

        Args:
            path: Path to the TOML file
        """
        super().__init__(file, mode="r+", encoding="utf-8", touch=touch)

    def read(self, **kwargs) -> TomlData | None:
        """Read the entire file (or up to n chars) as text with a shared lock."""
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        with LockShared(handle):
            handle.seek(0)
            data: str = handle.read(kwargs.pop("n", -1))
            convert_none: TomlWriteOpts = kwargs.get("convert_none", TomlWriteOpts.CONVERT_NONE)
            return self.to_dict(data, write_opts=convert_none) if data else None

    def write(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        data: TomlData,
        *,
        write_opts: TomlWriteOpts = TomlWriteOpts.NONE,
    ) -> None:
        """Replace file contents with text using an exclusive lock.

        Args:
            data: Data to write to the TOML file
            write_opts: Options for writing the TOML file

        Raises:
            ValueError: If file cannot be written
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")

        with LockExclusive(handle):
            handle.seek(0)
            handle.truncate(0)
            output: str = self.to_string(data, write_opts=write_opts) if isinstance(data, dict) else data
            handle.write(output)
            handle.flush()

    def to_dict(self, s: str, write_opts: TomlWriteOpts = TomlWriteOpts.NONE) -> dict[str, Any]:
        """Parse a TOML string into a dictionary.

        Args:
            s: TOML string to parse
            convert_none: Whether to convert "null" strings to None

        Returns:
            Parsed TOML data as dictionary

        Raises:
            tomllib.TOMLDecodeError: If file contains invalid TOML
            ValueError: If file cannot be read
        """
        try:
            parsed = tomllib.loads(s)
            if write_opts & TomlWriteOpts.CONVERT_NONE:
                parsed: dict[str, Any | None] = self.null_to_none(parsed)
            return parsed
        except tomllib.TOMLDecodeError as e:
            raise ValueError(f"Invalid TOML in {self.file}: {e}") from e
        except Exception as e:
            raise ValueError(f"Error reading TOML file {self.file}: {e}") from e

    def to_string(
        self,
        data: TomlData,
        *,
        write_opts: TomlWriteOpts = TomlWriteOpts.NONE,
    ) -> str:
        """Convert data to TOML string.

        Args:
            data: Data to serialize
            write_opts: Options for writing the TOML file

        Returns:
            TOML formatted string

        Raises:
            ValueError: If data cannot be serialized
        """
        # sort_keys: bool = bool(write_opts & TomlWriteOpts.SORT_KEYS)
        exclude_none: bool = bool(write_opts & TomlWriteOpts.EXCLUDE_NONE)
        convert_none: bool = bool(write_opts & TomlWriteOpts.CONVERT_NONE)
        try:
            if convert_none:
                data = self.none_to_null(data)
            if exclude_none:
                data = filter_out_nones(data)
            return tomli_w.dumps(data)
        except Exception as e:
            raise ValueError(f"Cannot serialize data to TOML: {e}") from e

    def null_to_none(self, data: TomlData) -> TomlData:
        """Convert "null" strings in the dictionary to None.

        Args:
            data: Data dictionary to convert
        Returns:
            Converted data dictionary
        """
        return _null_to_none(data)

    def none_to_null(self, data: TomlData) -> TomlData:
        """Convert None values in the dictionary to "null" strings.

        Args:
            data: Data dictionary to convert
        Returns:
            Converted data dictionary
        """
        return _none_to_null(data)

    def get_section(
        self,
        data: TomlData | None,
        section: str,
        default: TomlData | None = None,
    ) -> dict[str, Any] | None:
        """Get a specific section from TOML data.

        Args:
            data: TOML data to search
            section: Section name (supports dot notation like 'tool.poetry')
            default: Default value if section not found

        Returns:
            Section data or default
        """
        current: TomlData | None = data or self.read()
        if current is None or not isinstance(current, dict):
            return default
        for key in section.split("."):
            if not isinstance(current, dict) or key not in current:
                return default
            if isinstance(current, dict) and key in current:
                current = current[key]
        return current if isinstance(current, dict) else default

    def __enter__(self) -> Self:
        """Enter context manager."""
        self.read()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Exit context manager."""


__all__ = ["TomlData", "TomlFileHandler"]
