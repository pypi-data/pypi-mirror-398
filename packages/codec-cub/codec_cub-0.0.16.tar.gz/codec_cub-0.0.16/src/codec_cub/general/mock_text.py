"""A mock TextIO class for testing purposes."""

from threading import RLock
from typing import Any, TextIO

from funcy_bear.tools.names import Names

_lock = RLock()


class MockTextIO(TextIO):
    """A mock TextIO class that captures written output for testing purposes."""

    def __init__(self) -> None:
        """Initialize the mock TextIO."""
        self._buffer: list[str] = []
        self._counters: Names = Names()
        self.num_init = 1

    def __getattr__(self, name: str):
        with _lock:
            if name.startswith("num_"):
                if not hasattr(self._counters, name):
                    self._counters.set(name, 0)
                return getattr(self._counters, name)
            raise AttributeError(f"{self.__class__.__name__} has no attribute {name}")

    def __setattr__(self, attr_name: str, value: int) -> None:
        with _lock:
            if attr_name.startswith("num_"):
                if not self._counters.has(attr_name):
                    self._counters.set(attr_name, 0)
                if not isinstance(value, int) or value < 0:
                    raise ValueError(f"Counter {attr_name} must be a non-negative integer")
                self._counters.set(attr_name, value)
            else:
                super().__setattr__(attr_name, value)

    def write(self, s: Any) -> int:
        """Mock write method that appends to the buffer."""
        with _lock:
            self._buffer.append(s)
            self.num_write += 1
            return self.num_write

    def read(self, _: int = -1) -> str:
        """Mock read method that returns an empty string."""
        self.num_read += 1
        return " ".join(self._buffer)

    def output_buffer(self) -> list[str]:
        """Get the output buffer."""
        self.num_output_buffer += 1
        return self._buffer

    def clear(self) -> None:
        """Clear the output buffer."""
        self.num_clear += 1
        self._buffer.clear()

    def flush(self) -> None:
        """Mock flush method that does nothing."""
        self.num_flush += 1
        self._buffer.clear()

    def close(self) -> None:
        """Mock close method that does nothing."""
        self.num_close += 1

    def report(self) -> str:
        """Generate a report of method call counts."""
        info_dump: list[tuple[str, int]] = self._counters.items()
        return "\n".join([f"{name}: {count}" for name, count in info_dump])


__all__ = ["MockTextIO"]
