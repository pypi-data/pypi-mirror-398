"""Codec Cub package.

Parsing shit and shit
"""

from codec_cub._internal.cli import main
from codec_cub._internal.debug import METADATA

__version__: str = METADATA.version


__all__: list[str] = ["METADATA", "__version__", "main"]
