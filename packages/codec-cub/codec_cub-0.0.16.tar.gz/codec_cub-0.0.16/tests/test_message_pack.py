import pytest

from codec_cub.message_pack.msg_pack_handler import MsgPackHandler


@pytest.fixture
def message_packer() -> MsgPackHandler:
    """Fixture to provide a MsgPackHandler instance for tests."""
    return MsgPackHandler()


def test_pack_int(message_packer: MsgPackHandler) -> None:
    """Tests the expected hex output for packing integers."""
    test_cases: list[tuple[int, str]] = [
        (0, "00"),
        (127, "7f"),
        (-1, "ff"),
        (128, "cc80"),
        (255, "ccff"),
        (256, "cd0100"),
        (65535, "cdffff"),
        (65536, "ce00010000"),
        (4294967295, "ceffffffff"),
        (4294967296, "cf0000000100000000"),
        (18446744073709551615, "cfffffffffffffffff"),
        (-128, "d080"),
        (-129, "d1ff7f"),
        (-32768, "d18000"),
        (-32769, "d2ffff7fff"),
        (-2147483648, "d280000000"),
        (-2147483649, "d3ffffffff7fffffff"),
        (-9223372036854775808, "d38000000000000000"),
    ]

    for value, expected_hex in test_cases:
        message_packer.pack(value)
        packed_bytes: bytes = message_packer.get_buffer(clear=True)
        assert packed_bytes.hex() == expected_hex, f"Failed for value: {value}"


def test_str(message_packer: MsgPackHandler) -> None:
    """Tests the expected hex output for packing strings."""
    test_cases: list[tuple[str, str]] = [
        ("", "a0"),
        ("hello", "a568656c6c6f"),
        ("world", "a5776f726c64"),
        (
            "This is a crazy long string and I think it is so crazy, please think of all the wonderful people who brought me here to this place... people like my lovely Claire! I love you Claire!",
            "d9b6546869732069732061206372617a79206c6f6e6720737472696e6720616e642049207468696e6b20697420697320736f206372617a792c20706c65617365207468696e6b206f6620616c6c2074686520776f6e64657266756c2070656f706c652077686f2062726f75676874206d65206865726520746f207468697320706c6163652e2e2e2070656f706c65206c696b65206d79206c6f76656c7920436c61697265212049206c6f766520796f7520436c6169726521",
        ),
    ]

    for value, expected_hex in test_cases:
        message_packer.pack(value)
        packed_bytes: bytes = message_packer.get_buffer()
        assert packed_bytes.hex() == expected_hex, f"Failed for value: {value!r}"
        message_packer.clear()


def test_bytes(message_packer: MsgPackHandler) -> None:
    """Tests the expected hex output for packing bytes."""
    test_cases: list[tuple[bytes, str]] = [
        (b"", "c400"),
        (b"hello", "c40568656c6c6f"),
        (b"\x00\x01\x02\x03", "c40400010203"),
    ]

    for value, expected_hex in test_cases:
        message_packer.pack(value)
        packed_bytes: bytes = message_packer.get_buffer()
        assert packed_bytes.hex() == expected_hex, f"Failed for value: {value!r}"
        message_packer.clear()


def test_booleans(message_packer: MsgPackHandler) -> None:
    """Tests the expected hex output for packing booleans."""
    test_cases: list[tuple[bool, str]] = [
        (True, "c3"),
        (False, "c2"),
    ]

    for value, expected_hex in test_cases:
        message_packer.pack(value)
        packed_bytes: bytes = message_packer.get_buffer()
        assert packed_bytes.hex() == expected_hex, f"Failed for value: {value!r}"
        message_packer.clear()


def test_none(message_packer: MsgPackHandler) -> None:
    """Tests the expected hex output for packing None."""
    message_packer.pack(None)
    packed_bytes: bytes = message_packer.get_buffer()
    assert packed_bytes.hex() == "c0", "Failed for value: None"


def test_float(message_packer: MsgPackHandler) -> None:
    """Tests the expected hex output for packing floats."""
    test_cases: list[tuple[float, str]] = [
        (3.14, "cb40091eb851eb851f"),
        (-3.14, "cbc0091eb851eb851f"),
        (0.0, "cb0000000000000000"),
        (-0.0, "cb8000000000000000"),
    ]

    for value, expected_hex in test_cases:
        message_packer.pack(value)
        packed_bytes: bytes = message_packer.get_buffer()
        assert packed_bytes.hex() == expected_hex, f"Failed for value: {value!r}"
        message_packer.clear()


def test_list(message_packer: MsgPackHandler) -> None:
    """Tests the expected hex output for packing lists."""
    test_cases: list[tuple[list, str]] = [
        ([], "90"),
        ([1, 2, 3], "93010203"),
        (["a", "b", "c"], "93a161a162a163"),
        ([1, "two", 3.0], "9301a374776fcb4008000000000000"),
    ]

    for value, expected_hex in test_cases:
        message_packer.pack(value)
        packed_bytes: bytes = message_packer.get_buffer()
        assert packed_bytes.hex() == expected_hex, f"Failed for value: {value!r}"
        message_packer.clear()


def test_dict(message_packer: MsgPackHandler) -> None:
    """Tests the expected hex output for packing dictionaries."""
    test_cases: list[tuple[dict, str]] = [
        ({}, "80"),
        ({"a": 1, "b": 2}, "82a16101a16202"),
        ({"key": "value", "num": 42}, "82a36b6579a576616c7565a36e756d2a"),
    ]

    for value, expected_hex in test_cases:
        message_packer.pack(value)
        packed_bytes: bytes = message_packer.get_buffer()
        assert packed_bytes.hex() == expected_hex, f"Failed for value: {value!r}"
        message_packer.clear()


def test_nested_structures(message_packer: MsgPackHandler) -> None:
    """Tests the expected hex output for packing nested structures."""
    test_cases: list[tuple[object, str]] = [
        ({"list": [1, 2, {"key": "value"}]}, "81a46c69737493010281a36b6579a576616c7565"),
        ([{"a": 1}, {"b": 2}], "9281a1610181a16202"),
    ]

    for value, expected_hex in test_cases:
        message_packer.pack(value)
        packed_bytes: bytes = message_packer.get_buffer()
        assert packed_bytes.hex() == expected_hex, f"Failed for value: {value!r}"
        message_packer.clear()
