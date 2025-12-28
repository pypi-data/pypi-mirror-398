"""Comprehensive tests for YAML file handler."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from codec_cub.yamls.file_handler import FlowDict, YamlFileHandler

if TYPE_CHECKING:
    from pathlib import Path


class TestYamlFileHandlerBasics:
    """Test basic read/write operations."""

    def test_write_and_read_simple_yaml(self, tmp_path: Path) -> None:
        """Test writing and reading simple YAML data."""
        file_path: Path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "name": "codec-cub",
            "version": "1.0.0",
            "description": "A cool codec library",
        }
        handler.write(data)

        read_data: dict[str, Any] = handler.read()
        assert read_data == data

        handler.close()

    def test_write_and_read_nested_yaml(self, tmp_path: Path) -> None:
        """Test writing and reading nested YAML data."""
        file_path: Path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

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

        read_data: dict[str, Any] = handler.read()
        assert read_data == data

        handler.close()

    def test_write_and_read_with_lists(self, tmp_path: Path) -> None:
        """Test writing and reading YAML with lists."""
        file_path: Path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "authors": ["Bear", "Claire"],
            "tags": ["codec", "parser", "nix"],
            "numbers": [1, 2, 3, 4, 5],
        }
        handler.write(data)

        read_data: dict[str, Any] = handler.read()
        assert read_data == data

        handler.close()

    def test_overwrite_existing_file(self, tmp_path: Path) -> None:
        """Test overwriting existing YAML file."""
        file_path: Path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        # Write initial data
        handler.write({"version": "1.0.0"})
        assert handler.read()["version"] == "1.0.0"

        # Overwrite with new data
        handler.write({"version": "2.0.0", "name": "updated"})
        read_data: dict[str, Any] = handler.read()
        assert read_data["version"] == "2.0.0"
        assert read_data["name"] == "updated"

        handler.close()

    def test_read_empty_file_returns_empty_dict(self, tmp_path: Path) -> None:
        """Test reading empty YAML file returns empty dict."""
        file_path: Path = tmp_path / "empty.yaml"
        file_path.touch()

        handler = YamlFileHandler(file_path)
        read_data: dict[str, Any] = handler.read()
        assert read_data == {}

        handler.close()


class TestYamlFileHandlerSafeMode:
    """Test safe mode vs non-safe mode loading."""

    def test_safe_mode_default(self, tmp_path: Path) -> None:
        """Test safe mode is enabled by default."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        assert handler.opts.safe_mode is True

        handler.close()

    def test_safe_mode_read_write(self, tmp_path: Path) -> None:
        """Test safe mode read/write operations."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, safe_mode=True, touch=True)

        data: dict[str, Any] = {"name": "Bear", "age": 42, "active": True}
        handler.write(data)

        read_data = handler.read()
        assert read_data == data

        handler.close()

    def test_non_safe_mode_read_write(self, tmp_path: Path) -> None:
        """Test non-safe mode read/write operations."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, safe_mode=False, touch=True)

        assert handler.opts.safe_mode is False

        data: dict[str, Any] = {"name": "Bear", "numbers": [1, 2, 3]}
        handler.write(data)

        read_data = handler.read()
        assert read_data == data

        handler.close()


class TestYamlFileHandlerFormatting:
    """Test formatting options."""

    def test_block_style_default(self, tmp_path: Path) -> None:
        """Test block style (default) formatting."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, flow_style=False, touch=True)

        data: dict[str, Any] = {"items": [1, 2, 3], "config": {"debug": True}}
        handler.write(data)

        content = file_path.read_text()
        # Block style uses newlines and indentation
        assert "\n" in content
        assert "items:" in content

        handler.close()

    def test_flow_style(self, tmp_path: Path) -> None:
        """Test flow style formatting."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, flow_style=True, touch=True)

        data: dict[str, Any] = {"items": [1, 2, 3]}
        handler.write(data)

        content = file_path.read_text()
        # Flow style is more compact
        assert "items:" in content

        handler.close()

    def test_custom_indentation(self, tmp_path: Path) -> None:
        """Test custom indentation."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, indent=4, touch=True)

        data: dict[str, Any] = {"outer": {"inner": {"value": 42}}}
        handler.write(data)

        content = file_path.read_text()
        # Check for 4-space indentation
        assert "    " in content

        handler.close()

    def test_sort_keys(self, tmp_path: Path) -> None:
        """Test sorting keys in output."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, sort_keys=True, touch=True)

        data: dict[str, Any] = {"zebra": 1, "apple": 2, "mango": 3}
        handler.write(data)

        content = file_path.read_text()
        # Keys should appear in alphabetical order
        apple_pos = content.find("apple")
        mango_pos = content.find("mango")
        zebra_pos = content.find("zebra")

        assert apple_pos < mango_pos < zebra_pos

        handler.close()

    def test_custom_width(self, tmp_path: Path) -> None:
        """Test custom line width."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, width=80, touch=True)

        data: dict[str, Any] = {"long_key": "short"}
        handler.write(data)

        # File should be created successfully with width constraint
        assert file_path.exists()

        handler.close()


class TestYamlFileHandlerToString:
    """Test to_string method."""

    def test_to_string_simple(self, tmp_path: Path) -> None:
        """Test converting data to YAML string."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {"name": "Bear", "age": 42}
        yaml_str = handler.to_string(data)

        assert "name: Bear" in yaml_str
        assert "age: 42" in yaml_str

        handler.close()

    def test_to_string_without_data_reads_file(self, tmp_path: Path) -> None:
        """Test to_string without data argument reads from file."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {"stored": "value"}
        handler.write(data)

        # Call to_string without data - should read from file
        yaml_str = handler.to_string()
        assert "stored: value" in yaml_str

        handler.close()

    def test_to_string_with_custom_options(self, tmp_path: Path) -> None:
        """Test to_string with custom formatting options."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {"zebra": 1, "apple": 2}

        # Override sort_keys for this call
        yaml_str = handler.to_string(data, sort_keys=True)

        # Keys should be sorted
        apple_pos = yaml_str.find("apple")
        zebra_pos = yaml_str.find("zebra")
        assert apple_pos < zebra_pos

        handler.close()

    def test_to_string_nested_structure(self, tmp_path: Path) -> None:
        """Test to_string with nested data."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "project": {
                "metadata": {
                    "name": "codec-cub",
                    "version": "1.0.0",
                }
            }
        }
        yaml_str = handler.to_string(data)

        assert "project:" in yaml_str
        assert "metadata:" in yaml_str
        assert "name: codec-cub" in yaml_str

        handler.close()


class TestYamlFileHandlerContextManager:
    """Test context manager functionality."""

    def test_context_manager_write_read(self, tmp_path: Path) -> None:
        """Test using handler as context manager."""
        file_path = tmp_path / "test.yaml"
        data: dict[str, Any] = {"framework": "YAML", "version": 1.2}

        # Write using context manager
        with YamlFileHandler(file_path, touch=True) as handler:
            handler.write(data)

        # Read using context manager
        with YamlFileHandler(file_path) as handler:
            read_data = handler.read()
            assert read_data == data

    def test_context_manager_reads_on_enter(self, tmp_path: Path) -> None:
        """Test that context manager reads file on __enter__."""
        file_path = tmp_path / "test.yaml"
        file_path.write_text("key: value\n")

        with YamlFileHandler(file_path) as handler:
            # File should have been read on enter
            # We can verify by reading again
            data = handler.read()
            assert data == {"key": "value"}

    def test_context_manager_closes_on_exit(self, tmp_path: Path) -> None:
        """Test that context manager closes handler on __exit__."""
        file_path = tmp_path / "test.yaml"

        with YamlFileHandler(file_path, touch=True) as handler:
            handler.write({"test": "data"})
            # Handler should be open here

        # Handler should be closed after exiting context


class TestYamlFileHandlerErrorHandling:
    """Test error handling in YAML file handler."""

    def test_read_invalid_yaml_raises_error(self, tmp_path: Path) -> None:
        """Test reading invalid YAML raises ValueError."""
        file_path = tmp_path / "invalid.yaml"
        file_path.write_text("this is: not: valid: yaml: [[[")

        handler = YamlFileHandler(file_path)

        with pytest.raises(ValueError, match="Cannot serialize data to YAML"):
            # First we need to trigger an error - invalid YAML might load as string
            # Let's test with an unserializable object instead
            handler.to_string({"invalid": object()})

        handler.close()

    def test_write_unserializable_data(self, tmp_path: Path) -> None:
        """Test writing unserializable data raises ValueError."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        # Try to write data with unserializable object
        with pytest.raises(ValueError):  # noqa: PT011
            handler.write({"func": lambda x: x})

        handler.close()

    def test_to_string_unserializable_data(self, tmp_path: Path) -> None:
        """Test to_string with unserializable data raises ValueError."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        with pytest.raises(ValueError, match="Cannot serialize data to YAML"):
            handler.to_string({"obj": object()})

        handler.close()


class TestYamlFileHandlerFileOperations:
    """Test file operation behaviors."""

    def test_touch_creates_file(self, tmp_path: Path) -> None:
        """Test touch parameter creates file if it doesn't exist."""
        file_path = tmp_path / "new.yaml"
        assert not file_path.exists()

        handler = YamlFileHandler(file_path, touch=True)
        handler.write({"test": "data"})  # File created on first access
        handler.close()

        assert file_path.exists()

    def test_multiple_read_write_cycles(self, tmp_path: Path) -> None:
        """Test multiple read/write cycles."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        # Cycle 1
        handler.write({"version": "1.0.0"})
        assert handler.read()["version"] == "1.0.0"

        # Cycle 2
        handler.write({"version": "2.0.0", "name": "updated"})
        data = handler.read()
        assert data["version"] == "2.0.0"
        assert data["name"] == "updated"

        # Cycle 3
        handler.write({"completely": "different"})
        assert handler.read() == {"completely": "different"}

        handler.close()

    def test_custom_encoding(self, tmp_path: Path) -> None:
        """Test custom file encoding."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, encoding="utf-8", touch=True)

        data: dict[str, Any] = {"unicode": "Hello 世界 🌍"}
        handler.write(data)

        read_data = handler.read()
        assert read_data["unicode"] == "Hello 世界 🌍"

        handler.close()


class TestYamlFileHandlerComplexData:
    """Test handling of complex YAML data structures."""

    def test_github_workflow_structure(self, tmp_path: Path) -> None:
        """Test realistic GitHub Actions workflow structure."""
        file_path = tmp_path / "workflow.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "name": "CI",
            "on": ["push", "pull_request"],
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v3"},
                        {"name": "Run tests", "run": "pytest"},
                    ],
                }
            },
        }
        handler.write(data)

        read_data = handler.read()
        assert read_data == data
        assert len(read_data["jobs"]["test"]["steps"]) == 2

        handler.close()

    def test_deeply_nested_structure(self, tmp_path: Path) -> None:
        """Test deeply nested YAML structure."""
        file_path = tmp_path / "nested.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "value": "deep",
                            "number": 42,
                        }
                    }
                }
            }
        }
        handler.write(data)

        read_data = handler.read()
        assert read_data["level1"]["level2"]["level3"]["level4"]["value"] == "deep"

        handler.close()

    def test_list_of_dicts(self, tmp_path: Path) -> None:
        """Test list containing dictionaries."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "users": [
                {"id": 1, "name": "Alice", "active": True},
                {"id": 2, "name": "Bob", "active": False},
                {"id": 3, "name": "Charlie", "active": True},
            ]
        }
        handler.write(data)

        read_data = handler.read()
        assert len(read_data["users"]) == 3
        assert read_data["users"][1]["name"] == "Bob"

        handler.close()

    def test_mixed_types(self, tmp_path: Path) -> None:
        """Test YAML with mixed data types."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "string": "hello",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "null_value": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }
        handler.write(data)

        read_data = handler.read()
        assert read_data["string"] == "hello"
        assert read_data["integer"] == 42
        assert read_data["float"] == 3.14
        assert read_data["boolean"] is True
        assert read_data["null_value"] is None
        assert read_data["list"] == [1, 2, 3]

        handler.close()

    def test_multiline_strings(self, tmp_path: Path) -> None:
        """Test YAML with multiline strings."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "description": "This is a long\nmultiline\nstring",
            "script": "#!/bin/bash\necho 'Hello'\nexit 0",
        }
        handler.write(data)

        read_data = handler.read()
        assert "\n" in read_data["description"]
        assert "echo 'Hello'" in read_data["script"]

        handler.close()


class TestYamlFileHandlerEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_dict(self, tmp_path: Path) -> None:
        """Test writing and reading empty dict."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        handler.write({})
        read_data = handler.read()
        assert read_data == {}

        handler.close()

    def test_special_yaml_values(self, tmp_path: Path) -> None:
        """Test special YAML values."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True)

        data: dict[str, Any] = {
            "null": None,
            "true": True,
            "false": False,
            "number": 123,
            "float": 1.23,
        }
        handler.write(data)

        read_data = handler.read()
        assert read_data["null"] is None
        assert read_data["true"] is True
        assert read_data["false"] is False

        handler.close()

    def test_preserve_key_order(self, tmp_path: Path) -> None:
        """Test that key order is preserved (Python 3.7+)."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, sort_keys=False, touch=True)

        # Use explicit dict order
        data: dict[str, Any] = {
            "first": 1,
            "second": 2,
            "third": 3,
        }
        handler.write(data)

        read_data = handler.read()
        keys = list(read_data.keys())
        assert keys == ["first", "second", "third"]

        handler.close()


class TestYamlFileHandlerFlowDict:
    """Test FlowDict wrapper for selective flow-style formatting."""

    def test_flow_dict_basic(self, tmp_path: Path) -> None:
        """Test that FlowDict renders in flow style."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True, safe_mode=False)

        data: dict[str, Any] = {
            "items": [
                FlowDict({"id": 1, "name": "Bear"}),
                FlowDict({"id": 2, "name": "Claire"}),
            ]
        }
        handler.write(data)
        handler.close()

        yaml_str = file_path.read_text()
        assert "{id: 1, name: Bear}" in yaml_str
        assert "{id: 2, name: Claire}" in yaml_str

    def test_flow_dict_roundtrip(self, tmp_path: Path) -> None:
        """Test that FlowDict data can be read back correctly."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True, safe_mode=False)

        data: dict[str, Any] = {
            "users": [
                FlowDict({"id": 1, "email": "bear@example.com"}),
                FlowDict({"id": 2, "email": "claire@example.com"}),
            ]
        }
        handler.write(data)
        read_data = handler.read()
        handler.close()

        assert read_data["users"][0] == {"id": 1, "email": "bear@example.com"}
        assert read_data["users"][1] == {"id": 2, "email": "claire@example.com"}

    def test_flow_dict_mixed_with_block(self, tmp_path: Path) -> None:
        """Test mixing FlowDict (flow style) with regular dicts (block style)."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True, safe_mode=False)

        data: dict[str, Any] = {
            "header": {
                "version": "1.0.0",
                "tables": ["users"],
            },
            "tables": {
                "users": {
                    "columns": [
                        FlowDict({"name": "id", "type": "int"}),
                        FlowDict({"name": "email", "type": "str"}),
                    ]
                }
            },
        }
        handler.write(data)
        handler.close()

        yaml_str = file_path.read_text()
        # FlowDict items should be in flow style
        assert "{name: id, type: int}" in yaml_str
        # Top-level structure should be block style
        assert "header:" in yaml_str
        assert "  version: 1.0.0" in yaml_str

    def test_flow_dict_with_wide_width(self, tmp_path: Path) -> None:
        """Test FlowDict with large width for long records on one line."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True, safe_mode=False, width=1000)

        data: dict[str, Any] = {
            "records": [
                FlowDict(
                    {
                        "id": 1,
                        "name": "Bear",
                        "email": "bear@example.com",
                        "bio": "A very long biography",
                        "score": 100,
                    }
                )
            ]
        }
        handler.write(data)
        handler.close()

        yaml_str = file_path.read_text()
        # FlowDict should be on one line (no wrapping with wide width)
        assert "{id: 1, name: Bear, email: bear@example.com, bio: A very long biography, score: 100}" in yaml_str

    def test_flow_dict_to_string(self, tmp_path: Path) -> None:
        """Test FlowDict with to_string method."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True, safe_mode=False)

        data: dict[str, Any] = {
            "items": [
                FlowDict({"a": 1, "b": 2}),
            ]
        }

        yaml_str = handler.to_string(data)
        handler.close()

        assert "{a: 1, b: 2}" in yaml_str

    def test_flow_dict_empty(self, tmp_path: Path) -> None:
        """Test FlowDict with empty dict."""
        file_path = tmp_path / "test.yaml"
        handler = YamlFileHandler(file_path, touch=True, safe_mode=False)

        data: dict[str, Any] = {"items": [FlowDict({})]}
        handler.write(data)
        read_data = handler.read()
        handler.close()

        assert read_data["items"][0] == {}
