from __future__ import annotations

import json
from typing import IO, TYPE_CHECKING, Any, Self

from codec_cub.general.base_file_handler import BaseFileHandler

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


class TextFileHandler(BaseFileHandler[str]):
    """A simple text file handler for testing."""

    def read(self, **_) -> str:
        """Read the entire content of the text file."""
        handle: IO[Any] | None = self.handle()
        assert handle is not None
        handle.seek(0)
        return handle.read()

    def write(self, data: str, **_) -> None:
        """Write the entire content to the text file, replacing existing content."""
        handle: IO[Any] | None = self.handle()
        assert handle is not None
        handle.seek(0)
        handle.truncate(0)
        handle.write(data)
        handle.flush()


class JsonFileHandler(BaseFileHandler[dict[str, Any]]):
    """A JSON-based handler to exercise Pydantic conversion helpers."""

    def read(self, **_) -> dict[str, Any]:
        """Read and parse the entire content of the JSON file."""
        handle = self.handle()
        assert handle is not None
        handle.seek(0)
        content = handle.read()
        return json.loads(content) if content else {}

    def write(self, data: dict[str, Any], **_) -> None:
        """Write the entire content to the JSON file, replacing existing content."""
        handle = self.handle()
        assert handle is not None
        handle.seek(0)
        handle.truncate(0)
        handle.write(json.dumps(data))
        handle.flush()


def test_base_file_handler_read_write(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    handler = TextFileHandler(file_path, mode="w+")

    handler.write("hello")
    assert handler.read() == "hello"

    handler.close()
    assert handler.closed


def test_base_file_handler_clear_uses_lock(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    events: list[str] = []

    class DummyLock:
        def __init__(self, handle, exclusive=True) -> None:  # noqa: ARG002
            """A dummy file lock that records events."""
            events.append(f"init:{exclusive}")

        def __enter__(self) -> Self:
            """Enter the context, recording the event."""
            events.append("enter")
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            events.append("exit")

    monkeypatch.setattr("codec_cub.general.base_file_handler.FileLock", DummyLock)

    handler = TextFileHandler(tmp_path / "clear.txt", mode="w+")
    handler.write("data")
    handler.clear()

    assert events == ["init:True", "enter", "exit"]
    assert handler.read() == ""


def test_base_file_handler_seek_truncate_and_tell(tmp_path: Path) -> None:
    handler = TextFileHandler(tmp_path / "position.txt", mode="w+")
    handler.write("abcdef")

    handler.seek(3)
    assert handler.tell() == 3

    handler.truncate(4)
    handler.seek(0)
    assert handler.read() == "abcd"


def test_base_file_handler_context_manager(tmp_path: Path) -> None:
    handler = TextFileHandler(tmp_path / "context.txt", mode="w+")
    with handler as h:
        assert h is handler
        handler.write("ctx")

    assert handler.closed
