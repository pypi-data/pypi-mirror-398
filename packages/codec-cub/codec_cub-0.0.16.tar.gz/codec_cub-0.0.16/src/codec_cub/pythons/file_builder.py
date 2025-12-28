"""File builder that organizes code into logical sections with automatic formatting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self

from codec_cub.pythons.builders import ImportBuilder
from codec_cub.pythons.code_section import BodySection, CodeSection, FooterSection, HeaderSection, TypeCheckingSection
from codec_cub.pythons.common import SECTIONS_ORDER
from funcy_bear.constants import characters as ch
from funcy_bear.ops.strings.manipulation import join, quoted

if TYPE_CHECKING:
    from codec_cub.pythons._protocols import CodeBuilder
    from codec_cub.pythons.builders.fluent_builders import TypeAliasBuilder, VariableBuilder
    from codec_cub.pythons.common import Sections


def detect_section(item: object) -> Sections | None:
    """Detect appropriate section for an item based on its type.

    Uses isinstance checks on the CodeBuilder protocol to automatically
    route builder objects to the body section.

    Args:
        item: The item to check.

    Returns:
        The detected section name, or None if item is not a builder.
    """
    from codec_cub.pythons._protocols import CodeBuilder  # noqa: PLC0415

    if isinstance(item, CodeBuilder):
        return "body"

    return None


@dataclass(slots=True)
class SectionsHolder:
    """Dataclass representing the different sections of a Python file."""

    header: HeaderSection = field(default_factory=HeaderSection)
    imports: ImportBuilder = field(default_factory=ImportBuilder)
    type_checking: TypeCheckingSection = field(default_factory=TypeCheckingSection)
    body: BodySection = field(default_factory=BodySection)
    footer: FooterSection = field(default_factory=FooterSection)

    def add(self, section: Sections, line: str, indent: int = 0) -> None:
        """Add a line to the specified section.

        Args:
            section: The section to which the line should be added.
            line: The line to add.
            indent: Relative indent change for this line.
        """
        getattr(self, section).add(line, indent=indent)

    def get(self, section: Sections) -> CodeSection:
        """Get a specific section.

        Args:
            section: The section to retrieve.

        Returns:
            The corresponding section object.
        """
        return getattr(self, section)


class FileBuilder:
    """A file builder that organizes code into logical sections with automatic formatting.

    FileBuilder now includes integrated ImportManager for seamless import handling.
    Use add_import() and add_from_import() to add imports - they're auto-rendered!
    """

    def __init__(self) -> None:
        """Initialize the FileBuilder with empty sections and import manager."""
        self._sections = SectionsHolder()

    def add(self, item: str | CodeBuilder, section: Sections | None = None, indent: int = 0) -> Self:
        """Add an item to the buffer with smart section routing.

        If section is not specified, CodeBuilder objects are automatically routed
        to the body section. Strings require an explicit section parameter.

        Args:
            item: The item to add (string or CodeBuilder object).
            section: The section where the item should be added (auto-detected for builders).
            indent: Relative indent change for this line.

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If section is None and item is a string.

        Examples:
            >>> file.add(FunctionBuilder(...))  # Auto-routes to body
            >>> file.add("# Comment", section="header")  # Explicit section required
        """
        if section is None:
            section = detect_section(item)
            if section is None:
                raise ValueError("Section must be explicitly specified for string items")

        if not isinstance(item, str):
            item = item.render()

        self._sections.add(section, item, indent=indent)
        return self

    def add_import(self, module: str, *, is_third_party: bool = False, is_local: bool = False) -> Self:
        """Add a simple import statement (integrated with ImportManager).

        Args:
            module: Module name to import.
            is_third_party: Whether this is a third-party module.
            is_local: Whether this is a local/relative import.

        Returns:
            Self for method chaining.

        Examples:
            >>> builder.add_import("sys")
            >>> builder.add_import("requests", is_third_party=True)
        """
        self.imports.add_import(module, is_third_party=is_third_party, is_local=is_local)
        return self

    def add_from_import(
        self,
        module: str,
        names: str | list[str],
        *,
        is_third_party: bool = False,
        is_local: bool = False,
    ) -> Self:
        """Add a from...import statement (integrated with ImportManager).

        Args:
            module: Module to import from.
            names: Single name or list of names to import.
            is_third_party: Whether this is a third-party module.
            is_local: Whether this is a local/relative import.

        Returns:
            Self for method chaining.

        Examples:
            >>> builder.add_from_import("typing", ["Any", "Final"])
            >>> builder.add_from_import("__future__", "annotations")
        """
        self.imports.add_from_import(module, names, is_third_party=is_third_party, is_local=is_local)
        return self

    def get_section(self, section: Sections) -> CodeSection:
        """Get a specific section buffer for direct manipulation.

        Args:
            section: The section to retrieve.

        Returns:
            The CodeSection for the specified section.
        """
        return self._sections.get(section)

    @property
    def header(self) -> HeaderSection:
        """Get the header section.

        Returns:
            The header CodeSection.
        """
        return self._sections.header

    @property
    def imports(self) -> ImportBuilder:
        """Get the imports section.

        Returns:
            The imports CodeSection.
        """
        return self._sections.imports

    @property
    def type_checking(self) -> TypeCheckingSection:
        """Get the type_checking section.

        Returns:
            The type_checking CodeSection.
        """
        return self._sections.type_checking

    @property
    def body(self) -> BodySection:
        """Get the body section.

        Returns:
            The body CodeSection.
        """
        return self._sections.body

    @property
    def footer(self) -> FooterSection:
        """Get the footer section.

        Returns:
            The footer CodeSection.
        """
        return self._sections.footer

    # ============================================================================
    # Convenience proxy methods - delegate common operations to body section
    # ============================================================================

    def type_alias(self, name: str) -> TypeAliasBuilder:
        """Create a type alias in the body section (convenience proxy).

        Args:
            name: The type alias name.

        Returns:
            A TypeAliasBuilder for fluent API.

        Examples:
            >>> file.type_alias("StorageChoices").literal("json", "yaml", "toml")
        """
        return self.body.type_alias(name)

    def variable(self, name: str) -> VariableBuilder:
        """Create a variable in the body section (convenience proxy).

        Args:
            name: The variable name.

        Returns:
            A VariableBuilder for fluent API.

        Examples:
            >>> file.variable("storage_map").type_hint("dict[str, Storage]").value("{...}")
        """
        return self.body.variable(name)

    # ============================================================================
    # Import convenience shortcuts - common import patterns
    # ============================================================================

    def from_future(self, *names: str) -> Self:
        """Shortcut for importing from __future__.

        Args:
            *names: Names to import from __future__.

        Returns:
            Self for method chaining.

        Examples:
            >>> file.from_future("annotations")
            >>> file.from_future("annotations", "with_statement")
        """
        for name in names:
            self.add_from_import("__future__", name)
        return self

    def from_typing(self, *names: str) -> Self:
        """Shortcut for importing from typing.

        Args:
            *names: Names to import from typing.

        Returns:
            Self for method chaining.

        Examples:
            >>> file.from_typing("Any", "Dict", "Optional")
        """
        self.add_from_import("typing", list(names))
        return self

    def from_dataclasses(self, *names: str) -> Self:
        """Shortcut for importing from dataclasses.

        Args:
            *names: Names to import from dataclasses.

        Returns:
            Self for method chaining.

        Examples:
            >>> file.from_dataclasses("dataclass", "field")
        """
        self.add_from_import("dataclasses", list(names))
        return self

    def from_collections_abc(self, *names: str) -> Self:
        """Shortcut for importing from collections.abc.

        Args:
            *names: Names to import from collections.abc.

        Returns:
            Self for method chaining.

        Examples:
            >>> file.from_collections_abc("Callable", "Iterator", "Sequence")
        """
        self.add_from_import("collections.abc", list(names))
        return self

    def render(self, add_section_separators: bool = False) -> str:
        """Render the buffer into a single string with sections in order.

        Auto-renders ImportBuilder and adds imports to the imports section.

        Args:
            add_section_separators: If True, add blank lines between non-empty sections.

        Returns:
            A string containing all lines in the buffer, ordered by section.
        """
        # Trigger ImportBuilder render to populate its buffer
        self.imports.render()

        output_lines: list[str] = []

        for section in SECTIONS_ORDER:
            code_section: CodeSection = self.get_section(section)
            section_lines: list[str] = code_section.get()
            if section_lines:
                if output_lines and add_section_separators:
                    output_lines.append(ch.NEWLINE)
                output_lines.extend(section_lines)
        result: str = join(*output_lines, sep=ch.NEWLINE).rstrip(ch.NEWLINE)
        if result and not result.endswith(ch.NEWLINE):
            result += ch.NEWLINE
        return result

    def all_export(self, names: list[str], max_line_length: int = 120) -> None:
        """Generate __all__ export list using ListLiteralBuilder.

        Args:
            names: List of names to export.
            max_line_length: Maximum line length before switching to multiline format (default: 120).

        Returns:
            Formatted __all__ list string.
        """
        from .builders.fluent_builders import ListLiteralBuilder  # noqa: PLC0415

        builder = ListLiteralBuilder(indent=0)
        for name in names:
            builder.add(quoted(name))

        single_line: str = f"__all__ = {builder.render()}"
        if len(single_line) > max_line_length:
            builder.multiline()
            self.footer.add(f"__all__ = {builder.render()}")
        else:
            self.footer.add(single_line)
