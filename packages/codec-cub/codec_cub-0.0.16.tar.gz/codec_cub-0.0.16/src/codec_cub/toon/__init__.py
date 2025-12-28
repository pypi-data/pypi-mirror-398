"""An implementation of Token-Oriented Object Notation (TOON) codec.

Token-Oriented Object Notation (TOON) is a line-oriented, indentation-based text format
that encodes the JSON data model with explicit structure and minimal quoting.

Example:
    JSON input:
    {
      "users": [
        { "id": 1, "name": "Alice", "role": "admin" },
        { "id": 2, "name": "Bob", "role": "user" }
      ]
    }

    TOON conveys the same information with fewer tokens:
    users[2]{id,name,role}:
      1,Alice,admin
      2,Bob,user

Usage:
    >>> from codec_cub.toon import ToonCodec
    >>> codec = ToonCodec()
    >>> data = {"name": "Ada", "tags": ["python", "toon"]}
    >>> toon_str = codec.encode(data)
    >>> decoded = codec.decode(toon_str)

See Also:
    - Specification: https://github.com/toon-format/spec
    - ToonCodec: Main codec class
    - ToonCodecConfig: Configuration options
"""

from codec_cub.toon.builder import tabular, toon_dumps
from codec_cub.toon.codec import ToonCodec
from codec_cub.toon.file_handler import ToonFileHandler

__all__ = ["ToonCodec", "ToonFileHandler", "tabular", "toon_dumps"]
