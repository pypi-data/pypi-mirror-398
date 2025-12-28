"""Tests for ListLiteralBuilder and DictLiteralBuilder."""

from codec_cub.pythons.builders import DictLiteralBuilder, ListLiteralBuilder


def test_list_literal_empty() -> None:
    """Test empty list literal."""
    builder = ListLiteralBuilder()
    result = builder.render()
    assert result == "[]"


def test_list_literal_single_item() -> None:
    """Test list with single item."""
    builder = ListLiteralBuilder()
    result = builder.add("'a'").render()
    assert result == "['a']"


def test_list_literal_multiple_items() -> None:
    """Test list with multiple items."""
    builder = ListLiteralBuilder()
    result = builder.add("'a'").add("'b'").add("'c'").render()
    assert result == "['a', 'b', 'c']"


def test_list_literal_numbers() -> None:
    """Test list with numbers."""
    builder = ListLiteralBuilder()
    result = builder.add("1").add("2").add("3").render()
    assert result == "[1, 2, 3]"


def test_list_literal_multiline() -> None:
    """Test multiline list formatting."""
    builder = ListLiteralBuilder()
    result = builder.add("'a'").add("'b'").add("'c'").multiline().render()

    expected = """[
    'a',
    'b',
    'c',
]"""
    assert result == expected


def test_list_literal_multiline_empty() -> None:
    """Test empty list even with multiline enabled."""
    builder = ListLiteralBuilder()
    result = builder.multiline().render()
    assert result == "[]"


def test_list_literal_toggle_multiline() -> None:
    """Test toggling multiline formatting."""
    builder = ListLiteralBuilder()
    result: str = builder.add("'a'").multiline(enabled=True).multiline(enabled=False).render()
    assert result == "['a']"


def test_list_literal_with_indent() -> None:
    """Test list with base indentation."""
    builder = ListLiteralBuilder(indent=1)
    result = builder.add("'a'").add("'b'").multiline().render()

    expected = """    [
        'a',
        'b',
    ]"""
    assert result == expected


def test_list_literal_str_method() -> None:
    """Test __str__ method calls render."""
    builder = ListLiteralBuilder()
    builder.add("'a'").add("'b'")
    assert str(builder) == "['a', 'b']"


def test_list_literal_repr_method() -> None:
    """Test __repr__ method."""
    builder = ListLiteralBuilder()
    builder.add("'a'").add("'b'")
    result = repr(builder)
    assert "ListLiteralBuilder" in result
    assert "items=2" in result
    assert "multiline=False" in result


def test_list_literal_clear() -> None:
    """Test clearing list content."""
    builder = ListLiteralBuilder()
    builder.add("'a'").add("'b'").multiline()
    builder.clear()
    result = builder.render()
    assert result == "[]"


def test_dict_literal_empty() -> None:
    """Test empty dict literal."""
    builder = DictLiteralBuilder()
    result = builder.render()
    assert result == "{}"


def test_dict_literal_single_entry() -> None:
    """Test dict with single entry."""
    builder = DictLiteralBuilder()
    result = builder.entry("'host'", "'localhost'").render()
    assert result == "{'host': 'localhost'}"


def test_dict_literal_multiple_entries() -> None:
    """Test dict with multiple entries."""
    builder = DictLiteralBuilder()
    result = builder.entry("'host'", "'localhost'").entry("'port'", "8080").entry("'debug'", "True").render()
    assert result == "{'host': 'localhost', 'port': 8080, 'debug': True}"


def test_dict_literal_multiline() -> None:
    """Test multiline dict formatting."""
    builder = DictLiteralBuilder()
    result: str = builder.entry("'host'", "'localhost'").entry("'port'", "8080").multiline().render()

    expected = """{
    'host': 'localhost',
    'port': 8080,
}"""
    assert result == expected


def test_dict_literal_multiline_empty() -> None:
    """Test empty dict even with multiline enabled."""
    builder = DictLiteralBuilder()
    result: str = builder.multiline().render()
    assert result == "{}"


def test_dict_literal_toggle_multiline() -> None:
    """Test toggling multiline formatting."""
    builder = DictLiteralBuilder()
    result: str = builder.entry("'a'", "1").multiline(enabled=True).multiline(enabled=False).render()
    assert result == "{'a': 1}"


def test_dict_literal_with_indent() -> None:
    """Test dict with base indentation."""
    builder = DictLiteralBuilder(indent=1)
    result: str = builder.entry("'host'", "'localhost'").entry("'port'", "8080").multiline().render()

    expected = """    {
        'host': 'localhost',
        'port': 8080,
    }"""
    assert result == expected


def test_dict_literal_str_method() -> None:
    """Test __str__ method calls render."""
    builder = DictLiteralBuilder()
    builder.entry("'a'", "1").entry("'b'", "2")
    assert str(builder) == "{'a': 1, 'b': 2}"


def test_dict_literal_repr_method() -> None:
    """Test __repr__ method."""
    builder = DictLiteralBuilder()
    builder.entry("'a'", "1").entry("'b'", "2")
    result: str = repr(builder)
    assert "DictLiteralBuilder" in result
    assert "entries=2" in result
    assert "multiline=False" in result


def test_dict_literal_clear() -> None:
    """Test clearing dict content."""
    builder = DictLiteralBuilder()
    builder.entry("'a'", "1").entry("'b'", "2").multiline()
    builder.clear()
    result: str = builder.render()
    assert result == "{}"


def test_dict_literal_nested_values() -> None:
    """Test dict with nested list values."""
    builder = DictLiteralBuilder()
    list_builder = ListLiteralBuilder()
    list_value: str = list_builder.add("'a'").add("'b'").render()

    result: str = builder.entry("'items'", list_value).render()
    assert result == "{'items': ['a', 'b']}"


def test_list_literal_nested_dicts() -> None:
    """Test list with nested dict values."""
    builder = ListLiteralBuilder()
    dict_builder = DictLiteralBuilder()
    dict_value = dict_builder.entry("'name'", "'Alice'").render()

    result = builder.add(dict_value).render()
    assert result == "[{'name': 'Alice'}]"


def test_complex_nested_structure() -> None:
    """Test complex nested dict and list structure."""
    # Create a nested structure: {users: [{'name': 'Alice'}, {'name': 'Bob'}]}
    dict1: str = DictLiteralBuilder().entry("'name'", "'Alice'").render()
    dict2: str = DictLiteralBuilder().entry("'name'", "'Bob'").render()
    users_list: str = ListLiteralBuilder().add(dict1).add(dict2).render()
    result: str = DictLiteralBuilder().entry("'users'", users_list).render()

    assert result == "{'users': [{'name': 'Alice'}, {'name': 'Bob'}]}"


def test_multiline_nested_structure() -> None:
    """Test multiline nested structure."""
    dict_builder = DictLiteralBuilder(indent=1)
    list_builder = ListLiteralBuilder(indent=1)

    list_value: str = list_builder.add("'a'").add("'b'").multiline().render()
    result: str = dict_builder.entry("'items'", list_value).multiline().render()

    # Both the dict and the list are indented at level 1
    expected = """    {
        'items':     [
        'a',
        'b',
    ],
    }"""
    assert result == expected
