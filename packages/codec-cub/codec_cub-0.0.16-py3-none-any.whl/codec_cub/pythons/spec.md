---
title: Python Database (.pydb) File Format Specification
created: Monday, November 3rd 2025, 8:40:11 pm
modified: Monday, November 3rd 2025, 8:42:04 pm
---
# Python Database (.pydb) File Format Specification

## Overview

Python Database files (.pydb) are executable Python modules that store structured data in a human-readable, version-controllable format. Files are valid Python code that can be imported directly and provide type-safe access to tabular data.

## File Structure

Every .pydb file must contain these top-level attributes:

### VERSION

```python
VERSION: Final[tuple[int, ...]] = (1, 0, 0)
```

Semantic version of the database schema.

### TABLES

```python
TABLES: Final[tuple[str, ...]] = ("users", "posts")
```

Tuple of table names present in this database.

### COUNT

```python
COUNT: int = len(TABLES)
```

Number of tables in the database.

### SCHEMAS

```python
SCHEMAS: list[ColumnType] = [
    {
        "name": "id",
        "type": "int",
        "default": 0,
        "nullable": False,
        "primary_key": True,
        "autoincrement": True,
    },
    {
        "name": "username",
        "type": "str",
        "default": "",
        "nullable": False,
        "primary_key": False,
        "autoincrement": False,
    },
]
```

Schema definitions describing columns with name, type, and constraints.

### ROWS

```python
ROWS: list[RowProtocol] = [
    {"id": 1, "username": "alice", "email": "alice@example.com"},
    {"id": 2, "username": "bob", "email": "bob@example.com"},
]
```

The actual data rows as a list of dictionaries.

## Type Definitions

### ColumnType

```python
class ColumnType(TypedDict):
    """Column definition for database schema."""

    name: str
    type: str
    default: Any
    nullable: bool
    primary_key: bool
    autoincrement: bool
```

### RowProtocol

```python
class RowProtocol(Protocol):
    """Protocol for a database row."""
```

### PyDBProtocol

```python
class PyDBProtocol(Protocol):
    """Protocol for Python database modules."""

    VERSION: Final[tuple[int, ...]]
    TABLES: Final[tuple[str, ...]]
    COUNT: int
    SCHEMAS: list[ColumnType]
    ROWS: list[RowProtocol]
```

## Complete Example File

```python
"""Example Python Database file."""

from __future__ import annotations

from typing import Any, Final, Protocol, TypedDict

VERSION: Final[tuple[int, ...]] = (1, 0, 0)
TABLES: Final[tuple[str, ...]] = ("users",)
COUNT: int = len(TABLES)


class ColumnType(TypedDict):
    """Column definition for database schema."""

    name: str
    type: str
    default: Any
    nullable: bool
    primary_key: bool
    autoincrement: bool


class RowProtocol(Protocol):
    """Protocol for a database row."""


SCHEMAS: list[ColumnType] = [
    {
        "name": "id",
        "type": "int",
        "default": 0,
        "nullable": False,
        "primary_key": True,
        "autoincrement": True,
    },
    {
        "name": "username",
        "type": "str",
        "default": "",
        "nullable": False,
        "primary_key": False,
        "autoincrement": False,
    },
]

ROWS: list[RowProtocol] = [
    {"id": 1, "username": "alice"},
    {"id": 2, "username": "bob"},
]
```

## File Operations

### Loading a .pydb File

```python
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

def load_pydb(path: Path):
    """Load a .pydb file as a Python module."""
    name = path.stem
    spec = spec_from_file_location(
        name,
        path,
        loader=SourceFileLoader(name, str(path)),
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {path}")

    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
```

### Appending Rows

```python
import json

def append_row(file_path: Path, row: dict) -> None:
    """Append a row to the .pydb file."""
    row_str = json.dumps(row)

    with open(file_path, 'r+b') as f:
        # Seek to position before closing bracket
        f.seek(-OFFSET, 2)
        f.write(f"    {row_str},\n]\n".encode())
```

## Design Rationale

**Advantages:**
- Human-readable and editable
- Version control friendly
- Type-safe when imported
- No external dependencies

**Limitations:**
- Not suitable for large datasets
- No transaction support
- Linear scan queries only

**Use Cases:**
- Configuration management
- Development fixtures
- Small application databases
- Human-editable datasets
