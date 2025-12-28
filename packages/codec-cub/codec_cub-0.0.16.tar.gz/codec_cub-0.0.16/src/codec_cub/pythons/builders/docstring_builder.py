"""Builder for structured Python docstrings in Google style."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Self

from codec_cub.pythons._buffer import BufferHelper
from codec_cub.pythons.helpers import get_docstring
from funcy_bear.constants import characters as ch
from funcy_bear.ops.strings.manipulation import join
from funcy_bear.tools import Names

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(slots=True)
class SectionHandler:
    """Handler for a docstring section modification."""

    name: str
    method: Callable[..., Any]
    attr_ptr: str | list | None = None
    kwargs: dict[str, Any] = field(default_factory=dict)

    def add(self, item: Any) -> None:
        """Add an item to the section content if it's a list."""
        if isinstance(self.attr_ptr, list):
            self.attr_ptr.append(item)
        if isinstance(self.attr_ptr, str):
            self.attr_ptr += item

    @property
    def empty(self) -> bool:
        """Check if the section content is empty."""
        return self.attr_ptr is None or not bool(self.attr_ptr)

    def clear(self) -> None:
        """Clear the section content."""
        if isinstance(self.attr_ptr, list):
            self.attr_ptr.clear()
        elif isinstance(self.attr_ptr, str):
            self.attr_ptr = ch.EMPTY_STRING


class DocstringBuilder:
    """Fluent API for building Google-style docstrings.

    Examples:
        >>> doc = DocstringBuilder() \
        ...     .summary("Get storage backend by name.") \
        ...     .arg("storage", "Backend name") \
        ...     .returns("Storage class")
        >>> print(doc.render())
        Get storage backend by name.
    """

    def __init__(self, indent: int = 0) -> None:
        """Initialize an empty docstring builder."""
        self._sections: Names[SectionHandler] = Names()

        self._register(name="Summary", attr_ptr=ch.EMPTY_STRING, method=self._write, kwargs={"prefix": ch.EMPTY_STRING})
        self._register(name="Description", attr_ptr=ch.EMPTY_STRING, method=self._write)
        self._register(name="Args:", attr_ptr=[], method=self._add_list_section)
        self._register(name="Returns:", attr_ptr=ch.EMPTY_STRING, method=self._add_section)
        self._register(name="Yields:", attr_ptr=ch.EMPTY_STRING, method=self._add_section)
        self._register(name="Raises:", attr_ptr=[], method=self._add_list_section)
        self._register(name="Examples:", attr_ptr=[], method=self._add_examples)
        self._register(name="Note:", attr_ptr=[], method=self._add_notes)

        self._buffer: BufferHelper | None = None
        self.indent: int = indent

    def _register(self, name: str, attr_ptr: Any, method: Callable[..., Any], **kwargs) -> None:
        """Register a section modification for tracking (internal use)."""
        self._sections.add(
            name.replace(":", "").lower(),
            SectionHandler(name=name, attr_ptr=attr_ptr, method=method, **kwargs),
        )

    def _write(self, _: str, text: str, prefix: str = ch.NEWLINE, suffix: str = ch.NEWLINE) -> None:
        """Write text to the buffer with optional prefix/suffix."""
        self.buffer.write(text, prefix=prefix, suffix=suffix)

    def summary(self, text: str) -> Self:
        """Set the summary line (first line of docstring).

        Args:
            text: Summary text (should be one line).

        Returns:
            Self for method chaining.
        """
        self._sections.summary.add(text)
        return self

    def description(self, text: str) -> Self:
        """Set the extended description.

        Args:
            text: Description text (can be multiple lines).

        Returns:
            Self for method chaining.
        """
        self._sections.description.add(text)
        return self

    def arg(self, name: str, description: str) -> Self:
        """Add an argument description.

        Args:
            name: Parameter name.
            description: Parameter description.

        Returns:
            Self for method chaining.
        """
        self._sections.args.add((name, description))
        return self

    def returns(self, description: str) -> Self:
        """Set the return value description.

        Args:
            description: Return value description.

        Returns:
            Self for method chaining.
        """
        self._sections.returns.add(description)
        return self

    def raises(self, exception: str, description: str) -> Self:
        """Add an exception that can be raised.

        Args:
            exception: Exception class name.
            description: When/why the exception is raised.

        Returns:
            Self for method chaining.
        """
        self._sections.raises.add((exception, description))
        return self

    def yields(self, description: str) -> Self:
        """Set the yields description for generators.

        Args:
            description: What the generator yields.

        Returns:
            Self for method chaining.
        """
        self._sections.yields.add(description)
        return self

    def example(self, code: str) -> Self:
        """Add a usage example.

        Args:
            code: Example code (will be indented appropriately).

        Returns:
            Self for method chaining.
        """
        self._sections.examples.add(code)
        return self

    def note(self, text: str) -> Self:
        """Add a note section.

        Args:
            text: Note text.

        Returns:
            Self for method chaining.
        """
        self._sections.note.add(text)
        return self

    def _header(self, title: str) -> None:
        """Add a section header."""
        self.buffer.write(title, prefix=ch.NEWLINE, suffix=ch.NEWLINE)

    def _add_section(self, header: str, content: str) -> None:
        """Add a simple section with header and single indented line.

        Args:
            b: The buffer to write to.
            header: Section header (e.g., "Returns:").
            content: Section content (will be indented).
        """
        self._header(header)
        with self.buffer.indented(1):
            self.buffer.write(content, suffix=ch.NEWLINE)

    def _add_list_section(self, header: str, items: list[tuple[str, str]]) -> None:
        """Add a section with multiple indented items.

        Args:
            b: The buffer to write to.
            header: Section header (e.g., "Args:", "Raises:").
            items: List of (name, description) tuples.
        """
        self._header(header)
        with self.buffer.indented(1):
            for name, desc in items:
                self.buffer.write(f"{name}: {desc}", suffix=ch.NEWLINE)

    def _add_examples(self, header: str, examples: list[str]) -> None:
        """Add an examples section with multiple code examples.

        Args:
            b: The buffer to write to.
            examples: List of example code strings.
        """
        self._header(header)
        with self.buffer.indented(1):
            for example in examples:
                for line in example.split(ch.NEWLINE):
                    self.buffer.write(line, suffix=ch.NEWLINE) if line else self.buffer.write(ch.NEWLINE)

    def _add_notes(self, header: str, notes: list[str]) -> None:
        """Add a notes section with multiple notes.

        Args:
            b: The buffer to write to.
            notes: List of note strings.
        """
        self._header(header)
        with self.buffer.indented(1):
            for note in notes:
                self.buffer.write(note, suffix=ch.NEWLINE)

    def render(self, quotes: bool = False) -> str:
        """Render the docstring to a string.

        Args:
            quotes: Whether to wrap the result in triple quotes (default False).

        Returns:
            The formatted docstring content (without triple quotes).
        """
        if all(section.empty for section in self._sections.values()):
            return ch.EMPTY_STRING
        for section in self._sections.values():
            if not section.empty:
                section.method(section.name, section.attr_ptr, **section.kwargs)
        suffix = ch.NEWLINE if self.multiline else ch.EMPTY_STRING
        if not quotes and self.multiline:
            suffix: str = join(ch.NEWLINE, ch.INDENT)
        value: str = join(self.buffer.getvalue().rstrip(ch.NEWLINE), suffix)
        if quotes:
            value = get_docstring(value)
        self.clear()
        return value

    def clear(self) -> Self:
        """Clear all docstring content."""
        for section in self._sections.values():
            section.clear()
        if self._buffer:
            self._buffer = None
        return self

    @property
    def buffer(self) -> BufferHelper:
        """Get or create the internal buffer."""
        if self._buffer is None:
            self._buffer = BufferHelper(indent=self.indent)
        return self._buffer

    @property
    def multiline(self) -> bool:
        """Check if the docstring is multiline.

        Returns:
            True if the docstring has multiple lines, False otherwise.
        """
        return any(not section.empty for section in self._sections.values() if section.name != "Summary")

    def __str__(self) -> str:
        """String representation (calls render)."""
        return self.render()

    def __repr__(self) -> str:
        """Repr representation."""
        return f"DocstringBuilder(summary={self._sections.summary.attr_ptr!r})"


# if __name__ == "__main__":
#     doc = DocstringBuilder(indent=0)
#     doc.summary("Get storage backend by name.")
#     doc.arg("storage", "Backend name")
#     doc.returns("Storage class")
#     with open("docstring_example.py", "w") as f:
#         f.write(doc.render(quotes=True))
