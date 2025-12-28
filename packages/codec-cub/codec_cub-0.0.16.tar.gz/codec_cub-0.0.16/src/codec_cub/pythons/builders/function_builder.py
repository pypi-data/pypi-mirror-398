"""Builder for Python function definitions."""

from __future__ import annotations

from types import NoneType
from typing import TYPE_CHECKING, Self

from codec_cub.pythons._buffer import BufferHelper
from codec_cub.pythons._protocols import CodeBuilder
from codec_cub.pythons.builders.docstring_builder import DocstringBuilder
from codec_cub.pythons.helpers import render_args
from codec_cub.pythons.parts import Arg, Decorator, Docstring
from funcy_bear.constants import characters as ch
from funcy_bear.ops.strings.manipulation import join, paren
from funcy_bear.sentinels import NOTSET, NotSetType

if TYPE_CHECKING:
    from codec_cub.pythons.type_annotation import TypeHint


class FunctionBuilder(CodeBuilder):
    """Builder for Python function definitions."""

    def __init__(
        self,
        name: str,
        indent: int = 0,
        args: str | Arg | list[Arg] = ch.EMPTY_STRING,
        returns: str | type | TypeHint | NotSetType | tuple[type, ...] = NOTSET,
        decorators: list[str] | list[Decorator] | None = None,
        docstring: str | DocstringBuilder = ch.EMPTY_STRING,
        body: str = ch.EMPTY_STRING,
    ) -> None:
        """Initialize a FunctionBuilder.

        Args:
            name: Function name.
            args: Function arguments (without parentheses).
            returns: Optional return type annotation (NOTSET for no annotation, NoneType for -> None, or TypeHint object).
            decorators: Optional list of decorator strings (without @).
            docstring: Docstring content (string or DocstringBuilder object).
            indent: Base indentation level.
        """
        from codec_cub.pythons.helpers import get_decorators, get_returns  # noqa: PLC0415

        self.name: str = name
        self.args: str = render_args(args)
        self.returns: str = get_returns(returns, prefix=f" {ch.ARROW} ", suffix=ch.COLON)
        self._decorators: str = get_decorators(decorators) if decorators else ch.EMPTY_STRING

        docstring_str: str = docstring.render() if isinstance(docstring, DocstringBuilder) else docstring
        self._docstring: Docstring = Docstring(docstring_str)

        self._added_lines: BufferHelper = BufferHelper(indent=indent + 1)
        self._added_lines.write(body, suffix=ch.NEWLINE) if body else None
        self._body: BufferHelper = BufferHelper(indent=indent + 1)
        self._result: BufferHelper = BufferHelper()

    @property
    def signature(self) -> str:
        """Set or update the function signature.

        Returns:
            string representing the function signature.
        """
        return join("def ", self.name, paren(self.args), self.returns)

    def render(self) -> str:
        """Render the function to a string.

        Returns:
            The complete function definition as a string.
        """
        if self._decorators:
            self._result.write(self._decorators, suffix=ch.NEWLINE)

        has_body: bool = self._added_lines.not_empty
        has_docstring = bool(self._docstring)

        if not has_docstring and not has_body:
            # Ellipsis on same line as signature (e.g., for @overload)
            self._result.write(f"{self.signature} {ch.ELLIPSIS}", suffix=ch.NEWLINE)
        else:
            self._result.write(self.signature, suffix=ch.NEWLINE)
            if has_docstring:
                self._body.write(self._docstring.render(), suffix=ch.NEWLINE)
            self._result.write(self._body.getvalue())
            if has_body:
                self._result.write(self._added_lines.getvalue())
            else:
                self._body.write(ch.ELLIPSIS)
                self._result.write(self._body.getvalue())

        result: str = self._result.getvalue()
        self.clear()
        return result

    def clear(self) -> Self:
        """Clear the function body and docstring."""
        self.name = ch.EMPTY_STRING
        self.args = ch.EMPTY_STRING
        self.returns = ch.EMPTY_STRING
        self._decorators = ch.EMPTY_STRING
        self._docstring.clear()
        self._body.clear()
        self._result.clear()
        self._added_lines.clear()
        return self


class MethodBuilder(FunctionBuilder):
    """Builder for Python method definitions within classes."""

    def __init__(
        self,
        name: str,
        indent: int = 0,
        args: str | Arg | list[Arg] = ch.EMPTY_STRING,
        returns: str | type | TypeHint | NotSetType | tuple[type, ...] = NOTSET,
        decorators: list[str] | list[Decorator] | None = None,
        docstring: str | DocstringBuilder = ch.EMPTY_STRING,
        body: str = ch.EMPTY_STRING,
    ) -> None:
        """Initialize a MethodBuilder.

        Args:
            name: Method name.
            args: Method arguments (without parentheses).
            returns: Optional return type annotation (NOTSET for no annotation, NoneType for -> None, or TypeHint object).
            decorators: Optional list of decorator strings (without @).
            docstring: Docstring content (string or DocstringBuilder object).
            indent: Base indentation level.
        """
        self_arg = Arg("self")
        args = str(args).replace("self, ", "")
        args = join(self_arg, args, sep=", ") if args else self_arg
        super().__init__(name, indent, args, returns, decorators, docstring, body)


def generate_main_block(
    body: str | list[str | CodeBuilder],
    *,
    include_docstring: bool = False,
) -> str:
    """Generate if __name__ == "__main__": block using FunctionBuilder.

    Args:
        body: Body content - strings or CodeBuilder objects.
        include_docstring: Whether to add a docstring to main().

    Returns:
        Formatted main block string.
    """
    from codec_cub.pythons.code_section import CodeSection  # noqa: PLC0415

    main_func = FunctionBuilder(
        name="main",
        returns=NoneType,
        docstring="Run the main program." if include_docstring else ch.EMPTY_STRING,
    )

    if isinstance(body, str):
        main_func.add_line(body)
    else:
        for item in body:
            if isinstance(item, str):
                main_func.add_line(item)
            else:
                main_func.add_line(item.render())

    buffer = BufferHelper()
    buffer.write(main_func.render(), suffix=ch.NEWLINE)
    buffer.write(ch.NEWLINE)

    section = CodeSection()
    with section.if_block('__name__ == "__main__"'):
        section.add("main()")
    buffer.write(section.output())

    return buffer.getvalue()
