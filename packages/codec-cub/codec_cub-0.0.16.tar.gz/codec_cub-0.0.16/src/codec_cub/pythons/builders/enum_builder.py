"""General-purpose enum builder for Enum, IntEnum, StrEnum, Flag, etc."""

from __future__ import annotations

from typing import Self

from codec_cub.pythons._buffer import BufferHelper
from codec_cub.pythons.helpers import Decorator, get_decorators
from codec_cub.pythons.parts import Docstring
from funcy_bear.constants import characters as ch, py_chars as py
from funcy_bear.ops.strings.manipulation import join, quoted


class EnumBuilder:
    """General-purpose enum builder for Enum, IntEnum, StrEnum, Flag, etc.

    Supports all enum types by specifying the base class.
    """

    def __init__(
        self,
        name: str,
        members: dict[str, str | int] | list[str],
        base_class: str = "Enum",
        decorators: list[str] | list[Decorator] | None = None,
        docstring: str = ch.EMPTY_STRING,
    ) -> None:
        """Initialize an EnumBuilder.

        Args:
            name: Enum class name.
            members: Either dict of name->value pairs or list of names (auto values).
            base_class: Base enum type (Enum, IntEnum, StrEnum, Flag, etc.).
            decorators: Optional decorators.
            docstring: Optional docstring.
        """
        self.name: str = name
        self.base_class: str = base_class
        self._members: dict[str, str | int]
        self._members = dict.fromkeys(members, f"{py.AUTO_STR}()") if isinstance(members, list) else members
        self._decorators: str = get_decorators(decorators) if decorators else ch.EMPTY_STRING
        self._docstring: Docstring = Docstring(docstring)
        self._added_lines: BufferHelper = BufferHelper(indent=1)

    def add_line(self, line: str) -> Self:
        """Add a line to the enum body.

        Args:
            line: The line to add.

        Returns:
            Self for method chaining.
        """
        self._added_lines.write(line, suffix=ch.NEWLINE)
        return self

    def add_to_docs(
        self,
        additional_content: str,
        prefix: str = "",
        suffix: str = "",
    ) -> Self:
        """Add additional content to the docstring.

        Args:
            additional_content: The content to add to the docstring.
            prefix: An optional prefix to add before the additional content.
            suffix: An optional suffix to add after the additional content.

        Returns:
            Self for method chaining.
        """
        self._docstring.add(additional_content, prefix=prefix, suffix=suffix)
        return self

    def render(self) -> str:
        """Render the enum to a string.

        Returns:
            The complete enum definition as a string.
        """
        result = BufferHelper()

        if self._decorators:
            result.write(self._decorators, suffix=ch.NEWLINE)

        result.write(
            join(py.CLASS_STR, " ", self.name, ch.LEFT_PAREN, self.base_class, ch.RIGHT_PAREN, ch.COLON),
            suffix=ch.NEWLINE,
        )

        body = BufferHelper(indent=1)
        if self._docstring:
            body.write(self._docstring.render(), suffix=ch.NEWLINE)
            body.write(ch.NEWLINE)

        for member_name, member_value in self._members.items():
            mem_val: str | int = member_value
            if isinstance(member_value, str) and not member_value.startswith(
                (py.AUTO_STR, ch.DOUBLE_QUOTE, ch.SINGLE_QUOTE)
            ):
                mem_val = quoted(member_value)
            body.write(join(member_name, " ", ch.EQUALS, " ", str(mem_val)), suffix=ch.NEWLINE)

        if self._added_lines.not_empty:
            body.write(self._added_lines.getvalue())

        result.write(body.getvalue())
        return result.getvalue()
