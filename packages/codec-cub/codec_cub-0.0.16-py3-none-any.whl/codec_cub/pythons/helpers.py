"""Functions for File Builder operations related to strings and common patterns."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

from codec_cub.common import COMMA_SPACE
from codec_cub.pythons import common as co
from funcy_bear.constants import characters as ch, py_chars as py
from funcy_bear.ops.strings import manipulation as man
from funcy_bear.sentinels import NotSetType
from funcy_bear.tools import Dispatcher
from funcy_bear.type_stuffs.builtin_tools import type_name
from funcy_bear.typing_stuffs import is_instance_of, is_str, is_tuple

from .parts import Arg, Decorator
from .type_annotation import TypeHint

ret = Dispatcher("ret")


def generate_all_export(exports: list[str], line_length: int = 88, force_multiline: bool = False) -> str:
    """Generate __all__ export statement with proper formatting.

    Args:
        exports: List of names to include in __all__.
        line_length: Maximum line length for formatting.
        force_multiline: Whether to force multiline formatting.

    Returns:
        Formatted __all__ export string.
    """
    all_part = "__all__"
    equal: str = ch.SPACE + ch.EQUALS + ch.SPACE
    if not exports:
        return f"{all_part} {equal} []"

    single_line: str = f"{all_part} {equal} {man.bracketed(COMMA_SPACE.join(man.quoted(name) for name in exports))}"
    if len(single_line) <= line_length and not force_multiline:
        return single_line
    lines: list[str] = [f"{all_part} = [{ch.NEWLINE}"]
    for name in exports:
        lines.append(f"{ch.INDENT}{man.quoted(name)},{ch.NEWLINE}")
    lines.append(ch.RIGHT_BRACKET)
    return man.join(*lines)


@ret.register(partial(is_instance_of, types=NotSetType))
def _not_set(ret: Any, prefix: str = ch.EMPTY_STRING, suffix: str = ch.EMPTY_STRING) -> str:
    return suffix


@ret.register(partial(is_instance_of, types=TypeHint))
def _type_annotation(ret: TypeHint, prefix: str = ch.EMPTY_STRING, suffix: str = ch.EMPTY_STRING) -> str:
    return man.join(prefix, ret.render(), suffix)


@ret.register(is_str)
def _string_return(ret: str, prefix: str = ch.EMPTY_STRING, suffix: str = ch.EMPTY_STRING) -> str:
    return man.join(prefix, ret, suffix)


@ret.register(partial(is_instance_of, types=type))
def _typed_return(ret: type, prefix: str = ch.EMPTY_STRING, suffix: str = ch.EMPTY_STRING) -> str:
    return man.join(prefix, type_name(ret), suffix)


@ret.register(is_tuple)
def _tuple_return(ret: tuple[type, ...], prefix: str = ch.EMPTY_STRING, suffix: str = ch.EMPTY_STRING) -> str:
    return man.join(prefix, man.piped(co.to_type_names(ret)), suffix)


@ret.dispatcher()
def get_returns(ret: Any, prefix: str = ch.EMPTY_STRING, suffix: str = ch.EMPTY_STRING) -> str:
    """Set or update the return type annotation.

    Args:
        ret: The return type annotation as a string, type, or TypeHint.
        prefix: Optional prefix to add before the return type.
        suffix: Optional suffix to add after the return type.

    Returns:
        string representing the return type annotation (includes suffix even if NOTSET).
    """
    raise TypeError(f"Unsupported return type: {ret!r}")


def get_docstring(docstring: str) -> str:
    """Wrap the given docstring content in triple quotes.

    Args:
        docstring: The docstring content (without triple quotes).

    Returns:
        String representing the docstring with triple quotes.
    """
    return f"{ch.TRIPLE_QUOTE}{docstring}{ch.TRIPLE_QUOTE}"


def render_args(args: str | Arg | list[Arg]) -> str:
    """Render function arguments to a string.

    Args:
        args: Function arguments (string, Arg, or list of Args).

    Returns:
        The rendered arguments as a string.
    """
    return (
        args.render()
        if isinstance(args, Arg)
        else ", ".join(arg.render() for arg in args)
        if isinstance(args, list)
        else args
    )


def get_decorators(decorators: list[str] | list[Decorator]) -> str:
    """Render function decorators to a string.

    Args:
        decorators: Function decorators (list of strings or Decorators).

    Returns:
        The rendered decorators as a string.
    """
    return "\n".join(decorator.render() if isinstance(decorator, Decorator) else decorator for decorator in decorators)


def get_literal_type(values: Sequence[str], *, quote_values: bool = True) -> str:
    """Generate a Literal type annotation with proper formatting.

    Args:
        values: List of literal values.
        quote_values: Whether to add quotes around values (default True).

    Returns:
        Formatted Literal type string (e.g., 'Literal["a", "b", "c"]').
    """
    if not values:
        return py.LITERAL_STR + man.bracketed(ch.EMPTY_STRING)
    formatted_values: list[str] = [man.quoted(value) if quote_values else value for value in values]
    return py.LITERAL_STR + man.bracketed(COMMA_SPACE.join(formatted_values))


def get_type_alias(name: str, type_expr: str) -> str:
    """Generate a PEP 613 type alias statement (Python 3.12+ syntax).

    Args:
        name: The name of the type alias.
        type_expr: The type expression (e.g., 'Literal["a", "b"]' or 'dict[str, int]').

    Returns:
        Formatted type alias string (e.g., 'type StorageChoices = Literal["a", "b"]').
    """
    return f"type {name} = {type_expr}"


# ruff: noqa: ARG001
