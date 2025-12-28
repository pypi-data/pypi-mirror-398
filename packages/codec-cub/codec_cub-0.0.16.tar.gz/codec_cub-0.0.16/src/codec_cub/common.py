"""A set of common utilities for CodecCub."""

from typing import Any, Self

from funcy_bear.constants.characters import SPACE
from funcy_bear.constants.escaping import COMMA_SPACE


def first(obj: Any) -> Any:
    """Return the first item of a sequence or the object itself if not a sequence.

    Args:
        obj: The object to get the first item from.

    Returns:
        The first item of the sequence or the object itself.
    """
    try:
        return obj[0]
    except (TypeError, IndexError):
        return obj


def spaced(s: str) -> str:
    """Return the string with a leading and trailing space.

    Args:
        s: The string to space.

    Returns:
        The spaced string.
    """
    return f"{SPACE}{s}{SPACE}"


def comma_sep(items: list[str]) -> str:
    """Return a comma-separated string from a list of strings.

    Args:
        items: The list of strings.

    Returns:
        The comma-separated string.
    """
    return COMMA_SPACE.join(items)


def piped(*segs: object) -> str:
    """Join segments with pipe character.

    Args:
        *segs: The segments to join.

    Returns:
        The joined string.
    """
    return " | ".join(str(seg) for seg in segs)


class Wrapper:
    """A simple string wrapper with customizable delimiters and separator."""

    def __init__(self, c1: str, c2: str, sep: str, line_length: int = 80, multiline: bool = False) -> None:
        """Initialize the Wrapper with delimiters and separator.

        Args:
            c1: The opening character.
            c2: The closing character.
            sep: The separator between elements.
            line_length: The maximum line length for wrapping (default: 80).
            multiline: Whether to allow multiline wrapping (default: False).
        """
        self.char1: str = c1
        self.char2: str = c2
        self.sep: str = sep
        self.line_length: int = line_length
        self.multiline: bool = multiline
        self.elements: list[str] = []

    def clear(self) -> None:
        """Clear all elements from the wrapper."""
        self.elements.clear()

    def append(self, s: str, pre: str = "", suf: str = "") -> Self:
        """Append a string with optional prefix and suffix.

        Args:
            s: The string to append.
            pre: The prefix to add before the string.
            suf: The suffix to add after the string.

        Returns:
            Self: The Wrapper instance.
        """
        self.elements.append(f"{pre}{s}{suf}")
        return self

    def render(self, sep: str | None = None, pre: str = "", suf: str = "") -> str:
        """Generate the final wrapped string.

        Args:
            sep: The separator to use between elements. If None, uses the instance's separator.
            pre: The prefix to add before the closing character.
            suf: The suffix to add after the closing character.

        Returns:
            The final wrapped string.
        """
        _sep: str = sep if sep is not None else self.sep
        if not self.elements:
            return f"{self.char1}{_sep}{self.char2}"

        output: str = _sep.join([self.char1, *self.elements, f"{pre}{self.char2}{suf}"])
        if self.multiline and len(output) > self.line_length:
            temp: list[str] = []
            for index, line in enumerate(self.elements):
                pre_line: str = f"\n{pre}" if index == 0 else ""
                temp.append(f"{pre_line}{line}")
            return _sep.join([self.char1, *temp, f"\n{pre}{self.char2}{suf}"])
        return output


class TupleWrapper(Wrapper):
    """A string wrapper specifically for tuples, handling single-element cases."""

    def render(self, sep: str | None = None, pre: str = "", suf: str = "") -> str:
        """Generate the final wrapped string, adding a comma for single-element tuples.

        Args:
            sep: The separator to use between elements. If None, uses the instance's separator.
            pre: The prefix to add before the closing character.
            suf: The suffix to add after the closing character.

        Returns:
            The final wrapped string.
        """
        _sep: str = sep if sep is not None else self.sep
        if not self.elements:
            return f"{self.char1}{_sep}{self.char2}"

        if len(self.elements) == 1:
            return _sep.join([self.char1, f"{next(iter(self.elements))},", f"{pre}{self.char2}{suf}"])

        return _sep.join([self.char1, *self.elements, f"{pre}{self.char2}{suf}"])


__all__ = ["COMMA_SPACE", "TupleWrapper", "Wrapper", "comma_sep", "first", "piped", "spaced"]
