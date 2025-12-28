"""Comprehensive tests for Nix codec implementation."""

from __future__ import annotations

from typing import Any

import pytest

from codec_cub.config import NixCodecConfig
from codec_cub.nix.codec import NixCodec


class TestNixCodecPrimitives:
    """Test encoding and decoding of primitive values."""

    def test_encode_null(self) -> None:
        """Test encoding None to null."""
        codec = NixCodec()
        assert codec.encode(None) == "null"

    def test_decode_null(self) -> None:
        """Test decoding null to None."""
        codec = NixCodec()
        assert codec.decode("null") is None

    def test_encode_boolean_true(self) -> None:
        """Test encoding True."""
        codec = NixCodec()
        assert codec.encode(obj=True) == "true"

    def test_encode_boolean_false(self) -> None:
        """Test encoding False."""
        codec = NixCodec()
        assert codec.encode(obj=False) == "false"

    def test_decode_booleans(self) -> None:
        """Test decoding true and false."""
        codec = NixCodec()
        assert codec.decode("true") is True
        assert codec.decode("false") is False

    def test_encode_integer(self) -> None:
        """Test encoding integers."""
        codec = NixCodec()
        assert codec.encode(0) == "0"
        assert codec.encode(42) == "42"
        assert codec.encode(-17) == "-17"
        assert codec.encode(9999999) == "9999999"

    def test_decode_integer(self) -> None:
        """Test decoding integers."""
        codec = NixCodec()
        assert codec.decode("0") == 0
        assert codec.decode("42") == 42
        assert codec.decode("-17") == -17
        assert codec.decode("+99") == 99

    def test_encode_float(self) -> None:
        """Test encoding floats without exponent."""
        codec = NixCodec()
        assert codec.encode(3.14) == "3.14"
        assert codec.encode(2.5) == "2.5"
        assert codec.encode(0.0) == "0"
        assert codec.encode(1.0) == "1"

    def test_decode_float(self) -> None:
        """Test decoding floats."""
        codec = NixCodec()
        assert codec.decode("3.14") == 3.14
        assert codec.decode("2.5") == 2.5
        assert codec.decode("0.0") == 0.0
        assert codec.decode("+1.5") == 1.5
        assert codec.decode("-2.75") == -2.75


class TestNixCodecSpecialFloats:
    """Test handling of special float values."""

    def test_encode_nan(self) -> None:
        """Test encoding NaN becomes null."""
        codec = NixCodec()
        assert codec.encode(float("nan")) == "null"

    def test_encode_infinity(self) -> None:
        """Test encoding Infinity becomes null."""
        codec = NixCodec()
        assert codec.encode(float("inf")) == "null"
        assert codec.encode(float("-inf")) == "null"

    def test_encode_negative_zero(self) -> None:
        """Test encoding -0.0 normalizes to 0."""
        codec = NixCodec()
        assert codec.encode(-0.0) == "0"

    def test_float_precision(self) -> None:
        """Test float encoding respects configured precision."""
        config = NixCodecConfig(float_scale=3)
        codec = NixCodec(config)
        result: str = codec.encode(3.14159265359)
        # Should round to 3 decimal places
        assert result == "3.142"

    def test_float_trailing_zeros_stripped(self) -> None:
        """Test that trailing zeros are removed from floats."""
        codec = NixCodec()
        assert codec.encode(1.5000) == "1.5"
        assert codec.encode(2.0) == "2"


class TestNixCodecStrings:
    """Test encoding and decoding of strings."""

    def test_encode_simple_string(self) -> None:
        """Test encoding simple strings."""
        codec = NixCodec()
        assert codec.encode("hello") == '"hello"'
        assert codec.encode("Hello World") == '"Hello World"'

    def test_decode_simple_string(self) -> None:
        """Test decoding simple strings."""
        codec = NixCodec()
        assert codec.decode('"hello"') == "hello"
        assert codec.decode('"Hello World"') == "Hello World"

    def test_encode_empty_string(self) -> None:
        """Test encoding empty string."""
        codec = NixCodec()
        assert codec.encode("") == '""'

    def test_decode_empty_string(self) -> None:
        """Test decoding empty string."""
        codec = NixCodec()
        assert codec.decode('""') == ""

    def test_encode_string_with_escapes(self) -> None:
        """Test encoding strings with special characters."""
        codec = NixCodec()
        assert codec.encode('hello"world') == '"hello\\"world"'
        assert codec.encode("line1\nline2") == '"line1\\nline2"'
        assert codec.encode("tab\there") == '"tab\\there"'
        assert codec.encode("backslash\\test") == '"backslash\\\\test"'
        assert codec.encode("carriage\rreturn") == '"carriage\\rreturn"'

    def test_decode_string_with_escapes(self) -> None:
        """Test decoding strings with escape sequences."""
        codec = NixCodec()
        assert codec.decode('"hello\\"world"') == 'hello"world'
        assert codec.decode('"line1\\nline2"') == "line1\nline2"
        assert codec.decode('"tab\\there"') == "tab\there"
        assert codec.decode('"backslash\\\\test"') == "backslash\\test"


class TestNixCodecLists:
    """Test encoding and decoding of lists."""

    def test_encode_empty_list(self) -> None:
        """Test encoding empty list."""
        codec = NixCodec()
        assert codec.encode([]) == "[ ]"

    def test_decode_empty_list(self) -> None:
        """Test decoding empty list."""
        codec = NixCodec()
        assert codec.decode("[]") == []
        assert codec.decode("[ ]") == []

    def test_encode_inline_list(self) -> None:
        """Test encoding small lists inline."""
        codec = NixCodec()
        result: str = codec.encode([1, 2, 3])
        assert result == "[ 1 2 3 ]"

    def test_decode_inline_list(self) -> None:
        """Test decoding inline lists."""
        codec = NixCodec()
        assert codec.decode("[ 1 2 3 ]") == [1, 2, 3]
        assert codec.decode("[1 2 3]") == [1, 2, 3]

    def test_encode_list_mixed_types(self) -> None:
        """Test encoding list with mixed types."""
        codec = NixCodec()
        result: str = codec.encode([1, "two", True, None])
        assert result == '[ 1 "two" true null ]'

    def test_decode_list_mixed_types(self) -> None:
        """Test decoding list with mixed types."""
        codec = NixCodec()
        assert codec.decode('[ 1 "two" true null ]') == [1, "two", True, None]

    def test_encode_multiline_list(self) -> None:
        """Test encoding large lists as multiline."""
        config = NixCodecConfig(max_inline_list=3, inline_lists=False)
        codec = NixCodec(config)
        result: str = codec.encode([1, 2, 3, 4])
        assert "[\n" in result
        assert "  1\n" in result
        assert "  2\n" in result
        assert "]" in result

    def test_encode_nested_list(self) -> None:
        """Test encoding nested lists."""
        config = NixCodecConfig(inline_arrays=True)
        codec = NixCodec(config=config)
        result: str = codec.encode([[1, 2], [3, 4]])
        assert result == "[ [ 1 2 ] [ 3 4 ] ]"

    def test_decode_nested_list(self) -> None:
        """Test decoding nested lists."""
        codec = NixCodec()
        assert codec.decode("[ [ 1 2 ] [ 3 4 ] ]") == [[1, 2], [3, 4]]


class TestNixCodecAttrSets:
    """Test encoding and decoding of attribute sets (dicts)."""

    def test_encode_empty_attrset(self) -> None:
        """Test encoding empty dict."""
        codec = NixCodec()
        assert codec.encode({}) == "{ }"

    def test_decode_empty_attrset(self) -> None:
        """Test decoding empty attrset."""
        codec = NixCodec()
        assert codec.decode("{}") == {}
        assert codec.decode("{ }") == {}

    def test_encode_simple_attrset(self) -> None:
        """Test encoding simple dict."""
        codec = NixCodec()
        result: str = codec.encode({"name": "Bear", "age": 42})
        # Keys should be sorted by default
        assert "{\n" in result
        assert "age = 42;" in result
        assert 'name = "Bear";' in result
        assert "}" in result

    def test_decode_simple_attrset(self) -> None:
        """Test decoding simple attrset."""
        codec = NixCodec()
        nix_str = '{ name = "Bear"; age = 42; }'
        result: dict[str, str | int] = codec.decode(nix_str)
        assert result == {"name": "Bear", "age": 42}

    def test_encode_attrset_no_trailing_semicolon(self) -> None:
        """Test encoding without trailing semicolons."""
        config = NixCodecConfig(trailing_semicolon=False)
        codec = NixCodec(config)
        result = codec.encode({"x": 1})
        assert "x = 1\n" in result
        assert ";" not in result

    def test_encode_attrset_unsorted_keys(self) -> None:
        """Test encoding with unsorted keys."""
        config = NixCodecConfig(sort_keys=False)
        codec = NixCodec(config)
        # Note: dict ordering is preserved in Python 3.7+
        data: dict[str, int] = {"zebra": 1, "apple": 2}
        result: str = codec.encode(data)
        lines: list[str] = result.split("\n")
        # Should maintain insertion order
        assert any("zebra" in line for line in lines)
        assert any("apple" in line for line in lines)

    def test_decode_attrset_optional_semicolon(self) -> None:
        """Test decoding attrset with and without semicolons."""
        codec = NixCodec()
        assert codec.decode("{ x = 1; y = 2; }") == {"x": 1, "y": 2}
        assert codec.decode("{ x = 1 y = 2 }") == {"x": 1, "y": 2}

    def test_encode_quoted_keys(self) -> None:
        """Test encoding keys that need quoting."""
        codec = NixCodec()
        # Keys with spaces or special chars need quoting
        result: str = codec.encode({"my-key": 1, "2nd": 2})
        # "my-key" is a valid bare identifier in Nix
        assert "my-key = 1;" in result
        # "2nd" starts with digit, needs quoting
        assert '"2nd" = 2;' in result

    def test_decode_quoted_keys(self) -> None:
        """Test decoding attrset with quoted keys."""
        codec = NixCodec()
        assert codec.decode('{ "my key" = 1; }') == {"my key": 1}
        assert codec.decode('{ "123" = "value"; }') == {"123": "value"}

    def test_encode_nested_attrset(self) -> None:
        """Test encoding nested dicts."""
        codec = NixCodec()
        data: dict[str, dict[str, int]] = {"outer": {"inner": 42}}
        result: str = codec.encode(data)
        assert "outer = {" in result
        assert "inner = 42;" in result
        assert "};" in result

    def test_decode_nested_attrset(self) -> None:
        """Test decoding nested attrsets."""
        codec = NixCodec()
        nix_str = "{ outer = { inner = 42; }; }"
        assert codec.decode(nix_str) == {"outer": {"inner": 42}}


class TestNixCodecRoundTrip:
    """Test round-trip encoding and decoding."""

    def test_roundtrip_primitives(self) -> None:
        """Test round-trip with primitive values."""
        codec = NixCodec()
        test_values: list[Any] = [None, True, False, 0, 42, -17, 3.14, "hello", ""]
        for value in test_values:
            encoded: str = codec.encode(value)
            decoded: list[Any] = codec.decode(encoded)
            assert decoded == value, f"Failed for {value}"

    def test_roundtrip_list(self) -> None:
        """Test round-trip with lists."""
        codec = NixCodec()
        data: list[Any] = [1, 2, 3, "four", True, None]
        encoded: str = codec.encode(data)
        decoded: list[Any] = codec.decode(encoded)
        assert decoded == data

    def test_roundtrip_attrset(self) -> None:
        """Test round-trip with attrsets."""
        codec = NixCodec()
        data: dict[str, Any] = {"name": "Bear", "age": 42, "active": True, "score": 98.5}
        encoded: str = codec.encode(data)
        decoded: dict[str, Any] = codec.decode(encoded)
        assert decoded == data

    def test_roundtrip_nested_structure(self) -> None:
        """Test round-trip with complex nested structure."""
        codec = NixCodec()
        data: dict[str, Any] = {
            "users": [
                {"name": "Alice", "id": 1},
                {"name": "Bob", "id": 2},
            ],
            "settings": {"debug": True, "version": "1.0"},
            "counts": [10, 20, 30],
        }
        encoded: str = codec.encode(data)
        decoded: dict[str, Any] = codec.decode(encoded)
        assert decoded == data


class TestNixCodecComments:
    """Test comment handling in Nix decoder."""

    def test_decode_with_line_comment(self) -> None:
        """Test decoding with line comments."""
        codec = NixCodec()
        nix_str = """
        # This is a comment
        { x = 1; # inline comment
          y = 2; }
        """
        result: dict[str, int] = codec.decode(nix_str)
        assert result == {"x": 1, "y": 2}

    def test_decode_comment_only_lines(self) -> None:
        """Test decoding with comment-only lines."""
        codec = NixCodec()
        nix_str = """
        # Header comment
        # Another comment line
        42
        """
        assert codec.decode(nix_str) == 42

    def test_decode_inline_comment(self) -> None:
        """Test decoding with inline comments."""
        codec = NixCodec()
        assert codec.decode("true # this is true") is True
        assert codec.decode("[ 1 2 3 ] # a list") == [1, 2, 3]


class TestNixCodecConfiguration:
    """Test various configuration options."""

    def test_custom_indentation(self) -> None:
        """Test encoding with custom indentation."""
        config = NixCodecConfig(indent_spaces=4)
        codec = NixCodec(config)
        result: str = codec.encode({"outer": {"inner": 1}})
        assert "    inner = 1;" in result

    def test_custom_newline(self) -> None:
        """Test encoding with custom newline."""
        config = NixCodecConfig(newline="\r\n", inline_arrays=False)
        codec = NixCodec(config)
        result: str = codec.encode({"a": 1, "b": 2})
        assert "\r\n" in result

    def test_inline_list_threshold(self) -> None:
        """Test max_inline_list configuration."""
        config = NixCodecConfig(max_inline_list=2, inline_lists=False)
        codec = NixCodec(config)

        # List with 2 items should be inline
        small: str = codec.encode([1, 2])
        assert small == "[ 1 2 ]"

        # List with 3 items should be multiline
        large: str = codec.encode([1, 2, 3])
        assert "[\n" in large


class TestNixCodecErrorHandling:
    """Test error handling and edge cases."""

    def test_decode_invalid_syntax(self) -> None:
        """Test decoding invalid Nix syntax raises ValueError."""
        codec = NixCodec()
        with pytest.raises(ValueError, match="Nix parse error"):
            codec.decode("{ invalid syntax")

    def test_decode_incomplete_attrset(self) -> None:
        """Test decoding incomplete attrset."""
        codec = NixCodec()
        with pytest.raises(ValueError, match="Nix parse error"):
            codec.decode("{ x = 1")

    def test_decode_incomplete_list(self) -> None:
        """Test decoding incomplete list."""
        codec = NixCodec()
        with pytest.raises(ValueError, match="Nix parse error"):
            codec.decode("[ 1 2 3")

    def test_encode_unsupported_type(self) -> None:
        """Test encoding unsupported type raises TypeError."""
        codec = NixCodec()
        with pytest.raises(TypeError, match="Unsupported type"):
            codec.encode(object())

    def test_decode_extra_content(self) -> None:
        """Test decoding with extra content after valid expression."""
        codec = NixCodec()
        with pytest.raises(ValueError, match="Nix parse error"):
            codec.decode("42 extra")


class TestNixCodecBareIdentifiers:
    """Test bare identifier handling for attrset keys."""

    def test_bare_identifier_simple(self) -> None:
        """Test simple bare identifiers."""
        codec = NixCodec()
        result: str = codec.encode({"foo": 1, "bar_baz": 2, "test-key": 3})
        # All should be bare identifiers
        assert "foo = 1;" in result
        assert "bar_baz = 2;" in result
        assert "test-key = 3;" in result
        # No quotes needed
        assert '"foo"' not in result

    def test_quoted_identifier_required(self) -> None:
        """Test keys that require quoting."""
        codec = NixCodec()
        result: str = codec.encode({"with spaces": 1, "123": 2, "": 3})
        # These need quotes
        assert '"with spaces" = 1;' in result
        assert '"123" = 2;' in result
        assert '"" = 3;' in result

    def test_decode_mixed_identifiers(self) -> None:
        """Test decoding mix of bare and quoted identifiers."""
        codec = NixCodec()
        nix_str = '{ foo = 1; "bar baz" = 2; test-key = 3; }'
        result: dict[str, int] = codec.decode(nix_str)
        assert result == {"foo": 1, "bar baz": 2, "test-key": 3}


class TestNixCodecComplexExamples:
    """Test complex real-world examples."""

    def test_package_definition(self) -> None:
        """Test encoding/decoding a package-like structure."""
        codec = NixCodec()
        package: dict[str, Any] = {
            "name": "codec-cub",
            "version": "1.0.0",
            "dependencies": ["python", "pytest"],
            "meta": {
                "description": "A cool codec library",
                "license": "MIT",
            },
        }
        encoded: str = codec.encode(package)
        decoded: dict[str, Any] = codec.decode(encoded)
        assert decoded == package

    def test_deeply_nested_structure(self) -> None:
        """Test deeply nested structure."""
        codec = NixCodec()
        data: dict[str, dict[str, Any]] = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": 42,
                        "list": [1, 2, 3],
                    }
                }
            }
        }
        encoded: str = codec.encode(data)
        decoded: dict[str, dict[str, Any]] = codec.decode(encoded)
        assert decoded == data

    def test_array_of_objects(self) -> None:
        """Test array containing multiple objects."""
        codec = NixCodec()
        data: list[dict[str, Any]] = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]
        encoded: str = codec.encode(data)
        decoded: list[dict[str, Any]] = codec.decode(encoded)
        assert decoded == data

    def test_unified_data_format_structure(self) -> None:
        """Test encoding/decoding UnifiedDataFormat-like nested structure.

        This demonstrates NixCodec can handle complex nested data structures
        similar to database schemas with headers, table definitions, columns,
        and records - all deeply nested with mixed types.
        """
        codec = NixCodec()

        udf_data: dict[str, Any] = {
            "header": {
                "tables": ["users", "posts"],
                "version": "1.0.0",
                "created_at": "2025-11-23",
            },
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
                        {
                            "name": "username",
                            "type": "str",
                            "nullable": False,
                        },
                        {
                            "name": "email",
                            "type": "str",
                            "nullable": True,
                        },
                    ],
                    "count": 2,
                    "records": [
                        {"id": 1, "username": "alice", "email": "alice@example.com"},
                        {"id": 2, "username": "bob", "email": None},
                    ],
                },
                "posts": {
                    "name": "posts",
                    "columns": [
                        {"name": "id", "type": "int", "primary_key": True},
                        {"name": "title", "type": "str"},
                        {"name": "user_id", "type": "int"},
                        {"name": "published", "type": "bool"},
                    ],
                    "count": 3,
                    "records": [
                        {"id": 1, "title": "Hello World", "user_id": 1, "published": True},
                        {"id": 2, "title": "Nix is Great", "user_id": 1, "published": True},
                        {"id": 3, "title": "Draft Post", "user_id": 2, "published": False},
                    ],
                },
            },
        }

        # Encode to Nix format
        encoded: str = codec.encode(udf_data)

        # Verify it's valid Nix syntax (should contain attrsets and lists)
        assert "header = {" in encoded
        assert "tables = {" in encoded
        assert "users = {" in encoded
        assert "columns = [" in encoded
        assert "records = [" in encoded

        # Decode back to Python
        decoded: dict[str, Any] = codec.decode(encoded)

        # Verify complete round-trip preservation
        assert decoded == udf_data
        assert decoded["header"]["tables"] == ["users", "posts"]
        assert decoded["header"]["version"] == "1.0.0"
        assert decoded["tables"]["users"]["count"] == 2
        assert decoded["tables"]["posts"]["count"] == 3
        assert len(decoded["tables"]["users"]["records"]) == 2
        assert len(decoded["tables"]["posts"]["records"]) == 3
        assert decoded["tables"]["users"]["records"][0]["username"] == "alice"
        assert decoded["tables"]["posts"]["records"][2]["published"] is False
