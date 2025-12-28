"""TOON codec implementation.

Token-Oriented Object Notation (TOON) is a line-oriented, indentation-based text format
that encodes the JSON data model with explicit structure and minimal quoting.

TOON is particularly efficient for arrays of uniform objects, providing compact
representation with explicit lengths and field declarations.

Example:
    >>> from codec_cub.toon.codec import ToonCodec
    >>> from codec_cub.config import ToonCodecConfig
    >>>
    >>> # Create codec with default configuration
    >>> codec = ToonCodec()
    >>>
    >>> # Encode Python data to TOON
    >>> data = {
    ...     "users": [
    ...         {"id": 1, "name": "Alice", "role": "admin"},
    ...         {"id": 2, "name": "Bob", "role": "user"},
    ...     ]
    ... }
    >>> toon_str = codec.encode(data)
    >>> print(toon_str)
    users[2]{id,name,role}:
      1,Alice,admin
      2,Bob,user
    >>>
    >>> # Decode TOON back to Python
    >>> decoded = codec.decode(toon_str)
    >>> assert decoded == data

See Also:
    - Specification: https://github.com/toon-format/spec
    - ToonCodecConfig: Configuration options for encoding/decoding
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from codec_cub.config import ToonCodecConfig


class ToonCodec:
    r"""Encode and decode TOON (Token-Oriented Object Notation) format.

    This codec implements the TOON v2.0 specification, providing bidirectional
    conversion between Python objects and TOON text format.

    TOON Format Overview:
        - Objects: key: value with indentation-based nesting
        - Arrays: Explicit length declarations [N]
        - Tabular: Uniform object arrays with field lists {f1,f2}
        - Delimiters: Comma (default), tab, or pipe
        - Quoting: Minimal, context-aware quoting rules

    The codec normalizes Python values to the JSON data model:
        - None, NaN, ±Infinity → null
        - bool → true/false
        - int, float → canonical decimal (no exponents, no trailing zeros)
        - str → quoted when necessary
        - list → array
        - dict → object (key order preserved)

    Attributes:
        config: Configuration options for encoding/decoding

    Example:
        >>> # Basic usage with default config
        >>> codec = ToonCodec()
        >>> codec.encode({"name": "Ada", "active": True})
        'name: Ada\\nactive: true'

        >>> # Custom configuration
        >>> from codec_cub.config import ToonCodecConfig
        >>> config = ToonCodecConfig(delimiter="\\t", indent_spaces=4)
        >>> codec = ToonCodec(config)
    """

    def __init__(self, config: ToonCodecConfig | None = None) -> None:
        """Initialize ToonCodec with optional configuration.

        Args:
            config: Optional ToonCodecConfig. If None, uses default configuration.
        """
        from codec_cub.config import ToonCodecConfig  # noqa: PLC0415

        self._cfg: ToonCodecConfig = config if config is not None else ToonCodecConfig()

    @property
    def config(self) -> ToonCodecConfig:
        """Get the codec configuration."""
        return self._cfg

    def encode(self, obj: Any) -> str:
        """Encode a Python object to TOON format string.

        The encoder normalizes non-JSON values to the JSON data model before encoding:
            - Numbers: NaN/Infinity → null, -0 → 0
            - Finite numbers: Canonical decimal form (no exponents)
            - Objects: Key order preserved
            - Arrays: Tabular format when uniform objects with primitives

        Args:
            obj: Python object to encode (dict, list, primitive, or None)

        Returns:
            TOON formatted string

        Raises:
            ValueError: For unsupported types or encoding errors

        Example:
            >>> codec = ToonCodec()
            >>> data = {"tags": ["web", "api"], "count": 2}
            >>> print(codec.encode(data))
            tags[2]: web,api
            count: 2
        """
        from codec_cub.toon.encoder import ToonEncoder  # noqa: PLC0415

        encoder = ToonEncoder(self._cfg)
        return encoder.encode(obj)

    def decode(self, text: str) -> Any:
        r"""Decode a TOON format string to Python object.

        The decoder interprets TOON text according to the specification:
            - Quoted strings: Unescaped per §7.1 (only \\, \", \\n, \\r, \\t valid)
            - Unquoted tokens: true/false/null → bool/None, numeric → int/float, else → str
            - Arrays: Length declarations validated in strict mode
            - Objects: Indentation-based nesting

        Args:
            text: TOON formatted string

        Returns:
            Python object (dict, list, or primitive)

        Raises:
            ValueError: For invalid TOON syntax, malformed strings, or strict mode violations

        Example:
            >>> codec = ToonCodec()
            >>> toon = '''users[2]{id,name}:
            ...   1,Alice
            ...   2,Bob'''
            >>> data = codec.decode(toon)
            >>> data
            {'users': [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]}
        """
        from codec_cub.toon.decoder import ToonDecoder  # noqa: PLC0415

        decoder = ToonDecoder(self._cfg)
        return decoder.decode(text)

    def encode_to_file(self, obj: Any, file_path: str) -> None:
        """Encode object and write to file.

        Args:
            obj: Python object to encode
            file_path: Path to output file

        Example:
            >>> codec = ToonCodec()
            >>> codec.encode_to_file({"status": "ok"}, "output.toon")
        """
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.encode(obj))

    def decode_from_file(self, file_path: str | Path) -> Any:
        """Read and decode TOON file.

        Args:
            file_path: Path to input file

        Returns:
            Decoded Python object

        Example:
            >>> codec = ToonCodec()
            >>> data = codec.decode_from_file("input.toon")
        """
        return self.decode(Path(file_path).read_text(encoding="utf-8"))


__all__ = ["ToonCodec"]
