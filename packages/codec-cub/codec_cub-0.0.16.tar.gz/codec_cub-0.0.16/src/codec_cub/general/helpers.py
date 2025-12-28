"""A set of general file utility functions."""

from pathlib import Path
from typing import TYPE_CHECKING

from lazy_bear import LazyLoader

if TYPE_CHECKING:
    import hashlib
else:
    hashlib = LazyLoader("hashlib")


def touch(
    path: str | Path,
    mkdir: bool = False,
    create_file: bool = False,
    exist_ok: bool = True,
    parents: bool = True,
) -> Path:
    """Create a file if it doesn't exist yet and optionally create parent directories.

    This ensures a valid Path object is returned.

    Args:
        path (str | Path): Path to the file to create
        mkdir (bool): Whether to create missing parent directories, defaults to False
        create_file (bool): Whether to create the file if it doesn't exist, defaults to False
            This will create the file even if the file already exists. This can be useful to
            update the file's access and modification times.
        exist_ok (bool): Whether to ignore existing files/directories, defaults to True
        parents (bool): Whether to create parent directories recursively, defaults to True

    Returns:
        pathlib.Path: The Path object for the specified file
    """
    path = Path(path)
    if mkdir and not path.parent.exists():
        path.parent.mkdir(parents=parents, exist_ok=exist_ok)
    if create_file or not path.exists():
        path.touch(exist_ok=exist_ok)
    return path


def get_file_hash(path: Path) -> str:
    """Get a simple SHA256 hash of a file - fast and good enough for change detection.

    Args:
        path: Path to the file to hash

    Returns:
        str: Hex digest of the file contents, or empty string if file doesn't exist
    """
    try:
        return hashlib.sha256(path.read_bytes(), usedforsecurity=False).hexdigest()
    except Exception:
        return ""  # File read error, treat as "no file"


def has_file_changed(path: Path, last_known_hash: str) -> tuple[bool, str]:
    """Function version - check if file changed and return new hash.

    Args:
        path: Path to check
        last_known_hash: Previous hash to compare against

    Returns:
        tuple[bool, str]: (has_changed, current_hash)
    """
    current_hash: str = get_file_hash(path)
    return (current_hash != last_known_hash, current_hash)


class FileWatcher:
    """Simple file change detection using SHA1 hashing."""

    def __init__(self, filepath: str | Path) -> None:
        """Initialize FileWatcher.

        Args:
            filepath: Path to the file to watch
        """
        self.path = Path(filepath)
        self._last_hash: str = get_file_hash(self.path)

    @property
    def changed(self) -> bool:
        """Check if file has changed since last check."""
        return self.has_changed()

    def has_changed(self) -> bool:
        """Check if file has changed since last check.

        Returns:
            bool: True if file changed, False otherwise
        """
        current_hash: str = get_file_hash(self.path)
        if current_hash != self._last_hash:
            self._last_hash = current_hash
            return True
        return False

    @property
    def current_hash(self) -> str:
        """Get current file hash without updating internal state."""
        return get_file_hash(self.path)


class SettingsHelper:
    """Helper class for settings file operations."""

    def __init__(
        self,
        name: str,
        file: str | None,
        path: Path | str | None = None,
        ext: str | None = None,
        *,
        default_exemptions: tuple[str, ...] | frozenset[str] | None = None,
        default_ext: str = "json",
    ) -> None:
        """Initialize SettingsHelper.

        Args:
            name: App name (used as default file name and for default directory)
            file: Optional specific file name (overrides name for filename)
            path: Optional path - can be:
                - Full path to .json file (returns as-is)
                - Directory path (file will be created inside)
                - None (uses default settings directory)
            ext: File extension (default: "json")
            default_exemptions: Optional set of extensions that should use default_ext instead
            default_ext: Default extension to use if ext is in default_exemptions
            mkdir: Whether to create missing directories
        """
        self.name: str = name
        self._file_name: str | None = file
        self._path: Path | str | None = path
        self._ext: str = ext or default_ext
        self.default_exemptions: tuple[str, ...] | frozenset[str] = default_exemptions or frozenset()
        self.default_ext: str = default_ext

    @property
    def file_name(self) -> str:
        """Get the effective file name."""
        if self._file_name is not None:
            return Path(self._file_name).stem
        return self.name

    @property
    def path(self) -> Path:
        """Get the full path to the settings file."""
        from funcy_bear.tools.dir_manager import get_settings_path  # noqa: PLC0415

        if self._path is not None:
            path_value: Path = Path(self._path)
            if path_value.is_file():
                return path_value.parent
            return path_value
        return get_settings_path(self.name)

    @property
    def ext(self) -> str:
        """Get the effective file extension."""
        if self._ext in self.default_exemptions:
            return self.default_ext
        return self._ext

    @property
    def full_path(self) -> Path:
        """Get the full path to the settings file."""
        return self.path / f"{self.file_name}.{self.ext}"


def derive_settings_path(
    name: str,
    file: str | None = None,
    path: Path | str | None = None,
    ext: str | None = None,
    *,
    default_exemptions: tuple[str, ...] | frozenset[str] | None = None,
    default_ext: str = "json",
) -> Path:
    """Get the path to the settings file based on app name, optional file name, and optional path.

    Args:
        name: App name (used as default file name and for default directory)
        file: Optional specific file name (overrides name for filename)
        path: Optional path - can be:
            - Full path to file (returns as-is)
            - Directory path (file will be created inside)
            - None (uses default settings directory)
        ext: File extension (default: "json")
        default_exemptions: Optional set of extensions that should use default_ext instead
        default_ext: Default extension to use if ext is in default_exemptions

    Returns:
        Path: Full path to the settings file
    """
    return SettingsHelper(
        name,
        file,
        path,
        ext,
        default_exemptions=default_exemptions,
        default_ext=default_ext,
    ).full_path
