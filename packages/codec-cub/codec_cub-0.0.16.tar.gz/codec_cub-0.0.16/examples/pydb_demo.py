"""PyDB Demo - Python Database with Fast Appends

This demonstrates the PyDB codec which stores structured data in
executable Python files with fast byte-counting appends.
"""  # noqa: INP001

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from codec_cub.pythons import PyDBCodec


def main() -> None:
    """Demonstrate PyDB features."""
    codec = PyDBCodec()

    db_path: Path = Path(__file__).parent / "users.py"

    print("🔧 Creating database file...")
    codec.create(
        file_path=db_path,
        version=(1, 0, 0),
        tables={
            "users": {
                "columns": [
                    {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                    {"name": "name", "type": "str", "nullable": False, "primary_key": False},
                    {"name": "email", "type": "str", "nullable": True, "primary_key": False},
                    {"name": "active", "type": "bool", "nullable": False, "primary_key": False},
                ],
                "rows": [
                    {"id": 1, "name": "Alice", "email": "alice@example.com", "active": True},
                    {"id": 2, "name": "Bob", "email": None, "active": True},
                ],
            }
        },
    )
    print(f"✅ Created: {db_path.name}")

    print("\n📄 Generated file content:")
    print("─" * 60)
    print(db_path.read_text())
    print("─" * 60)

    print("\n⚡ Fast appending rows (no parsing!)...")
    codec.append_row(db_path, {"id": 3, "name": "Charlie", "email": "charlie@example.com", "active": True})
    codec.append_row(db_path, {"id": 4, "name": "Diana", "email": "diana@example.com", "active": False})
    print("✅ Appended 2 rows using byte-counting")

    print("\n📦 Loading as Python module...")
    module = codec.load(db_path)

    print(f"Version: {module.VERSION}")
    print(f"Tables: {module.TABLES}")
    print(f"Table Count: {module.COUNT}")
    print(f"Row Count: {len(module.ROWS)}")

    print("\n👥 All users:")
    for row in module.ROWS:
        status: Literal["✓", "✗"] = "✓" if row["active"] else "✗"
        email: str = row["email"] or "no email"
        print(f"  {status} {row['name']:10} (ID: {row['id']}) - {email}")

    print("\n🔍 Query examples (using list comprehensions):")

    # Filter active users
    active_users = [row for row in module.ROWS if row["active"]]
    print(f"  Active users: {len(active_users)}")
    for user in active_users:
        print(f"    - {user['name']}")

    # Find user by ID
    user: Any = next((row for row in module.ROWS if row["id"] == 3), None)  # noqa: PLR2004
    if user:
        print(f"  User #3: {user['name']}")

    # Users with email
    with_email = [row for row in module.ROWS if row["email"] is not None]
    print(f"  Users with email: {len(with_email)}")

    print("\n✨ Key Benefits:")
    print("  • Human-readable Python files")
    print("  • Git-friendly diffs")
    print("  • Native import (no parsing!)")
    print("  • O(1) append via byte-counting")
    print("  • Type-safe with IDE autocomplete")
    print("  • Works with funcy_bear.query tools!")


if __name__ == "__main__":
    main()
