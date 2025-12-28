"""Type annotation builder for generating Python type hints."""

from __future__ import annotations

from typing import Self

from codec_cub.common import comma_sep, piped
from funcy_bear.constants.py_chars import LITERAL_STR as LIT
from funcy_bear.ops.strings import manipulation as man


class TypeHint:
    """Builder for Python type annotations with support for generics, unions, and literals.

    Examples:
        >>> TypeHint("int").render()
        'int'
        >>> TypeHint.literal("foo", "bar").render()
        'Literal["foo", "bar"]'
        >>> TypeHint.type_of("Storage").render()
        'type[Storage]'
        >>> TypeHint.dict_of("str", "int").render()
        'dict[str, int]'
        >>> TypeHint.optional("str").render()
        'str | None'
    """

    def __init__(self, type_name: str = "", final: bool = False) -> None:
        """Initialize a simple type annotation.

        Args:
            type_name: The name of the type (e.g., "int", "str", "MyClass").
        """
        self._annotation: str = type_name
        self._final: bool = final

    @classmethod
    def literal(cls, *values: str | int | bool, final: bool = False) -> Self:
        """Create a Literal type annotation.

        Args:
            *values: The literal values. Strings will be quoted.
            final: Whether to mark the Literal as Final.

        Returns:
            TypeHint for a Literal type.

        Examples:
            >>> TypeHint.literal("foo", "bar").render()
            'Literal["foo", "bar"]'
            >>> TypeHint.literal(1, 2, 3).render()
            'Literal[1, 2, 3]'
        """
        formatted_values: list[str] = []
        for value in values:
            if isinstance(value, str):
                formatted_values.append(man.quoted(value))
            else:
                formatted_values.append(str(value))
        values_str: str = comma_sep(formatted_values)
        return cls(f"{LIT}{man.bracketed(values_str)}", final=final)

    @classmethod
    def type_of(cls, type_name: str, final: bool = False) -> Self:
        """Create a type[T] annotation.

        Args:
            type_name: The type name (e.g., "Storage", "BaseModel").
            final: Whether to mark the type as Final.

        Returns:
            TypeHint for a type[T].

        Examples:
            >>> TypeHint.type_of("Storage").render()
            'type[Storage]'
        """
        return cls(f"type{man.bracketed(type_name)}", final=final)

    @classmethod
    def dict_of(cls, key_type: str | TypeHint, value_type: str | TypeHint, final: bool = False) -> Self:
        """Create a dict[K, V] annotation.

        Args:
            key_type: The key type.
            value_type: The value type.
            final: Whether to mark the dict as Final.

        Returns:
            TypeHint for a dict[K, V].

        Examples:
            >>> TypeHint.dict_of("str", "int").render()
            'dict[str, int]'
        """
        key_str: str = key_type.render() if isinstance(key_type, TypeHint) else key_type
        value_str: str = value_type.render() if isinstance(value_type, TypeHint) else value_type
        return cls(f"dict{man.bracketed(f'{key_str}, {value_str}')}", final=final)

    @classmethod
    def list_of(cls, item_type: str | TypeHint, final: bool = False) -> Self:
        """Create a list[T] annotation.

        Args:
            item_type: The item type.
            final: Whether to mark the list as Final.

        Returns:
            TypeHint for a list[T].

        Examples:
            >>> TypeHint.list_of("str").render()
            'list[str]'
        """
        item_str: str = item_type.render() if isinstance(item_type, TypeHint) else item_type
        return cls(f"list{man.bracketed(item_str)}", final=final)

    @classmethod
    def set_of(cls, item_type: str | TypeHint, final: bool = False) -> Self:
        """Create a set[T] annotation.

        Args:
            item_type: The item type.
            final: Whether to mark the set as Final.

        Returns:
            TypeHint for a set[T].

        Examples:
            >>> TypeHint.set_of("int").render()
            'set[int]'
        """
        item_str: str = item_type.render() if isinstance(item_type, TypeHint) else item_type
        return cls(f"set{man.bracketed(item_str)}", final=final)

    @classmethod
    def tuple_of(cls, *types: str | TypeHint, final: bool = False) -> Self:
        """Create a tuple[T1, T2, ...] annotation.

        Args:
            *types: The element types.
            final: Whether to mark the tuple as Final.

        Returns:
            TypeHint for a tuple.

        Examples:
            >>> TypeHint.tuple_of("str", "int", "bool").render()
            'tuple[str, int, bool]'
        """
        types_str: str = comma_sep([t.render() if isinstance(t, TypeHint) else t for t in types])
        return cls(f"tuple{man.bracketed(types_str)}", final=final)

    @classmethod
    def optional(cls, type_name: str | TypeHint, final: bool = False) -> Self:
        """Create a T | None annotation.

        Args:
            type_name: The type that can be None.
            final: Whether to mark the optional as Final.

        Returns:
            TypeHint for T | None.

        Examples:
            >>> TypeHint.optional("str").render()
            'str | None'
        """
        type_str: str = type_name if isinstance(type_name, str) else type_name.render()
        return cls(f"{type_str} | None", final=final)

    @classmethod
    def union(cls, *types: str | TypeHint, final: bool = False) -> Self:
        """Create a T1 | T2 | ... union annotation.

        Args:
            *types: The types in the union.
            final: Whether to mark the union as Final.

        Returns:
            TypeHint for a union type.

        Examples:
            >>> TypeHint.union("str", "int", "bool").render()
            'str | int | bool'
        """
        union_str: str = piped(*[t.render() if isinstance(t, TypeHint) else t for t in types])
        return cls(union_str, final=final)

    @classmethod
    def generic(cls, base: str, *type_params: str | TypeHint, final: bool = False) -> Self:
        """Create a generic type annotation like Generic[T1, T2].

        Args:
            base: The base type name (e.g., "Callable", "Iterator").
            *type_params: The type parameters.
            final: Whether to mark the generic as Final.

        Returns:
            TypeHint for a generic type.

        Examples:
            >>> TypeHint.generic("Callable", "int", "str").render()
            'Callable[int, str]'
            >>> TypeHint.generic("Iterator", "str").render()
            'Iterator[str]'
        """
        params_str: str = comma_sep([p.render() if isinstance(p, TypeHint) else p for p in type_params])
        return cls(f"{base}{man.bracketed(params_str)}", final=final)

    def render(self) -> str:
        """Render the type annotation to a string.

        Returns:
            The type annotation as a string.
        """
        if self._final:
            return f"Final{man.bracketed(self._annotation)}"
        return self._annotation

    def __str__(self) -> str:
        """String representation (calls render)."""
        return self.render()

    def __repr__(self) -> str:
        """Repr representation."""
        return f"TypeHint({self._annotation!r}, final={self._final})"


def literal(*values: str | int | bool, final: bool = False) -> TypeHint:
    """Create a Literal type annotation.

    Args:
        *values: The literal values. Strings will be quoted.
        final: Whether to mark the Literal as Final.

    Returns:
        TypeHint for a Literal type.
    """
    return TypeHint.literal(*values, final=final)


def union(*types: str | TypeHint) -> TypeHint:
    """Create a T1 | T2 | ... union annotation.

    Args:
        *types: The types in the union.

    Returns:
        TypeHint for a union type.
    """
    return TypeHint.union(*types)


def optional(type_name: str | TypeHint) -> TypeHint:
    """Create a T | None annotation.

    Args:
        type_name: The type that can be None.

    Returns:
        TypeHint for T | None.
    """
    return TypeHint.optional(type_name)


def generic(base: str, *type_params: str | TypeHint) -> TypeHint:
    """Create a generic type annotation like Generic[T1, T2].

    Args:
        base: The base type name (e.g., "Callable", "Iterator").
        *type_params: The type parameters.

    Returns:
        TypeHint for a generic type.
    """
    return TypeHint.generic(base, *type_params)


def dict_of(key_type: str | TypeHint, value_type: str | TypeHint) -> TypeHint:
    """Create a dict[K, V] annotation.

    Args:
        key_type: The key type.
        value_type: The value type.

    Returns:
        TypeHint for a dict[K, V].
    """
    return TypeHint.dict_of(key_type, value_type)


def list_of(item_type: str | TypeHint) -> TypeHint:
    """Create a list[T] annotation.

    Args:
        item_type: The item type.

    Returns:
        TypeHint for a list[T].
    """
    return TypeHint.list_of(item_type)


def set_of(item_type: str | TypeHint) -> TypeHint:
    """Create a set[T] annotation.

    Args:
        item_type: The item type.

    Returns:
        TypeHint for a set[T].
    """
    return TypeHint.set_of(item_type)


def tuple_of(*types: str | TypeHint) -> TypeHint:
    """Create a tuple[T1, T2, ...] annotation.

    Args:
        *types: The element types.

    Returns:
        TypeHint for a tuple.
    """
    return TypeHint.tuple_of(*types)


def type_of(type_name: str) -> TypeHint:
    """Create a type[T] annotation.

    Args:
        type_name: The type name (e.g., "Storage", "BaseModel").

    Returns:
        TypeHint for a type[T].
    """
    return TypeHint.type_of(type_name)
