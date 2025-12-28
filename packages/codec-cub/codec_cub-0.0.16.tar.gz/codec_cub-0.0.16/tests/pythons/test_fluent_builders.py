"""Tests for fluent builders."""

from __future__ import annotations

from codec_cub.pythons import TypeHint
from codec_cub.pythons.file_builder import CodeSection


def test_type_alias_literal() -> None:
    """Test type alias with literal values."""
    section = CodeSection("body")

    section.type_alias("StorageChoices").literal("json", "yaml", "toml")

    result = "\n".join(section.get())

    assert 'type StorageChoices = Literal["json", "yaml", "toml"]' in result


def test_type_alias_from_annotation() -> None:
    """Test type alias from TypeHint."""
    section = CodeSection("body")

    dict_type = TypeHint.dict_of("str", "int")
    section.type_alias("ConfigMap").from_annotation(dict_type)

    result = "\n".join(section.get())

    assert "type ConfigMap = dict[str, int]" in result


def test_type_alias_from_string() -> None:
    """Test type alias from string."""
    section = CodeSection("body")

    section.type_alias("UserId").from_annotation(TypeHint("int"))

    result: str = section.join()

    assert "type UserId = int" in result


def test_type_alias_union() -> None:
    """Test type alias with union."""
    section = CodeSection("body")

    section.type_alias("IntOrStr").union(TypeHint("int"), TypeHint("str"))

    result: str = section.join()

    assert "type IntOrStr = int | str" in result


def test_variable_with_type_hint() -> None:
    """Test variable with type hint."""
    section = CodeSection("body")
    int_type = TypeHint("int")
    section.variable("count").type_hint(int_type).value("42")
    result: str = section.join()
    assert "count: int = 42" in result


def test_variable_without_type_hint() -> None:
    """Test variable without type hint."""
    section = CodeSection("body")
    section.variable("age").value("120")
    result: str = section.join()
    assert "age: int = 120" in result


def test_variable_with_type_annotation() -> None:
    """Test variable with TypeHint."""
    section = CodeSection("body")

    dict_type: TypeHint = TypeHint.dict_of("str", "int")
    section.variable("config").type_hint(dict_type).value("{}")

    result = "\n".join(section.get())

    assert "config: dict[str, int] = {}" in result


def test_chaining_multiple_operations() -> None:
    """Test chaining multiple fluent operations."""
    section = CodeSection("body")

    section.type_alias("Choices").literal("a", "b", "c")
    type_alias = TypeHint.literal("a", "b", "c")
    section.variable("default").type_hint(type_alias).value('"a"')
    section.type_alias("OptionalInt").from_annotation(TypeHint.optional("int"))

    result: str = section.join()


def test_fluent_builders_get_smart_spacing() -> None:
    """Test that fluent builders benefit from smart spacing."""
    section = CodeSection("body")

    section.type_alias("A").literal("x", "y")
    section.type_alias("B").literal("p", "q")

    lines = section.get()

    newline_count = len([line for line in lines if line == "\n"])
    assert newline_count == 2
