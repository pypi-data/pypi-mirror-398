"""Tests for TypeHint integration with FunctionBuilder and Arg."""

from __future__ import annotations

from codec_cub.pythons import Arg, FunctionBuilder
from codec_cub.pythons.type_annotation import TypeHint


def test_function_with_type_annotation_return() -> None:
    """Test FunctionBuilder with TypeHint for return type."""
    func = FunctionBuilder(
        name="get_storage",
        args="storage: str",
        returns=TypeHint.type_of("Storage"),
        body="return Storage()",
    )

    result = func.render()

    assert "def get_storage(storage: str) -> type[Storage]:" in result
    assert "return Storage()" in result


def test_function_with_literal_return() -> None:
    """Test FunctionBuilder with Literal type annotation."""
    func = FunctionBuilder(
        name="get_mode",
        returns=TypeHint.literal("read", "write", "execute"),
        body='return "read"',
    )

    result = func.render()

    assert 'def get_mode() -> Literal["read", "write", "execute"]:' in result


def test_function_with_optional_return() -> None:
    """Test FunctionBuilder with optional return type."""
    func = FunctionBuilder(
        name="find_user",
        args="user_id: int",
        returns=TypeHint.optional("User"),
        body="return None",
    )

    result = func.render()

    assert "def find_user(user_id: int) -> User | None:" in result


def test_function_with_dict_return() -> None:
    """Test FunctionBuilder with dict return type."""
    func = FunctionBuilder(
        name="get_config",
        returns=TypeHint.dict_of("str", "int"),
        body="return {}",
    )

    result = func.render()

    assert "def get_config() -> dict[str, int]:" in result


def test_function_with_complex_nested_return() -> None:
    """Test FunctionBuilder with complex nested return type."""
    # dict[str, list[tuple[int, str]]]
    tuple_type = TypeHint.tuple_of("int", "str")
    list_type = TypeHint.list_of(tuple_type)
    dict_type = TypeHint.dict_of("str", list_type)

    func = FunctionBuilder(
        name="get_complex_data",
        returns=dict_type,
        body="return {}",
    )

    result = func.render()

    assert "def get_complex_data() -> dict[str, list[tuple[int, str]]]:" in result


def test_arg_with_type_annotation() -> None:
    """Test Arg with TypeHint."""
    arg = Arg(
        name="storage",
        annotations=TypeHint.literal("json", "yaml", "toml"),
    )

    result = arg.render()

    assert result == 'storage: Literal["json", "yaml", "toml"]'


def test_arg_with_type_annotation_and_default() -> None:
    """Test Arg with TypeHint and default value."""
    arg = Arg(
        name="mode",
        annotations=TypeHint.optional("str"),
        default="None",
    )

    result = arg.render()

    assert result == "mode: str | None = None"


def test_arg_with_dict_type_annotation() -> None:
    """Test Arg with dict TypeHint."""
    arg = Arg(
        name="config",
        annotations=TypeHint.dict_of("str", "int"),
        default="{}",
    )

    result = arg.render()

    assert result == "config: dict[str, int] = {}"


def test_function_with_typed_args_list() -> None:
    """Test FunctionBuilder with list of typed Args."""
    args = [
        Arg(name="name", annotations="str"),
        Arg(name="age", annotations=TypeHint.optional("int"), default="None"),
        Arg(name="tags", annotations=TypeHint.list_of("str"), default="[]"),
    ]

    func = FunctionBuilder(
        name="create_user",
        args=args,
        returns=TypeHint("User"),
        body="return User(name, age, tags)",
    )

    result = func.render()

    assert "def create_user(name: str, age: int | None = None, tags: list[str] = []) -> User:" in result


def test_function_with_union_return() -> None:
    """Test FunctionBuilder with union return type."""
    func = FunctionBuilder(
        name="parse_value",
        args="data: str",
        returns=TypeHint.union("int", "float", "str"),
        body="return data",
    )

    result = func.render()

    assert "def parse_value(data: str) -> int | float | str:" in result


def test_function_with_generic_return() -> None:
    """Test FunctionBuilder with generic return type."""
    func = FunctionBuilder(
        name="get_iterator",
        returns=TypeHint.generic("Iterator", "str"),
        body="...",
    )

    result = func.render()

    assert "def get_iterator() -> Iterator[str]:" in result
