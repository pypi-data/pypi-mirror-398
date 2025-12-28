from typing import Protocol, Self, runtime_checkable

from funcy_bear.constants.characters import EMPTY_STRING, NEWLINE

from ._buffer import BufferHelper
from .parts import Docstring


@runtime_checkable
class Renderable(Protocol):
    """Protocol for objects that can render themselves as code strings.

    Any object implementing this protocol can be added to a CodeSection
    or FileBuilder, allowing for composable code generation.
    """

    def render(self, indent: int = 0) -> str: ...


@runtime_checkable
class CodeBuilder(Protocol):
    """Protocol for objects that can render themselves as code strings.

    Any object implementing this protocol can be added to a CodeSection
    or FileBuilder, allowing for composable code generation.
    """

    _docstring: Docstring
    _added_lines: BufferHelper

    def add_line(self, line: str) -> Self:
        """Add a line to the code element.

        Args:
            line: The line to add.

        Returns:
            Self for method chaining.
        """
        self._added_lines.write(line, suffix=NEWLINE)
        return self

    def add_to_docs(
        self,
        additional_content: str,
        prefix: str = EMPTY_STRING,
        suffix: str = EMPTY_STRING,
    ) -> Self:
        """Add additional content to the docstring.

        Args:
            additional_content: The content to add to the docstring.
            prefix: An optional prefix to add before the additional content.
            suffix: An optional suffix to add after the additional content.

        Returns:
            The updated CodeBuilder instance.
        """
        self._docstring.add(additional_content, prefix=prefix, suffix=suffix)
        return self

    def render(self) -> str:
        """Render this code element to a string with proper indentation.

        Returns:
            The rendered code as a string.
        """
        ...
