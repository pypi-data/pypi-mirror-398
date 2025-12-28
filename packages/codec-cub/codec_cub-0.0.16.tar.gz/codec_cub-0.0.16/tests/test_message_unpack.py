"""Tests for MessagePack unpacking functionality."""

from io import BytesIO
from typing import Any, LiteralString

import pytest

from codec_cub.message_pack.msg_pack_handler import MsgPackHandler
from codec_cub.message_pack.unpacking import unpack_one
from codec_cub.text.bytes_handler import BytesFileHandler


def pack_and_unpack(value: Any) -> Any:
    """Helper to pack a value and then unpack it."""
    packer = MsgPackHandler()
    packer.pack(value)
    packed: bytes = packer.get_buffer()

    unpacker = BytesFileHandler(buffer=BytesIO)
    unpacker.write(packed)
    unpacker.to_offset(0)
    return unpack_one(unpacker)


def unpack_from_hex(hex_str: str):
    """Helper to unpack from a hex string."""
    data: bytes = bytes.fromhex(hex_str)
    unpacker = BytesFileHandler(buffer=BytesIO)
    unpacker.write(data)
    unpacker.to_offset(0)
    return unpack_one(unpacker)


class TestUnpackRoundTrip:
    """Test that pack/unpack round-trips work correctly."""

    def test_none(self) -> None:
        """Test None (nil)."""
        assert pack_and_unpack(None) is None

    def test_booleans(self) -> None:
        """Test boolean values."""
        assert pack_and_unpack(value=True) is True
        assert pack_and_unpack(value=False) is False

    def test_positive_fixint(self) -> None:
        """Test positive fixints (0-127)."""
        for i in [0, 1, 42, 127]:
            assert pack_and_unpack(i) == i

    def test_negative_fixint(self) -> None:
        """Test negative fixints (-32 to -1)."""
        for i in [-1, -16, -32]:
            assert pack_and_unpack(i) == i

    def test_uint8(self) -> None:
        """Test uint8 (128-255)."""
        assert pack_and_unpack(128) == 128
        assert pack_and_unpack(255) == 255

    def test_uint16(self) -> None:
        """Test uint16 (256-65535)."""
        assert pack_and_unpack(256) == 256
        assert pack_and_unpack(65535) == 65535

    def test_uint32(self) -> None:
        """Test uint32 (65536-4294967295)."""
        assert pack_and_unpack(65536) == 65536
        assert pack_and_unpack(4294967295) == 4294967295

    def test_uint64(self) -> None:
        """Test uint64 (4294967296-18446744073709551615)."""
        assert pack_and_unpack(4294967296) == 4294967296
        assert pack_and_unpack(18446744073709551615) == 18446744073709551615

    def test_int8(self) -> None:
        """Test int8 (-128 to -33)."""
        assert pack_and_unpack(-128) == -128
        assert pack_and_unpack(-33) == -33

    def test_int16(self) -> None:
        """Test int16 (-32768 to -129)."""
        assert pack_and_unpack(-129) == -129
        assert pack_and_unpack(-32768) == -32768

    def test_int32(self) -> None:
        """Test int32 (-2147483648 to -32769)."""
        assert pack_and_unpack(-32769) == -32769
        assert pack_and_unpack(-2147483648) == -2147483648

    def test_int64(self) -> None:
        """Test int64 (-9223372036854775808 to -2147483649)."""
        assert pack_and_unpack(-2147483649) == -2147483649
        assert pack_and_unpack(-9223372036854775808) == -9223372036854775808

    def test_float(self) -> None:
        """Test float32 and float64."""
        assert pack_and_unpack(3.14) == pytest.approx(3.14)
        assert pack_and_unpack(-2.5) == pytest.approx(-2.5)

    def test_fixstr(self) -> None:
        """Test fixstr (0-31 bytes)."""
        assert pack_and_unpack("") == ""
        assert pack_and_unpack("hello") == "hello"
        assert pack_and_unpack("a" * 31) == "a" * 31

    def test_str8(self) -> None:
        """Test str8 (32-255 bytes)."""
        s: LiteralString = "x" * 100
        assert pack_and_unpack(s) == s

    def test_str16(self) -> None:
        """Test str16 (256-65535 bytes)."""
        s: LiteralString = "y" * 300
        assert pack_and_unpack(s) == s

    def test_bytes(self) -> None:
        """Test binary data."""
        assert pack_and_unpack(b"binary") == b"binary"
        assert pack_and_unpack(b"\x00\xff\xaa") == b"\x00\xff\xaa"

    def test_fixarray(self) -> None:
        """Test fixarray (0-15 elements)."""
        assert pack_and_unpack([]) == []
        assert pack_and_unpack([1, 2, 3]) == [1, 2, 3]
        assert pack_and_unpack(["a", "b", "c"]) == ["a", "b", "c"]

    def test_array16(self) -> None:
        """Test array16 (16+ elements)."""
        arr: list[int] = list(range(20))
        assert pack_and_unpack(arr) == arr

    def test_fixmap(self) -> None:
        """Test fixmap (0-15 key-value pairs)."""
        assert pack_and_unpack({}) == {}
        assert pack_and_unpack({"a": 1, "b": 2}) == {"a": 1, "b": 2}

    def test_nested_structures(self) -> None:
        """Test nested lists and dicts."""
        nested: dict[str, Any] = {"list": [1, 2, {"key": "value"}]}
        assert pack_and_unpack(nested) == nested

        nested_list: list[dict[str, int]] = [{"a": 1}, {"b": 2}]
        assert pack_and_unpack(nested_list) == nested_list


class TestUnpackFromHex:
    """Test unpacking from known MessagePack hex strings."""

    def test_nil(self) -> None:
        """Test nil (None)."""
        assert unpack_from_hex("c0") is None

    def test_booleans(self) -> None:
        """Test boolean values."""
        assert unpack_from_hex("c2") is False
        assert unpack_from_hex("c3") is True

    def test_positive_fixint(self) -> None:
        """Test positive fixints (0-127)."""
        assert unpack_from_hex("00") == 0
        assert unpack_from_hex("2a") == 42
        assert unpack_from_hex("7f") == 127

    def test_negative_fixint(self) -> None:
        """Test negative fixints (-32 to -1)."""
        assert unpack_from_hex("ff") == -1
        assert unpack_from_hex("e0") == -32

    def test_uint8(self) -> None:
        """Test uint8 (128-255)."""
        assert unpack_from_hex("cc80") == 128
        assert unpack_from_hex("ccff") == 255

    def test_uint16(self) -> None:
        """Test uint16 (256-65535)."""
        assert unpack_from_hex("cd0100") == 256
        assert unpack_from_hex("cdffff") == 65535

    def test_int8(self) -> None:
        """Test int8 (-128 to -33)."""
        assert unpack_from_hex("d080") == -128

    def test_fixstr(self) -> None:
        """Test fixstr (0-31 bytes)."""
        assert unpack_from_hex("a0") == ""
        assert unpack_from_hex("a568656c6c6f") == "hello"

    def test_fixarray(self) -> None:
        """Test fixarray (0-15 elements)."""
        assert unpack_from_hex("90") == []
        assert unpack_from_hex("93010203") == [1, 2, 3]

    def test_fixmap(self) -> None:
        """Test fixmap (0-15 key-value pairs)."""
        assert unpack_from_hex("80") == {}
        assert unpack_from_hex("82a16101a16202") == {"a": 1, "b": 2}
