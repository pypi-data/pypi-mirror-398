# MessagePack Implementation

A clean, metadata-driven MessagePack implementation for efficient binary serialization.

## Overview

This module provides a complete MessagePack encoder/decoder with:
- **Zero magic numbers** - All constants derived from enum metadata
- **Plugin-based handlers** - Clean separation of concerns for each type
- **Efficient caching** - `MsgPackHandler` for reusable buffer management
- **Full MessagePack spec** - Supports all standard types (nil, bool, int, float, str, bin, array, map)

## Architecture

```
message_pack/
├── packing.py              # Public API: pack(), unpack(), MsgPackHandler
├── unpacking.py            # Unpacking entry point
├── _packing.py             # Packing Handlers
├── _unpacking.py           # Unpacking Handlers
└── common/
    ├── _msgpack_tag.py     # Tag enum with metadata
    ├── _fix_families.py    # FixFamily enum with metadata
    └── exceptions.py       # MessagePack exceptions
```

## Quick Start

### Basic Packing/Unpacking

```python
from codec_cub.message_pack import pack, unpack

# Pack Python objects
data = {"name": "Bear", "age": 42, "items": [1, 2, 3]}
packed = pack(data)  # Returns bytes

# Unpack MessagePack bytes
unpacked = unpack(packed)  # Returns {'name': 'Bear', ...}
```

### Using MsgPackHandler (with buffer caching)

```python
from codec_cub.message_pack import MsgPackHandler

# Create handler with reusable buffer
handler = MsgPackHandler()

# Pack and unpack multiple objects
data1 = {"first": "object"}
packed1 = handler.pack(data1)
unpacked1 = handler.unpack_one(packed1)

data2 = [1, 2, 3, 4, 5]
packed2 = handler.pack(data2)
unpacked2 = handler.unpack_one(packed2)

# Stream unpacking (multiple objects in one buffer)
stream = pack_one(obj1) + pack_one(obj2) + pack_one(obj3)
results = handler.unpack_stream(stream)  # Returns [obj1, obj2, obj3]

# Context manager for auto-cleanup
with MsgPackHandler() as h:
    packed = h.pack({"data": "test"})
    # Buffer auto-cleared on exit
```

### File-Based I/O

```python
from codec_cub.message_pack import MsgPackFileHandler

# Write/read MessagePack files
handler = MsgPackFileHandler(file="data.msgpack", touch=True)
handler.write({"name": "Bear", "data": [1, 2, 3]})
data = handler.read()
handler.close()
```

## Key Features

### Metadata-Driven Design

All MessagePack tags and fix families are defined as rich enums with metadata:

```python
from codec_cub.encoders.message_pack.common import Tag, FixFamily

# Tags have size, bounds, and type information
Tag.INT16.meta.size        # 2 bytes
Tag.INT16.meta.low         # -32768
Tag.INT16.meta.high        # 32767
Tag.INT16.meta.be_bytes(42)  # b'\x00\x2a'

# FixFamilies have base byte, masks, and bounds
FixFamily.FIXSTR.meta.base   # 0xa0
FixFamily.FIXSTR.meta.high   # 31 (max length)
```

### Handler-Based Dispatch

Unpacking uses clean handler dictionaries:

```python
# FIX_HANDLERS: dict[FixFamily, Callable]
# TAG_HANDLERS: dict[Tag, Callable]

# Each handler knows how to unpack its specific type
def unpack_fixstr(buf, byte_val):
    length = FixFamily.FIXSTR.meta.extract_length(byte_val)
    data = buf.read(n=length, tick=length)
    return data.decode("utf-8")
```

Packing uses type-checking dispatch:

```python
# TYPE_HANDLERS: list[tuple[condition, handler]]
TYPE_HANDLERS = [
    (partial(is_instance_of, types=bool), pack_bool),
    (partial(is_instance_of, types=int), pack_int),
    (partial(is_instance_of, types=str), pack_str),
    # ...
]
```

### Integer Optimization

Integers automatically use the smallest encoding:

```python
pack(42)      # pos fixint (1 byte)
pack(200)     # UINT8 (2 bytes)
pack(-1)      # neg fixint (1 byte)
pack(-200)    # INT16 (3 bytes)
pack(70000)   # INT32 (5 bytes)
```

### Offset Management

The unpacking system uses `tick` parameter for automatic offset advancement:

```python
# Read tag byte and advance offset by 1
tag_byte = buf.read(n=1, tick=1)

# Read string data and advance offset by length
data = buf.read(n=length, tick=length)
```

## Supported Types

| Python Type     | MessagePack Format                    | Notes                       |
| --------------- | ------------------------------------- | --------------------------- |
| `None`          | nil                                   | Single byte 0xc0            |
| `bool`          | true/false                            | Single bytes 0xc2/0xc3      |
| `int`           | fixint, int8/16/32/64, uint8/16/32/64 | Range-based selection       |
| `float`         | float64                               | 8-byte IEEE 754             |
| `str`           | fixstr, str8/16/32                    | UTF-8 encoded               |
| `bytes`         | bin8/16/32                            | Raw binary data             |
| `list`, `tuple` | fixarray, array16/32                  | Recursive packing           |
| `dict`          | fixmap, map16/32                      | Keys sorted for consistency |

## Testing

Comprehensive test coverage in `tests/`:
- `test_message_pack.py` - Packing tests
- `test_message_unpack.py` - Unpacking tests (hex and round-trip)
- `test_msgpack_handler.py` - MsgPackHandler feature tests

Run tests:
```bash
uv run pytest tests/test_message_pack.py -v
uv run pytest tests/test_message_unpack.py -v
uv run pytest tests/test_msgpack_handler.py -v
```

## Design Principles

1. **No Magic Numbers** - All constants from enum metadata
2. **Type Safety** - Full type hints with pyright
3. **Immutable Metadata** - Frozen data structures for consistency
4. **Clean Handlers** - Each type has dedicated pack/unpack function
5. **Efficient Caching** - Reusable buffers via `MsgPackHandler`
6. **Test-Driven** - 40+ passing tests covering all features

## Future Extensions

The handler-based design makes it easy to add:
- **Extension types** (0xC7-C9, 0xD4-D8) for custom types
- **Plugin system** for user-defined serializers
- **Streaming** for large datasets
- **Compression** integration

## Related Modules

- `files/msgpack/` - File handler integration (`MsgPackFileHandler`)
- `datastore/` - Future `MsgPackStorage` backend
- `constants/binary_types.py` - Binary type definitions used by metadata
- `rich_enums/` - Enum base classes with metadata support

Keep it messagepacked, Bear! 🐻🤘

```python
from enum import IntEnum

class Tag(IntEnum):
    """MessagePack tags (spec constants)."""

    NIL = 0xC0
    FALSE = 0xC2
    TRUE = 0xC3
    BIN8 = 0xC4
    BIN16 = 0xC5
    BIN32 = 0xC6
    FLOAT64 = 0xCB
    UINT8 = 0xCC
    UINT16 = 0xCD
    UINT32 = 0xCE
    UINT64 = 0xCF
    INT8 = 0xD0
    INT16 = 0xD1
    INT32 = 0xD2
    INT64 = 0xD3
    STR8 = 0xD9
    STR16 = 0xDA
    STR32 = 0xDB
    ARRAY16 = 0xDC
    ARRAY32 = 0xDD
    MAP16 = 0xDE
    MAP32 = 0xDF
```
