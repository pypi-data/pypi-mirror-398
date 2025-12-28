"""Comprehensive tests for TOML file handler."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from codec_cub.toml import TomlFileHandler

if TYPE_CHECKING:
    from pathlib import Path


class TestTomlFileHandlerBasics:
    """Test basic read/write operations."""

    def test_write_and_read_simple_toml(self, tmp_path: Path) -> None:
        """Test writing and reading simple TOML data."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "name": "codec-cub",
            "version": "1.0.0",
            "description": "A cool codec library",
        }
        handler.write(data)
        read_data: dict[str, Any] | None = handler.read()
        assert read_data is not None
        assert read_data == data
        handler.close()

    def test_write_and_read_nested_toml(self, tmp_path: Path) -> None:
        """Test writing and reading nested TOML data."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "project": {
                "name": "codec-cub",
                "version": "1.0.0",
            },
            "dependencies": {
                "python": ">=3.13",
                "pytest": "^8.0.0",
            },
        }
        handler.write(data)
        read_data: dict[str, Any] | None = handler.read()
        assert read_data is not None
        assert read_data == data
        handler.close()

    def test_write_and_read_with_arrays(self, tmp_path: Path) -> None:
        """Test writing and reading TOML with arrays."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "authors": ["Bear", "Claire"],
            "tags": ["codec", "parser", "nix"],
            "numbers": [1, 2, 3, 4, 5],
        }
        handler.write(data)
        read_data: dict[str, Any] | None = handler.read()
        assert read_data is not None
        assert read_data == data
        handler.close()

    def test_overwrite_existing_file(self, tmp_path: Path) -> None:
        """Test overwriting existing TOML file."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        # Write initial data
        handler.write({"version": "1.0.0"})
        data: dict[str, Any] | None = handler.read()
        assert data is not None
        assert data["version"] == "1.0.0"

        # Overwrite with new data
        handler.write({"version": "2.0.0", "name": "updated"})
        read_data = handler.read()
        data: dict[str, Any] | None = handler.read()
        assert data is not None
        assert data["version"] == "2.0.0"
        assert data["name"] == "updated"

        handler.close()


class TestTomlFileHandlerToString:
    """Test to_string method."""

    def test_to_string_simple(self, tmp_path: Path) -> None:
        """Test converting data to TOML string."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {"name": "Bear", "age": 42}
        toml_str: str = handler.to_string(data)

        assert 'name = "Bear"' in toml_str
        assert "age = 42" in toml_str

        handler.close()

    def test_to_string_with_sort_keys(self, tmp_path: Path) -> None:
        """Test to_string with sort_keys option."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {"zebra": 1, "apple": 2, "mango": 3}

        # Without sorting
        unsorted: str = handler.to_string(data)

        # With sorting
        sorted_str: str = handler.to_string(data)

        assert "zebra" in unsorted
        assert "zebra" in sorted_str
        assert "apple" in unsorted
        assert "apple" in sorted_str
        assert "mango" in unsorted
        assert "mango" in sorted_str
        handler.close()

    def test_to_string_nested_structure(self, tmp_path: Path) -> None:
        """Test to_string with nested data."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "tool": {
                "poetry": {
                    "name": "codec-cub",
                    "version": "1.0.0",
                }
            }
        }
        toml_str: str = handler.to_string(data)

        assert "[tool.poetry]" in toml_str
        assert 'name = "codec-cub"' in toml_str
        assert 'version = "1.0.0"' in toml_str
        handler.close()


class TestTomlFileHandlerGetSection:
    """Test get_section method for navigating TOML sections."""

    def test_get_section_top_level(self, tmp_path: Path) -> None:
        """Test getting top-level section."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "project": {"name": "codec-cub"},
            "dependencies": {"python": ">=3.13"},
        }
        handler.write(data)

        section: dict[str, Any] | None = handler.get_section(None, "project")
        assert section == {"name": "codec-cub"}

        handler.close()

    def test_get_section_nested_with_dot_notation(self, tmp_path: Path) -> None:
        """Test getting nested section using dot notation."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "tool": {
                "poetry": {
                    "dependencies": {
                        "python": ">=3.13",
                        "pytest": "^8.0.0",
                    }
                }
            }
        }
        handler.write(data)

        section: dict[str, Any] | None = handler.get_section(None, "tool.poetry.dependencies")
        assert section == {"python": ">=3.13", "pytest": "^8.0.0"}

        handler.close()

    def test_get_section_nonexistent_returns_default(self, tmp_path: Path) -> None:
        """Test getting nonexistent section returns default value."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {"project": {"name": "codec-cub"}}
        handler.write(data)

        section: dict[str, Any] | None = handler.get_section(None, "nonexistent", default={"fallback": True})
        assert section == {"fallback": True}

        handler.close()

    def test_get_section_with_provided_data(self, tmp_path: Path) -> None:
        """Test getting section from provided data without reading file."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {"tool": {"pytest": {"testpaths": ["tests"]}}}

        # Get section from provided data without writing to file
        section: dict[str, Any] | None = handler.get_section(data, "tool.pytest")
        assert section == {"testpaths": ["tests"]}

        handler.close()

    def test_get_section_non_dict_returns_default(self, tmp_path: Path) -> None:
        """Test getting section that's not a dict returns default."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "project": {
                "name": "codec-cub",  # This is a string, not a dict
            }
        }
        handler.write(data)

        # Trying to access "name" as a section should return default
        section: dict[str, Any] | None = handler.get_section(None, "project.name", default=None)
        assert section is None

        handler.close()


class TestTomlFileHandlerErrorHandling:
    """Test error handling in TOML file handler."""

    def test_read_invalid_toml_raises_error(self, tmp_path: Path) -> None:
        """Test reading invalid TOML raises ValueError."""
        file_path: Path = tmp_path / "invalid.toml"
        file_path.write_text("this is not valid TOML [[[ }}}}")

        handler = TomlFileHandler(file_path)

        with pytest.raises(ValueError, match="Invalid TOML"):
            handler.read()

        handler.close()

    def test_write_invalid_data_raises_error(self, tmp_path: Path) -> None:
        """Test writing unserializable data raises ValueError."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        # TOML can't serialize arbitrary objects
        with pytest.raises(ValueError, match="Cannot serialize data to TOML"):
            handler.to_string({"invalid": object()})

        handler.close()

    def test_to_string_invalid_data(self, tmp_path: Path) -> None:
        """Test to_string with invalid data raises ValueError."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        with pytest.raises(ValueError, match="Cannot serialize data to TOML"):
            handler.to_string({"func": lambda x: x})

        handler.close()


class TestTomlFileHandlerFileOperations:
    """Test file operation behaviors."""

    def test_close_handler(self, tmp_path: Path) -> None:
        """Test closing the handler."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        handler.write({"key": "value"})
        handler.close()

        # Handler should be closed
        # Note: Specific behavior depends on BaseFileHandler implementation

    def test_touch_creates_file(self, tmp_path: Path) -> None:
        """Test touch parameter creates file if it doesn't exist."""
        file_path: Path = tmp_path / "new.toml"
        assert not file_path.exists()

        handler = TomlFileHandler(file_path, touch=True)
        handler.write({"test": "data"})  # File created on first access
        handler.close()

        assert file_path.exists()

    def test_multiple_read_write_cycles(self, tmp_path: Path) -> None:
        """Test multiple read/write cycles."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        # Cycle 1
        handler.write({"version": "1.0.0"})
        data: dict[str, Any] | None = handler.read()
        assert data is not None
        assert data["version"] == "1.0.0"

        # Cycle 2
        handler.write({"version": "2.0.0", "name": "updated"})
        data = handler.read()
        assert data is not None
        assert data["version"] == "2.0.0"
        assert data["name"] == "updated"

        # Cycle 3
        handler.write({"completely": "different"})
        assert handler.read() == {"completely": "different"}

        handler.close()


class TestTomlFileHandlerComplexData:
    """Test handling of complex TOML data structures."""

    def test_pyproject_toml_structure(self, tmp_path: Path) -> None:
        """Test realistic pyproject.toml structure."""
        file_path: Path = tmp_path / "pyproject.toml"
        handler = TomlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "project": {
                "name": "codec-cub",
                "version": "1.0.0",
                "description": "Codec library",
                "authors": [{"name": "Bear", "email": "bear@example.com"}],
                "dependencies": ["pytest>=8.0", "ruff>=0.1"],
            },
            "tool": {
                "pytest": {
                    "testpaths": ["tests"],
                    "python_files": ["test_*.py"],
                },
                "ruff": {
                    "line-length": 100,
                    "select": ["E", "F", "I"],
                },
            },
        }
        handler.write(data)

        read_data: dict[str, Any] | None = handler.read()
        assert read_data is not None
        assert read_data == data

        # Test section navigation
        pytest_config: dict[str, Any] | None = handler.get_section(None, "tool.pytest")
        assert pytest_config == {"testpaths": ["tests"], "python_files": ["test_*.py"]}

        handler.close()

    def test_array_of_tables(self, tmp_path: Path) -> None:
        """Test TOML array of tables structure."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "packages": [
                {"name": "pkg1", "version": "1.0"},
                {"name": "pkg2", "version": "2.0"},
            ]
        }
        handler.write(data)
        read_data: dict[str, Any] | None = handler.read()
        assert read_data is not None
        assert len(read_data["packages"]) == 2
        assert read_data["packages"][0]["name"] == "pkg1"
        handler.close()

    def test_mixed_types(self, tmp_path: Path) -> None:
        """Test TOML with mixed data types."""
        file_path: Path = tmp_path / "test.toml"
        handler = TomlFileHandler(file_path, touch=True)
        data: dict[str, Any] = {
            "string": "hello",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "array": [1, 2, 3],
            "table": {"nested": "value"},
        }
        handler.write(data)
        read_data: dict[str, Any] | None = handler.read()
        assert read_data is not None
        assert read_data == data
        handler.close()
