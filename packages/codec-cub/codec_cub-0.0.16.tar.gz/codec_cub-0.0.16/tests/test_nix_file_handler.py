"""Tests for NixFileHandler."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003
from typing import Any, Self

import pytest

from codec_cub.nix.file_handler import NixData, NixFileHandler


class TestNixFileHandler:
    """Test suite for NixFileHandler."""

    def test_write_read_round_trip(self, tmp_path: Path) -> None:
        """Test writing and reading a nested structure."""
        file_path: Path = tmp_path / "sample.nix"
        handler = NixFileHandler(file_path, touch=True)

        data: dict[str, Any] = {"name": "codec-cub", "versions": [1, 2, 3], "active": True}
        handler.write(data)

        assert handler.read() == data

        handler.close()

    def test_read_empty_file_raises(self, tmp_path: Path) -> None:
        """Test reading an empty Nix file raises ValueError."""
        file_path: Path = tmp_path / "empty.nix"
        file_path.touch()

        handler = NixFileHandler(file_path)

        assert handler.read() is None

        handler.close()

    def test_touch_creates_file_on_first_access(self, tmp_path: Path) -> None:
        """Test touch option creates file before reading."""
        file_path: Path = tmp_path / "created.nix"
        handler = NixFileHandler(file_path, touch=True)
        assert handler.read() is None
        assert file_path.exists()
        handler.close()

    def test_write_uses_codec_and_exclusive_lock(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test write uses NixCodec.encode and exclusive lock."""
        file_path: Path = tmp_path / "exclusive.nix"
        events: list[str] = []

        class DummyLock:
            def __init__(self, handle: Any) -> None:  # noqa: ARG002
                events.append("init")

            def __enter__(self) -> Self:
                events.append("enter")
                return self

            def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
                events.append("exit")

        class DummyCodec:
            def __init__(self) -> None:
                self.calls: list[Any] = []

            def encode(self, data: Any) -> str:
                self.calls.append(data)
                return "encoded-nix"

        handler = NixFileHandler(file_path, touch=True, codec=DummyCodec())  # pyright: ignore[reportArgumentType]
        monkeypatch.setattr("codec_cub.nix.file_handler.LockExclusive", DummyLock)

        handler.write({"answer": 42})

        assert file_path.read_text() == "encoded-nix"
        assert handler._codec.calls == [{"answer": 42}]  # pyright: ignore[reportAttributeAccessIssue]
        assert events == ["init", "enter", "exit"]

        handler.close()

    def test_read_uses_codec_and_shared_lock(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test read uses NixCodec.decode and shared lock."""
        file_path: Path = tmp_path / "shared.nix"
        file_path.write_text("raw-nix")

        events: list[str] = []

        class DummyLock:
            def __init__(self, handle: Any) -> None:  # noqa: ARG002
                events.append("init")

            def __enter__(self) -> Self:
                events.append("enter")
                return self

            def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
                events.append("exit")

        class DummyCodec:
            def __init__(self) -> None:
                self.calls: list[str] = []

            def decode(self, text: str) -> dict[str, str]:
                self.calls.append(text)
                return {"decoded": "ok"}

        handler = NixFileHandler(file_path, codec=DummyCodec())  # pyright: ignore[reportArgumentType]
        monkeypatch.setattr("codec_cub.nix.file_handler.LockShared", DummyLock)
        dummy_codec: DummyCodec = handler._codec  # pyright: ignore[reportAssignmentType, reportAttributeAccessIssue]

        result: NixData = handler.read()

        assert result == {"decoded": "ok"}
        assert dummy_codec.calls == ["raw-nix"]
        assert events == ["init", "enter", "exit"]

        handler.close()

    def test_read_raises_when_handle_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test read raises ValueError when handle is unavailable."""
        handler = NixFileHandler(tmp_path / "missing.nix", touch=True)
        monkeypatch.setattr(handler, "handle", lambda *_, **__: None)

        with pytest.raises(ValueError, match="File handle is not available"):
            handler.read()
