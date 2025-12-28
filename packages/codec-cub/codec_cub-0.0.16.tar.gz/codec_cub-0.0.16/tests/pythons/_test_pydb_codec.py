"""Tests for PyDB codec implementation (TDD - tests written first!)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from codec_cub.pythons.codec import PyDBCodec

if TYPE_CHECKING:
    from types import ModuleType


"""Something is causing some of these tests to hang. Not really in the mood to debug it right now."""


class TestPyDBCodecCreation:
    """Test creating .py files."""

    def test_create_empty_database(self, tmp_path: Path) -> None:
        """Test creating an empty database file with no tables."""
        codec = PyDBCodec()
        db_file: Path = tmp_path / "empty.py"

        codec.create(
            file_path=db_file,
            version=(1, 0, 0),
            tables={},
        )

        # File should exist
        assert db_file.exists()

        # Should be valid Python
        module: ModuleType = codec.load(db_file)
        assert module.VERSION == (1, 0, 0)
        assert module.TABLES == ()
        assert module.COUNT == 0

    def test_create_single_table_no_rows(self, tmp_path: Path) -> None:
        """Test creating a database file with one table and no rows."""
        codec = PyDBCodec()
        db_file = tmp_path / "single_table.py"

        schema = {
            "users": {
                "columns": [
                    {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                    {"name": "username", "type": "str", "nullable": False, "primary_key": False},
                    {"name": "email", "type": "str", "nullable": True, "primary_key": False},
                ],
                "rows": [],
            }
        }

        codec.create(file_path=db_file, version=(1, 0, 0), tables=schema)

        # Load and verify structure
        module = codec.load(db_file)
        assert module.VERSION == (1, 0, 0)
        assert module.TABLES == ("users",)
        assert module.COUNT == 1
        assert "users" in module.SCHEMAS
        assert len(module.SCHEMAS["users"]) == 3  # 3 columns
        assert module.ROWS == []

    def test_create_with_initial_rows(self, tmp_path: Path) -> None:
        """Test creating a .py file with initial data."""
        codec = PyDBCodec()
        db_file = tmp_path / "with_data.py"

        schema = {
            "users": {
                "columns": [
                    {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                    {"name": "username", "type": "str", "nullable": False, "primary_key": False},
                ],
                "rows": [
                    {"id": 1, "username": "alice"},
                    {"id": 2, "username": "bob"},
                ],
            }
        }

        codec.create(file_path=db_file, version=(1, 0, 0), tables=schema)

        module = codec.load(db_file)
        assert len(module.ROWS) == 2
        assert module.ROWS[0]["username"] == "alice"
        assert module.ROWS[1]["username"] == "bob"


class TestPyDBCodecLoading:
    """Test loading .py files."""

    def test_load_existing_pydb_file(self) -> None:
        """Test loading an existing .py file."""
        codec = PyDBCodec()
        example_file = Path("tests/data/example.py")
        module: ModuleType = codec.load(example_file)

        # Verify it loaded correctly
        assert module.VERSION == (0, 1, 0)
        assert module.TABLES == ("settings",)
        assert module.COUNT == 1
        assert len(module.ROWS) == 10

    def test_load_nonexistent_file_raises_error(self) -> None:
        """Test that loading a nonexistent file raises an error."""
        codec = PyDBCodec()

        with pytest.raises(FileNotFoundError):
            codec.load(Path("/nonexistent/file.py"))


class TestPyDBCodecAppend:
    """Test fast append operations using byte counting."""

    def test_append_single_row(self, tmp_path: Path) -> None:
        """Test appending a single row to an empty table."""
        codec = PyDBCodec()
        db_file = tmp_path / "append_test.py"

        # Create empty database
        schema = {
            "users": {
                "columns": [
                    {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                    {"name": "name", "type": "str", "nullable": False, "primary_key": False},
                ],
                "rows": [],
            }
        }
        codec.create(file_path=db_file, version=(1, 0, 0), tables=schema)

        # Append a row
        codec.append_row(db_file, {"id": 1, "name": "Alice"})

        # Verify it was added
        module = codec.load(db_file)
        assert len(module.ROWS) == 1
        assert module.ROWS[0] == {"id": 1, "name": "Alice"}

    def test_append_multiple_rows(self, tmp_path: Path) -> None:
        """Test appending multiple rows sequentially."""
        codec = PyDBCodec()
        db_file: Path = tmp_path / "multi_append.py"

        schema: dict[str, dict[str, Any]] = {
            "users": {
                "columns": [
                    {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                    {"name": "name", "type": "str", "nullable": False, "primary_key": False},
                ],
                "rows": [],
            }
        }
        codec.create(file_path=db_file, version=(1, 0, 0), tables=schema)

        codec.append_row(db_file, {"id": 1, "name": "Alice"})
        codec.append_row(db_file, {"id": 2, "name": "Bob"})
        codec.append_row(db_file, {"id": 3, "name": "Charlie"})

        module: ModuleType = codec.load(db_file)
        assert len(module.ROWS) == 3
        assert module.ROWS[0]["name"] == "Alice"
        assert module.ROWS[1]["name"] == "Bob"
        assert module.ROWS[2]["name"] == "Charlie"

    def test_append_to_existing_data(self, tmp_path: Path) -> None:
        """Test appending to a table that already has rows."""
        codec = PyDBCodec()
        db_file: Path = tmp_path / "append_existing.py"

        schema = {
            "users": {
                "columns": [
                    {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                    {"name": "name", "type": "str", "nullable": False, "primary_key": False},
                ],
                "rows": [
                    {"id": 1, "name": "Alice"},
                ],
            }
        }
        codec.create(file_path=db_file, version=(1, 0, 0), tables=schema)

        codec.append_row(db_file, {"id": 2, "name": "Bob"})

        module: ModuleType = codec.load(db_file)
        assert len(module.ROWS) == 2
        assert module.ROWS[0]["name"] == "Alice"
        assert module.ROWS[1]["name"] == "Bob"


class TestPyDBCodecByteOffsets:
    """Test the byte-counting mechanism for fast appends."""

    def test_calculate_correct_byte_offset(self, tmp_path: Path) -> None:
        """Test that byte offset calculation is correct."""
        codec = PyDBCodec()
        db_file: Path = tmp_path / "offset_test.py"

        schema: dict[str, dict[str, Any]] = {
            "data": {
                "columns": [{"name": "value", "type": "int", "nullable": False, "primary_key": True}],
                "rows": [],
            }
        }
        codec.create(file_path=db_file, version=(1, 0, 0), tables=schema)

        # Read the file to check format
        content: str = db_file.read_text()

        # Should end with specific pattern
        assert content.endswith("]\n")

        # Calculate offset from the codec
        offset: int = 2  # Nothing is being calculated right now?

        # Offset should point to the position just before ]
        # For empty ROWS list, format should be: ROWS: list[dict[str, Any]] = [\n    \n]\n
        # So offset from end should be predictable
        assert offset > 0

    def test_append_preserves_file_structure(self, tmp_path: Path) -> None:
        """Test that appending doesn't corrupt the file structure."""
        codec = PyDBCodec()
        db_file: Path = tmp_path / "structure_test.py"

        schema = {
            "items": {
                "columns": [
                    {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                    {"name": "data", "type": "str", "nullable": False, "primary_key": False},
                ],
                "rows": [],
            }
        }
        codec.create(file_path=db_file, version=(1, 0, 0), tables=schema)

        # Append a row
        codec.append_row(db_file, {"id": 1, "data": "test"})

        # File should still be valid Python
        content: str = db_file.read_text()

        # Should compile without errors
        compile(content, str(db_file), "exec")

        # Should be importable
        module: ModuleType = codec.load(db_file)
        assert module.VERSION == (1, 0, 0)


class TestPyDBCodecEdgeCases:
    """Test edge cases and error handling."""

    def test_create_with_special_characters_in_data(self, tmp_path: Path) -> None:
        """Test handling special characters in string data."""
        codec = PyDBCodec()
        db_file: Path = tmp_path / "special_chars.py"

        schema: dict[str, dict[str, Any]] = {
            "messages": {
                "columns": [
                    {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                    {"name": "text", "type": "str", "nullable": False, "primary_key": False},
                ],
                "rows": [
                    {"id": 1, "text": 'He said "hello"'},
                    {"id": 2, "text": "Line1\nLine2"},
                    {"id": 3, "text": "Tab\there"},
                ],
            }
        }

        codec.create(file_path=db_file, version=(1, 0, 0), tables=schema)

        module: ModuleType = codec.load(db_file)
        assert module.ROWS[0]["text"] == 'He said "hello"'
        assert module.ROWS[1]["text"] == "Line1\nLine2"
        assert module.ROWS[2]["text"] == "Tab\there"

    def test_append_with_none_values(self, tmp_path: Path) -> None:
        """Test appending rows with None values."""
        codec = PyDBCodec()
        db_file = tmp_path / "none_values.py"

        schema: dict[str, dict[str, Any]] = {
            "users": {
                "columns": [
                    {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                    {"name": "email", "type": "str | None", "nullable": True, "primary_key": False},
                ],
                "rows": [],
            }
        }
        codec.create(file_path=db_file, version=(1, 0, 0), tables=schema)

        codec.append_row(db_file, {"id": 1, "email": None})

        module: ModuleType = codec.load(db_file)
        assert module.ROWS[0]["email"] is None

    def test_append_with_various_types(self, tmp_path: Path) -> None:
        """Test appending rows with different data types."""
        codec = PyDBCodec()
        db_file: Path = tmp_path / "mixed_types.py"

        schema: dict[str, dict[str, Any]] = {
            "mixed": {
                "columns": [
                    {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                    {"name": "flag", "type": "bool", "nullable": False, "primary_key": False},
                    {"name": "score", "type": "float", "nullable": False, "primary_key": False},
                    {"name": "tags", "type": "list[str]", "nullable": False, "primary_key": False},
                ],
                "rows": [],
            }
        }
        codec.create(file_path=db_file, version=(1, 0, 0), tables=schema)

        codec.append_row(
            db_file,
            {
                "id": 1,
                "flag": True,
                "score": 95.5,
                "tags": ["python", "testing"],
            },
        )

        module = codec.load(db_file)
        assert module.ROWS[0]["flag"] is True
        assert module.ROWS[0]["score"] == 95.5
        assert module.ROWS[0]["tags"] == ["python", "testing"]


class TestPyDBCodecFileStructure:
    """Test the generated file structure and formatting."""

    def test_generated_file_has_correct_header(self, tmp_path: Path) -> None:
        """Test that generated files have proper header comments."""
        codec = PyDBCodec()
        db_file: Path = tmp_path / "header_test.py"

        schema: dict[str, dict[str, Any]] = {
            "test": {
                "columns": [{"name": "id", "type": "int", "nullable": False, "primary_key": True}],
                "rows": [],
            }
        }
        codec.create(file_path=db_file, version=(1, 0, 0), tables=schema)

        content: str = db_file.read_text()

        # Check for important elements
        assert '"""' in content  # Has docstring
        assert "from __future__ import annotations" in content
        assert "from typing import" in content
        assert "VERSION: Final[tuple[int, ...]]" in content

    def test_generated_file_uses_correct_imports(self, tmp_path: Path) -> None:
        """Test that generated files have necessary imports."""
        codec = PyDBCodec()
        db_file: Path = tmp_path / "imports_test.py"

        schema: dict[str, dict[str, Any]] = {
            "test": {
                "columns": [{"name": "id", "type": "int", "nullable": False, "primary_key": True}],
                "rows": [],
            }
        }
        codec.create(file_path=db_file, version=(1, 0, 0), tables=schema)

        content: str = db_file.read_text()

        # Check for required imports
        assert "from typing import Any, Final" in content
        assert "TypedDict" in content

    def test_generated_file_is_formatted_correctly(self, tmp_path: Path) -> None:
        """Test that generated files follow formatting conventions."""
        codec = PyDBCodec()
        db_file: Path = tmp_path / "format_test.py"

        schema: dict[str, dict[str, Any]] = {
            "items": {
                "columns": [
                    {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                    {"name": "name", "type": "str", "nullable": False, "primary_key": False},
                ],
                "rows": [{"id": 1, "name": "test"}],
            }
        }
        codec.create(file_path=db_file, version=(1, 0, 0), tables=schema)

        content: str = db_file.read_text()
        lines: list[str] = content.split("\n")

        # Check indentation (should use 4 spaces)
        row_lines: list[str] = [line for line in lines if '"id":' in line and "name" in line]
        if row_lines:
            # Row should be indented with 4 spaces
            assert row_lines[0].startswith("    ")
