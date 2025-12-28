"""Utility classes and functions for building function arguments and decorators."""

from __future__ import annotations

from dataclasses import dataclass

from codec_cub.pythons import common as co
from codec_cub.pythons._buffer import StringBuilder
from funcy_bear.constants import characters as ch, py_chars as py
from funcy_bear.ops.strings import manipulation as man
from funcy_bear.sentinels import NOTSET, NotSetType
from funcy_bear.type_stuffs.builtin_tools import type_name

from .type_annotation import TypeHint, union


@dataclass(slots=True)
class ArgumentBase:
    """Base class for function argument representations."""

    name: str
    annotations: str | TypeHint = ch.EMPTY_STRING
    default: str | NotSetType = NOTSET

    @property
    def type(self) -> str:
        """Get the type annotation as a string.

        Returns:
            The type annotation as a string.
        """
        if isinstance(self.annotations, TypeHint):
            return self.annotations.render()

        if isinstance(self.annotations, str):
            if ch.PIPE in self.annotations:
                return union(*[part.strip() for part in self.annotations.split(ch.PIPE)]).render()
            return self.annotations

        if isinstance(self.annotations, tuple):
            return man.piped(co.to_type_names(self.annotations))

        return type_name(self.annotations)  # pyright: ignore[reportArgumentType]

    def render(self) -> str:
        """Render the argument to a string.

        Returns:
            The argument as a string.
        """
        s = StringBuilder(self.name)
        if self.type:
            s.join(ch.COLON, ch.SPACE, self.type)
        if not isinstance(self.default, NotSetType):
            s.join(ch.SPACE, ch.EQUALS, ch.SPACE, self.default)
        return s.consume()

    @classmethod
    def empty(cls, empty_str: str = ch.EMPTY_STRING) -> str:
        """Create an ArgumentBase representing an empty argument.

        Returns:
            An ArgumentBase instance with no name, annotations, or default.
        """
        return cls(name=empty_str).render()


@dataclass(slots=True)
class Arg(ArgumentBase):
    """Represents a function argument with optional type annotation and default value."""

    arg: bool = False
    kwarg: bool = False

    def render(self) -> str:
        """Render the argument to a string.

        Returns:
            The argument as a string.
        """
        s: StringBuilder = StringBuilder().join(man.get_asterisks(self.arg, self.kwarg), self.name)
        if self.type:
            s.join(ch.COLON, ch.SPACE, self.type)
        if self.default:
            s.join(ch.SPACE, ch.EQUALS, ch.SPACE, self.default)
        return s.consume()


@dataclass(slots=True)
class Decorator(ArgumentBase):
    """Represents a function decorator."""

    name: str
    args: str | Arg | list[Arg] = ch.EMPTY_STRING
    called: bool = False

    def render(self) -> str:
        """Render the decorator to a string.

        Returns:
            The decorator as a string.
        """
        from .helpers import render_args  # noqa: PLC0415

        s = StringBuilder(ch.AT, self.name)
        if self.called or self.args:
            s.add(ch.LEFT_PAREN)
            s.join(render_args(self.args) if self.args else ch.EMPTY_STRING, ch.RIGHT_PAREN)
        return s.consume()


@dataclass(slots=True)
class Variable(ArgumentBase):
    """Represents a variable with optional type annotation and default value."""

    @property
    def type(self) -> str:
        """Get the type annotation as a string.

        Returns:
            The type annotation as a string.
        """
        if isinstance(self.annotations, TypeHint):
            return self.annotations.render()
        return self.annotations


@dataclass(slots=True)
class Attribute(ArgumentBase):
    """Represents a class attribute (for dataclasses, Pydantic models, etc.).

    Similar to Variable but with additional options for class attributes like
    ClassVar, field metadata, etc.
    """

    class_var: bool = False

    @property
    def type(self) -> str:
        """Get the type annotation as a string.

        Returns:
            The type annotation as a string.
        """
        if isinstance(self.annotations, TypeHint):
            return self.annotations.render()

        if isinstance(self.annotations, str):
            if ch.PIPE in self.annotations:
                return union(*[part.strip() for part in self.annotations.split(ch.PIPE)]).render()
            return self.annotations

        if isinstance(self.annotations, tuple):
            return man.piped(co.to_type_names(self.annotations))

        return type_name(self.annotations)  # pyright: ignore[reportArgumentType]

    def render(self) -> str:
        """Render the attribute to a string.

        Returns:
            The attribute as a string.
        """
        s = StringBuilder(self.name)
        if self.type:
            type_str: str = self.type
            if self.class_var:
                s.join(ch.COLON, py.CLASS_VAR_STR, ch.LEFT_BRACKET, type_str, ch.RIGHT_BRACKET)  # ClassVar[type_str]
            else:
                s.join(ch.COLON, ch.SPACE, type_str)  # : type_str
        if self.default:
            s.join(ch.SPACE, ch.EQUALS, ch.SPACE, self.default)  #  = default
        return s.consume()


@dataclass(slots=True)
class Docstring:
    """Represents a docstring."""

    content: str

    def add(self, additional_content: str, prefix: str = ch.EMPTY_STRING, suffix: str = ch.EMPTY_STRING) -> Docstring:
        """Add additional content to the docstring.

        Args:
            additional_content: The content to add to the docstring.
            prefix: An optional prefix to add before the additional content.
            suffix: An optional suffix to add after the additional content.

        Returns:
            The updated Docstring instance.
        """
        self.content += man.join(prefix, additional_content, suffix)
        return self

    def render(self) -> str:
        """Render the docstring to a string.

        Returns:
            The docstring as a string.
        """
        from .helpers import get_docstring  # noqa: PLC0415

        return get_docstring(self.content)

    def clear(self) -> Docstring:
        """Clear the docstring content.

        Returns:
            The updated Docstring instance.
        """
        self.content = ch.EMPTY_STRING
        return self

    def __bool__(self) -> bool:
        """Return True if docstring has content, False otherwise."""
        return bool(self.content)
