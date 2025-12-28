from pathlib import Path

from codec_cub.text.bytes_handler import BytesFileHandler


def test_bytes_file_handler_read_write(tmp_path: Path) -> None:
    """Test the BytesFileHandler read and write methods."""
    file_path: Path = tmp_path / "test_bytes_file.bin"
    handler = BytesFileHandler(file=file_path, touch=True)

    # Write bytes to the file
    data_to_write = b"Hello, Bear Dereth!"
    handler.write(data=data_to_write)

    # Read bytes from the file
    read_data: bytes = handler.read()
    assert read_data == data_to_write, "Read data does not match written data."
    handler.clear()


def test_bytes_file_handler_partial_read(tmp_path: Path) -> None:
    """Test the BytesFileHandler partial read method."""
    file_path: Path = tmp_path / "test_bytes_file_partial.bin"
    handler = BytesFileHandler(file=file_path, touch=True)

    # Write bytes to the file
    data_to_write = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    handler.write(data=data_to_write)

    # Read first 10 bytes from the file
    read_data: bytes = handler.read(n=10)
    assert read_data == b"ABCDEFGHIJ", "Partial read data does not match expected data."
    handler.clear()


def test_bytes_file_handler_clear(tmp_path: Path) -> None:
    """Test the BytesFileHandler clear method."""
    file_path: Path = tmp_path / "test_bytes_file_clear.bin"
    handler = BytesFileHandler(file=file_path, touch=True)

    empty_read: bytes = handler.read()
    assert empty_read == b"", "File should be empty after initialization."
    # file will be here since our handler was initialized with touch=True
    assert file_path.exists(), "File should exist after initialization."

    # Write bytes to the file
    data_to_write = b"Data to be cleared."
    handler.write(data=data_to_write)

    # Clear the file
    handler.clear()

    # Read from the file to ensure it's empty
    read_data: bytes = handler.read()
    assert read_data == b"", "File was not cleared properly."


def test_bytes_file_handler_lazy_open(tmp_path: Path) -> None:
    """Test that the BytesFileHandler lazily opens the file."""
    file_path: Path = tmp_path / "test_bytes_file_lazy.bin"
    handler = BytesFileHandler(file=file_path, touch=False)

    # At this point, the file should not exist
    assert not file_path.exists(), "File should not exist before any operation."

    # Write bytes to the file, which should trigger the lazy open
    data_to_write = b"Lazy open test."
    handler.write(data=data_to_write)

    # Now the file should exist
    assert file_path.exists(), "File should exist after write operation."
    handler.clear()


def test_bytes_file_handler_encoding(tmp_path: Path) -> None:
    """Test the BytesFileHandler with different encodings."""
    file_path: Path = tmp_path / "test_bytes_file_encoding.bin"
    handler = BytesFileHandler(file=file_path, touch=True)

    # Write bytes to the file
    data_to_write: bytes = "こんにちは、ベアデレス!".encode()  # Japanese for "Hello, Bear Dereth!"
    handler.write(data=data_to_write)

    # Read bytes from the file
    read_data: bytes = handler.read()
    assert read_data == data_to_write, "Read data does not match written data with UTF-8 encoding."
    handler.clear()


def test_bytes_file_handler_multiple_writes(tmp_path: Path) -> None:
    """Test multiple write operations on the BytesFileHandler."""
    file_path: Path = tmp_path / "test_bytes_file_multiple_writes.bin"
    handler = BytesFileHandler(file=file_path, touch=True)

    # First write
    first_data: bytes = b"First write."
    handler.write(data=first_data)

    # Second write
    second_data: bytes = b"Second write."
    handler.write(data=second_data)

    # Read bytes from the file
    read_data: bytes = handler.read()
    assert read_data == second_data, "Read data does not match the last written data."
    handler.clear()
