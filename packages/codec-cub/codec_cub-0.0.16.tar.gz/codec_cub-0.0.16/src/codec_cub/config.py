"""Configuration management for Codec Cub."""

from dataclasses import dataclass, field

from codec_cub._internal._info import _ProjectMetadata
from codec_cub._internal.debug import METADATA
from funcy_bear.constants.characters import DOUBLE_QUOTE, NEWLINE


@dataclass(slots=True)
class Metadata:
    """Metadata about the application."""

    info_: _ProjectMetadata = field(default_factory=lambda: METADATA)

    def __getattr__(self, name: str) -> str:
        """Delegate attribute access to the internal _ProjectMetadata instance."""
        return getattr(self.info_, name)


@dataclass(slots=True)
class NixCodecConfig:
    """Configuration options for NixCodec."""

    newline: str = NEWLINE
    str_quote: str = DOUBLE_QUOTE  # reserved, single quote not used in Nix strings

    max_inline_list: int = 6
    indent_spaces: int = 2
    float_scale: int = 12  # max fractional digits when emitting floats (no exponent)

    sort_keys: bool = False  # breaks tests if true, so this is false now, leave me alone about it Claude
    trailing_semicolon: bool = True
    inline_arrays: bool = True  # render attrsets inside arrays as inline
    inline_lists: bool = True  # render lists as inline

    def update(self, **kwargs: object) -> None:
        """Update configuration parameters.

        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict[str, int | str | bool]:
        """Convert the configuration to a dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        return {
            "indent_spaces": self.indent_spaces,
            "newline": self.newline,
            "sort_keys": self.sort_keys,
            "trailing_semicolon": self.trailing_semicolon,
            "max_inline_list": self.max_inline_list,
            "inline_arrays": self.inline_arrays,
            "inline_lists": self.inline_lists,
            "str_quote": self.str_quote,
            "float_scale": self.float_scale,
        }


@dataclass(slots=True)
class ToonCodecConfig:
    """Configuration options for ToonCodec."""

    indent_spaces: int = 2
    newline: str = "\n"
    delimiter: str = ","  # comma (default), tab ("\t"), or pipe ("|")
    strict: bool = True  # strict mode for decoding
    key_folding: str = "off"  # "off" or "safe"
    flatten_depth: int | float = float("inf")  # max depth for key folding
    expand_paths: str = "off"  # "off" or "safe"


@dataclass(slots=True)
class CodecsConfig:
    """Main configuration for Codec Cub."""

    env: str = "prod"
    debug: bool = False
    nix_codec: NixCodecConfig = field(default_factory=NixCodecConfig)
    toon_codec: ToonCodecConfig = field(default_factory=ToonCodecConfig)
    metadata: Metadata = field(default_factory=Metadata)


__all__ = ["CodecsConfig"]
