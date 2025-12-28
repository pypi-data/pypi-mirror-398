"""Tests for smart spacing detection in CodeSection."""

from __future__ import annotations

from codec_cub.pythons import Decorator, FunctionBuilder
from codec_cub.pythons.builders import ClassBuilder
from codec_cub.pythons.file_builder import CodeSection


def test_overload_function_gets_one_newline() -> None:
    """Test that @overload functions automatically get 1 newline."""
    section = CodeSection("body")

    func = FunctionBuilder(
        name="test",
        args="x: int",
        returns="str",
        decorators=[Decorator("overload")],
    )

    # Add without specifying end parameter
    section.add(func)

    lines: list[str] = section.get()

    # Should have 1 newline at the end
    assert lines[-1] == "\n"
    # But NOT 2 newlines
    assert len([line for line in lines if line == "\n"]) == 1


def test_regular_function_gets_two_newlines() -> None:
    """Test that regular functions automatically get 2 newlines."""
    section = CodeSection("body")

    func = FunctionBuilder(
        name="test",
        args="x: int",
        returns="str",
        body="return str(x)",
    )

    # Add without specifying end parameter
    section.add(func)

    lines: list[str] = section.get()

    # Should have 2 newlines at the end
    newline_count: int = len([line for line in lines if line == "\n"])
    assert newline_count == 2


def test_class_gets_two_newlines() -> None:
    """Test that classes automatically get 2 newlines."""
    section = CodeSection("body")

    cls = ClassBuilder(
        name="TestClass",
    )

    # Add without specifying end parameter
    section.add(cls)

    lines: list[str] = section.get()

    # Should have 2 newlines at the end
    newline_count: int = len([line for line in lines if line == "\n"])
    assert newline_count == 2


def test_type_alias_gets_one_newline() -> None:
    """Test that type aliases automatically get 1 newline."""
    section = CodeSection("body")

    # Add a type alias (PEP 613 syntax)
    section.add('type MyType = Literal["a", "b", "c"]')

    lines: list[str] = section.get()

    # Should have 1 newline at the end
    assert lines[-1] == "\n"
    newline_count: int = len([line for line in lines if line == "\n"])
    assert newline_count == 1


def test_variable_with_annotation_gets_one_newline() -> None:
    """Test that annotated variables automatically get 1 newline."""
    section = CodeSection("body")

    # Add a variable with type annotation
    section.add("my_var: int = 42")

    lines: list[str] = section.get()

    # Should have 1 newline at the end
    assert lines[-1] == "\n"
    newline_count: int = len([line for line in lines if line == "\n"])
    assert newline_count == 1


def test_plain_string_gets_no_newlines() -> None:
    """Test that plain strings get no automatic newlines."""
    section = CodeSection("body")

    # Add a comment or other plain string
    section.add("# This is a comment")

    lines: list[str] = section.get()

    # Should NOT have any newlines (user controls spacing)
    newline_count: int = len([line for line in lines if line == "\n"])
    assert newline_count == 0


def test_manual_end_overrides_smart_spacing() -> None:
    """Test that manual end parameter overrides smart spacing."""
    section = CodeSection("body")

    func = FunctionBuilder(
        name="test",
        returns="None",
        body="pass",
    )

    # Normally gets 2 newlines, but we override to 5
    section.add(func, end=5)

    lines: list[str] = section.get()

    # Should have exactly 5 newlines
    newline_count: int = len([line for line in lines if line == "\n"])
    assert newline_count == 5


def test_multiple_overloads_stack_nicely() -> None:
    """Test that multiple overloads stack with 1 newline between each."""
    section = CodeSection("body")

    # Add 3 overloads
    for i in range(3):
        func = FunctionBuilder(
            name="test",
            args=f"x: Literal[{i}]",
            returns="int",
            decorators=[Decorator("overload")],
        )
        section.add(func)

    lines: list[str] = section.get()

    # Count @overload occurrences
    overload_count: int = len([line for line in lines if "@overload" in line])
    assert overload_count == 3

    # Each overload should have 1 newline after it (3 total)
    newline_count: int = len([line for line in lines if line == "\n"])
    assert newline_count == 3
