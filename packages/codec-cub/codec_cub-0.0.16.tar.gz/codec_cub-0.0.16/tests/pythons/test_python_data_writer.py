"""Tests for PythonFileHandler."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from codec_cub.pythons import ClassBuilder, FunctionBuilder, PythonFileHandler
from codec_cub.pythons.parts import Attribute

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def temp_file(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a temporary Python file for testing."""
    return tmp_path_factory.mktemp("data") / "test_output.py"


class TestPythonFileHandlerBasics:
    """Test basic PythonFileHandler functionality."""

    def test_write_simple_variables(self, temp_file: Path) -> None:
        """Test writing simple variables without type hints."""
        writer = PythonFileHandler(temp_file)
        writer.write(
            variables={
                "DEBUG": True,
                "TIMEOUT": 30,
                "NAME": "TestApp",
            }
        )

        content = temp_file.read_text()
        assert "DEBUG = True" in content
        assert "TIMEOUT = 30" in content
        assert "NAME = 'TestApp'" in content

    def test_write_with_docstring(self, temp_file: Path) -> None:
        """Test writing with module docstring."""
        writer = PythonFileHandler(temp_file)
        writer.write(variables={"VERSION": (1, 0, 0)}, docstring="Auto-generated configuration")

        content = temp_file.read_text()
        assert '"""' in content
        assert "Auto-generated configuration" in content

    def test_write_with_type_hints(self, temp_file: Path) -> None:
        """Test writing variables with type hints."""
        writer = PythonFileHandler(temp_file)
        writer.write(
            variables={
                "CONFIG": {"debug": True, "timeout": 30},
                "VERSION": (1, 2, 3),
            },
            type_hints={
                "CONFIG": "dict[str, Any]",
                "VERSION": "tuple[int, int, int]",
            },
        )

        content = temp_file.read_text()
        assert "CONFIG: dict[str, Any]" in content
        assert "VERSION: tuple[int, int, int]" in content
        assert "from typing import Any" in content

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Test that touch=True creates parent directories."""
        nested_file: Path = tmp_path / "nested" / "deep" / "file.py"
        writer = PythonFileHandler(nested_file, touch=True)
        writer.write(variables={"TEST": 123})

        assert nested_file.exists()
        assert nested_file.parent.exists()


class TestPythonFileHandlerDataStructures:
    """Test writing complex data structures."""

    def test_write_nested_dict(self, temp_file: Path) -> None:
        """Test writing nested dictionaries."""
        writer = PythonFileHandler(temp_file)
        writer.write(
            variables={
                "CONFIG": {
                    "database": {"host": "localhost", "port": 5432},
                    "cache": {"enabled": True, "ttl": 300},
                }
            }
        )

        content: str = temp_file.read_text()
        assert "'database'" in content
        assert "'host'" in content
        assert "'localhost'" in content
        assert "'cache'" in content

    def test_write_nested_list(self, temp_file: Path) -> None:
        """Test writing nested lists."""
        writer = PythonFileHandler(temp_file)
        writer.write(
            variables={
                "MATRIX": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
                "NAMES": ["Alice", "Bob", "Charlie"],
            }
        )

        content = temp_file.read_text()
        assert "[[1, 2, 3], [4, 5, 6], [7, 8, 9]]" in content
        assert "['Alice', 'Bob', 'Charlie']" in content

    def test_write_list_of_dicts(self, temp_file: Path) -> None:
        """Test writing list of dictionaries (common pattern)."""
        writer = PythonFileHandler(temp_file)
        writer.write(
            variables={
                "USERS": [
                    {"id": 1, "name": "Alice", "active": True},
                    {"id": 2, "name": "Bob", "active": False},
                ]
            },
            type_hints={"USERS": "list[dict[str, Any]]"},
        )

        content: str = temp_file.read_text()
        assert "USERS: list[dict[str, Any]]" in content
        assert "'id': 1" in content
        assert "'name': 'Alice'" in content

    def test_write_tuples(self, temp_file: Path) -> None:
        """Test writing tuples (including single-element tuples)."""
        writer = PythonFileHandler(temp_file)
        writer.write(
            variables={
                "COORDS": (10, 20, 30),
                "SINGLE": (42,),
                "EMPTY": (),
            }
        )

        content: str = temp_file.read_text()
        assert "COORDS = (10, 20, 30)" in content
        assert "SINGLE = (42,)" in content  # Trailing comma for single element
        assert "EMPTY = ()" in content

    def test_write_none_values(self, temp_file: Path) -> None:
        """Test writing None values."""
        writer = PythonFileHandler(temp_file)
        writer.write(variables={"NULLABLE": None, "CONFIG": {"default": None}})

        content = temp_file.read_text()
        assert "NULLABLE = None" in content
        assert "'default': None" in content


class TestPythonFileHandlerComplexScenarios:
    """Test complex real-world scenarios."""

    def test_unified_data_format_structure(self, temp_file: Path) -> None:
        """Test writing a UnifiedDataFormat-like structure.

        Simulates UnifiedDataFormat.model_dump() output.
        """
        udf_data = {
            "header": {"tables": ["users", "posts"], "version": "1.0.0"},
            "tables": {
                "users": {
                    "name": "users",
                    "columns": [
                        {
                            "name": "id",
                            "type": "int",
                            "nullable": False,
                            "primary_key": True,
                        },
                        {"name": "username", "type": "str", "nullable": False},
                    ],
                    "count": 2,
                    "records": [
                        {"id": 1, "username": "alice"},
                        {"id": 2, "username": "bob"},
                    ],
                },
                "posts": {
                    "name": "posts",
                    "columns": [
                        {"name": "id", "type": "int", "primary_key": True},
                        {"name": "title", "type": "str"},
                        {"name": "user_id", "type": "int"},
                    ],
                    "count": 1,
                    "records": [{"id": 1, "title": "Hello World", "user_id": 1}],
                },
            },
        }

        writer = PythonFileHandler(temp_file)
        writer.write(
            variables={"SAMPLE_UDF": udf_data},
            docstring="Test fixture for UnifiedDataFormat",
            type_hints={"SAMPLE_UDF": "dict[str, Any]"},
        )

        content: str = temp_file.read_text()

        assert "Test fixture for UnifiedDataFormat" in content
        assert "SAMPLE_UDF: dict[str, Any]" in content
        assert "'header'" in content
        assert "'tables'" in content
        assert "'users'" in content
        assert "'records'" in content

        module = {}
        exec(content, module)  # noqa: S102
        assert "SAMPLE_UDF" in module
        print(module["SAMPLE_UDF"])
        assert module["SAMPLE_UDF"]["header"]["tables"] == ["users", "posts"]

    def test_multiple_variables_with_mixed_types(self, temp_file: Path) -> None:
        """Test writing multiple variables with different types."""
        writer = PythonFileHandler(temp_file)
        writer.write(
            variables={
                "VERSION": (1, 2, 3),
                "CONFIG": {"debug": True, "workers": 4},
                "FEATURES": ["auth", "cache", "logging"],
                "TIMEOUT": 30,
                "ENABLED": True,
                "METADATA": None,
            },
            docstring="Application configuration",
            type_hints={
                "VERSION": "tuple[int, int, int]",
                "CONFIG": "dict[str, Any]",
                "FEATURES": "list[str]",
            },
        )

        content = temp_file.read_text()

        assert "VERSION: tuple[int, int, int] = (1, 2, 3)" in content
        assert "CONFIG: dict[str, Any]" in content
        assert "FEATURES: list[str]" in content
        assert "TIMEOUT = 30" in content
        assert "ENABLED = True" in content

    def test_with_custom_imports(self, temp_file: Path) -> None:
        """Test adding custom imports."""
        writer = PythonFileHandler(temp_file)
        writer.write(
            variables={"DATA": {"key": "value"}},
            imports=["os", "sys"],
            from_imports={"pathlib": ["Path"], "datetime": ["datetime", "timedelta"]},
        )

        content = temp_file.read_text()

        assert "import os" in content
        assert "import sys" in content
        assert "from pathlib import Path" in content
        assert "from datetime import datetime, timedelta" in content

    def test_executable_output(self, temp_file: Path) -> None:
        """Test that generated Python files are executable."""
        writer = PythonFileHandler(temp_file)
        writer.write(
            variables={
                "CONFIG": {"api_url": "https://api.example.com", "timeout": 30},
                "RETRY_COUNTS": [1, 2, 4, 8, 16],
            }
        )

        content = temp_file.read_text()

        namespace = {}
        exec(content, namespace)  # noqa: S102

        assert namespace["CONFIG"]["api_url"] == "https://api.example.com"
        assert namespace["RETRY_COUNTS"] == [1, 2, 4, 8, 16]


class TestPythonFileHandlerEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dict(self, temp_file: Path) -> None:
        """Test writing empty dict."""
        writer = PythonFileHandler(temp_file)
        writer.write(variables={"EMPTY": {}})

        content = temp_file.read_text()
        assert "EMPTY = {}" in content

    def test_empty_list(self, temp_file: Path) -> None:
        """Test writing empty list."""
        writer = PythonFileHandler(temp_file)
        writer.write(variables={"EMPTY": []})

        content = temp_file.read_text()
        assert "EMPTY = []" in content

    def test_strings_with_quotes(self, temp_file: Path) -> None:
        """Test strings containing quotes are properly escaped."""
        writer = PythonFileHandler(temp_file)
        writer.write(
            variables={
                "MESSAGE": 'He said, "Hello!"',
                "PATH": "C:\\Users\\Test\\file.txt",
            }
        )

        content = temp_file.read_text()

        namespace = {}
        exec(content, namespace)  # noqa: S102
        assert namespace["MESSAGE"] == 'He said, "Hello!"'
        assert namespace["PATH"] == "C:\\Users\\Test\\file.txt"

    def test_numbers_and_floats(self, temp_file: Path) -> None:
        """Test various number types."""
        writer = PythonFileHandler(temp_file)
        writer.write(
            variables={
                "INT": 42,
                "FLOAT": 3.14159,
                "NEGATIVE": -100,
                "ZERO": 0,
            }
        )

        content = temp_file.read_text()
        assert "INT = 42" in content
        assert "FLOAT = 3.14159" in content
        assert "NEGATIVE = -100" in content
        assert "ZERO = 0" in content


class TestPythonFileHandlerBuilders:
    """Test PythonFileHandler with CodeBuilder objects."""

    def test_builders_parameter(self, temp_file: Path) -> None:
        """Test passing builders via the builders parameter."""
        writer = PythonFileHandler(temp_file)

        user_class = ClassBuilder(
            name="User",
            attributes=[
                Attribute(name="id", annotations="int"),
                Attribute(name="name", annotations="str"),
            ],
            docstring="User model",
        )

        process_func = FunctionBuilder(name="process_user", args="user: User", returns="None", body="pass")

        writer.write(
            variables={"VERSION": (1, 0, 0)},
            builders=[user_class, process_func],
            docstring="Generated module with classes and functions",
            type_hints={"VERSION": "tuple[int, int, int]"},
        )

        content = temp_file.read_text()

        assert "Generated module with classes and functions" in content
        assert "class User:" in content
        assert "User model" in content
        assert "id: int" in content
        assert "name: str" in content
        assert "def process_user(user: User) -> None:" in content
        assert "VERSION: tuple[int, int, int] = (1, 0, 0)" in content

    def test_builders_in_variables_dict(self, temp_file: Path) -> None:
        """Test passing builders directly in variables dict."""
        writer = PythonFileHandler(temp_file)

        writer.write(
            variables={
                "CONFIG": {"debug": True, "timeout": 30},
                "UserClass": ClassBuilder(
                    name="User", attributes=[Attribute(name="id", annotations="int")], docstring="User model"
                ),
                "TIMEOUT": 60,
            },
            docstring="Mixed data and code",
        )

        content = temp_file.read_text()

        assert "Mixed data and code" in content
        assert "CONFIG" in content
        assert "'debug': True" in content
        assert "class User:" in content
        assert "User model" in content
        assert "id: int" in content
        assert "TIMEOUT = 60" in content

        assert "UserClass =" not in content

    def test_mix_builders_and_data(self, temp_file: Path) -> None:
        """Test mixing builders parameter and regular data."""
        writer = PythonFileHandler(temp_file)

        writer.write(
            variables={
                "API_URL": "https://api.example.com",
                "USERS": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            },
            builders=[
                ClassBuilder(
                    name="Config", attributes=[Attribute(name="api_url", annotations="str")], docstring="Config class"
                ),
                FunctionBuilder(name="get_config", returns="Config", body="return Config()"),
            ],
            type_hints={"USERS": "list[dict[str, Any]]"},
        )

        content = temp_file.read_text()

        assert "API_URL = 'https://api.example.com'" in content
        assert "USERS: list[dict[str, Any]]" in content
        assert "class Config:" in content
        assert "Config class" in content
        assert "def get_config() -> Config:" in content

    def test_only_builders_no_variables(self, temp_file: Path) -> None:
        """Test using only builders with no variables."""
        writer = PythonFileHandler(temp_file)

        writer.write(
            builders=[
                ClassBuilder(name="User", attributes=[Attribute(name="id", annotations="int")]),
                ClassBuilder(name="Post", attributes=[Attribute(name="title", annotations="str")]),
            ],
            docstring="Models module",
        )

        content = temp_file.read_text()

        assert "Models module" in content
        assert "class User:" in content
        assert "class Post:" in content
        assert "id: int" in content
        assert "title: str" in content

    def test_executable_with_builders(self, temp_file: Path) -> None:
        """Test that generated files with builders are executable."""
        writer = PythonFileHandler(temp_file)

        writer.write(
            variables={"MULTIPLIER": 2},
            builders=[
                FunctionBuilder(
                    name="multiply",
                    args="x: int",
                    returns="int",
                    body="return x * MULTIPLIER",
                    docstring="Multiply by MULTIPLIER constant",
                )
            ],
        )

        content = temp_file.read_text()

        namespace = {}
        exec(content, namespace)  # noqa: S102

        assert namespace["MULTIPLIER"] == 2
        assert "multiply" in namespace
        assert namespace["multiply"](5) == 10
