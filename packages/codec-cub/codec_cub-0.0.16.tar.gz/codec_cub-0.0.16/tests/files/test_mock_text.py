"""Minimal tests for MockTextIO test helper."""

import pytest

from codec_cub.general.mock_text import MockTextIO


class TestMockTextIOBasics:
    """Test basic MockTextIO functionality."""

    def test_initialization(self):
        """Test MockTextIO initializes correctly."""
        mock = MockTextIO()
        assert mock.num_init == 1
        assert mock.output_buffer() == []

    def test_write(self):
        """Test write method captures output."""
        mock = MockTextIO()
        mock.write("Hello")
        mock.write("World")

        assert "Hello" in mock.output_buffer()
        assert "World" in mock.output_buffer()
        assert mock.num_write == 2

    def test_read(self) -> None:
        """Test read method returns joined buffer."""
        mock = MockTextIO()
        mock.write("Hello")
        mock.write("World")

        result: str = mock.read()
        assert result == "Hello World"
        assert mock.num_read == 1

    def test_clear(self) -> None:
        """Test clear empties the buffer."""
        mock = MockTextIO()
        mock.write("test")
        mock.clear()

        assert mock.output_buffer() == []
        assert mock.num_clear == 1

    def test_flush(self) -> None:
        """Test flush clears the buffer."""
        mock = MockTextIO()
        mock.write("test")
        mock.flush()

        assert mock.output_buffer() == []
        assert mock.num_flush == 1

    def test_close(self) -> None:
        """Test close method increments counter."""
        mock = MockTextIO()
        mock.close()
        assert mock.num_close == 1

    def test_report(self) -> None:
        """Test report generates summary of calls."""
        mock = MockTextIO()
        mock.write("test")
        mock.read()
        mock.flush()

        report: str = mock.report()
        assert "num_write" in report
        assert "num_read" in report
        assert "num_flush" in report


class TestMockTextIOCounters:
    """Test counter functionality."""

    def test_custom_counter_creation(self) -> None:
        """Test creating custom counter."""
        mock = MockTextIO()
        mock.num_custom = 5
        assert mock.num_custom == 5

    def test_counter_increment(self) -> None:
        """Test counter can be incremented."""
        mock = MockTextIO()
        mock.num_test = 0
        mock.num_test += 1
        assert mock.num_test == 1

    def test_invalid_counter_value(self) -> None:
        """Test setting counter to invalid value raises error."""
        mock = MockTextIO()
        with pytest.raises(ValueError, match="must be a non-negative integer"):
            mock.num_bad = -1

    def test_invalid_counter_type(self) -> None:
        """Test setting counter to non-int raises error."""
        mock = MockTextIO()
        with pytest.raises(ValueError, match="must be a non-negative integer"):
            mock.num_bad = "not an int"  # type: ignore[assignment]

    def test_nonexistent_attribute(self) -> None:
        """Test accessing nonexistent attribute raises AttributeError."""
        mock = MockTextIO()
        with pytest.raises(AttributeError):
            _ = mock.nonexistent_attr
