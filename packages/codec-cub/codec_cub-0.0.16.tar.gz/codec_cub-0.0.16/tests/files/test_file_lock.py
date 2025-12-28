from __future__ import annotations

from typing import IO

import pytest

from codec_cub.general.file_lock import EXCLUSIVE_LOCK, SHARED_LOCK, UNLOCK, FileLock, LockExclusive, LockShared


class DummyHandle(IO):
    def __init__(self) -> None:
        """A dummy file-like object with a fileno method."""
        self._fileno = 69

    def fileno(self) -> int:
        """Return a dummy file descriptor."""
        return self._fileno


def test_file_lock_acquire_and_release(monkeypatch: pytest.MonkeyPatch) -> None:
    handle = DummyHandle()
    calls: list[int] = []

    def fake_flock(fd: int, operation: int) -> None:
        calls.append(operation)

    monkeypatch.setattr("codec_cub.general.file_lock.fcntl.flock", fake_flock)

    with FileLock(handle, exclusive=True):
        assert calls[-1] == EXCLUSIVE_LOCK

    assert calls[-1] == UNLOCK


def test_lock_exclusive_and_shared_modes(monkeypatch: pytest.MonkeyPatch) -> None:
    handle = DummyHandle()
    calls: list[int] = []

    def fake_flock(fd: int, operation: int) -> None:
        calls.append(operation)

    monkeypatch.setattr("codec_cub.general.file_lock.fcntl.flock", fake_flock)

    with LockExclusive(handle):
        assert calls[-1] == EXCLUSIVE_LOCK

    with LockShared(handle):
        assert calls[-1] == SHARED_LOCK


def test_file_lock_releases_on_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    handle = DummyHandle()
    calls: list[int] = []

    def fake_flock(fd: int, operation: int) -> None:
        calls.append(operation)

    monkeypatch.setattr("codec_cub.general.file_lock.fcntl.flock", fake_flock)

    with pytest.raises(RuntimeError), FileLock(handle):
        raise RuntimeError("boom")

    assert calls[-1] == UNLOCK
