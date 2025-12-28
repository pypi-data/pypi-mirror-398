"""Fluent builders for common code patterns."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from codec_cub.common import comma_sep
from codec_cub.pythons._buffer import BufferHelper
from codec_cub.pythons.code_section import CodeSection  # noqa: TC001
from codec_cub.pythons.helpers import get_literal_type, get_type_alias
from codec_cub.pythons.parts import Variable
from codec_cub.pythons.type_annotation import TypeHint
from funcy_bear.constants import characters as ch
from funcy_bear.ops.strings import manipulation as man
from funcy_bear.type_stuffs.inference.runtime import infer_type

if TYPE_CHECKING:
    from collections.abc import Sequence


class TypeAliasBuilder:
    """Fluent builder for PEP 613 type aliases.

    Examples:
        >>> section.type_alias("StorageChoices").literal("json", "yaml", "toml")
        >>> section.type_alias("IntOrStr").union("int", "str")
    """

    def __init__(self, section: CodeSection, name: str) -> None:
        """Initialize the type alias builder.

        Args:
            section: The code section to add the alias to.
            name: The name of the type alias.
        """
        self._section: CodeSection = section
        self._name: str = name

    def literal(self, *values: str) -> Self:
        """Create a Literal type alias.

        Args:
            *values: The literal values.

        Returns:
            Self for method chaining.
        """
        literal_type: str = get_literal_type(list(values))
        alias_str: str = get_type_alias(self._name, literal_type)
        self._section.add(alias_str)
        return self

    def from_annotation(self, annotation: TypeHint) -> Self:
        """Create a type alias from a TypeHint.

        Args:
            annotation: The type annotation.

        Returns:
            Self for method chaining.
        """
        type_str: str = annotation.render()
        alias_str: str = get_type_alias(self._name, type_str)
        self._section.add(alias_str)
        return self

    def union(self, *types: TypeHint) -> Self:
        """Create a union type alias.

        Args:
            *types: The types in the union.

        Returns:
            Self for method chaining.
        """
        union_type: TypeHint = TypeHint.union(*types)
        return self.from_annotation(union_type)


class VariableBuilder:
    """Fluent builder for variable declarations.

    Examples:
        >>> section.variable("storage_map") \
        ...     .type_hint("dict[str, type[Storage]]") \
        ...     .value("{...}")
    """

    def __init__(self, section: CodeSection, name: str) -> None:
        """Initialize the variable builder.

        Args:
            section: The code section to add the variable to.
            name: The variable name.
        """
        self._section: CodeSection = section
        self._name: str = name
        self._variable: Variable = Variable(name=name)
        self._value: str | None = None

    def type_hint(self, h: TypeHint | str, final: bool = False) -> Self:
        """Set the type hint for the variable.

        Args:
            h: The type annotation.

        Returns:
            Self for method chaining.
        """
        if isinstance(h, str):
            h = TypeHint(h, final=final)
        type_hint: str = h.render()
        self._variable.annotations = type_hint
        return self

    def value(self, val: str | Any) -> Self:
        """Set the value and add the variable to the section.

        Args:
            val: The value expression.

        Returns:
            Self for method chaining.
        """
        self._variable.default = val
        if not self._variable.annotations:
            inferred_type: str = infer_type(val)
            self._variable.annotations = inferred_type
        self._section.add(self._variable.render(), end=-1)
        return self

    def to_tuple(self, values: Sequence) -> Self:
        """Set the variable value as a tuple of the given values.

        Args:
            values: The values for the tuple.

        Returns:
            Self for method chaining.
        """
        from codec_cub.pythons.python_data_writer import to_str  # noqa: PLC0415

        self.value(to_str(tuple(values)))
        return self


class ListLiteralBuilder:
    """Fluent builder for Python list literals.

    Examples:
        >>> builder = ListLiteralBuilder()
        >>> builder.add("'a'").add("'b'").add("'c'").render()
        "['a', 'b', 'c']"

        >>> builder = ListLiteralBuilder()
        >>> builder.add("'a'").add("'b'").multiline().render()
        "[
            'a',
            'b',
        ]"
    """

    def __init__(self, indent: int = 0) -> None:
        """Initialize the list literal builder.

        Args:
            indent: Base indentation level.
        """
        self._items: list[str] = []
        self._multiline: bool = False
        self._trailing_blank_line: bool = False
        self._buffer: BufferHelper | None = None
        self.indent: int = indent

    @property
    def buffer(self) -> BufferHelper:
        """Get or create the internal buffer."""
        if self._buffer is None:
            self._buffer = BufferHelper(indent=self.indent)
        return self._buffer

    def add(self, v: str) -> Self:
        """Add an item to the list.

        Args:
            v: The item expression (already formatted as string/number/etc).

        Returns:
            Self for method chaining.
        """
        self._items.append(v)
        return self

    def multiline(self, enabled: bool = True) -> Self:
        """Enable or disable multiline formatting.

        Args:
            enabled: Whether to use multiline format.

        Returns:
            Self for method chaining.
        """
        self._multiline = enabled
        return self

    def trailing_blank_line(self, enabled: bool = True) -> Self:
        """Add a blank indented line before the closing bracket in multiline mode.

        This is useful for maintaining consistent byte offsets when appending to files.

        Args:
            enabled: Whether to add the trailing blank line.

        Returns:
            Self for method chaining.
        """
        self._trailing_blank_line = enabled
        return self

    def render(self) -> str:
        """Render the list literal to a string.

        Returns:
            The formatted list literal.
        """
        if not self._items and not self._trailing_blank_line:
            return man.bracketed("")

        if not self._multiline:
            items_str: str = comma_sep(self._items)
            self.clear()
            return man.bracketed(items_str)

        self.buffer.write(ch.LEFT_BRACKET, suffix=ch.NEWLINE)
        with self.buffer.indented():
            for item in self._items:
                self.buffer.write(f"{item},", suffix=ch.NEWLINE)
            if self._trailing_blank_line:
                self.buffer.write(ch.EMPTY_STRING, suffix=ch.NEWLINE)
        self.buffer.write(ch.RIGHT_BRACKET)
        value: str = self.buffer.getvalue()
        self.clear()
        return value

    def clear(self) -> Self:
        """Clear all list content."""
        self._items.clear()
        self._multiline = False
        self._trailing_blank_line = False
        if self._buffer:
            self._buffer = None
        return self

    def __str__(self) -> str:
        """String representation (calls render)."""
        return self.render()

    def __repr__(self) -> str:
        """Repr representation."""
        return f"ListLiteralBuilder(items={len(self._items)}, multiline={self._multiline})"


class DictLiteralBuilder:
    """Fluent builder for Python dict literals.

    Examples:
        >>> builder = DictLiteralBuilder()
        >>> builder.entry("'host'", "'localhost'").entry("'port'", "8080").render()
        "{'host': 'localhost', 'port': 8080}"

        >>> builder = DictLiteralBuilder()
        >>> builder.entry("'host'", "'localhost'").multiline().render()
        "{
            'host': 'localhost',
        }"
    """

    def __init__(self, indent: int = 0) -> None:
        """Initialize the dict literal builder.

        Args:
            indent: Base indentation level.
        """
        self._entries: list[tuple[str, str]] = []
        self._multiline: bool = False
        self._buffer: BufferHelper | None = None
        self.indent: int = indent

    @property
    def buffer(self) -> BufferHelper:
        """Get or create the internal buffer."""
        if self._buffer is None:
            self._buffer = BufferHelper(indent=self.indent)
        return self._buffer

    def entry(self, k: str, v: str) -> Self:
        """Add a key-value entry to the dict.

        Args:
            k: The key expression (already formatted as string).
            v: The value expression (already formatted).

        Returns:
            Self for method chaining.
        """
        self._entries.append((k, v))
        return self

    def multiline(self, enabled: bool = True) -> Self:
        """Enable or disable multiline formatting.

        Args:
            enabled: Whether to use multiline format.

        Returns:
            Self for method chaining.
        """
        self._multiline = enabled
        return self

    def render(self) -> str:
        """Render the dict literal to a string.

        Returns:
            The formatted dict literal.
        """
        if not self._entries:
            return man.braced("")

        if not self._multiline:
            entries_str: str = comma_sep([f"{k}: {v}" for k, v in self._entries])
            self.clear()
            return man.braced(entries_str)

        self.buffer.write(ch.LEFT_BRACE, suffix=ch.NEWLINE)
        with self.buffer.indented():
            for key, value in self._entries:
                self.buffer.write(f"{key}: {value},", suffix=ch.NEWLINE)
        self.buffer.write(ch.RIGHT_BRACE)
        value: str = self.buffer.getvalue()
        self.clear()
        return value

    def clear(self) -> Self:
        """Clear all dict content."""
        self._entries.clear()
        self._multiline = False
        if self._buffer:
            self._buffer = None
        return self

    def __str__(self) -> str:
        """String representation (calls render)."""
        return self.render()

    def __repr__(self) -> str:
        """Repr representation."""
        return f"DictLiteralBuilder(entries={len(self._entries)}, multiline={self._multiline})"


class TupleLiteralBuilder:
    """Fluent builder for Python tuple literals.

    Examples:
        >>> builder = TupleLiteralBuilder()
        >>> builder.add("'a'").add("'b'").add("'c'").render()
        "('a', 'b', 'c')"

        >>> builder = TupleLiteralBuilder()
        >>> builder.add("'a'").add("'b'").multiline().render()
        "(
            'a',
            'b',
        )"
    """

    def __init__(self, indent: int = 0) -> None:
        """Initialize the tuple literal builder.

        Args:
            indent: Base indentation level.
        """
        self._items: list[str] = []
        self._multiline: bool = False
        self._buffer: BufferHelper | None = None
        self.indent: int = indent

    @property
    def buffer(self) -> BufferHelper:
        """Get or create the internal buffer."""
        if self._buffer is None:
            self._buffer = BufferHelper(indent=self.indent)
        return self._buffer

    @property
    def single_item(self) -> bool:
        """Check if the tuple has a single item."""
        return len(self._items) == 1

    def add(self, v: str) -> Self:
        """Add an item to the tuple.

        Args:
            v: The item expression (already formatted as string/number/etc).

        Returns:
            Self for method chaining.
        """
        self._items.append(v)
        return self

    def multiline(self, enabled: bool = True) -> Self:
        """Enable or disable multiline formatting.

        Args:
            enabled: Whether to use multiline format.

        Returns:
            Self for method chaining.
        """
        self._multiline = enabled
        return self

    def render(self) -> str:
        """Render the tuple literal to a string.

        Returns:
            The formatted tuple literal.
        """
        if not self._items:
            return man.paren("")

        if not self._multiline:
            items_str: str = ", ".join(self._items) + ("," if self.single_item else "")
            self.clear()
            return man.paren(items_str)

        self.buffer.write(ch.LEFT_PAREN, suffix=ch.NEWLINE)
        with self.buffer.indented():
            for item in self._items:
                self.buffer.write(f"{item},", suffix=ch.NEWLINE)
        self.buffer.write(ch.RIGHT_PAREN)
        value: str = self.buffer.getvalue()
        self.clear()
        return value

    def clear(self) -> Self:
        """Clear all tuple content."""
        self._items.clear()
        self._multiline = False
        if self._buffer:
            self._buffer = None
        return self

    def __str__(self) -> str:
        """String representation (calls render)."""
        return self.render()

    def __repr__(self) -> str:
        """Repr representation."""
        return f"TupleLiteralBuilder(items={len(self._items)}, multiline={self._multiline})"
