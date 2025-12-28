"""Code section buffer with indentation management and context managers for code blocks."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Self

from codec_cub.pythons._buffer import BufferHelper, StringBuilder
from codec_cub.pythons._protocols import CodeBuilder, Renderable
from codec_cub.pythons.builders import EnumBuilder
from codec_cub.pythons.builders.class_builder import ClassBuilder
from codec_cub.pythons.builders.function_builder import FunctionBuilder
from codec_cub.pythons.common import NewLineReturn
from funcy_bear.constants import characters as ch, py_chars as py
from funcy_bear.ops.strings.manipulation import join

if TYPE_CHECKING:
    from collections.abc import Generator

    from codec_cub.pythons.builders import DictLiteralBuilder, ListLiteralBuilder, TypeAliasBuilder, VariableBuilder


class CodeSection:
    """A code section buffer with indentation management and context managers for code blocks."""

    _section_name: str = "CodeSection"

    def __init__(self, name: str | None = None) -> None:
        """Initialize the CodeSection with a name and empty buffer."""
        self.section_name: str = name if name else self._section_name
        self._buffer: BufferHelper = BufferHelper()

    def _add(self, *segments: str, sep: str = ch.EMPTY_STRING) -> None:
        """Concatenate segments and write to buffer."""
        values: list[Any] = []
        for seg in segments:
            if isinstance(seg, Renderable):
                values.append(seg.render())
            else:
                values.append(seg)
        line: str = join(*values, sep=sep)
        self._buffer.write(line, suffix=ch.EMPTY_STRING if line.endswith(ch.NEWLINE) else ch.NEWLINE)

    def docstring(self, *doc_lines: str, indent: int = 0) -> None:
        """Begin a docstring block.

        Args:
            *doc_lines: Lines of the docstring.
            indent: Relative indent change (can be negative to outdent relative to class).
        """
        if indent != 0:
            self._buffer.tick(indent)
        self._add(ch.TRIPLE_QUOTE)
        for line in doc_lines:
            self._add(line)
        self._add(ch.TRIPLE_QUOTE)
        if indent != 0:
            self._buffer.tock(indent)

    def _detect_spacing(self, item: str | CodeBuilder, original_item: str | CodeBuilder) -> int:
        """Detect appropriate spacing for the given item.

        Args:
            item: The rendered string (if CodeBuilder was passed, this is the rendered output).
            original_item: The original item (CodeBuilder or string).

        Returns:
            Number of newlines to add after this item.
        """
        if isinstance(original_item, FunctionBuilder):
            decorators: str = getattr(original_item, "_decorators", "")
            if (isinstance(item, str) and "@overload" in item) or (decorators and "overload" in decorators):
                return NewLineReturn.ONE
            return NewLineReturn.TWO

        if isinstance(original_item, (ClassBuilder, EnumBuilder)):
            return NewLineReturn.TWO

        if isinstance(item, str):  # noqa: SIM102
            if (item.startswith("type ") and ch.EQUALS in item) or (
                ch.COLON in item and ch.EQUALS in item and not item.strip().startswith(py.DEF_STR)
            ):
                return NewLineReturn.ONE

        return NewLineReturn.ZERO

    def add(self, *ln: str | CodeBuilder, indent: int = 0, end: int | None = None) -> Self:
        """Add line(s) or CodeBuilder object(s) to the buffer with smart spacing.

        Args:
            *ln: Line(s) or CodeBuilder object(s) to add to the buffer.
            indent: Relative indent change (can be negative to outdent relative to class).
            end: Number of newlines to add after the content. If None (default), auto-detects based on content type.

        """
        if indent != 0:
            self._buffer.tick(indent)

        lines_to_add: list[str] = []
        original_items: list[str | CodeBuilder] = []

        for item in ln:
            original_items.append(item)
            if isinstance(item, CodeBuilder):
                lines_to_add.append(item.render())
            else:
                lines_to_add.append(item)

        for line in lines_to_add:
            self._add(line)

        if indent != 0:
            self._buffer.tock(indent)

        if end is None and lines_to_add and original_items:
            end = self._detect_spacing(lines_to_add[0], original_items[0])

        if end is not None and end > 0:
            self.newline(end)
        return self

    def newline(self, n: int = 1) -> Self:
        """Add newlines to the buffer.

        Args:
            n: Number of newlines to add, default is 1.
        """
        for _ in range(n):
            self._buffer.write(ch.NEWLINE)
        return self

    def tick(self) -> Self:
        """Increment the current indentation level by 1."""
        self._buffer.tick()
        return self

    def tock(self) -> Self:
        """Decrement the current indentation level by 1."""
        self._buffer.tock()
        return self

    def set_indent(self, level: int) -> Self:
        """Set the absolute indentation level.

        Args:
            level: The indentation level to set (0 = no indent).
        """
        self._buffer.indent = level
        return self

    def reset_indent(self) -> Self:
        """Reset indentation to 0."""
        self._buffer.indent = 0
        return self

    def get(self) -> list[str]:
        """Get the current buffer lines.

        Returns:
            A list of strings representing the buffer lines.
        """
        content: str = self._buffer.getvalue()
        if not content:
            return []

        lines = []
        parts: list[str] = content.split("\n")
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                if part:
                    lines.append(part)
            elif part:
                lines.append(part)
            else:
                lines.append("\n")
        return lines

    def type_alias(self, name: str) -> TypeAliasBuilder:
        """Create a fluent type alias builder.

        Args:
            name: The name of the type alias.

        Returns:
            A TypeAliasBuilder for fluent API.

        Examples:
            >>> section.type_alias("StorageChoices").literal("json", "yaml", "toml")
            >>> section.type_alias("IntOrStr").union("int", "str")
        """
        from codec_cub.pythons.builders.fluent_builders import TypeAliasBuilder  # noqa: PLC0415

        return TypeAliasBuilder(self, name)

    def variable(self, name: str) -> VariableBuilder:
        """Create a fluent variable builder.

        Args:
            name: The variable name.

        Returns:
            A VariableBuilder for fluent API.

        Examples:
            >>> section.variable("storage_map").type_hint("dict[str, type[Storage]]").value(
            ...     "{...}"
            ... )
        """
        from codec_cub.pythons.builders.fluent_builders import VariableBuilder  # noqa: PLC0415

        return VariableBuilder(self, name)

    def list_literal(self) -> ListLiteralBuilder:
        """Create a fluent list literal builder.

        Returns:
            A ListLiteralBuilder for fluent API.

        Examples:
            >>> from codec_cub.pythons.fluent_builders import ListLiteralBuilder
            >>> builder = ListLiteralBuilder()
            >>> builder.add("'a'").add("'b'").multiline().render()
        """
        from codec_cub.pythons.builders.fluent_builders import ListLiteralBuilder  # noqa: PLC0415

        return ListLiteralBuilder(indent=self._buffer.indent)

    def dict_literal(self) -> DictLiteralBuilder:
        """Create a fluent dict literal builder.

        Returns:
            A DictLiteralBuilder for fluent API.

        Examples:
            >>> from codec_cub.pythons.fluent_builders import DictLiteralBuilder
            >>> builder = DictLiteralBuilder()
            >>> builder.entry("'host'", "'localhost'").multiline().render()
        """
        from codec_cub.pythons.builders.fluent_builders import DictLiteralBuilder  # noqa: PLC0415

        return DictLiteralBuilder(indent=self._buffer.indent)

    def output(self) -> str:
        """Get the current buffer content as a single string.

        Returns:
            The buffer content as a string.
        """
        return self._buffer.getvalue()

    def join(self) -> str:
        """Get the current buffer content as a single string.

        Returns:
            The buffer content as a string.
        """
        return self._buffer.getvalue()

    @contextmanager
    def block(self, header: str) -> Generator[None, Any]:
        """Context manager for a generic code block with automatic indentation.

        Args:
            header: The header line (will have colon appended if not present).

        Yields:
            None
        """
        self.add(header if header.endswith(ch.COLON) else join(header, ch.COLON))
        self.tick()
        try:
            yield
        finally:
            self.tock()

    @contextmanager
    def function(self, name: str, args: str = ch.EMPTY_STRING, returns: str | None = None) -> Generator[None, Any]:
        """Context manager for a function definition.

        Args:
            name: Function name.
            args: Function arguments (without parentheses).
            returns: Optional return type annotation.

        Yields:
            None
        """
        s = StringBuilder(join(py.DEF_STR, ch.SPACE, name, ch.LEFT_PAREN, args, ch.RIGHT_PAREN))
        if returns:
            s.join(ch.SPACE, ch.ARROW, ch.SPACE, returns)
        with self.block(s.consume()):
            yield

    @contextmanager
    def class_def(self, name: str, bases: str = ch.EMPTY_STRING) -> Generator[None, Any]:
        """Context manager for a class definition.

        Args:
            name: Class name.
            bases: Optional base classes (without parentheses).

        Yields:
            None
        """
        s = StringBuilder(join(py.CLASS_STR, ch.SPACE, name))
        if bases:
            s.join(ch.LEFT_PAREN, bases, ch.RIGHT_PAREN)
        with self.block(s.consume()):
            yield

    @contextmanager
    def if_block(self, condition: str = "") -> Generator[Any, Any, Any]:
        """Context manager for an if statement.

        Args:
            condition: The condition to test.

        Yields:
            None
        """
        if self.section_name == py.TYPE_CHECKING_STR.lower():
            condition = py.TYPE_CHECKING_STR
        if not condition:
            condition = ch.TRUE_LITERAL
        with self.block(join(py.IF_STR, ch.SPACE, condition)):
            yield

    @contextmanager
    def elif_block(self, condition: str) -> Generator[None, Any]:
        """Context manager for an elif statement.

        Args:
            condition: The condition to test.

        Yields:
            None
        """
        with self.block(join(py.ELIF_STR, ch.SPACE, condition)):
            yield

    @contextmanager
    def else_block(self) -> Generator[None, Any]:
        """Context manager for an else statement.

        Yields:
            None
        """
        with self.block(py.ELSE_STR):
            yield

    @contextmanager
    def with_block(self, expression: str, as_var: str | None = None) -> Generator[None, Any]:
        """Context manager for a with statement.

        Args:
            expression: The context manager expression.
            as_var: Optional variable name for 'as' clause.

        Yields:
            None
        """
        s = StringBuilder(py.WITH_STR, ch.SPACE, expression)
        if as_var:
            s.join(ch.SPACE, py.AS_STR, ch.SPACE, as_var)
        with self.block(s.consume()):
            yield

    @contextmanager
    def try_block(self) -> Generator[None, Any]:
        """Context manager for a try statement.

        Yields:
            None
        """
        with self.block(py.TRY_STR):
            yield

    @contextmanager
    def except_block(self, exception: str | None = None, as_var: str | None = None) -> Generator[None, Any]:
        """Context manager for an except statement.

        Args:
            exception: Optional exception type to catch.
            as_var: Optional variable name for 'as' clause.

        Yields:
            None
        """
        s = StringBuilder(py.EXCEPT_STR)
        if exception:
            s.join(ch.SPACE, exception)
        if as_var:
            s.join(ch.SPACE, py.AS_STR, ch.SPACE, as_var)
        with self.block(s.consume()):
            yield

    @contextmanager
    def finally_block(self) -> Generator[None, Any]:
        """Context manager for a finally statement.

        Yields:
            None
        """
        with self.block(py.FINALLY_STR):
            yield

    @contextmanager
    def for_loop(self, variable: str, iterable: str) -> Generator[None, Any]:
        """Context manager for a for loop.

        Args:
            variable: Loop variable name.
            iterable: Expression to iterate over.

        Yields:
            None
        """
        with self.block(join(py.FOR_STR, ch.SPACE, variable, ch.SPACE, py.IN_STR, ch.SPACE, iterable)):
            yield

    @contextmanager
    def while_loop(self, condition: str) -> Generator[None, Any]:
        """Context manager for a while loop.

        Args:
            condition: The loop condition.

        Yields:
            None
        """
        with self.block(f"while {condition}"):
            yield


class HeaderSection(CodeSection):
    """A specialized code section for the header of a Python file."""

    _section_name: str = "header"


class TypeCheckingSection(CodeSection):
    """A specialized code section for type checking imports."""

    _section_name: str = "type_checking"


class BodySection(CodeSection):
    """A specialized code section for the body of a Python file."""

    _section_name: str = "body"


class FooterSection(CodeSection):
    """A specialized code section for the footer of a Python file."""

    _section_name: str = "footer"
