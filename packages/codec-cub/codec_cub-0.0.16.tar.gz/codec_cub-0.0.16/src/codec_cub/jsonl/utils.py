"""JSON Lines serialization utilities."""

from __future__ import annotations

from functools import singledispatch
import json
from typing import IO, Any

from codec_cub.general.file_lock import LockShared
from funcy_bear.ops.strings import to_lines


def filter_items(data: list[Any]) -> list[dict | str]:
    """Filter out invalid entries from the data.

    Args:
        data: A list of dictionaries or strings to be filtered.

    Returns:
        A list of valid dictionaries or strings.
    """
    return [ln for ln in data if (isinstance(ln, str) and ln.strip()) or isinstance(ln, dict)]


@singledispatch
def jsonl_serialize(data: Any) -> list[str]:
    """Serialize an object to a JSON Lines format.

    Args:
        data: The object to serialize.

    Returns:
        A list of json strings representing the serialized object.

    Raises:
        TypeError: If the object type is not supported for serialization.
    """
    raise TypeError(f"Object of type {type(data).__name__} is not JSON serializable")


@jsonl_serialize.register
def _(data: dict) -> list[str]:
    """Serialize a dictionary to JSON Lines format."""
    return [json.dumps(record, ensure_ascii=False) for record in data.values()]


@jsonl_serialize.register
def _(data: list) -> list[str]:
    """Serialize a list of dictionaries or strings to JSON Lines format."""
    return [json.dumps(record, ensure_ascii=False) for record in data]


@jsonl_serialize.register
def _(data: str) -> list[str]:
    """Serialize a string to JSON Lines format."""
    return to_lines(data)


def deserialize(handle: IO[Any], n: int = -1) -> list[Any]:
    """Read JSON Lines data from a file handle and deserialize it into a list of dictionaries.

    Args:
        handle: The file handle to read from.
        n: The maximum number of characters to read (default: -1, read all).

    Returns:
        A list of dictionaries read from the JSON Lines file.
    """
    data: list[Any] = []
    with LockShared(handle):
        handle.seek(0)
        raw: str = handle.read(n)
        if not raw.strip():
            return data
        for index_line in enumerate(to_lines(raw)):
            data.append(deserialize_line(*index_line))
        return data


def deserialize_line(i: int, line: str) -> dict[Any, Any]:
    """Deserialize a single line of JSONL data and append it to the data list.

    Args:
        i: The index of the line being processed (for error reporting).
        line: The line of JSONL data to deserialize.


    Raises:
        ValueError: If there is an error decoding the JSONL data.
        TypeError: If the decoded line is not a JSON object.
    """
    try:
        record: dict | Any = json.loads(line, strict=False)
        if not isinstance(record, dict):
            raise TypeError(f"Line {i + 1} is not a JSON object: {line}")
        return record
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSONL data on line {i + 1}: {e}") from e
