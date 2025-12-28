"""Import manager for organizing and deduplicating Python imports."""

from __future__ import annotations

from typing import Final, Literal, Self

from codec_cub.common import COMMA_SPACE
from codec_cub.pythons.code_section import CodeSection
from funcy_bear.constants import characters as ch
from funcy_bear.ops.strings.manipulation import join

FUTURE: Final[str] = "__future__"


class ImportBuilder(CodeSection):
    """Manages imports and automatically deduplicates them.

    Organizes imports into standard library, third-party, and local sections.
    """

    _section_name: str = "imports"

    def __init__(self) -> None:
        """Initialize the ImportBuilder."""
        super().__init__("imports")
        self._future_imports: set[str] = set()
        self._standard_imports: set[str] = set()
        self._third_party_imports: set[str] = set()
        self._local_imports: set[str] = set()
        self._from_imports: dict[str, set[str]] = {}
        self._rendered: bool = False

    def add_import(self, module: str, *, is_third_party: bool = False, is_local: bool = False) -> Self:
        """Add a simple import statement.

        Args:
            module: Module name to import.
            is_third_party: Whether this is a third-party module.
            is_local: Whether this is a local/relative import.

        Returns:
            Self for method chaining.
        """
        if module.startswith("__future__"):
            self._future_imports.add(module)
        elif is_local:
            self._local_imports.add(module)
        elif is_third_party:
            self._third_party_imports.add(module)
        else:
            self._standard_imports.add(module)
        return self

    def add_from_import(
        self,
        module: str,
        names: str | list[str],
        *,
        is_third_party: bool = False,
        is_local: bool = False,
    ) -> Self:
        """Add a from...import statement.

        Args:
            module: Module to import from.
            names: Single name or list of names to import.
            is_third_party: Whether this is a third-party module.
            is_local: Whether this is a local/relative import.

        Returns:
            Self for method chaining.
        """
        if isinstance(names, str):
            names = [names]

        classification: Literal["third", "local", "std"] = "third" if is_third_party else "local" if is_local else "std"
        key: str = join(module, ch.PIPE, classification)
        existing_keys: list[str] = [k for k in self._from_imports if k.startswith(module + ch.PIPE)]
        if existing_keys and existing_keys[0] != key:
            key = existing_keys[0]
        if key not in self._from_imports:
            self._from_imports[key] = set()
        self._from_imports[key].update(names)
        return self

    def _from_import(self, m: str, f: str) -> None:
        """Write a from...import statement to the buffer."""
        self._buffer.write(join("from", ch.SPACE, m, ch.SPACE, "import", ch.SPACE, f), suffix=ch.NEWLINE)

    def _import(self, m: str) -> None:
        """Write an import statement to the buffer."""
        self._buffer.write(join("import", ch.SPACE, m), suffix=ch.NEWLINE)

    @property
    def _std_from(self) -> dict[str, set[str]]:
        """Get standard library from-imports."""
        return {k: v for k, v in self._from_imports.items() if k.endswith("|std")}

    @property
    def _third_from(self) -> dict[str, set[str]]:
        """Get third-party from-imports."""
        return {k: v for k, v in self._from_imports.items() if k.endswith("|third")}

    @property
    def _local_from(self) -> dict[str, set[str]]:
        """Get local from-imports."""
        return {k: v for k, v in self._from_imports.items() if k.endswith("|local")}

    def _render_imports(self, name: str, imports: dict[str, set[str]], new_line: bool = True) -> None:
        """Render a set of imports into formatted strings.

        Args:
            name: Category name of the imports (standard, third_party, local).
            imports: Dictionary of from-imports to render.
            new_line: Whether to add a newline after rendering.
        """
        import_name: str = f"_{name}_imports"
        if getattr(self, import_name) or imports:
            for module in sorted(getattr(self, import_name)):
                self._import(module)
            for key in sorted(imports.keys()):
                module: str = key.split(ch.PIPE)[0]
                names: str = COMMA_SPACE.join(sorted(imports[key]))
                self._from_import(module, names)
            if new_line:
                self.newline()

    def render(self) -> str:
        """Render all imports organized by category.

        Returns:
            Formatted import statements with proper grouping.
        """
        if self._rendered:
            return self.output()

        if self._future_imports:
            for module in sorted(self._future_imports):
                mod: str = module.split(FUTURE + ch.DOT)[1]
                self.add_from_import(FUTURE, mod)
            self.newline()
        self._render_imports("standard", self._std_from)
        self._render_imports("third_party", self._third_from)
        self._render_imports("local", self._local_from, new_line=False)
        self._rendered = True
        return self.output()

    def reset(self) -> Self:
        """Reset the ImportBuilder to its initial state."""
        self._future_imports.clear()
        self._standard_imports.clear()
        self._third_party_imports.clear()
        self._local_imports.clear()
        self._from_imports.clear()
        self._buffer.clear()
        self._rendered = False
        return self


__all__ = ["ImportBuilder"]
