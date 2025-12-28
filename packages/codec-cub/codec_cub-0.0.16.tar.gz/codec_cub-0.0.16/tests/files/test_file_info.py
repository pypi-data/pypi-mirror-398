"""Tests for FileInfo dataclass."""

from pathlib import Path
import time
from typing import TYPE_CHECKING

from codec_cub.general.file_info import FileInfo

if TYPE_CHECKING:
    from os import stat_result


class TestFileInfoBasics:
    """Test basic FileInfo functionality."""

    def test_create_fileinfo(self, temp_file_with_text: Path) -> None:
        """Test creating FileInfo instance."""
        info = FileInfo(path=temp_file_with_text)
        assert info.path == temp_file_with_text

    def test_name_property(self, temp_file_with_text: Path) -> None:
        """Test name property returns file name."""
        info = FileInfo(path=temp_file_with_text)
        assert info.name == "test_file.txt"

    def test_ext_property(self, temp_file_with_text: Path) -> None:
        """Test ext property returns extension without dot."""
        info = FileInfo(path=temp_file_with_text)
        assert info.ext == "txt"

    def test_ext_property_no_extension(self, tmp_path: Path) -> None:
        """Test ext property with file having no extension."""
        file: Path = tmp_path / "noext"
        file.touch()
        info = FileInfo(path=file)
        assert info.ext == ""

    def test_exists_property_true(self, temp_file_with_text: Path) -> None:
        """Test exists returns True for existing file."""
        info = FileInfo(path=temp_file_with_text)
        assert info.does_exist is True

    def test_exists_property_false(self, nonexistent_file: Path) -> None:
        """Test exists returns False for nonexistent file."""
        info = FileInfo(path=nonexistent_file)
        assert info.does_exist is False

    def test_is_file_property_true(self, temp_file_with_text: Path) -> None:
        """Test is_file returns True for file."""
        info = FileInfo(path=temp_file_with_text)
        assert info.is_file() is True

    def test_is_file_property_false_nonexistent(self, nonexistent_file: Path) -> None:
        """Test is_file returns False for nonexistent path."""
        info = FileInfo(path=nonexistent_file)
        assert info.is_file() is False

    def test_is_file_property_false_directory(self, tmp_path: Path) -> None:
        """Test is_file returns False for directory."""
        info = FileInfo(path=tmp_path)
        assert info.is_file() is False


class TestFileInfoTouch:
    """Test touch method."""

    def test_touch_creates_file(self, nonexistent_file: Path) -> None:
        """Test touch creates a new file."""
        info = FileInfo(path=nonexistent_file)
        assert not info.does_exist

        info.touch(create_file=True, exist_ok=True)
        info.invalidate_cache()
        assert info.does_exist
        assert info.is_file()

    def test_touch_updates_existing_file(self, temp_file_with_text: Path) -> None:
        """Test touch updates modification time of existing file."""
        info = FileInfo(path=temp_file_with_text)
        original_mtime: float | None = info.modified

        time.sleep(0.01)  # Ensure time difference
        info.touch(create_file=True, exist_ok=True)
        info.invalidate_cache()
        new_mtime: float | None = info.modified
        assert new_mtime is not None
        assert original_mtime is not None
        assert new_mtime > original_mtime


class TestFileInfoStat:
    """Test stat-related properties."""

    def test_stat_property_existing_file(self, temp_file_with_text: Path) -> None:
        """Test stat property returns stat_result for existing file."""
        info = FileInfo(path=temp_file_with_text)
        stat: stat_result | None = info.stat()

        assert stat is not None
        assert hasattr(stat, "st_size")
        assert hasattr(stat, "st_mtime")
        assert hasattr(stat, "st_ctime")

    def test_stat_property_nonexistent_file(self, nonexistent_file: Path) -> None:
        """Test stat property returns None for nonexistent file."""
        info = FileInfo(path=nonexistent_file)
        assert info.get_stat is None

    def test_size_property(self, temp_file_with_text: Path) -> None:
        """Test size property returns correct file size."""
        info = FileInfo(path=temp_file_with_text)
        expected_size: int = len("Hello, World!")
        assert info.size == expected_size

    def test_size_property_nonexistent(self, nonexistent_file: Path) -> None:
        """Test size returns 0 for nonexistent file."""
        info = FileInfo(path=nonexistent_file)
        assert info.size == 0

    def test_created_property(self, temp_file_with_text: Path) -> None:
        """Test created property returns timestamp."""
        info = FileInfo(path=temp_file_with_text)
        created: float | None = info.created

        assert created is not None
        assert isinstance(created, float)
        assert created > 0

    def test_created_property_nonexistent(self, nonexistent_file: Path) -> None:
        """Test created returns None for nonexistent file."""
        info = FileInfo(path=nonexistent_file)
        assert info.created is None

    def test_modified_property(self, temp_file_with_text: Path) -> None:
        """Test modified property returns timestamp."""
        info = FileInfo(path=temp_file_with_text)
        modified: float | None = info.modified

        assert modified is not None
        assert isinstance(modified, float)
        assert modified > 0

    def test_modified_property_nonexistent(self, nonexistent_file: Path) -> None:
        """Test modified returns None for nonexistent file."""
        info = FileInfo(path=nonexistent_file)
        assert info.modified is None


class TestFileInfoHash:
    """Test file hash functionality."""

    def test_file_hash_property(self, temp_file_with_text: Path) -> None:
        """Test file_hash property returns SHA256 hash."""
        info = FileInfo(path=temp_file_with_text)
        file_hash: str = info.file_hash

        assert file_hash
        assert isinstance(file_hash, str)
        assert len(file_hash) == 64  # SHA256 hex digest length

    def test_file_hash_consistent(self, temp_file_with_text: Path) -> None:
        """Test file_hash returns same value for same content."""
        info = FileInfo(path=temp_file_with_text)
        hash1: str = info.file_hash
        hash2: str = info.file_hash

        assert hash1 == hash2

    def test_file_hash_changes_on_content_change(self, temp_file_with_text: Path) -> None:
        """Test file_hash changes when file content changes."""
        info = FileInfo(path=temp_file_with_text)
        hash1: str = info.file_hash

        temp_file_with_text.write_text("Different content")
        hash2: str = info.file_hash

        assert hash1 != hash2

    def test_file_hash_nonexistent(self, nonexistent_file: Path) -> None:
        """Test file_hash returns empty string for nonexistent file."""
        info = FileInfo(path=nonexistent_file)
        assert info.file_hash == ""

    def test_file_hash_directory(self, tmp_path: Path) -> None:
        """Test file_hash returns empty string for directory."""
        info = FileInfo(path=tmp_path)
        assert info.file_hash == ""
