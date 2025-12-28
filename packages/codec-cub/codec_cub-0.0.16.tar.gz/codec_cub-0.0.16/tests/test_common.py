import pytest

from funcy_bear.ops.strings.escaping import escape_string, return_escaped, return_unescaped, unescape_string
from funcy_bear.ops.strings.manipulation import extract, first_item


def test_escape_string_multiple_escape_types() -> None:
    input_str = 'Line1\nLine2\t"Quote"\rBackslash\\'
    expected = '"Line1\\nLine2\\t\\"Quote\\"\\rBackslash\\\\"'
    assert escape_string(input_str) == expected


def test_escape_string_without_special_characters() -> None:
    assert escape_string("simple") == '"simple"'


@pytest.mark.parametrize("bad_sequence", ["x", "u"])
def test_unescape_string_invalid_escape_sequences(bad_sequence: str) -> None:
    with pytest.raises(ValueError, match=rf"Invalid escape sequence: \\{bad_sequence}"):
        unescape_string(f"bad\\{bad_sequence}escape")


def test_unescape_string_mixed_sequences() -> None:
    raw = r"Line1\nLine2\t\\Path\\"
    assert unescape_string(raw) == "Line1\nLine2\t\\Path\\"


def test_return_unescaped_invalid_sequence() -> None:
    with pytest.raises(ValueError, match=r"Invalid escape sequence: \\z"):
        return_unescaped("z")


@pytest.mark.parametrize(
    ("escaped", "result"),
    [
        ("\\", "\\"),
        ('"', '"'),
        ("n", "\n"),
        ("r", "\r"),
        ("t", "\t"),
    ],
)
def test_return_unescaped_valid_sequences(escaped: str, result: str) -> None:
    assert return_unescaped(escaped) == result


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("\\", "\\\\"),
        ('"', '\\"'),
        ("\n", "\\n"),
        ("\r", "\\r"),
        ("\t", "\\t"),
        ("x", "x"),
    ],
)
def test_return_escaped_variants(value: str, expected: str) -> None:
    assert return_escaped(value) == expected


def test_first_token_empty_iterable() -> None:
    with pytest.raises(ValueError, match="Invalid index"):
        first_item([])


def test_first_item_nested_structure() -> None:
    nested = [[1, 2], {"key": "value"}]
    assert first_item(nested) is nested[0]


def test_first_item_tuple() -> None:
    assert first_item((1, 2, 3)) == 1


@pytest.mark.parametrize("value", ["", "a"])
def test_extract_short_strings(value: str) -> None:
    assert extract(value) == ""


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ('"a"', "a"),
        ("[]", ""),
        ("{foo}", "foo"),
    ],
)
def test_extract_regular_strings(value: str, expected: str) -> None:
    assert extract(value) == expected
