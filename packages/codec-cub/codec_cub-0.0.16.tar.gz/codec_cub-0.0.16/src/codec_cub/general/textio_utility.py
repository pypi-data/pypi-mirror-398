"""This module provides textio-like classes for various purposes, including a mock TextIO for testing."""

from collections.abc import Callable, Iterable, Iterator
import sys
from typing import IO, Self, TextIO

from singleton_base import SingletonWrap


class NullFile(TextIO, IO[str]):
    """A null file that discards all writes, implementing the singleton pattern.

    It does this to ensure there is only one instance of NullFile throughout the application since
    there is no need for multiple instances of a null file.
    """

    def flush(self) -> None: ...
    def writelines(self, __lines: Iterable[str]) -> None: ...
    def close(self) -> None: ...
    def isatty(self) -> bool:
        return False

    def closed(self) -> bool:  # type: ignore[override]
        return True

    def read(self, __n: int = 1) -> str:
        return ""

    def readable(self) -> bool:
        return False

    def seekable(self) -> bool:
        return False

    def writable(self) -> bool:
        return False

    def readline(self, __limit: int = 1) -> str:
        return ""

    def readlines(self, __hint: int = 1) -> list[str]:
        return []

    def seek(self, __offset: int, __whence: int = 1) -> int:
        return 0

    def tell(self) -> int:
        return 0

    def truncate(self, __size: int | None = 1) -> int:
        return 0

    def __next__(self) -> str:
        return ""

    def __iter__(self) -> Iterator[str]:
        return iter([""])

    def __enter__(self) -> Self:
        return self

    def __bool__(self) -> bool:
        return False

    def __exit__(self, _: object, __: object, ___: object) -> None:
        """Nothing to clean up."""

    def write(self, text: str) -> int:
        return 0

    def fileno(self) -> int:
        return -1


def stdout() -> TextIO:
    """Get current stdout, respecting any redirects."""
    return sys.stdout


def stderr() -> TextIO:
    """Get current stderr, respecting any redirects."""
    return sys.stderr


NullCls: SingletonWrap[NullFile] = SingletonWrap(NullFile)


def null_file() -> TextIO:
    """Get a null file that discards all writes."""
    return NullCls.get()


STDOUT: Callable[[], TextIO] = stdout
"""Callable that returns the current stdout"""
STDERR: Callable[[], TextIO] = stderr
"""Callable that returns the current stderr"""
DEVNULL: Callable[[], TextIO] = null_file
"""A null file callable that discards all writes."""
NULL_FILE: TextIO = null_file()
"""A singleton instance of NullFile that discards all writes."""


__all__ = [
    "DEVNULL",
    "STDERR",
    "STDOUT",
    "NullFile",
    "stderr",
    "stdout",
]

# ruff: noqa: D102 PYI063 ARG002
