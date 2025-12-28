"""A codec and builder for Python files.

Python Database (PyDB) provides a way to store structured data in executable
Python modules. Files are human-readable, version-controllable, and natively
importable without parsing.

The Python builders provide general-purpose code generation for any Python code,
not just PyDB. They support dataclasses, Pydantic models, enums, and more.

Example (PyDB):
    >>> from codec_cub.pythons import PyDBCodec
    >>> codec = PyDBCodec()
    >>> codec.create(Path("data.py"), version=(1, 0, 0), tables={...})
    >>> codec.append_row(Path("data.py"), {"id": 1, "name": "Alice"})
    >>> module = codec.load(Path("data.py"))

Example (Python Builders):
    >>> from codec_cub.pythons import ClassBuilder, Attribute, Decorator
    >>> user_class = ClassBuilder(
    ...     name="User",
    ...     decorators=[Decorator("dataclass")],
    ...     attributes=[
    ...         Attribute("id", int),
    ...         Attribute("name", str),
    ...     ],
    ... )
    >>> print(user_class.render())
"""

from __future__ import annotations

from .builders import EnumBuilder, ImportBuilder
from .builders.class_builder import ClassBuilder, Dataclass, PydanticModel
from .builders.docstring_builder import DocstringBuilder
from .builders.fluent_builders import DictLiteralBuilder, ListLiteralBuilder, TypeAliasBuilder, VariableBuilder
from .builders.function_builder import FunctionBuilder, MethodBuilder
from .codec import PyDBCodec
from .file_builder import FileBuilder
from .helpers import generate_all_export, get_literal_type, get_type_alias
from .parts import Arg, Attribute, Decorator, Docstring, Variable
from .python_data_writer import PythonFileHandler
from .type_annotation import TypeHint, dict_of, list_of, literal, optional, set_of, tuple_of, type_of, union

__all__ = [
    "Arg",
    "Attribute",
    "ClassBuilder",
    "Dataclass",
    "Decorator",
    "DictLiteralBuilder",
    "Docstring",
    "DocstringBuilder",
    "EnumBuilder",
    "FileBuilder",
    "FunctionBuilder",
    "ImportBuilder",
    "ListLiteralBuilder",
    "MethodBuilder",
    "PyDBCodec",
    "PydanticModel",
    "PythonFileHandler",
    "TypeAliasBuilder",
    "TypeHint",
    "Variable",
    "VariableBuilder",
    "dict_of",
    "generate_all_export",
    "get_literal_type",
    "get_type_alias",
    "list_of",
    "literal",
    "optional",
    "set_of",
    "tuple_of",
    "type_of",
    "union",
]
