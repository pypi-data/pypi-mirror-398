"""Tests for MsgPackHandler class."""

from typing import Any

from codec_cub.message_pack.msg_pack_handler import MsgPackHandler
from codec_cub.message_pack.packing import pack


class TestMsgPackHandler:
    """Test suite for MsgPackHandler."""

    def test_pack_unpack_dict(self) -> None:
        """Test packing and unpacking a dictionary."""
        handler = MsgPackHandler()
        data: dict[str, Any] = {"name": "Bear", "age": 42, "active": True}
        packed: bytes = handler.pack_one(data)
        unpacked: Any = handler.unpack_one(packed)
        assert unpacked == data

    def test_pack_unpack_list(self) -> None:
        """Test packing and unpacking a list."""
        handler = MsgPackHandler()
        data: list[int] = [1, 2, 3, 4, 5]
        packed: bytes = handler.pack_one(data)
        unpacked: list[int] = handler.unpack_one(packed)
        assert unpacked == data

    def test_pack_unpack_nested(self) -> None:
        """Test packing and unpacking nested structures."""
        handler = MsgPackHandler()
        data: dict[str, Any] = {
            "users": [
                {"id": 1, "name": "Bear"},
                {"id": 2, "name": "Claire"},
            ],
            "count": 2,
        }
        packed: bytes = handler.pack_one(data)
        unpacked: dict[str, Any] = handler.unpack_one(packed)
        assert unpacked == data

    def test_multiple_cycles(self) -> None:
        """Test multiple pack/unpack cycles with same handler."""
        handler = MsgPackHandler(data=None)

        # Cycle 1
        data1: dict[str, Any] = {"name": "Bear", "count": 42}
        packed1: bytes = handler.pack_one(data1)
        unpacked1: dict[str, Any] = handler.unpack_one(packed1)
        assert unpacked1 == data1

        # Cycle 2
        data2: list[int] = [1, 2, 3, 4, 5]
        packed2: bytes = handler.pack_one(data2)
        unpacked2: list[int] = handler.unpack_one(packed2)
        assert unpacked2 == data2

        # Cycle 3
        data3: dict[str, dict[str, dict[str, int]]] = {"nested": {"deep": {"value": 123}}}
        packed3: bytes = handler.pack_one(data3)
        unpacked3: Any = handler.unpack_one(packed3)
        assert unpacked3 == data3

    def test_pack(self) -> None:
        """Test pack method."""
        handler = MsgPackHandler()
        handler.pack({"test": 1})
        handler.pack([2, 3])
        buffer: bytes = handler.get_buffer()
        assert len(buffer) > 0

    def test_clear(self):
        """Test clear method."""
        handler = MsgPackHandler()
        handler.pack_one({"data": "test"})
        handler.clear()
        buffer: bytes = handler.get_buffer()
        assert len(buffer) == 0

    def test_get_buffer_clear(self) -> None:
        """Test get_buffer with clear=True."""
        handler = MsgPackHandler()
        handler.pack({"data": "test"})
        buffer1: bytes = handler.get_buffer(clear=False)
        assert len(buffer1) > 0
        buffer2: bytes = handler.get_buffer(clear=True)
        assert buffer1 == buffer2
        buffer3: bytes = handler.get_buffer()
        assert len(buffer3) == 0

    def test_pack_primitives(self) -> None:
        """Test packing various primitive types."""
        handler = MsgPackHandler()
        test_cases: list[Any] = [
            None,
            True,
            False,
            0,
            42,
            -1,
            3.14,
            "hello",
            b"bytes",
        ]
        for value in test_cases:
            packed: bytes = handler.pack_one(value)
            unpacked: list[Any] = handler.unpack_one(packed)
            assert unpacked == value, f"Failed for {value!r}"

    def test_unpack_stream(self) -> None:
        """Test unpacking multiple objects from a stream."""
        handler = MsgPackHandler()
        obj1: dict[str, Any] = {"id": 1, "name": "Bear"}
        obj2: list[int] = [1, 2, 3]
        obj3 = "hello"
        packed: bytes = pack(obj1) + pack(obj2) + pack(obj3)
        results: Any = handler.unpack_stream(packed)
        assert len(results) == 3
        assert results[0] == obj1
        assert results[1] == obj2
        assert results[2] == obj3

    def test_size_property(self) -> None:
        """Test size property returns buffer length."""
        handler = MsgPackHandler()
        assert handler.size == 0
        data: dict[str, int] = {"test": 123}
        handler.pack(data)
        assert handler.size > 0
        handler.clear()
        assert handler.size == 0

    def test_context_manager(self) -> None:
        """Test context manager clears buffer on exit."""
        with MsgPackHandler() as handler:
            handler.pack({"data": "test"})
            assert handler.size > 0
        assert handler.size == 0

    def test_init_with_bytes_data(self) -> None:
        """Test initializing handler with bytes data."""
        data: dict[str, Any] = {"name": "Bear", "age": 42}
        packed: bytes = pack(data)
        handler = MsgPackHandler()

        # Use unpack_one to unpack pre-packed bytes
        unpacked: dict[str, Any] = handler.unpack_one(packed)
        assert unpacked == data

    def test_unpack_stream_single_object(self) -> None:
        """Test unpack_stream with single object."""
        handler = MsgPackHandler()
        data: dict[str, str] = {"single": "object"}
        packed: bytes = pack(data)
        results: Any = handler.unpack_stream(packed)
        assert len(results) == 1
        assert results[0] == data

    def test_unpack_stream_empty(self) -> None:
        """Test unpack_stream with empty data."""
        handler = MsgPackHandler()
        results: Any = handler.unpack_stream(b"")
        assert results == []
