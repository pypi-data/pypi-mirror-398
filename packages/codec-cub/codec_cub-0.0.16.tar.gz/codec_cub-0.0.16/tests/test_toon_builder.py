"""Tests for TOON builder API with forced tabular formatting."""

from __future__ import annotations

from typing import Any

import pytest

from codec_cub.config import ToonCodecConfig
from codec_cub.toon import ToonCodec
from codec_cub.toon.builder import Tabular, tabular, toon_dumps


class TestTabularWrapper:
    """Test the Tabular wrapper for forced tabular encoding."""

    def test_tabular_import(self) -> None:
        """Test that Tabular and tabular can be imported from builder module."""
        assert Tabular is not None
        assert tabular is not None

    def test_tabular_creation(self) -> None:
        """Test creating a Tabular wrapper with rows and fields."""
        rows: list[dict[str, Any]] = [
            {"id": 1, "name": "Bear"},
            {"id": 2, "name": "Claire"},
        ]
        fields: list[str] = ["id", "name"]
        wrapper = Tabular(rows=rows, fields=fields)

        assert wrapper.rows == rows
        assert wrapper.fields == fields
        assert wrapper.fill_missing is True  # default

    def test_tabular_with_fill_missing(self) -> None:
        """Test Tabular wrapper with fill_missing enabled."""
        rows: list[Any] = [
            {"id": 1, "name": "Bear"},
            {"id": 2},  #  missing 'name'
        ]
        fields: list[str] = ["id", "name"]
        wrapper = Tabular(rows=rows, fields=fields, fill_missing=True)

        assert wrapper.fill_missing is True

    def test_tabular_convenience_function(self) -> None:
        """Test the tabular() convenience function."""
        rows: list[dict[str, int]] = [{"a": 1}, {"a": 2}]
        wrapper: Tabular = tabular(rows, fields=["a"])
        assert wrapper.rows == rows
        assert wrapper.fields == ["a"]

    def test_tabular_convenience_with_fill_missing(self) -> None:
        """Test tabular() with fill_missing parameter."""
        wrapper: Tabular = tabular([{"x": 1}], fields=["x", "y"], fill_missing=True)
        assert wrapper.fill_missing is True
        assert wrapper.fields == ["x", "y"]


class TestTabularClassMethods:
    """Test Tabular class methods: detect, from_rows, nulled."""

    def test_tabular_nulled(self) -> None:
        """Test Tabular.nulled() creates empty non-tabular result."""
        result: Tabular = Tabular.nulled()
        assert result.rows == []
        assert result.fields == []
        assert result.is_tabular is False

    def test_tabular_detect_uniform_dicts(self) -> None:
        """Test Tabular.detect() with uniform dict array."""
        items: list[dict[str, Any]] = [
            {"id": 1, "name": "Bear"},
            {"id": 2, "name": "Claire"},
        ]
        result: Tabular = Tabular.detect(items)
        assert result.is_tabular is True
        assert set(result.fields) == {"id", "name"}
        assert result.rows == items

    def test_tabular_detect_mismatched_keys(self) -> None:
        """Test Tabular.detect() returns nulled for mismatched keys."""
        items: list[dict[str, Any]] = [
            {"id": 1, "name": "Bear"},
            {"id": 2},  # missing 'name'
        ]
        result: Tabular = Tabular.detect(items)
        assert result.is_tabular is False

    def test_tabular_detect_nested_values(self) -> None:
        """Test Tabular.detect() returns nulled for nested dict/list values."""
        items: list[dict[str, Any]] = [
            {"id": 1, "meta": {"foo": "bar"}},
            {"id": 2, "meta": {"foo": "baz"}},
        ]
        result: Tabular = Tabular.detect(items)
        assert result.is_tabular is False

    def test_tabular_detect_empty_list(self) -> None:
        """Test Tabular.detect() returns nulled for empty list."""
        result: Tabular = Tabular.detect([])
        assert result.is_tabular is False

    def test_tabular_detect_non_dicts(self) -> None:
        """Test Tabular.detect() returns nulled for non-dict items."""
        result: Tabular = Tabular.detect([1, 2, 3])
        assert result.is_tabular is False

    def test_tabular_from_rows_basic(self) -> None:
        """Test Tabular.from_rows() auto-detects fields from all keys."""
        rows: list[dict[str, Any]] = [
            {"id": 1, "name": "Bear"},
            {"id": 2, "name": "Claire", "email": "claire@example.com"},
        ]
        result: Tabular = Tabular.from_rows(rows)
        assert set(result.fields) == {"id", "name", "email"}
        assert result.rows == rows
        assert result.fill_missing is True  # default

    def test_tabular_from_rows_with_fill_missing(self) -> None:
        """Test Tabular.from_rows() with fill_missing enabled."""
        rows: list[dict[str, Any]] = [{"a": 1}, {"b": 2}]
        result: Tabular = Tabular.from_rows(rows, fill_missing=True)
        assert result.fill_missing is True
        assert set(result.fields) == {"a", "b"}

    def test_tabular_from_rows_empty(self) -> None:
        """Test Tabular.from_rows() with empty list."""
        result: Tabular = Tabular.from_rows([])
        assert result.rows == []
        assert result.fields == []
        assert result.is_tabular is False

    def test_tabular_is_tabular_property(self) -> None:
        """Test is_tabular property based on fields presence."""
        with_fields = Tabular(rows=[{"a": 1}], fields=["a"])
        assert with_fields.is_tabular is True

        without_fields = Tabular(rows=[], fields=[])
        assert without_fields.is_tabular is False


class TestToonDumps:
    """Test toon_dumps() function for building TOON strings."""

    def test_toon_dumps_import(self) -> None:
        """Test that toon_dumps can be imported."""
        assert toon_dumps is not None

    def test_toon_dumps_simple_dict(self) -> None:
        """Test toon_dumps with a simple dict (no wrappers)."""
        data: dict[str, Any] = {"name": "Bear", "active": True}
        result: str = toon_dumps(data)
        assert "name: Bear" in result
        assert "active: true" in result

    def test_toon_dumps_with_tabular(self) -> None:
        """Test toon_dumps recognizes Tabular wrapper and forces tabular format."""
        data: dict[str, Tabular] = {
            "users": tabular(
                rows=[
                    {"id": 1, "name": "Bear", "email": "bear@example.com"},
                    {"id": 2, "name": "Claire", "email": "claire@example.com"},
                ],
                fields=["id", "name", "email"],
            )
        }
        result: str = toon_dumps(data)

        # Should produce tabular format with field header
        assert "users[2]{id,name,email}:" in result
        assert "1,Bear,bear@example.com" in result
        assert "2,Claire,claire@example.com" in result

    def test_toon_dumps_tabular_with_missing_fields(self) -> None:
        """Test tabular encoding fills missing fields with null."""
        data: dict[str, Tabular] = {
            "records": tabular(
                rows=[
                    {"id": 1, "name": "Bear", "email": "bear@example.com"},
                    {"id": 2, "name": "Claire"},  # missing email
                ],
                fields=["id", "name", "email"],
                fill_missing=True,
            )
        }
        result: str = toon_dumps(data)

        assert "records[2]{id,name,email}:" in result
        assert "1,Bear,bear@example.com" in result
        assert "2,Claire,null" in result  # email filled with null

    def test_toon_dumps_empty_tabular(self) -> None:
        """Test tabular encoding with empty rows."""
        data: dict[str, Tabular] = {"items": tabular(rows=[], fields=["a", "b"])}
        result: str = toon_dumps(data)

        # Empty array should still show header
        assert "items[0]:" in result

    def test_toon_dumps_nested_with_tabular(self) -> None:
        """Test toon_dumps with nested structure containing tabular."""
        data: dict[str, Any] = {
            "header": {"version": "1.0.0"},
            "tables": {
                "users": {
                    "columns": tabular(
                        rows=[
                            {"name": "id", "type": "int"},
                            {"name": "email", "type": "str"},
                        ],
                        fields=["name", "type"],
                    ),
                    "count": 0,
                }
            },
        }
        result: str = toon_dumps(data)

        assert "header:" in result
        assert "version: 1.0.0" in result
        assert "columns[2]{name,type}:" in result
        assert "id,int" in result
        assert "email,str" in result

    def test_toon_dumps_with_config(self) -> None:
        """Test toon_dumps accepts optional config."""
        config = ToonCodecConfig(indent_spaces=4)
        data: dict[str, dict[str, int]] = {"nested": {"value": 42}}
        result: str = toon_dumps(data, config=config)

        # Should use 4-space indentation
        assert "    value: 42" in result

    def test_toon_dumps_fallback_on_regular_list(self) -> None:
        """Test that regular lists without Tabular wrapper encode normally."""
        data: dict[str, list[str]] = {
            "tags": ["web", "api", "python"],
        }
        result: str = toon_dumps(data)

        # Should use inline primitive array format
        assert "tags[3]: web,api,python" in result


class TestToonDumpsRoundTrip:
    """Test that toon_dumps output can be decoded back correctly."""

    def test_roundtrip_tabular(self) -> None:
        """Test encoding with Tabular and decoding produces equivalent data."""
        original_rows: list[dict[str, Any]] = [
            {"id": 1, "name": "Bear"},
            {"id": 2, "name": "Claire"},
        ]
        data: dict[str, Tabular] = {"users": tabular(rows=original_rows, fields=["id", "name"])}

        toon_str: str = toon_dumps(data)
        codec = ToonCodec()
        decoded = codec.decode(toon_str)

        assert decoded["users"] == original_rows

    def test_roundtrip_tabular_with_nulls(self) -> None:
        """Test roundtrip with fill_missing produces nulls in decoded data."""
        original_rows: list[dict[str, Any]] = [
            {"id": 1, "name": "Bear", "score": 100},
            {"id": 2, "name": "Claire"},  # missing score
        ]
        data: dict[str, Tabular] = {
            "users": tabular(
                rows=original_rows,
                fields=["id", "name", "score"],
                fill_missing=True,
            )
        }

        toon_str: str = toon_dumps(data)
        codec = ToonCodec()
        decoded = codec.decode(toon_str)

        assert decoded["users"][0] == {"id": 1, "name": "Bear", "score": 100}
        assert decoded["users"][1] == {"id": 2, "name": "Claire", "score": None}

    def test_tabular_fill_missing_false_raises(self) -> None:
        """Test that fill_missing=False raises ValueError for missing fields."""
        data: dict[str, Tabular] = {
            "users": tabular(
                rows=[{"id": 1, "name": "Bear"}, {"id": 2}],  # second row missing 'name'
                fields=["id", "name"],
                fill_missing=False,
            )
        }
        with pytest.raises(ValueError, match="Field 'name' missing"):
            toon_dumps(data)

    def test_roundtrip_tabular_from_rows(self) -> None:
        """Test round-trip with Tabular.from_rows() using inconsistent fields."""
        rows: list[dict[str, Any]] = [
            {"id": 1, "name": "Bear", "email": "bear@example.com"},
            {"id": 2, "name": "Claire"},  # missing email
            {"id": 3, "score": 100},  # missing name and email, has extra field
        ]
        data: dict[str, Tabular] = {"users": Tabular.from_rows(rows)}

        toon_str: str = toon_dumps(data)
        codec = ToonCodec()
        decoded = codec.decode(toon_str)

        # from_rows() detects union of all keys: {id, name, email, score}
        # fill_missing=True fills missing fields with null
        assert decoded["users"][0]["id"] == 1
        assert decoded["users"][0]["name"] == "Bear"
        assert decoded["users"][0]["email"] == "bear@example.com"
        assert decoded["users"][0]["score"] is None

        assert decoded["users"][1]["id"] == 2
        assert decoded["users"][1]["name"] == "Claire"
        assert decoded["users"][1]["email"] is None
        assert decoded["users"][1]["score"] is None

        assert decoded["users"][2]["id"] == 3
        assert decoded["users"][2]["name"] is None
        assert decoded["users"][2]["email"] is None
        assert decoded["users"][2]["score"] == 100
