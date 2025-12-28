"""Tests for EnumBuilder implementing CodeBuilder protocol."""

from __future__ import annotations

from codec_cub.pythons import EnumBuilder
from codec_cub.pythons._protocols import CodeBuilder
from codec_cub.pythons.file_builder import CodeSection


def test_enum_builder_implements_protocol() -> None:
    """Test that EnumBuilder implements the CodeBuilder protocol."""
    enum = EnumBuilder(
        name="Color",
        members=["RED", "GREEN", "BLUE"],
        base_class="StrEnum",
    )

    assert isinstance(enum, CodeBuilder)


def test_enum_builder_auto_renders_in_code_section() -> None:
    """Test that EnumBuilder auto-renders when added to CodeSection."""
    section = CodeSection("body")

    enum = EnumBuilder(
        name="Status",
        members={"PENDING": 1, "ACTIVE": 2, "DONE": 3},
        base_class="IntEnum",
        docstring="Status codes for tasks.",
    )

    section.add(enum)

    result = "\n".join(section.get())

    assert "class Status(IntEnum):" in result
    assert "Status codes for tasks." in result
    assert "PENDING = 1" in result
    assert "ACTIVE = 2" in result
    assert "DONE = 3" in result


def test_enum_builder_add_line() -> None:
    """Test that add_line() method works."""
    enum = EnumBuilder(
        name="Priority",
        members=["LOW", "MEDIUM", "HIGH"],
    )

    enum.add_line("# Custom helper method")
    enum.add_line("def get_level(self) -> int:")
    enum.add_line("    return list(Priority).index(self)")

    result = enum.render()

    assert "# Custom helper method" in result
    assert "def get_level(self) -> int:" in result
    assert "return list(Priority).index(self)" in result


def test_enum_builder_add_to_docs() -> None:
    """Test that add_to_docs() method works."""
    enum = EnumBuilder(
        name="Mode",
        members=["READ", "WRITE", "EXECUTE"],
        docstring="File access modes.",
    )

    enum.add_to_docs("\n\nExamples:\n    >>> Mode.READ\n    <Mode.READ: 'READ'>")

    result = enum.render()

    assert "File access modes." in result
    assert "Examples:" in result
    assert ">>> Mode.READ" in result


def test_enum_builder_gets_smart_spacing() -> None:
    """Test that EnumBuilder gets smart spacing (2 newlines)."""
    section = CodeSection("body")

    enum = EnumBuilder(
        name="Color",
        members=["RED", "GREEN", "BLUE"],
    )

    section.add(enum)

    lines = section.get()

    # Should have 2 newlines at the end (smart spacing for classes)
    newline_count = len([line for line in lines if line == "\n"])
    assert newline_count == 2
