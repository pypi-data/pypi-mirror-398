"""Nix codec implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lark.exceptions import LarkError
from lazy_bear import lazy

from codec_cub.config import NixCodecConfig

if TYPE_CHECKING:
    from codec_cub.nix.encoder import _NixEncoder
    from codec_cub.nix.parser import _NixParser
else:
    _NixEncoder = lazy("codec_cub.nix.encoder").to("_NixEncoder")
    _NixParser = lazy("codec_cub.nix.parser").to("_NixParser")


class NixCodec:
    """Encode/decode a pragmatic Nix subset:

    Python → Nix
      None → null
      bool → true/false
      int  → decimal
      float (finite) → decimal/no-exponent; -0.0 => 0; non-finite => null
      str  → "..."
      list/tuple → [ v1 v2 ... ]
      dict[str, Any] → { key = value; ... } with keys as identifiers or strings

    Decoding recognizes the same subset. This does NOT evaluate Nix expressions.
    """

    def __init__(self, config: NixCodecConfig | None = None) -> None:
        """Initialize NixCodec with optional configuration."""
        self._cfg: NixCodecConfig = config or NixCodecConfig()
        self._encoder = _NixEncoder(cfg=self._cfg)
        self._decoder: _NixParser = _NixParser(cfg=self._cfg)

    def update_config(self, **kwargs: Any) -> None:
        """Update the NixCodecConfig with new parameters.

        Args:
            **kwargs: Configuration parameters to update in NixCodecConfig
        """
        self._cfg.update(**kwargs)

    def encode(self, obj: Any) -> str:
        """Encode a Python object to Nix syntax string.

        Args:
            obj: Python object to encode
        Returns:
            Nix syntax string representation of the object
        """
        return self._encoder.encode(obj)

    def decode(self, text: str) -> Any:
        """Decode a Nix syntax string to a Python object.

        Args:
            text: Nix syntax string to decode
            flatten: Whether to flatten nested lists/dicts (default: False)

        Returns:
            Decoded Python object
        """
        try:
            parsed: Any = self._decoder.parse_string(text=text)
        except LarkError as exc:
            raise ValueError(f"Nix parse error: {exc}") from exc
        return parsed
