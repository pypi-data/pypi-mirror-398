"""Tests for ToonFileHandler class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from codec_cub.config import ToonCodecConfig
from codec_cub.toon import ToonFileHandler

if TYPE_CHECKING:
    from pathlib import Path


class TestToonFileHandler:
    """Test suite for ToonFileHandler."""

    def test_write_read_dict(self, tmp_path: Path) -> None:
        """Test writing and reading a dictionary."""
        file_path: Path = tmp_path / "test.toon"
        handler = ToonFileHandler(file_path, touch=True)

        data: dict[str, Any] = {"name": "Bear", "age": 42, "active": True}
        handler.write(data)

        read_data: dict[str, Any] | list[Any] | None = handler.read()
        assert read_data == data

        handler.close()

    def test_write_read_list(self, tmp_path: Path) -> None:
        """Test writing and reading a list."""
        file_path: Path = tmp_path / "test.toon"
        handler = ToonFileHandler(file_path, touch=True)

        data: list[Any] = [1, 2, 3, 4, 5]
        handler.write(data)

        read_data: dict[str, Any] | list[Any] | None = handler.read()
        assert read_data == data

        handler.close()

    def test_write_read_nested(self, tmp_path: Path) -> None:
        """Test writing and reading nested structures."""
        file_path: Path = tmp_path / "test.toon"
        handler = ToonFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "users": [
                {"id": 1, "name": "Bear"},
                {"id": 2, "name": "Claire"},
            ],
            "count": 2,
        }
        handler.write(data)

        read_data: dict[str, Any] | list[Any] | None = handler.read()
        assert read_data == data

        handler.close()

    def test_read_empty_file(self, tmp_path: Path) -> None:
        """Test reading an empty TOON file."""
        file_path: Path = tmp_path / "empty.toon"
        file_path.touch()

        handler = ToonFileHandler(file_path)
        read_data: dict[str, Any] | list[Any] | None = handler.read()
        assert read_data is None

        handler.close()

    def test_to_string(self, tmp_path: Path) -> None:
        """Test converting data to TOON string."""
        file_path: Path = tmp_path / "test.toon"
        handler = ToonFileHandler(file_path, touch=True)

        data: dict[str, Any] = {"name": "Bear", "count": 42}
        toon_str: str = handler.to_string(data)

        assert "name: Bear" in toon_str
        assert "count: 42" in toon_str

        handler.close()

    def test_custom_config(self, tmp_path: Path) -> None:
        """Test handler with custom ToonCodecConfig."""
        file_path: Path = tmp_path / "test.toon"
        config = ToonCodecConfig(delimiter="|", indent_spaces=4)
        handler = ToonFileHandler(file_path, touch=True, config=config)

        data: list[int] = [1, 2, 3]
        handler.write(data)

        read_data: dict[str, Any] | list[Any] | None = handler.read()
        assert read_data == data

        toon_str: str = handler.to_string(data)
        assert "|" in toon_str

        handler.close()

    def test_tabular_array_roundtrip(self, tmp_path: Path) -> None:
        """Test round-trip of root tabular array data."""
        file_path: Path = tmp_path / "tabular.toon"
        handler = ToonFileHandler(file_path, touch=True)

        data: list[dict[str, Any]] = [
            {"id": 1, "name": "Alice", "role": "admin"},
            {"id": 2, "name": "Bob", "role": "user"},
        ]
        handler.write(data)

        read_data: dict[str, Any] | list[Any] | None = handler.read()
        assert read_data == data

        handler.close()

    def test_multiple_write_read_cycles(self, tmp_path: Path) -> None:
        """Test multiple write/read cycles with same handler."""
        file_path: Path = tmp_path / "cycles.toon"
        handler = ToonFileHandler(file_path, touch=True)

        # Cycle 1
        data1: dict[str, Any] = {"name": "Bear", "count": 42}
        handler.write(data1)
        read_data1: dict[str, Any] | list[Any] | None = handler.read()
        assert read_data1 == data1

        # Cycle 2
        data2: list[int] = [10, 20, 30]
        handler.write(data2)
        read_data2: dict[str, Any] | list[Any] | None = handler.read()
        assert read_data2 == data2

        handler.close()

    def test_context_manager(self, tmp_path: Path) -> None:
        """Test using ToonFileHandler as context manager."""
        file_path: Path = tmp_path / "context.toon"

        data: dict[str, Any] = {"framework": "TOON", "version": 2.0}

        with ToonFileHandler(file_path, touch=True) as handler:
            handler.write(data)

        with ToonFileHandler(file_path) as handler:
            read_data: dict[str, Any] | list[Any] | None = handler.read()
            assert read_data == data
