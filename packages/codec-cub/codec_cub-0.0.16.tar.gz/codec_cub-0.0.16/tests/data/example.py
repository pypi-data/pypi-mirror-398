"""Automatically generated Python module for database 'example.pydb'.

You can edit this file directly since this _IS_ the database source,
but be careful to maintain correct syntax.
"""  # noqa: INP001
# fmt: off

from __future__ import annotations

from typing import Any, Final, Literal, TypedDict

VERSION: Final[tuple[int, ...]] = (0, 1, 0)
TABLES: Final[tuple[Literal["settings"]]] = ("settings",)
COUNT: int = len(TABLES)

class ColumnType(TypedDict):
    """Row type for 'settings' table."""

    name: str
    type: str
    default: Any
    nullable: bool
    primary_key: bool
    autoincrement: bool
    
SCHEMAS: dict[str, list[ColumnType]] = {
    "settings": [
        {"name": "id", "type": "int", "default": 0, "nullable": False, "primary_key": True, "autoincrement": True},
        {"name": "key", "type": "str", "default": "", "nullable": False, "primary_key": False, "autoincrement": False},
        {"name": "value", "type": "Any", "default": None, "nullable": False, "primary_key": False, "autoincrement": False},
        {"name": "type", "type": "str", "default": "", "nullable": False, "primary_key": False, "autoincrement": False},
    ]
}


ROWS: list[dict[str, Any]] = [
    {"id": 1, "key": "app_name", "value": "Bear Dereth", "type": "str"},
    {"id": 2, "key": "version", "value": "1.0.0", "type": "str"},
    {"id": 3, "key": "debug_mode", "value": True, "type": "bool"},
    {"id": 4, "key": "max_connections", "value": 100, "type": "int"},
    {"id": 5, "key": "timeout_seconds", "value": 30.5, "type": "float"},
    {"id": 6, "key": "theme", "value": "dark", "type": "str"},
    {"id": 7, "key": "language", "value": "en", "type": "str"},
    {"id": 8, "key": "auto_save", "value": True, "type": "bool"},
    {"id": 9, "key": "cache_size_mb", "value": 512, "type": "int"},
    {"id": 10, "key": "log_level", "value": "INFO", "type": "str"},
    
]
