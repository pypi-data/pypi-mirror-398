# Python Code Generation Utilities

A powerful, type-safe toolkit for programmatically generating clean Python code with automatic formatting, indentation management, and section organization.

## Overview

The `pythons` module provides a fluent API for building Python code programmatically. It's designed for:
- Dynamic code generation (plugins, configs, APIs)
- AST-to-source compilation
- Code transformation tools
- Template-based generators

**Key Features:**
- ✅ **Section-based organization** (header, imports, type_checking, body, footer)
- ✅ **Automatic import management** with deduplication
- ✅ **Smart indentation** using context managers
- ✅ **Type-safe builders** for functions, classes, enums, dataclasses
- ✅ **Fluent API** with method chaining
- ✅ **Protocol-based design** for extensibility
- ✅ **Zero manual string formatting** required

## Quick Start

### Basic Example

```python
from codec_cub.pythons import FileBuilder

# Create a new Python file
file = FileBuilder()

# Add imports using shortcuts
file.from_future("annotations")
file.from_typing("Literal", "Final")

# Add a type alias (auto-routes to body section!)
file.type_alias("Status").literal("active", "inactive", "pending")

# Add a variable
file.variable("DEFAULT_STATUS").type_hint("Final[Status]").value('"active"')

# Render the complete file
print(file.render())
```

**Output:**
```python
from __future__ import annotations

from typing import Final, Literal

type Status = Literal["active", "inactive", "pending"]
DEFAULT_STATUS: Final[Status] = "active"
```

### Function Generation

```python
from codec_cub.pythons import FileBuilder, FunctionBuilder, DocstringBuilder

file = FileBuilder()
file.from_typing("Any")

# Build a function with docstring
func = (
    FunctionBuilder("process_data")
    .arg("data", "dict[str, Any]")
    .arg("verbose", "bool", default="False")
    .returns("list[str]")
    .docstring(
        DocstringBuilder()
        .summary("Process input data and return results.")
        .arg("data", "Input data dictionary")
        .arg("verbose", "Enable verbose logging")
        .returns("List of processed result strings")
    )
    .add_line("results: list[str] = []")
    .add_line("for key, value in data.items():")
    .add_line('    results.append(f"{key}: {value}")', indent=1)
    .add_line("return results")
)

# Smart routing - no section needed!
file.add(func)

print(file.render())
```

**Output:**
```python
from typing import Any


def process_data(data: dict[str, Any], verbose: bool = False) -> list[str]:
    """Process input data and return results.

    Args:
        data: Input data dictionary
        verbose: Enable verbose logging

    Returns:
        List of processed result strings
    """
    results: list[str] = []
    for key, value in data.items():
        results.append(f"{key}: {value}")
    return results
```

## Core Concepts

### FileBuilder - Section Organization

Every Python file is organized into five sections:

```python
file = FileBuilder()

# 1. Header - Module docstrings, file-level comments
file.header.docstring("Module for storage backends.")

# 2. Imports - Automatically organized by category
file.add_import("sys")  # stdlib
file.add_from_import("requests", "Session", is_third_party=True)
file.add_from_import(".config", "Settings", is_local=True)

# 3. Type Checking - TYPE_CHECKING imports
with file.type_checking.if_block():
    file.type_checking.add("from ._protocols import Protocol")

# 4. Body - Main code (classes, functions, variables)
file.body.add("CONSTANT = 42")

# 5. Footer - __all__ exports, if __name__ == "__main__"
file.all_export(["CONSTANT", "process_data"])
```

### Import Shortcuts

Common import patterns have convenient shortcuts:

```python
file = FileBuilder()

# __future__ imports
file.from_future("annotations")
file.from_future("annotations", "with_statement")

# typing imports
file.from_typing("Any", "Dict", "Optional", "TypeVar")

# dataclasses imports
file.from_dataclasses("dataclass", "field")

# collections.abc imports
file.from_collections_abc("Callable", "Iterator", "Sequence")
```

### Smart .add() Routing

The `add()` method automatically detects the appropriate section for builder objects:

```python
file = FileBuilder()

# Auto-routes to body section - no section parameter needed!
file.add(FunctionBuilder("foo").returns("None"))
file.add(ClassBuilder("Bar"))
file.add(EnumBuilder("Status"))

# Strings require explicit section
file.add("# Important comment", section="header")
```

### Convenience Proxy Methods

Common operations delegate directly to the body section:

```python
file = FileBuilder()

# These are equivalent:
file.body.type_alias("ID").from_annotation("int")
file.type_alias("ID").from_annotation("int")  # Proxy!

file.body.variable("counter").value("0")
file.variable("counter").value("0")  # Proxy!
```

## Builders Reference

### TypeHint

Helper for creating complex type annotations:

```python
from codec_cub.pythons import TypeHint

# Simple types
TypeHint("int")  # → "int"
TypeHint.type_of("MyClass")  # → "type[MyClass]"

# Generic types
TypeHint.list_of("str")  # → "list[str]"
TypeHint.dict_of("str", "int")  # → "dict[str, int]"
TypeHint.set_of("int")  # → "set[int]"
TypeHint.tuple_of("int", "str")  # → "tuple[int, str]"

# Union and Optional
TypeHint.union("int", "str")  # → "int | str"
TypeHint.optional("str")  # → "str | None"

# Literal types
TypeHint.literal("active", "pending")  # → 'Literal["active", "pending"]'
TypeHint.literal(1, 2, 3)  # → "Literal[1, 2, 3]"

# Callables
TypeHint.callable(["int", "str"], "bool")  # → "Callable[[int, str], bool]"

# Nested
TypeHint.dict_of(
    "str",
    TypeHint.list_of(TypeHint.optional("int"))
)  # → "dict[str, list[int | None]]"
```

### FunctionBuilder

Build function definitions with full type safety:

```python
from codec_cub.pythons import FunctionBuilder, Decorator

func = (
    FunctionBuilder("calculate")
    .arg("x", "int")
    .arg("y", "int", default="0")
    .returns("int")
    .decorator(Decorator("staticmethod"))
    .add_line("return x + y")
)

# Or use constructor for simple cases
func = FunctionBuilder(
    name="calculate",
    args=["x: int", "y: int = 0"],
    returns="int",
    body="return x + y"
)
```

**Function Overloads:**

```python
from codec_cub.pythons import FunctionBuilder, Decorator

# Overload signatures (ellipsis on same line)
file.add(
    FunctionBuilder("get", decorators=[Decorator("overload")])
    .arg("key", 'Literal["name"]')
    .returns("str")
)

file.add(
    FunctionBuilder("get", decorators=[Decorator("overload")])
    .arg("key", 'Literal["age"]')
    .returns("int")
)

# Implementation
file.add(
    FunctionBuilder("get")
    .arg("key", "str")
    .returns("str | int")
    .add_line('return data[key]')
)
```

### ClassBuilder

Build class definitions with inheritance and methods:

```python
from codec_cub.pythons import ClassBuilder, FunctionBuilder

cls = (
    ClassBuilder("User")
    .inherit("BaseModel")
    .docstring("User model with authentication.")
    .add_line("name: str")
    .add_line("email: str")
    .newline()
    .add(
        FunctionBuilder("__init__")
        .arg("self")
        .arg("name", "str")
        .arg("email", "str")
        .add_line("self.name = name")
        .add_line("self.email = email")
    )
)

file.add(cls)
```

### Dataclass and PydanticModel

Specialized builders extending ClassBuilder:

```python
from codec_cub.pythons import Dataclass, PydanticModel

# Dataclass with auto-generated __init__, __repr__, etc.
dc = (
    Dataclass("Config")
    .field("host", "str", default='"localhost"')
    .field("port", "int", default="8080")
    .field("debug", "bool", default="False")
)

# Pydantic model with validation
model = (
    PydanticModel("UserCreate")
    .field("username", "str")
    .field("email", "str")
    .field("age", "int | None", default="None")
)
```

### EnumBuilder

Build enum definitions:

```python
from codec_cub.pythons import EnumBuilder

status_enum = (
    EnumBuilder("Status")
    .member("ACTIVE", '"active"')
    .member("INACTIVE", '"inactive"')
    .member("PENDING", '"pending"')
)

file.add(status_enum)
```

### DocstringBuilder

Structured docstrings in Google style:

```python
from codec_cub.pythons import DocstringBuilder

doc = (
    DocstringBuilder()
    .summary("Fetch user data from the API.")
    .description(
        "This function retrieves user information by ID.",
        "It handles authentication and rate limiting automatically."
    )
    .arg("user_id", "The unique identifier for the user")
    .arg("timeout", "Request timeout in seconds (default: 30)")
    .returns("User object with full profile data")
    .raises("ValueError", "If user_id is invalid")
    .raises("HTTPError", "If the API request fails")
    .example(
        'user = fetch_user(123)',
        'print(user.name)'
    )
)
```

### Literal Builders

Build dict and list literals with proper formatting:

```python
from codec_cub.pythons import DictLiteralBuilder, ListLiteralBuilder

# Dictionary literal
dict_builder = (
    DictLiteralBuilder()
    .entry('"name"', '"Alice"')
    .entry('"age"', "30")
    .entry('"active"', "True")
    .multiline()  # Force multiline format
)

file.variable("user_data").value(dict_builder.render())

# List literal
list_builder = (
    ListLiteralBuilder()
    .add('"apple"')
    .add('"banana"')
    .add('"cherry"')
)

file.variable("fruits").value(list_builder.render())
```

## Advanced Examples

### Dynamic Plugin Registry

See `examples/plugin_generator_demo.py` for a complete example of generating a type-safe plugin registry with:
- Auto-discovered backends
- Literal type aliases
- Function overloads for each backend
- Automatic import management

```python
from codec_cub.pythons import FileBuilder, FunctionBuilder, TypeHint, Decorator

file = FileBuilder()
file.from_future("annotations")
file.from_typing("Literal", "overload")

# Generate type alias from discovered plugins
backends = ["json", "yaml", "toml"]
file.type_alias("BackendType").literal(*backends)

# Generate overloads for each backend
for backend in backends:
    file.add(
        FunctionBuilder("get_backend", decorators=[Decorator("overload")])
        .arg("name", TypeHint.literal(backend))
        .returns(f"{backend.title()}Backend")
    )

# Implementation
file.add(
    FunctionBuilder("get_backend")
    .arg("name", "BackendType")
    .returns("Backend")
    .add_line("return registry[name]()")
)
```

### Context Manager Generation

```python
from codec_cub.pythons import FileBuilder, ClassBuilder, FunctionBuilder

file = FileBuilder()
file.from_typing("Self")

cls = (
    ClassBuilder("DatabaseConnection")
    .add_line("_conn: Connection | None = None")
    .newline()
    .add(
        FunctionBuilder("__enter__")
        .arg("self")
        .returns("Self")
        .add_line("self._conn = connect()")
        .add_line("return self")
    )
    .add(
        FunctionBuilder("__exit__")
        .arg("self")
        .arg("*args")
        .returns("None")
        .add_line("if self._conn:")
        .add_line("    self._conn.close()")
    )
)

file.add(cls)
```

## Architecture

```
pythons/
├── __init__.py              # Public API exports
├── _protocols.py            # CodeBuilder protocol
├── _buffer.py               # BufferHelper for indentation
├── file_builder.py          # Main FileBuilder class
├── code_section.py          # Section implementations
├── builders/
│   ├── import_builder.py    # Import management
│   ├── function_builder.py  # Function definitions
│   ├── class_builder.py     # Class definitions
│   ├── enum_builder.py      # Enum definitions
│   └── fluent_builders.py   # TypeAlias, Variable builders
├── type_annotation.py       # Type annotation helpers
├── parts.py                 # ArgumentBase, Attribute, Decorator
├── helpers.py               # Utility functions
└── README.md                # This file
```

### Design Patterns

**Builder Pattern**: Fluent APIs for constructing code elements
```python
FunctionBuilder("foo").arg("x", "int").returns("str").add_line("...")
```

**Template Method**: CodeSection base class defines structure, subclasses customize
```python
class BodySection(CodeSection):
    def type_alias(self, name: str) -> TypeAliasBuilder: ...
```

**Protocol-Based**: Smart routing uses isinstance() on CodeBuilder protocol
```python
if isinstance(item, CodeBuilder):
    section = "body"  # Auto-route builders
```

**Context Managers**: Automatic indentation management
```python
with file.body.indent():
    file.body.add("indented content")
```

## Testing

The pythons module has comprehensive test coverage:

```bash
# Run all pythons tests
pytest tests/pythons/ -v

# Specific test modules
pytest tests/pythons/test_file_builder.py -v
pytest tests/pythons/test_function_builder.py -v
pytest tests/pythons/test_type_annotation.py -v

# Run demos
python examples/plugin_generator_demo.py
python examples/builders_demo.py
```

**Test Coverage:**
- ✅ FileBuilder section organization
- ✅ Import management and deduplication
- ✅ Function builders with overloads
- ✅ Class builders with inheritance
- ✅ Dataclass and Pydantic models
- ✅ Enum builders
- ✅ Type annotation helpers
- ✅ Docstring generation
- ✅ Smart spacing and formatting
- ✅ Literal builders (dict, list)
- ✅ Auto-rendering in CodeSection

## Best Practices

### 1. Use Proxy Methods for Simple Cases

```python
# Good - clean and concise
file.type_alias("ID").from_annotation("int")
file.variable("count").value("0")

# Also fine - explicit
file.body.type_alias("ID").from_annotation("int")
file.body.variable("count").value("0")
```

### 2. Use Import Shortcuts

```python
# Good - readable
file.from_typing("Any", "Dict", "List")
file.from_future("annotations")

# Avoid - verbose
file.add_from_import("typing", ["Any", "Dict", "List"])
file.add_from_import("__future__", "annotations")
```

### 3. Let Smart Routing Handle Sections

```python
# Good - automatic routing
file.add(FunctionBuilder("foo"))
file.add(ClassBuilder("Bar"))

# Avoid - manual section management
file.add(FunctionBuilder("foo").render(), section="body")
```

### 4. Chain Builder Methods

```python
# Good - fluent and readable
func = (
    FunctionBuilder("process")
    .arg("data", "list[int]")
    .returns("int")
    .add_line("return sum(data)")
)

# Avoid - imperative style
func = FunctionBuilder("process")
func.arg("data", "list[int]")
func.returns("int")
func.add_line("return sum(data)")
```

### 5. Use TypeHint Helpers

```python
# Good - type-safe construction
file.variable("cache").type_hint(
    TypeHint.dict_of("str", TypeHint.optional("int"))
)

# Avoid - raw strings (error-prone)
file.variable("cache").type_hint("dict[str, int | None]")
```

## Performance

- **Memory**: Efficient buffer management with StringIO
- **Imports**: O(1) deduplication using sets
- **Rendering**: O(n) where n is total lines of code
- **Indentation**: O(1) context manager overhead

Suitable for generating files with thousands of lines of code.

## Contributing

Before committing changes to the pythons module:

1. Run quality checks:
   ```bash
   nox -s ruff_fix   # Format and lint
   nox -s pyright    # Type checking
   nox -s tests      # Test suite
   ```

2. Update tests if adding new builders or features

3. Update this README with usage examples

## Future Enhancements

Potential additions (not yet implemented):
- Import statement builder (from x import y as z)
- Decorator builder with arguments
- Property/getter/setter helpers
- Async function builders
- Match/case statement builders (Python 3.10+)
- Exception handler builders (try/except/finally)

## License

MIT License (consistent with parent project)
