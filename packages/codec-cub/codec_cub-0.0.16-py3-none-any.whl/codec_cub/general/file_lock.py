"""Context manager for file locking using fcntl."""

from __future__ import annotations

import fcntl
from typing import IO, Any, Self, final

EXCLUSIVE_LOCK: int = fcntl.LOCK_EX
SHARED_LOCK: int = fcntl.LOCK_SH
UNLOCK: int = fcntl.LOCK_UN


def flock(handle: IO[Any], operation: int) -> None:
    """Apply a file lock operation on the given file handle."""
    fcntl.flock(handle.fileno(), operation)


def ex_lock(handle: IO[Any]) -> None:
    """Apply an exclusive lock on the given file handle."""
    flock(handle=handle, operation=EXCLUSIVE_LOCK)


def sh_lock(handle: IO[Any]) -> None:
    """Apply a shared lock on the given file handle."""
    flock(handle=handle, operation=SHARED_LOCK)


def unlock(handle: IO[Any]) -> None:
    """Unlock the given file handle."""
    flock(handle=handle, operation=UNLOCK)


class FileLock:
    """Context manager for file locking using fcntl."""

    def __init__(self, handle: IO[Any], exclusive: bool = True) -> None:
        """Initialize the file lock."""
        self.handle: IO[Any] = handle
        self.lock_type: int = EXCLUSIVE_LOCK if exclusive else SHARED_LOCK

    def lock(self) -> Self:
        """Lock the file."""
        flock(handle=self.handle, operation=self.lock_type)
        return self

    def unlock(self) -> None:
        """Unlock the file."""
        unlock(handle=self.handle)

    def __enter__(self) -> Self:
        return self.lock()

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.unlock()


@final
class LockExclusive(FileLock):
    """Context manager for exclusive file locking."""

    def __init__(self, handle: IO[Any]) -> None:
        """Initialize exclusive file lock."""
        super().__init__(handle=handle, exclusive=True)


@final
class LockShared(FileLock):
    """Context manager for shared file locking."""

    def __init__(self, handle: IO[Any]) -> None:
        """Initialize shared file lock."""
        super().__init__(handle=handle, exclusive=False)


__all__ = ["FileLock", "LockExclusive", "LockShared", "ex_lock", "sh_lock", "unlock"]
