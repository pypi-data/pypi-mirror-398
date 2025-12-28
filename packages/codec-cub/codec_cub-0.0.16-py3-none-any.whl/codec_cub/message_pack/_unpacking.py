"""Handlers for MessagePack Tag unpacking."""

from functools import partial
from struct import unpack as struct_unpack
from typing import Any

from lazy_bear import LazyLoader

from codec_cub.message_pack.common import ByteReaderProtocol
from funcy_bear.ops.binarystuffs import from_be_bytes
from funcy_bear.ops.value_stuffs import equal_value
from funcy_bear.tools.dispatcher import Dispatcher

from .common._fix_families import FixFamily, fix_matches
from .common._msgpack_tag import BIN_TYPES, INT_TYPES, LITERAL_TYPES, STR_TYPES, Tag


def unpack_one(br: ByteReaderProtocol) -> Any:
    """Unpack a single MessagePack object from the byte reader."""
    return LazyLoader("codec_cub.message_pack.unpacking").to("unpack_one")(br)


def _read_length(tag: Tag, br: ByteReaderProtocol, signed: bool = False) -> int:
    """Read a length value based on the tag's size."""
    data: bytes = br.read(n=tag.meta.size, tick=tag.meta.size)
    return from_be_bytes(data, signed=signed)


tag = Dispatcher(arg="tag")
fix = Dispatcher(arg="v")


@tag.dispatcher()
def unpack_tags(tag: Tag, br: ByteReaderProtocol) -> Any:  # noqa: ARG001
    """Unpack a MessagePack tag."""
    raise TypeError(f"No handler for tag: {tag}")


@tag.register(partial(equal_value, value=LITERAL_TYPES))
def unpack_literal(tag: Tag, br: ByteReaderProtocol) -> Any:  # noqa: ARG001
    """Unpack a literal tag (NIL, TRUE, FALSE)."""
    return tag.meta.literal


@tag.register(partial(equal_value, value=Tag.FLOAT64))
def unpack_float64(tag: Tag, br: ByteReaderProtocol) -> float:
    """Unpack a 64-bit float."""
    return struct_unpack(">d", br.read(n=tag.meta.size, tick=tag.meta.size))[0]


@tag.register(partial(equal_value, value=INT_TYPES))
def unpack_int(tag: Tag, br: ByteReaderProtocol) -> int:
    """Read an integer based on the tag's size and signedness."""
    return from_be_bytes(br.read(n=tag.meta.size, tick=tag.meta.size), signed=tag.meta.signed)


@tag.register(partial(equal_value, value=STR_TYPES))
def unpack_str(tag: Tag, br: ByteReaderProtocol) -> str:
    """Unpack a string (STR8/16/32)."""
    length: int = _read_length(tag, br)
    data: bytes = br.read(n=length, tick=length)
    return data.decode("utf-8")


@tag.register(partial(equal_value, value=BIN_TYPES))
def unpack_bin(tag: Tag, br: ByteReaderProtocol) -> bytes:
    """Unpack binary data (BIN8/16/32)."""
    length: int = _read_length(tag, br)
    return br.read(n=length, tick=length)


@tag.register(partial(equal_value, value=(Tag.ARRAY16, Tag.ARRAY32)))
def unpack_array(tag: Tag, br: ByteReaderProtocol) -> list:
    """Unpack an array (ARRAY16/32)."""
    return [unpack_one(br) for _ in range(_read_length(tag, br))]


@tag.register(partial(equal_value, value=(Tag.MAP16, Tag.MAP32)))
def unpack_map(tag: Tag, br: ByteReaderProtocol) -> dict:
    """Unpack a map (MAP16/32)."""
    return {unpack_one(br): unpack_one(br) for _ in range(_read_length(tag, br))}


@fix.dispatcher()
def unpack_fix(v: int, br: ByteReaderProtocol) -> Any:  # noqa: ARG001
    """Unpack a fix family item from the byte reader.

    Args:
        br: The byte reader to read from.
        v: The first byte that matched the fix family pattern.

    Returns:
        The unpacked item.
    """
    raise TypeError(f"No fix handler for value: {v}")


@fix.register(partial(fix_matches, enum=FixFamily.FIXSTR))
def unpack_fixstr(v: int, br: ByteReaderProtocol) -> str:
    """Unpack a fixstr from the byte reader.

    Args:
        br: The byte reader to read from.
        v: The first byte that matched the fixstr pattern.

    Returns:
        The decoded string.
    """
    length: int = FixFamily.FIXSTR.meta.extract_length(v)
    data: bytes = br.read(n=length, tick=length)
    return data.decode("utf-8")


@fix.register(partial(fix_matches, enum=FixFamily.FIXARRAY))
def unpack_fixarray(v: int, br: ByteReaderProtocol) -> list:
    """Unpack a fixarray from the byte reader.

    Args:
        br: The byte reader to read from.
        v: The first byte that matched the fixarray pattern.

    Returns:
        The unpacked list.
    """
    length: int = FixFamily.FIXARRAY.meta.extract_length(v)
    return [unpack_one(br) for _ in range(length)]


@fix.register(partial(fix_matches, enum=FixFamily.FIXMAP))
def unpack_fixmap(v: int, br: ByteReaderProtocol) -> dict:
    """Unpack a fixmap from the byte reader.

    Args:
        br: The byte reader to read from.
        v: The first byte that matched the fixmap pattern.

    Returns:
        The unpacked dict.
    """
    length: int = FixFamily.FIXMAP.meta.extract_length(v)
    return {unpack_one(br): unpack_one(br) for _ in range(length)}


@fix.register(partial(fix_matches, enum=FixFamily.POS_FIXINT))
def unpack_pos_fixint(v: int, br: ByteReaderProtocol) -> int:  # noqa: ARG001
    """Unpack a positive fixint.

    Args:
        br: The byte reader (unused for fixints).
        v: The byte value itself is the integer.

    Returns:
        The integer value.
    """
    return v


@fix.register(partial(fix_matches, enum=FixFamily.NEG_FIXINT))
def unpack_neg_fixint(v: int, br: ByteReaderProtocol) -> int:  # noqa: ARG001
    """Unpack a negative fixint.

    Args:
        br: The byte reader (unused for fixints).
        v: The byte value to decode as signed.

    Returns:
        The negative integer value.
    """
    return from_be_bytes(bytes([v]), signed=True)
