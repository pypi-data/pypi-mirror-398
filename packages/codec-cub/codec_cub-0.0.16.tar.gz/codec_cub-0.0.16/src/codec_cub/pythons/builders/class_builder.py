"""API for building Python class definitions"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from codec_cub.common import COMMA_SPACE
from codec_cub.pythons._buffer import BufferHelper
from codec_cub.pythons._protocols import CodeBuilder
from codec_cub.pythons.helpers import Arg, Decorator, get_decorators
from codec_cub.pythons.parts import Attribute, Docstring
from funcy_bear.constants import characters as ch, py_chars as py
from funcy_bear.ops.strings import manipulation as man
from funcy_bear.sentinels import NOTSET, NotSetType

from .function_builder import MethodBuilder

if TYPE_CHECKING:
    from codec_cub.pythons.type_annotation import TypeHint

    from .docstring_builder import DocstringBuilder
    from .function_builder import FunctionBuilder


class ClassBuilder(CodeBuilder):
    """Builder for Python class definitions with support for attributes and methods.

    Supports dataclasses, Pydantic models, and regular classes with inline attributes.
    """

    def __init__(
        self,
        name: str,
        indent: int = 0,
        bases: str | list[str] = ch.EMPTY_STRING,
        type_p: str | list[str] = ch.EMPTY_STRING,
        decorators: list[str] | list[Decorator] | None = None,
        attributes: list[Attribute] | None = None,
        methods: list[FunctionBuilder] | None = None,
        docstring: str = ch.EMPTY_STRING,
        body: str = ch.EMPTY_STRING,
    ) -> None:
        """Initialize a ClassBuilder.

        Args:
            name: Class name.
            bases: Optional base classes (without parentheses).
            type_p: Optional type parameters (for generics).
            decorators: Optional list of decorator strings (without @).
            attributes: Optional list of class attributes (for dataclasses/Pydantic).
            methods: Optional list of FunctionBuilder instances.
            docstring: Optional class docstring.
            body: Optional raw body content (use if not using attributes/methods).
            indent: Base indentation level.
        """
        self.name: str = name
        if isinstance(bases, list):
            bases_str: str = COMMA_SPACE.join(bases)
        else:
            bases_str = bases
        self._bases: str = man.paren(bases_str) if bases_str else ch.EMPTY_STRING
        self._type_p: str = (
            man.bracketed(COMMA_SPACE.join(type_p))
            if isinstance(type_p, list)
            else man.bracketed(type_p)
            if type_p
            else ch.EMPTY_STRING
        )
        self._decorators: str = get_decorators(decorators) if decorators else ch.EMPTY_STRING
        self._attributes: list[Attribute] = attributes or []
        self._methods: list[FunctionBuilder] = methods or []
        self._docstring: Docstring = Docstring(docstring)
        self._body: BufferHelper = BufferHelper(indent=indent + 1)
        self._added_lines: BufferHelper = BufferHelper(indent=indent + 1)
        self._added_lines.write(body, suffix=ch.NEWLINE) if body else None
        self._result: BufferHelper = BufferHelper()

    def method(
        self,
        name: str,
        indent: int = 0,
        args: str | Arg | list[Arg] = ch.EMPTY_STRING,
        returns: str | type | TypeHint | NotSetType | tuple[type, ...] = NOTSET,
        decorators: list[str] | list[Decorator] | None = None,
        docstring: str | DocstringBuilder = ch.EMPTY_STRING,
        body: str = ch.EMPTY_STRING,
    ) -> Self:
        """Add a method to the class.

        Args:
            name: Method name.
            args: Method arguments (without parentheses).
            returns: Optional return type annotation (NOTSET for no annotation, NoneType for -> None, or TypeHint object).
            decorators: Optional list of decorator strings (without @).
            docstring: Docstring content (string or DocstringBuilder object).
            body: Method body content.
            indent: Base indentation level.

        Returns:
            Self for method chaining.
        """
        self._methods.append(
            MethodBuilder(
                name=name,
                indent=indent + 1,
                args=args,
                returns=returns,
                decorators=decorators,
                docstring=docstring,
                body=body,
            )
        )
        return self

    @property
    def signature(self) -> str:
        """Set or update the class signature.

        Returns:
            string representing the class signature.
        """
        return man.join(py.CLASS_STR, ch.SPACE, self.name, self._type_p, self._bases, ch.COLON)

    def render(self) -> str:
        """Render the class to a string.

        Returns:
            The complete class definition as a string.
        """
        if self._decorators:
            self._result.write(self._decorators, suffix=ch.NEWLINE)
        self._result.write(self.signature, suffix=ch.NEWLINE)

        if self._docstring:
            self._body.write(self._docstring.render(), suffix=ch.NEWLINE)

        if self._attributes:
            for attr in self._attributes:
                self._body.write(attr.render(), suffix=ch.NEWLINE)
            if self._methods:
                self._body.write(ch.NEWLINE)

        if self._methods:
            for i, method in enumerate(self._methods):
                if i > 0:
                    self._body.write(ch.NEWLINE)
                self._body.write(method.render())

        if self._added_lines.not_empty:
            self._body.write(self._added_lines.getvalue())

        if not self._body.not_empty:
            self._body.write(ch.ELLIPSIS)

        self._result.write(self._body.getvalue())
        result: str = self._result.getvalue()
        self.clear()
        return result

    def clear(self) -> Self:
        """Clear the class body and docstring."""
        self.name = ch.EMPTY_STRING
        self._bases = ch.EMPTY_STRING
        self._decorators = ch.EMPTY_STRING
        self._attributes = []
        self._methods = []
        self._docstring.clear()
        self._body.clear()
        self._result.clear()
        self._added_lines.clear()
        return self


class Dataclass(ClassBuilder):
    """Builder for Python dataclass definitions."""

    def __init__(
        self,
        name: str,
        indent: int = 0,
        bases: str | list[str] = ch.EMPTY_STRING,
        type_p: str | list[str] = ch.EMPTY_STRING,
        decorators: list[str] | list[Decorator] | None = None,
        attributes: list[Attribute] | None = None,
        methods: list[FunctionBuilder] | None = None,
        docstring: str = ch.EMPTY_STRING,
        body: str = ch.EMPTY_STRING,
    ) -> None:
        """Initialize a Dataclass builder.

        Args:
            name: Class name.
            bases: Optional base classes (without parentheses).
            type_p: Optional type parameters (for generics).
            decorators: Optional list of decorator strings (without @).
            attributes: Optional list of class attributes.
            methods: Optional list of FunctionBuilder instances.
            docstring: Optional class docstring.
            body: Optional raw body content (use if not using attributes/methods).
            indent: Base indentation level.
        """
        all_decorators: list[Decorator] = [Decorator("dataclass")]
        if decorators:
            all_decorators.extend([Decorator(d) if isinstance(d, str) else d for d in decorators])
        super().__init__(
            name=name,
            indent=indent,
            bases=bases,
            type_p=type_p,
            decorators=all_decorators,
            attributes=attributes,
            methods=methods,
            docstring=docstring,
            body=body,
        )


class PydanticModel(ClassBuilder):
    """Builder for Pydantic model class definitions."""

    def __init__(
        self,
        name: str,
        indent: int = 0,
        bases: str | list[str] = "BaseModel",
        type_p: str | list[str] = ch.EMPTY_STRING,
        decorators: list[str] | list[Decorator] | None = None,
        attributes: list[Attribute] | None = None,
        methods: list[FunctionBuilder] | None = None,
        docstring: str = ch.EMPTY_STRING,
        body: str = ch.EMPTY_STRING,
    ) -> None:
        """Initialize a Pydantic model builder.

        Args:
            name: Class name.
            bases: Optional base classes (without parentheses).
            type_p: Optional type parameters (for generics).
            decorators: Optional list of decorator strings (without @).
            attributes: Optional list of class attributes.
            methods: Optional list of FunctionBuilder instances.
            docstring: Optional class docstring.
            body: Optional raw body content (use if not using attributes/methods).
            indent: Base indentation level.
        """
        super().__init__(
            name=name,
            indent=indent,
            bases=bases,
            type_p=type_p,
            decorators=decorators,
            attributes=attributes,
            methods=methods,
            docstring=docstring,
            body=body,
        )
