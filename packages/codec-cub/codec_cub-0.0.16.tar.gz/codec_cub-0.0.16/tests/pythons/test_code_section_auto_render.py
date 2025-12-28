"""Tests for CodeSection auto-rendering of CodeBuilder objects."""

from __future__ import annotations

from codec_cub.pythons import FunctionBuilder
from codec_cub.pythons.file_builder import CodeSection


def test_add_auto_renders_code_builder() -> None:
    """Test that CodeSection.add() automatically calls .render() on CodeBuilder objects."""
    section = CodeSection("body")

    # Create a simple function
    func = FunctionBuilder(
        name="hello",
        args="name: str",
        returns="str",
        body='return f"Hello, {name}!"',
    )

    # Add the function WITHOUT calling .render() manually
    section.add(func)

    # Get the rendered output
    result: str = "\n".join(section.get())

    # Should contain the function signature
    assert "def hello(name: str) -> str:" in result
    assert 'return f"Hello, {name}!"' in result


def test_add_still_accepts_strings() -> None:
    """Test that CodeSection.add() still works with plain strings."""
    section = CodeSection("body")

    # Add a plain string (annotated variables get smart spacing of 1 newline)
    section.add("x: int = 42")

    lines: list[str] = section.get()
    # Should have the variable plus 1 newline from smart spacing
    assert "x: int = 42" in "\n".join(lines)
    newline_count: int = len([line for line in lines if line == "\n"])
    assert newline_count == 1


def test_add_mixed_strings_and_builders() -> None:
    """Test that CodeSection.add() can handle both strings and CodeBuilder objects."""
    section = CodeSection("body")

    # Add a comment
    section.add("# A simple function")

    # Add a function builder
    func = FunctionBuilder(
        name="add",
        args="a: int, b: int",
        returns="int",
        body="return a + b",
    )
    section.add(func)

    result: str = "\n".join(section.get())

    # Should have both the comment and the function
    assert "# A simple function" in result
    assert "def add(a: int, b: int) -> int:" in result
    assert "return a + b" in result


def test_add_with_end_parameter() -> None:
    """Test that the end parameter adds newlines after auto-rendered content."""
    section = CodeSection("body")

    func = FunctionBuilder(
        name="test",
        returns="None",
        body="pass",
    )

    # Add with 2 trailing newlines
    section.add(func, end=2)

    lines: list[str] = section.get()

    # Should have the function plus 2 newlines at the end
    assert lines[-1] == "\n"  # Last line is a newline
    assert lines[-2] == "\n"  # Second-to-last line is also a newline
