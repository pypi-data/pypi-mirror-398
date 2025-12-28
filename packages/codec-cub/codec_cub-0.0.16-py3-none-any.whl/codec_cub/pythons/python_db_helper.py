"""A proof of concept Python file handler for reading/writing Python database modules.

This is still experimental and not really ready for production use. Put less weight on
the seriousness you might give to analyzing this code.
"""

from __future__ import annotations

from dataclasses import MISSING, dataclass
from typing import TYPE_CHECKING, Any, Final, Literal, NamedTuple, Protocol

from codec_cub.general.base_file_handler import BaseFileHandler
from codec_cub.pythons.file_builder import FileBuilder
from codec_cub.pythons.python_data_writer import to_str
from codec_cub.pythons.type_annotation import TypeHint
from codec_cub.text.bytes_handler import BytesFileHandler
from funcy_bear.sentinels import NOTSET

if TYPE_CHECKING:
    from _typeshed import StrPath


class _FieldInfo(NamedTuple):
    name: str
    type: str
    default: Any


@dataclass
class ColumnType:
    """Row type for 'settings' table."""

    name: str
    type: str
    nullable: bool = False
    unique: bool | None = None
    comment: str | None = None
    foreign_key: str | None = None
    default: Any | None = None
    ondelete: str | None = None
    onupdate: str | None = None
    primary_key: bool | None = None
    autoincrement: bool | None = None

    @classmethod
    def fields(cls) -> list[_FieldInfo]:
        """Get the fields of the ColumnType as a dictionary.

        Returns:
            A dictionary of field names to their values.
        """
        fields: list[_FieldInfo] = []
        for key, value in cls.__dataclass_fields__.items():
            fields.append(
                _FieldInfo(
                    name=key,
                    type=value.type,
                    default=value.default if value.default is not MISSING else NOTSET,
                )
            )
        return fields


class RowProtocol(Protocol):
    """Protocol for a database row."""


class PyDBProtocol(Protocol):
    """Protocol for Python database modules."""

    VERSION: Final[tuple[int, ...]]
    TABLES: Final[tuple]
    TABLE_COUNT: int

    SCHEMAS: dict[str, list[ColumnType]]
    ROW_COUNT: int
    ROWS: list[RowProtocol]


# TODO: This should be moved out of here because this is less of a file handler or codec
# and more of a "storage" that tries to articulate the UnifiedDataFormat from bear-shelf.


def column_type_class() -> str:
    """Generate the ColumnType TypedDict class definition.

    Returns:
        Complete class definition as a string
    """
    from codec_cub.pythons.builders.class_builder import Dataclass  # noqa: PLC0415
    from codec_cub.pythons.parts import Attribute  # noqa: PLC0415

    fields: list[_FieldInfo] = ColumnType.fields()
    attributes: list[Attribute] = [
        Attribute(
            name=field.name,
            annotations=TypeHint(field.type),
            default=field.default,
        )
        for field in fields
    ]

    cls = Dataclass(name="ColumnType", docstring="Column definition for database schema.", attributes=attributes)
    return cls.render()


class PythonWriter(BaseFileHandler):
    """A file handler for writing and reading from Python files."""

    def __init__(self, file: StrPath, touch: bool = False) -> None:
        """Initialize the Python file handler.

        Args:
            file: Path to the Python file
            touch: Whether to create the file if it doesn't exist
        """
        super().__init__(file=file)
        self._bytes = BytesFileHandler(file=file, touch=touch)

    def read(self, **kwargs) -> PyDBProtocol:  # noqa: ARG002
        """Read and return the Python database module."""
        return self._load_module(self.file)  # type: ignore[return-value]

    def write(self, data: dict[str, Any], **kwargs) -> None:  # noqa: ARG002
        """Write a complete .pydb file from structured data.

        Args:
            data: Dictionary containing:
                - version: tuple[int, ...] - Semantic version
                - tables: list[str] - Table names
                - schemas: list[dict] - Column definitions
                - rows: list[dict] - Data rows
            **kwargs: Additional keyword arguments (unused)

        Example:
            >>> data = {
            ...     "version": (1, 0, 0),
            ...     "tables": ["users"],
            ...     "schemas": [
            ...         {
            ...             "name": "id",
            ...             "type": "int",
            ...             "default": 0,
            ...             "nullable": False,
            ...             "primary_key": True,
            ...             "autoincrement": True,
            ...         }
            ...     ],
            ...     "rows": [{"id": 1, "username": "alice"}],
            ... }
            >>> writer.write(data)
        """
        file = FileBuilder()

        file.header.docstring("Python Database file - Auto-generated")
        file.from_future("annotations")
        file.from_typing("Any", "Final", "Protocol")
        file.from_dataclasses("dataclass")

        version: tuple[int, ...] = data.get("version", (1, 0, 0))
        tables: list[Any] = data.get("tables", [])
        schemas: list[Any] = data.get("schemas", [])
        rows: list[Any] = data.get("rows", [])

        file.variable("VERSION").type_hint("tuple[int, ...]", final=True).to_tuple(version)
        file.variable("TABLES").type_hint("tuple[str, ...]", final=True).to_tuple(tables)
        file.variable("COUNT").type_hint("int").value("len(TABLES)")
        file.body.newline()
        # file.body.add(self._generate_column_type_class())
        file.body.add(self._generate_row_protocol_class())
        file.variable("SCHEMAS").type_hint(TypeHint.list_of("ColumnType")).value(to_str(schemas))
        file.body.newline()
        file.variable("ROWS").type_hint(TypeHint.list_of("RowProtocol")).value(to_str(rows))
        output: str = file.render(add_section_separators=True)
        self.file.write_text(output)

    def append(self, data: dict[str, Any] | list[dict[str, Any]], **kwargs) -> None:  # noqa: ARG002
        """Append rows to an existing .pydb file.

        Args:
            data: Single row dict or list of row dicts to append
            **kwargs: Additional keyword arguments (unused)

        Example:
            >>> writer.append({"id": 3, "username": "charlie"})
            >>> writer.append([{"id": 4, "username": "dave"}, {"id": 5, "username": "eve"}])
        """
        rows: list[dict[str, Any]] = [data] if isinstance(data, dict) else data
        content: str = self.file.read_text()
        rows_marker = "ROWS: list[RowProtocol] = ["
        if rows_marker not in content:
            raise ValueError("Invalid pydb file: ROWS definition not found")

        closing_bracket_idx: int = content.rfind("]")
        if closing_bracket_idx == -1:
            raise ValueError("Invalid pydb file: closing bracket not found")

        before_close: str = content[:closing_bracket_idx].rstrip()
        new_rows_code: str = ",\n    ".join(to_str(row) for row in rows)
        needs_comma: bool = not before_close.endswith("[")
        comma: Literal[",", ""] = "," if needs_comma else ""
        new_content: str = f"{before_close}{comma}\n    {new_rows_code},\n]"
        self.file.write_text(new_content)

    @staticmethod
    def _generate_row_protocol_class() -> str:
        """Generate the RowProtocol Protocol class definition.

        Returns:
            Complete class definition as a string
        """
        from codec_cub.pythons.builders.class_builder import ClassBuilder  # noqa: PLC0415

        cls = ClassBuilder(
            name="RowProtocol",
            bases="Protocol",
            docstring="Protocol for a database row.",
        )
        return cls.render()
