"""JSON file handler built on top of TextFileHandler.

This handler is intentionally format-agnostic at the IO layer. It exposes
read_text/write_text for JSON storage to perform serialization separately.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, overload

from lazy_bear import LazyLoader

from codec_cub.text.file_handler import TextFileHandler
from funcy_bear.constants.type_constants import JSONLike, LitFalse, LitTrue

if TYPE_CHECKING:
    import json

    from funcy_bear.constants.type_constants import StrPath
else:
    json = LazyLoader("json")


class JSONFileHandler(TextFileHandler):
    """Thin subclass for semantic clarity (JSON full-text IO)."""

    def __init__(
        self,
        file: StrPath,
        mode: str = "r+",
        encoding: str = "utf-8",
        touch: bool = False,
    ) -> None:
        """Initialize the JSON file handler.

        Args:
            file: Path to the JSON file
            mode: File open mode (default: "r+")
            encoding: File encoding (default: "utf-8")
            touch: Whether to create the file if it doesn't exist (default: False)
        """
        super().__init__(file=file, mode=mode, encoding=encoding, touch=touch)

    def write(self, data: Any, **kwargs) -> None:
        """Write a Python object as JSON to the file."""
        if isinstance(data, JSONLike):
            string: str = json.dumps(data, **kwargs)
        else:
            string = str(data)
        super().write(string)

    @overload
    def read(self, as_json: LitTrue = True) -> JSONLike: ...

    @overload
    def read(self, as_json: LitFalse) -> str: ...

    def read(self, as_json: bool = True, **kwargs) -> str | JSONLike | None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Read the raw text content of the file or parse as JSON if specified."""
        string: str = super().read()
        if string and as_json:
            return json.loads(string, **kwargs)
        return string if string else None

    def to_string(self, **kwargs) -> str:
        """Return the raw text content of the file."""
        string: str = self.read(as_json=False)
        return json.dumps(json.loads(string), **kwargs) if string else ""

    def to_json(self) -> JSONLike | None:
        """Return the JSON content of the file as a Python object."""
        value: JSONLike = self.read(as_json=True)
        return value if isinstance(value, JSONLike) else None


__all__ = ["JSONFileHandler"]
