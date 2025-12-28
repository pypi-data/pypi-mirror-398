"""A dataclass to hold file metadata information."""

from __future__ import annotations

from enum import Enum
from functools import cached_property
from pathlib import Path
import sys
from typing import TYPE_CHECKING

from funcy_bear.constants import GIGABYTES, KILOBYTES, MEGABYTES
from funcy_bear.constants.type_constants import StrPath  # noqa: TC001

from .helpers import get_file_hash, touch as _touch

if TYPE_CHECKING:
    from os import stat_result

    from funcy_bear.protocols.general import PathInfo


IS_BINARY = -1


class OS(Enum):
    """Enum for operating system platforms."""

    WINDOWS = "windows"
    LINUX = "linux"
    DARWIN = "darwin"
    UNKNOWN = "unknown"


def get_platform() -> OS:
    """Get the current operating system platform."""
    platform_str: str = sys.platform.lower()
    if platform_str.startswith("win"):
        return OS.WINDOWS
    if platform_str.startswith("linux"):
        return OS.LINUX
    if platform_str.startswith("darwin"):
        return OS.DARWIN
    return OS.UNKNOWN


class FileInfo(Path):
    """Dataclass to hold file metadata information."""

    def __init__(self, path: StrPath) -> None:
        """Initialize FileInfo with a Path object."""
        self.path: Path = Path(path)

    def touch(self, exist_ok: bool = True, **kwargs) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Create the file if it does not exist."""
        _touch(self.path, exist_ok=exist_ok, **kwargs)

    def __fspath__(self) -> str:
        """Return the file system path representation."""
        return str(self.path)

    def exists(self, **kwargs) -> bool:
        """Check if the file exists."""
        return self.path.exists(**kwargs)

    def is_file(self, **kwargs) -> bool:
        """Check if the path is a file."""
        return self.path.is_file(**kwargs) if self.does_exist else False

    def is_dir(self, **kwargs) -> bool:
        """Check if the path is a directory."""
        return self.path.is_dir(**kwargs) if self.does_exist else False

    def is_symlink(self) -> bool:
        """Check if the path is a symbolic link."""
        return self.path.is_symlink() if self.does_exist else False

    def resolve(self, strict: bool = False) -> Path:
        """Resolve the path to its absolute form."""
        return self.path.resolve(strict=strict)

    def copy(self, dst: StrPath, **kwargs) -> Path:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Copy file to destination.

        Args:
            dst: Destination path
            **kwargs: Additional arguments for Python 3.14+ Path.copy()

        Returns:
            The path to the copied file.
        """
        dest_path = Path(dst)
        if sys.version_info >= (3, 14):
            return self.path.copy(dest_path, **kwargs)
        import shutil

        shutil.copy2(self.path, dest_path)
        return dest_path

    def copy_into(self, dst: StrPath, **kwargs) -> Path:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Copy the file into a new location.

        Args:
            dst: Destination path
            **kwargs: Additional arguments for Python 3.14+ Path.copy_into()

        Returns:
            The path to the copied file.
        """
        dest_path = Path(dst)
        if sys.version_info >= (3, 14):
            return self.path.copy_into(dest_path, **kwargs)
        import shutil

        shutil.copy2(self.path, dest_path)
        return dest_path

    def move(self, dst: StrPath, **kwargs) -> Path:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Move the file to a new location.

        Args:
            dst: Destination path
            **kwargs: Additional arguments for Python 3.14+ Path.move()

        Returns:
            The path to the moved file.
        """
        dest_path = Path(dst)
        if sys.version_info >= (3, 14):
            return self.path.move(dest_path, **kwargs)
        import shutil

        shutil.move(self.path, dest_path)
        return dest_path

    def move_into(self, dst: StrPath, **kwargs) -> Path:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Move the file into a new location.

        Args:
            dst: Destination path
            **kwargs: Additional arguments for Python 3.14+ Path.move_into()

        Returns:
            The path to the moved file.
        """
        dest_path = Path(dst)
        if sys.version_info >= (3, 14):
            return self.path.move_into(dest_path, **kwargs)
        import shutil

        shutil.move(self.path, dest_path)
        return dest_path

    def chmod(self, mode: int, **kwargs) -> None:
        """Change the file's mode."""
        self.path.chmod(mode, **kwargs)

    def rmdir(self, del_all: bool = False) -> None:
        """Remove the directory.

        Args:
            del_all: If True, remove all contents recursively.

        Raises:
            OSError: If the directory is not empty and del_all is False.
        """
        if del_all:
            import shutil

            shutil.rmtree(self.path)
        else:
            self.path.rmdir()

    @property
    def _raw_paths(self) -> tuple[str, ...]:
        """Get the raw paths from the underlying Path object."""
        return self.path._raw_paths  # type: ignore[attr-defined]

    @property
    def _str(self) -> str:
        """Get the string representation of the underlying Path object."""
        return str(self.path)

    @_str.setter
    def _str(self, value: str) -> None:
        """Set the string representation of the underlying Path object."""
        self.path = Path(value)

    @property
    def info(self) -> PathInfo:
        """Get the file info (available in Python 3.14+)."""
        if sys.version_info >= (3, 14):
            return self.path.info
        raise NotImplementedError("Path.info is not available in Python versions below 3.14.")

    @property
    def name(self) -> str:
        """Get the file name."""
        return self.path.name

    @property
    def ext(self) -> str:
        """Get the file extension."""
        return self.path.suffix.lstrip(".")

    @property
    def does_exist(self) -> bool:
        """Check if the file exists."""
        return self.exists()

    @property
    def file_hash(self) -> str:
        """Get the SHA256 hash of the file."""
        if not self.does_exist or not self.is_file():
            return ""
        return get_file_hash(self.path)

    @cached_property
    def is_binary(self) -> bool:
        """Check if the file is binary by attempting to read it as text."""
        if not self.is_file():
            return False
        try:
            self.path.read_text(encoding="utf-8")
            return False
        except UnicodeDecodeError:
            return True

    @cached_property
    def get_stat(self) -> stat_result | None:  # type: ignore[override]
        """Get the file's stat result."""
        if not self.does_exist:
            return None
        return self.path.stat()

    @cached_property
    def size(self) -> int:
        """Get the file size in bytes."""
        return self.get_stat.st_size if self.get_stat is not None else 0

    @cached_property
    def length(self) -> int:
        """Get the number of lines in the file."""
        if not self.does_exist or not self.is_file():
            return 0
        if self.is_binary:
            return IS_BINARY
        return len(self.path.read_text(encoding="utf-8").splitlines())

    @cached_property
    def length_str(self) -> str:
        """Get a human-readable string for the number of lines in the file."""
        if self.length == IS_BINARY:
            return "binary"
        return f"{self.length} lines"

    @cached_property
    def size_str(self) -> str:
        """Get a human-readable file size string."""
        if self.size >= GIGABYTES:
            return f"{self.size / GIGABYTES:.2f} GB"
        if self.size >= MEGABYTES:
            return f"{self.size / MEGABYTES:.2f} MB"
        if self.size >= KILOBYTES:
            return f"{self.size / KILOBYTES:.2f} KB"
        return f"{self.size} bytes"

    @cached_property
    def created(self) -> float | None:
        """Get the file creation time as a timestamp."""
        platform: OS = get_platform()

        if platform is OS.DARWIN and hasattr(self.get_stat, "st_birthtime"):
            return getattr(self.get_stat, "st_birthtime", None)
        if platform is OS.WINDOWS and self.get_stat is not None:
            return self.get_stat.st_ctime
        return self.get_stat.st_mtime if self.get_stat is not None else None

    @cached_property
    def modified(self) -> float | None:
        """Get the file modification time as a timestamp."""
        return self.get_stat.st_mtime if self.get_stat is not None else None

    def invalidate_cache(self) -> None:
        """Invalidate cached properties."""
        for attr in [
            "is_binary",
            "get_stat",
            "size",
            "length",
            "length_str",
            "size_str",
            "created",
            "modified",
            "does_exist",
        ]:
            if attr in self.__dict__:
                del self.__dict__[attr]


# ruff: noqa: PLC0415
