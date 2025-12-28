"""Demonstration of the TOON codec implementation.

This script showcases the key features of the Token-Oriented Object Notation (TOON) format,
including tabular arrays, nested objects, and different delimiter options.
"""  # noqa: INP001

import json

from codec_cub.config import ToonCodecConfig
from codec_cub.toon import ToonCodec


def print_example(title: str, data: dict, codec: ToonCodec | None = None) -> None:
    """Print an example with both JSON-like and TOON representations."""
    if codec is None:
        codec = ToonCodec()

    print(f"\n{'=' * 70}")
    print(f"{title}")
    print(f"{'=' * 70}")

    print("\nPython data:")

    print(json.dumps(data, indent=2))

    print("\nTOON format:")
    toon_str: str = codec.encode(data)
    print(toon_str)

    print("\nRound-trip verification:")
    decoded = codec.decode(toon_str)
    if decoded == data:
        print("✓ Round-trip successful!")
    else:
        print("✗ Round-trip failed!")
        print(f"Expected: {data}")
        print(f"Got: {decoded}")


def main() -> None:
    """Run TOON codec demonstrations."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                    TOON Codec Demonstration                          ║
║            Token-Oriented Object Notation v2.0                       ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    # Example 1: Tabular Arrays (Most Efficient)
    print_example(
        "Example 1: Tabular Arrays",
        {
            "users": [
                {"id": 1, "name": "Alice", "role": "admin"},
                {"id": 2, "name": "Bob", "role": "user"},
                {"id": 3, "name": "Carol", "role": "user"},
            ]
        },
    )

    # Example 2: Nested Objects
    print_example(
        "Example 2: Nested Objects",
        {
            "company": "Acme Corp",
            "location": {"city": "San Francisco", "state": "CA", "coordinates": {"lat": 37.7749, "lon": -122.4194}},
        },
    )

    # Example 3: Inline Primitive Arrays
    print_example(
        "Example 3: Inline Primitive Arrays",
        {"project": "TOON Codec", "tags": ["parsing", "encoding", "python"], "scores": [98.5, 87.3, 92.1]},
    )

    # Example 4: Mixed Data Types
    print_example(
        "Example 4: Mixed Data Types",
        {"id": 42, "name": "Ada Lovelace", "active": True, "score": 95.5, "metadata": None},
    )

    # Example 5: Tab Delimiter
    config_tab = ToonCodecConfig(delimiter="\t")
    codec_tab = ToonCodec(config_tab)
    print_example(
        "Example 5: Tab Delimiter",
        {
            "items": [
                {"sku": "A1", "name": "Widget", "price": 9.99},
                {"sku": "B2", "name": "Gadget", "price": 14.50},
            ]
        },
        codec_tab,
    )

    # Example 6: Pipe Delimiter
    config_pipe = ToonCodecConfig(delimiter="|")
    codec_pipe = ToonCodec(config_pipe)
    print_example(
        "Example 6: Pipe Delimiter", {"status": "ok", "values": ["alpha", "beta", "gamma", "delta"]}, codec_pipe
    )

    # Example 7: Complex Nested Structure
    print_example(
        "Example 7: Complex Nested Structure",
        {
            "api": "TOON Service",
            "version": "2.0",
            "endpoints": [
                {"path": "/users", "method": "GET", "auth": True},
                {"path": "/users", "method": "POST", "auth": True},
                {"path": "/health", "method": "GET", "auth": False},
            ],
            "config": {"timeout": 30, "retry": {"max_attempts": 3, "backoff": 2.0}},
        },
    )

    # Token Efficiency Comparison
    print(f"\n{'=' * 70}")
    print("Token Efficiency Comparison (JSON vs TOON)")
    print(f"{'=' * 70}\n")

    comparison_data = {
        "products": [
            {"id": 1, "name": "Product A", "price": 19.99, "stock": 100},
            {"id": 2, "name": "Product B", "price": 29.99, "stock": 50},
            {"id": 3, "name": "Product C", "price": 39.99, "stock": 75},
        ]
    }

    json_str: str = json.dumps(comparison_data)
    codec = ToonCodec()
    toon_str: str = codec.encode(comparison_data)

    print("JSON representation:")
    print(json.dumps(comparison_data, indent=2))
    print(f"\nJSON length: {len(json_str)} characters (minified)")

    print("\nTOON representation:")
    print(toon_str)
    print(f"\nTOON length: {len(toon_str)} characters")

    savings = ((len(json_str) - len(toon_str)) / len(json_str)) * 100
    print(f"\nSpace savings: {savings:.1f}%")

    print(f"\n{'=' * 70}")
    print("✓ TOON Codec PoC Demonstration Complete!")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
