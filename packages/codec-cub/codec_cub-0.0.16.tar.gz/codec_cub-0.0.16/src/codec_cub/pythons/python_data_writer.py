"""Generic Python data structure writer for serializing dicts/lists to Python files."""

from __future__ import annotations

from importlib.machinery import ModuleSpec, SourceFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import TYPE_CHECKING, Any

from codec_cub.pythons._protocols import CodeBuilder
from codec_cub.pythons.builders.fluent_builders import DictLiteralBuilder, ListLiteralBuilder, TupleLiteralBuilder
from codec_cub.pythons.file_builder import FileBuilder
from codec_cub.pythons.type_annotation import TypeHint
from codec_cub.text.bytes_handler import BytesFileHandler
from codec_cub.text.file_handler import TextFileHandler
from funcy_bear.ops.func_stuffs import all_of, complement
from funcy_bear.tools import Dispatcher
from funcy_bear.typing_stuffs import is_bool, is_dict, is_int, is_list, is_none, is_str, is_tuple

if TYPE_CHECKING:
    from types import ModuleType

    from funcy_bear.typing_stuffs import StrPath


class PythonFileHandler(TextFileHandler):
    """Write arbitrary Python data structures (dicts/lists) to executable Python files.

    Perfect for:
    - Test fixtures (serialized Pydantic models)
    - Configuration files
    - Data snapshots
    - Generated constants

    Example:
        >>> writer = PythonFileHandler("fixtures/data.py")
        >>> writer.write(
        ...     variables={"CONFIG": {"debug": True}, "VERSION": (1, 0, 0)},
        ...     docstring="Auto-generated configuration",
        ...     type_hints={"CONFIG": "dict[str, Any]"},
        ... )
    """

    def __init__(self, file: StrPath, touch: bool = False) -> None:
        """Initialize the Python data writer.

        Args:
            file: Path to the Python file to write
            touch: Whether to create parent directories if they don't exist
        """
        super().__init__(file=file, touch=touch)
        self._bytes = BytesFileHandler(file=file, touch=touch)

    def _imports(
        self,
        file: FileBuilder,
        variables: dict[str, Any],
        type_hints: dict[str, str | TypeHint],
        imports: list[str],
        from_imports: dict[str, list[str]],
    ) -> None:
        needs_typing: dict[str, str | TypeHint] | bool = type_hints or any(
            isinstance(v, (dict, list)) and v for v in variables.values() if not isinstance(v, CodeBuilder)
        )
        file.from_future("annotations")

        if needs_typing:
            file.from_typing("Any")

        if imports:
            for module in imports:
                file.add_import(module)

        if from_imports:
            for module, names in from_imports.items():
                file.add_from_import(module, names)

    def _variables(
        self,
        file: FileBuilder,
        variables: dict[str, Any],
        type_hints: dict[str, str | TypeHint],
    ) -> None:
        for var_name, value in variables.items():
            if isinstance(value, CodeBuilder):
                file.add(value)
            else:
                hint: str | TypeHint | None = type_hints.get(var_name)
                if hint is not None:
                    if isinstance(hint, str):
                        hint = TypeHint(hint)
                    file.variable(var_name).type_hint(hint).value(to_str(value))
                else:
                    file.body.add(f"{var_name} = {to_str(value)}")

    @staticmethod
    def _load_module(path: StrPath) -> ModuleType:
        """Load a Python module from the given file path.

        Args:
            path: Path to the Python file

        Returns:
            The loaded Python module
        """
        pydb = Path(path)
        name: str = pydb.stem
        spec: ModuleSpec | None = spec_from_file_location(
            name,
            pydb,
            loader=SourceFileLoader(name, str(pydb)),
        )
        if spec is None:
            raise ImportError(f"Could not load module spec from path: {path}")
        if spec.loader is None:
            raise ImportError(f"No loader found for module spec from path: {path}")
        module: ModuleType = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def write(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        variables: dict[str, Any] | None = None,
        *,
        docstring: str | None = None,
        type_hints: dict[str, str | TypeHint] | None = None,
        imports: list[str] | None = None,
        from_imports: dict[str, list[str]] | None = None,
        builders: list[CodeBuilder] | None = None,
    ) -> None:
        """Write Python based input data to the file.

        Args:
            variables: Dictionary mapping variable names to their values (or CodeBuilder objects)
            docstring: Optional module-level docstring
            type_hints: Optional type hints for variables (var_name -> type)
            imports: Optional list of modules to import (e.g., ["os", "sys"])
            from_imports: Optional dict of from imports (e.g., {"typing": ["Any", "Dict"]})
            builders: Optional list of CodeBuilder objects (classes, functions, enums)

        Example:
            >>> writer.write(
            ...     variables={
            ...         "CONFIG": {"debug": True},
            ...         "VERSION": (1, 2, 3),
            ...     },
            ...     builders=[
            ...         ClassBuilder("User", attributes=[...]),
            ...         FunctionBuilder("process").returns("None"),
            ...     ],
            ...     docstring="Generated module",
            ...     type_hints={"CONFIG": "dict[str, Any]"},
            ... )

        Note:
            If a variable value is a CodeBuilder, it will be rendered directly
            to the body section (not as a variable assignment).
        """
        file = FileBuilder()

        if docstring:
            file.header.docstring(docstring)

        variables = variables or {}
        builders = builders or []
        type_hints = type_hints or {}
        imports = imports or []
        from_imports = from_imports or {}

        self._imports(file, variables, type_hints, imports, from_imports)
        self._variables(file, variables, type_hints)

        for builder in builders:
            file.add(builder)

        output: str = file.render(add_section_separators=True)
        super().write(output)

    def read(self) -> Any:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Read and execute the Python file, returning its module object.

        Returns:
            The executed module object
        """
        return self._load_module(self.file)


d = Dispatcher("value")


@d.dispatcher()
def to_str(value: Any) -> str:
    """Convert a Python value to its code string representation.

    Handles nested dicts, lists, tuples, and primitives with proper formatting.

    Args:
        value: The Python value to convert

    Returns:
        String representation suitable for Python code
    """
    return str(value)


@d.register(is_dict)
def _dict_str(value: dict[Any, Any]) -> str:
    dict_builder = DictLiteralBuilder(indent=0)
    if not value:
        return dict_builder.render()
    for k, v in value.items():
        dict_builder.entry(to_str(k), to_str(v))
    return dict_builder.render()


@d.register(is_list)
def _list_str(value: list[Any]) -> str:
    list_builder = ListLiteralBuilder(indent=0)
    if not value:
        return list_builder.render()
    for v in value:
        list_builder.add(to_str(v))
    return list_builder.render()


@d.register(is_tuple)
def _tuple_str(value: tuple[Any, ...]) -> str:
    tuple_builder = TupleLiteralBuilder(indent=0)
    if not value:
        return tuple_builder.render()
    for v in value:
        tuple_builder.add(to_str(v))
    return tuple_builder.render()


@d.register(is_str)
def _str_str(value: str) -> str:
    return repr(value)


@d.register(all_of(complement(is_int), is_bool))
def _bool_str(value: bool) -> str:
    return "True" if value else "False"


@d.register(is_none)
def _none_str(value: Any) -> str:  # noqa: ARG001
    return "None"
