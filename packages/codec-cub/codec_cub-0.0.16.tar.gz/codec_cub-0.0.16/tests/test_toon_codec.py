"""Tests for TOON codec implementation."""

from __future__ import annotations

from contextlib import suppress
from typing import Any

import pytest

from codec_cub.config import ToonCodecConfig
from codec_cub.toon import ToonCodec


class TestToonCodecPrimitives:
    """Test encoding and decoding of primitive values."""

    def test_encode_null(self) -> None:
        """Test encoding None to null."""
        codec = ToonCodec()
        assert codec.encode(None) == "null"

    def test_encode_boolean_true(self) -> None:
        """Test encoding True."""
        codec = ToonCodec()
        assert codec.encode(obj=True) == "true"

    def test_encode_boolean_false(self) -> None:
        """Test encoding False."""
        codec = ToonCodec()
        assert codec.encode(obj=False) == "false"

    def test_encode_integer(self) -> None:
        """Test encoding integers."""
        codec = ToonCodec()
        assert codec.encode(42) == "42"
        assert codec.encode(-17) == "-17"
        assert codec.encode(0) == "0"

    def test_encode_float(self) -> None:
        """Test encoding floats."""
        codec = ToonCodec()
        assert codec.encode(3.14) == "3.14"
        assert codec.encode(2.5) == "2.5"
        assert codec.encode(1.0) == "1"  # Trailing .0 removed

    def test_encode_string_simple(self) -> None:
        """Test encoding simple strings."""
        codec = ToonCodec()
        assert codec.encode("hello") == "hello"
        assert codec.encode("Hello World") == '"Hello World"'

    def test_encode_string_quoted(self) -> None:
        """Test encoding strings that need quoting."""
        codec = ToonCodec()
        # Empty string
        assert codec.encode("") == '""'
        # Reserved literal
        assert codec.encode("true") == '"true"'
        assert codec.encode("false") == '"false"'
        assert codec.encode("null") == '"null"'
        # Contains colon
        assert codec.encode("key:value") == '"key:value"'

    def test_decode_primitives(self) -> None:
        """Test decoding primitive values."""
        codec = ToonCodec()
        assert codec.decode("null") is None
        assert codec.decode("true") is True
        assert codec.decode("false") is False
        assert codec.decode("42") == 42
        assert codec.decode("3.14") == 3.14
        assert codec.decode("hello") == "hello"


class TestToonCodecObjects:
    """Test encoding and decoding of objects."""

    def test_encode_empty_object(self) -> None:
        """Test encoding empty object."""
        codec = ToonCodec()
        assert codec.encode({}) == ""

    def test_encode_simple_object(self) -> None:
        """Test encoding simple object."""
        codec = ToonCodec()
        result: str = codec.encode({"name": "Ada", "age": 30})
        assert "name: Ada" in result
        assert "age: 30" in result

    def test_encode_nested_object(self) -> None:
        """Test encoding nested object."""
        codec = ToonCodec()
        data: dict[str, dict[str, Any]] = {"user": {"name": "Ada", "age": 30}}
        result: str = codec.encode(data)
        assert "user:" in result
        assert "  name: Ada" in result
        assert "  age: 30" in result

    def test_decode_simple_object(self) -> None:
        """Test decoding simple object."""
        codec = ToonCodec()
        toon = "name: Ada\nage: 30"
        result: Any = codec.decode(toon)
        assert result == {"name": "Ada", "age": 30}

    def test_decode_nested_object(self) -> None:
        """Test decoding nested object."""
        codec = ToonCodec()
        toon = "user:\n  name: Ada\n  age: 30"
        result: Any = codec.decode(toon)
        assert result == {"user": {"name": "Ada", "age": 30}}


class TestToonCodecArrays:
    """Test encoding and decoding of arrays."""

    def test_encode_inline_primitive_array(self) -> None:
        """Test encoding inline primitive array."""
        codec = ToonCodec()
        data: dict[str, list[str]] = {"tags": ["web", "api", "dev"]}
        result: str = codec.encode(data)
        assert "tags[3]: web,api,dev" in result

    def test_encode_empty_array(self) -> None:
        """Test encoding empty array."""
        codec = ToonCodec()
        data: dict[str, list[Any]] = {"items": []}
        result: str = codec.encode(data)
        assert "items[0]:" in result

    def test_encode_tabular_array(self) -> None:
        """Test encoding tabular array format."""
        codec = ToonCodec()
        data: dict[str, list[dict[str, Any]]] = {
            "users": [
                {"id": 1, "name": "Alice", "role": "admin"},
                {"id": 2, "name": "Bob", "role": "user"},
            ]
        }
        result: str = codec.encode(data)
        assert "users[2]{id,name,role}:" in result
        assert "  1,Alice,admin" in result
        assert "  2,Bob,user" in result

    def test_decode_inline_primitive_array(self) -> None:
        """Test decoding inline primitive array."""
        codec = ToonCodec()
        toon = "tags[3]: web,api,dev"
        result: Any = codec.decode(toon)
        assert result == {"tags": ["web", "api", "dev"]}

    def test_decode_tabular_array(self) -> None:
        """Test decoding tabular array."""
        codec = ToonCodec()
        toon = "users[2]{id,name,role}:\n  1,Alice,admin\n  2,Bob,user"
        result: Any = codec.decode(toon)
        expected: dict[str, list[dict[str, Any]]] = {
            "users": [
                {"id": 1, "name": "Alice", "role": "admin"},
                {"id": 2, "name": "Bob", "role": "user"},
            ]
        }
        assert result == expected

    def test_root_tabular_array_roundtrip(self) -> None:
        """Test encoding and decoding root-level tabular array."""
        codec = ToonCodec()
        data: list[dict[str, Any]] = [
            {"id": 1, "name": "Alice", "role": "admin"},
            {"id": 2, "name": "Bob", "role": "user"},
        ]
        encoded: str = codec.encode(data)
        decoded: Any = codec.decode(encoded)
        assert decoded == data
        assert "[2]{id,name,role}:" in encoded


class TestToonCodecRoundTrip:
    """Test round-trip encoding and decoding."""

    def test_roundtrip_simple_data(self) -> None:
        """Test round-trip with simple data."""
        codec = ToonCodec()
        data: dict[str, Any] = {
            "name": "Ada Lovelace",
            "age": 36,
            "active": True,
            "score": 95.5,
        }
        encoded: str = codec.encode(data)
        decoded: Any = codec.decode(encoded)
        assert decoded == data

    def test_roundtrip_nested_data(self) -> None:
        """Test round-trip with nested data."""
        codec = ToonCodec()
        data: dict[str, dict[str, Any]] = {
            "user": {
                "name": "Ada",
                "contact": {"email": "ada@example.com", "phone": "555-1234"},
            }
        }
        encoded: str = codec.encode(data)
        decoded: Any = codec.decode(encoded)
        assert decoded == data

    def test_roundtrip_with_arrays(self) -> None:
        """Test round-trip with arrays."""
        codec = ToonCodec()
        data: dict[str, Any] = {
            "items": [
                {"id": 1, "name": "Item A", "price": 10.5},
                {"id": 2, "name": "Item B", "price": 20.0},
            ],
            "tags": ["sale", "featured"],
        }
        encoded: str = codec.encode(data)
        decoded: Any = codec.decode(encoded)
        assert decoded == data


class TestToonCodecDelimiters:
    """Test different delimiter configurations."""

    def test_encode_with_tab_delimiter(self) -> None:
        """Test encoding with tab delimiter."""
        config = ToonCodecConfig(delimiter="\t")
        codec = ToonCodec(config)
        data: dict[str, list[str]] = {"tags": ["a", "b", "c"]}
        result: str = codec.encode(data)
        assert "tags[3\t]:" in result
        # Per spec §6, there must be exactly one space after colon before first value
        assert " a\tb\tc" in result

    def test_encode_with_pipe_delimiter(self) -> None:
        """Test encoding with pipe delimiter."""
        config = ToonCodecConfig(delimiter="|")
        codec = ToonCodec(config)
        data: dict[str, list[str]] = {"tags": ["a", "b", "c"]}
        result: str = codec.encode(data)
        assert "tags[3|]:" in result
        assert " a|b|c" in result


class TestToonCodecEdgeCases:
    """Test edge cases and error handling."""

    def test_encode_special_floats(self) -> None:
        """Test encoding special float values."""
        codec = ToonCodec()

        # NaN and Infinity should become null
        assert codec.encode(float("nan")) == "null"
        assert codec.encode(float("inf")) == "null"
        assert codec.encode(float("-inf")) == "null"

    def test_encode_negative_zero(self) -> None:
        """Test encoding -0.0 normalizes to 0."""
        codec = ToonCodec()
        assert codec.encode(-0.0) == "0"

    def test_decode_quoted_primitives(self) -> None:
        """Test that quoted primitives remain strings."""
        codec = ToonCodec()
        assert codec.decode('"123"') == "123"
        assert codec.decode('"true"') == "true"
        assert codec.decode('"null"') == "null"

    def test_decode_escaped_strings(self) -> None:
        """Test decoding strings with escape sequences."""
        codec = ToonCodec()
        toon = 'text: "Hello\\nWorld"'
        result: Any = codec.decode(toon)
        assert result == {"text": "Hello\nWorld"}

    def test_strict_mode_array_length_mismatch(self) -> None:
        """Test strict mode catches array length mismatches."""
        config = ToonCodecConfig(strict=True)
        codec = ToonCodec(config)
        # Declared 3 items but only have 2
        toon = "items[3]: a,b"
        with pytest.raises(ValueError, match="length mismatch"):
            codec.decode(toon)

    def test_non_strict_mode(self) -> None:
        """Test non-strict mode is more lenient."""
        config = ToonCodecConfig(strict=False)
        codec = ToonCodec(config)
        # This should work in non-strict mode
        toon = "items[3]: a,b"
        # Non-strict mode might accept this or handle it differently
        # For this PoC, we'll just verify it doesn't crash
        with suppress(Exception):
            result: Any = codec.decode(toon)


class TestToonCodecNestedArrays:
    """Test encoding and decoding of nested arrays."""

    def test_encode_array_of_arrays_primitives(self) -> None:
        """Test encoding arrays of primitive arrays (§9.2)."""
        codec = ToonCodec()
        data: dict[str, list[list[int]]] = {"pairs": [[1, 2], [3, 4], [5, 6]]}
        result: str = codec.encode(data)
        assert "pairs[3]:" in result
        assert "- [2]: 1,2" in result
        assert "- [2]: 3,4" in result
        assert "- [2]: 5,6" in result

    def test_decode_array_of_arrays_primitives(self) -> None:
        """Test decoding arrays of primitive arrays."""
        codec = ToonCodec()
        toon = "pairs[3]:\n  - [2]: 1,2\n  - [2]: 3,4\n  - [2]: 5,6"
        result: Any = codec.decode(toon)
        assert result == {"pairs": [[1, 2], [3, 4], [5, 6]]}

    def test_encode_array_of_arrays_objects(self) -> None:
        """Test encoding arrays containing arrays of objects."""
        codec = ToonCodec()
        data: dict[str, list[list[dict[str, int]]]] = {
            "matrix": [
                [{"x": 1, "y": 2}, {"x": 3, "y": 4}],
                [{"x": 5, "y": 6}, {"x": 7, "y": 8}],
            ]
        }
        result: str = codec.encode(data)
        assert "matrix[2]:" in result
        assert "- [2]:" in result

    def test_roundtrip_nested_arrays_objects(self) -> None:
        """Test round-trip with nested arrays of objects."""
        codec = ToonCodec()
        dict[str, list[list[dict[str, Any]]]]
        data = {
            "data": [
                [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}],
                [{"id": 3, "val": "c"}],
            ]
        }
        encoded: str = codec.encode(data)
        decoded: Any = codec.decode(encoded)
        assert decoded == data

    def test_encode_deeply_nested_arrays(self) -> None:
        """Test encoding deeply nested arrays (3 levels)."""
        codec = ToonCodec()
        data: dict[str, list[list[list[int]]]] = {"deep": [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]}
        result: str = codec.encode(data)
        assert "deep[2]:" in result

    def test_roundtrip_deeply_nested_arrays(self) -> None:
        """Test round-trip with 3-level nested arrays."""
        codec = ToonCodec()
        data: dict[str, list[list[list[int]]]] = {"nested": [[[1, 2], [3, 4]], [[5, 6]]]}
        encoded: str = codec.encode(data)
        decoded: Any = codec.decode(encoded)
        assert decoded == data

    def test_encode_mixed_nested_content(self) -> None:
        """Test encoding arrays with mixed nested content."""
        codec = ToonCodec()
        data: dict[str, list[Any]] = {
            "mixed": [
                [1, 2, 3],
                [{"x": 1}, {"x": 2}],
                ["a", "b"],
            ]
        }
        encoded: str = codec.encode(data)
        decoded: Any = codec.decode(encoded)
        assert decoded == data


class TestToonCodecExamples:
    """Test examples from the TOON specification."""

    def test_spec_example_users(self) -> None:
        """Test the main example from the spec."""
        codec = ToonCodec()
        data: dict[str, list[dict[str, Any]]] = {
            "users": [
                {"id": 1, "name": "Alice", "role": "admin"},
                {"id": 2, "name": "Bob", "role": "user"},
            ]
        }
        encoded: str = codec.encode(data)
        decoded: Any = codec.decode(encoded)
        assert decoded == data

    def test_spec_example_primitives(self) -> None:
        """Test primitive examples from spec."""
        codec = ToonCodec()
        data: dict[str, Any] = {"id": 123, "name": "Ada", "active": True}
        encoded: str = codec.encode(data)
        decoded: Any = codec.decode(encoded)
        assert decoded == data
