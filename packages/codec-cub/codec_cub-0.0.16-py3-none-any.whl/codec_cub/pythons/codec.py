"""PyDB codec for creating and manipulating Python database files."""

from __future__ import annotations

from io import SEEK_END
from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

from funcy_bear.constants import characters as ch
from funcy_bear.ops.math import neg

from ._buffer import BufferHelper
from .builders.class_builder import ClassBuilder
from .builders.fluent_builders import ListLiteralBuilder
from .file_builder import FileBuilder
from .parts import Attribute
from .type_annotation import TypeHint as Anno

if TYPE_CHECKING:
    from importlib.machinery import ModuleSpec, SourceFileLoader
    from importlib.util import module_from_spec, spec_from_file_location
    from pathlib import Path
    from types import ModuleType

    from .code_section import CodeSection

else:
    ModuleSpec, SourceFileLoader = lazy("importlib.machinery").to("ModuleSpec", "SourceFileLoader")
    module_from_spec, spec_from_file_location = lazy("importlib.util").to("module_from_spec", "spec_from_file_location")


BYTE_OFFSET = 7
"""Byte offset from end of file to insert new row before closing bracket. Example: "    \n]\n" is 7 bytes."""

TYPED_DICT: list[str] = ["TypedDict"]


class PyDBCodec:
    """Encode and decode Python Database (.py) format.

    PyDB files are executable Python modules that store structured data
    in a human-readable, version-controllable format.

    Features:
        - Create .py database files with schema and initial data
        - Fast append operations using byte counting
        - Load database files as Python modules (no parsing needed!)
        - Type-safe access to data

    Example:
        >>> codec = PyDBCodec()
        >>> codec.create(
        ...     file_path=Path("data.py"),
        ...     version=(1, 0, 0),
        ...     tables={"users": {"columns": [...], "rows": [...]}},
        ... )
        >>> codec.append_row(Path("data.py"), {"id": 1, "name": "Alice"})
        >>> module = codec.load(Path("data.py"))
        >>> print(module.ROWS)
    """

    def __init__(self) -> None:
        """Initialize PyDBCodec."""
        self.builder = FileBuilder()
        self.tables: dict[str, dict[str, list[dict[str, Any]]]] = {}

    def create(
        self,
        file_path: Path,
        version: tuple[int, ...],
        tables: dict[str, dict[str, list[dict[str, Any]]]],
    ) -> None:
        """Create a new Python database file with schema and optional initial data.

        Args:
            file_path: Path where the database file will be created
            version: Semantic version tuple (e.g., (1, 0, 0))
            tables: Dictionary mapping table names to their schema and rows
                   Format: {
                       "table_name": {
                           "columns": [
                               {"name": str, "type": str, "nullable": bool, "primary_key": bool},
                               ...
                           ],
                           "rows": [dict, ...]  # Optional initial data
                       }
                   }

        Raises:
            ValueError: If schema is invalid
            IOError: If file cannot be written
        """
        self.tables = tables
        self._build_header(file_path)
        self._build_imports()
        self._build_metadata(version, list(tables.keys()))
        self._build_column_type_class()
        self._build_table_row_classes()
        self._build_schemas()
        self._build_rows()

        content: str = self.builder.render()
        file_path.write_text(content)

    def _build_header(self, file_path: Path) -> None:
        """Build file header with docstring and formatting directive."""
        header: CodeSection = self.builder.header
        header.add(f'"""Python Database file: {file_path.stem}.py"""')
        header.add("# fmt: off")
        header.newline()

    def _build_imports(self) -> None:
        """Build import statements using integrated ImportManager."""
        self.builder.add_from_import("__future__", "annotations")
        self.builder.add_from_import("typing", ["Any", "Final", "Literal", "TypedDict"])

    def _build_metadata(self, version: tuple[int, ...], table_names: list[str]) -> None:
        """Build VERSION, TABLES, and COUNT constants."""
        body: CodeSection = self.builder.body

        version_str: str = repr(version)
        body.variable("VERSION").type_hint(Anno("Final[tuple[int, ...]]")).value(version_str)

        if table_names:
            tables_literal: Anno = Anno.literal(*table_names)
            tables_type: Anno = Anno.generic("Final", Anno.list_of(tables_literal))
            body.variable("TABLES").type_hint(tables_type).value(repr(table_names))
        else:
            body.variable("TABLES").type_hint(Anno("Final[list]")).value("[]")

        body.variable("COUNT").type_hint(Anno("int")).value(str(len(table_names)))
        body.newline()

    def _build_column_type_class(self) -> None:
        """Build ColumnType TypedDict class for schema definitions."""
        column_type_class = ClassBuilder(
            name="ColumnType",
            bases=TYPED_DICT,
            docstring="Column definition for database schema.",
            attributes=[
                Attribute("name", "str"),
                Attribute("type", "str"),
                Attribute("default", "Any"),
                Attribute("nullable", "bool"),
                Attribute("primary_key", "bool"),
                Attribute("autoincrement", "bool"),
            ],
        )
        self.builder.body.add(column_type_class)
        self.builder.body.newline()

    def _build_table_row_classes(self) -> None:
        """Build TypedDict classes for each table's row type."""
        body: CodeSection = self.builder.body

        for table_name, table_data in self.tables.items():
            class_name: str = self._table_row_class_name(table_name)
            columns: list[dict[str, Any]] = table_data.get("columns", [])

            # we need to manually build the attributes, if the column is nullable = True, then we need to do a | None
            attrs = []
            for col in columns:
                col_type = col["type"]
                if col.get("nullable", False):
                    col_type = f"{col_type} | None"
                attrs.append(Attribute(name=col["name"], annotations=col_type))

            row_class = ClassBuilder(
                name=class_name,
                bases=TYPED_DICT,
                docstring=f"Row type for '{table_name}' table.",
                attributes=attrs,
            )
            body.add(row_class)

    def _build_schemas(self) -> None:
        """Build SCHEMAS dictionary mapping table names to column definitions."""
        from .builders.fluent_builders import DictLiteralBuilder, ListLiteralBuilder

        body: CodeSection = self.builder.body
        schemas_dict = DictLiteralBuilder(indent=body._buffer.indent)

        if self.tables:
            for table_name, table_data in self.tables.items():
                columns: list[dict[str, Any]] = table_data.get("columns", [])
                columns_list = ListLiteralBuilder(indent=body._buffer.indent + 1)
                for col in columns:
                    col_dict: dict[str, Any] = {
                        "name": col["name"],
                        "type": col["type"],
                        "default": col.get(
                            "default", None if col.get("nullable") else 0 if col["type"] == "int" else ""
                        ),
                        "nullable": col.get("nullable", False),
                        "primary_key": col.get("primary_key", False),
                        "autoincrement": col.get("autoincrement", False),
                    }
                    columns_list.add(repr(col_dict))
                schemas_dict.entry(repr(table_name), columns_list.multiline().render())
            schemas_value: str = schemas_dict.multiline().render()
        else:
            schemas_value = "{}"

        body.variable("SCHEMAS").type_hint(Anno.dict_of("str", "list[ColumnType]")).value(schemas_value)
        body.newline()

    def _build_rows(self) -> None:
        """Build ROWS list with typed row types."""
        body: CodeSection = self.builder.body

        all_rows = []
        for table_data in self.tables.values():
            all_rows.extend(table_data.get("rows", []))

        rows_list = ListLiteralBuilder(indent=body._buffer.indent)
        for row in all_rows:
            rows_list.add(repr(row))

        if self.tables:
            row_types: list[str] = [self._table_row_class_name(name) for name in self.tables]
            rows_type: Anno = (
                Anno.list_of(row_types[0]) if len(row_types) == 1 else Anno.list_of(Anno.union(*row_types))
            )
        else:
            rows_type = Anno.list_of("dict[str, Any]")

        rows_value: str = rows_list.multiline().trailing_blank_line().render()
        body.variable("ROWS").type_hint(rows_type).value(rows_value)

    def _table_row_class_name(self, table_name: str) -> str:
        """Generate a TypedDict class name for a table.

        Args:
            table_name: The table name (e.g., "users", "settings")

        Returns:
            PascalCase class name (e.g., "UsersRow", "SettingsRow")
        """
        return f"{table_name.title().replace('_', '')}Row"

    def load(self, file_path: Path) -> ModuleType:
        """Load a Python database file as a module.

        Args:
            file_path: Path to the database file

        Returns:
            The loaded module with attributes: VERSION, TABLES, COUNT, SCHEMAS, ROWS

        Raises:
            FileNotFoundError: If file doesn't exist
            ImportError: If file is not valid Python
        """
        if not file_path.exists():
            raise FileNotFoundError(f"PyDB file not found: {file_path}")

        name: str = file_path.stem
        spec: ModuleSpec | None = spec_from_file_location(
            name,
            file_path,
            loader=SourceFileLoader(name, str(file_path)),
        )
        if spec is None:
            raise ImportError(f"Could not load module spec from path: {file_path}")
        if spec.loader is None:
            raise ImportError(f"No loader found for module spec from path: {file_path}")

        module: ModuleType = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def append_row(self, file_path: Path, row: dict[str, Any]) -> None:
        """Append a row to the database file using fast byte-counting.

        This method uses byte offset calculation to append data without
        parsing the entire file, making it very fast even for large files.

        Args:
            file_path: Path to the database file
            row: Dictionary containing the row data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If row data is invalid
        """
        buffer = BufferHelper(indent=1)

        buffer.write(repr(row), suffix=ch.COMMA + ch.NEWLINE)
        buffer.write(ch.EMPTY_STRING, suffix=ch.NEWLINE)
        buffer.indent = 0
        buffer.write(ch.RIGHT_BRACKET, suffix=ch.NEWLINE)

        new_content: str = buffer.getvalue()

        with open(file_path, "r+b") as f:
            f.seek(neg(BYTE_OFFSET), SEEK_END)
            f.truncate()
            f.write(new_content.encode("utf-8"))
            f.truncate()


__all__ = ["PyDBCodec"]

# ruff: noqa: PLC0415
