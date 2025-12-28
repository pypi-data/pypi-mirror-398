"""Tests for DocstringBuilder integration with FunctionBuilder."""

from __future__ import annotations

from codec_cub.pythons import DocstringBuilder, FunctionBuilder


def test_function_with_docstring_builder() -> None:
    """Test FunctionBuilder with DocstringBuilder."""
    doc = (
        DocstringBuilder()
        .summary("Get storage backend by name.")
        .arg("storage", "Backend name")
        .returns("Storage class")
    )

    func = FunctionBuilder(
        name="get_storage",
        args="storage: str",
        returns="type[Storage]",
        docstring=doc,
        body="return Storage()",
    )

    result = func.render()

    assert "def get_storage(storage: str) -> type[Storage]:" in result
    assert "Get storage backend by name." in result
    assert "Args:" in result
    assert "storage: Backend name" in result
    assert "Returns:" in result
    assert "Storage class" in result


def test_function_with_complete_docstring() -> None:
    """Test FunctionBuilder with complete DocstringBuilder."""
    doc = (
        DocstringBuilder()
        .summary("Process user data.")
        .description("This function validates and processes user information.")
        .arg("name", "User's full name")
        .arg("age", "User's age")
        .returns("Processed user object")
        .raises("ValueError", "If age is negative")
        .example(">>> process_user('Alice', 30)\nUser(name='Alice', age=30)")
    )

    func = FunctionBuilder(
        name="process_user",
        args="name: str, age: int",
        returns="User",
        docstring=doc,
        body="if age < 0:\n        raise ValueError('Age cannot be negative')\n    return User(name, age)",
    )

    result = func.render()

    assert "def process_user(name: str, age: int) -> User:" in result
    assert "Process user data." in result
    assert "This function validates and processes user information." in result
    assert "Args:" in result
    assert "name: User's full name" in result
    assert "age: User's age" in result
    assert "Returns:" in result
    assert "Processed user object" in result
    assert "Raises:" in result
    assert "ValueError: If age is negative" in result
    assert "Examples:" in result
    assert ">>> process_user('Alice', 30)" in result


def test_function_with_empty_docstring_builder() -> None:
    """Test FunctionBuilder with empty DocstringBuilder."""
    doc = DocstringBuilder()

    func = FunctionBuilder(
        name="foo",
        docstring=doc,
        body="pass",
    )

    result = func.render()

    assert "def foo():" in result
    assert '"""' not in result


def test_function_with_string_docstring_still_works() -> None:
    """Test that FunctionBuilder still accepts string docstrings."""
    func = FunctionBuilder(
        name="get_name",
        docstring="Get the user's name.",
        body="return 'Alice'",
    )

    result: str = func.render()

    assert "def get_name():" in result
    assert "Get the user's name." in result


def test_function_with_yields_docstring() -> None:
    """Test FunctionBuilder with yields section."""
    doc: DocstringBuilder = (
        DocstringBuilder().summary("Generate numbers.").arg("n", "Upper limit").yields("Next number in sequence")
    )

    func = FunctionBuilder(
        name="count",
        args="n: int",
        returns="Iterator[int]",
        docstring=doc,
        body="for i in range(n):\n        yield i",
    )

    result = func.render()

    assert "def count(n: int) -> Iterator[int]:" in result
    assert "Generate numbers." in result
    assert "Yields:" in result
    assert "Next number in sequence" in result
