"""File handler for Nix files."""

from __future__ import annotations

from typing import IO, TYPE_CHECKING, Any

from lazy_bear import lazy

from codec_cub.general.base_file_handler import BaseFileHandler
from funcy_bear.constants.type_constants import StrPath  # noqa: TC001

from .codec import NixCodec, NixCodecConfig

if TYPE_CHECKING:
    from codec_cub.general.file_lock import LockExclusive, LockShared
else:
    LockExclusive, LockShared = lazy("codec_cub.general.file_lock").to("LockExclusive", "LockShared")


type AllObjs = str | int | float | bool | dict[str, Any] | list[Any]

type NixData = AllObjs | None | list[AllObjs] | dict[str, AllObjs]


class NixFileHandler(BaseFileHandler[NixData]):
    """File handler for Nix files with locking and codec integration.

    Supports reading and writing Python objects to Nix expression syntax.
    Uses shared locks for reads and exclusive locks for writes to enable
    safe concurrent access.
    """

    def __init__(
        self,
        file: StrPath,
        touch: bool = False,
        codec: NixCodec | None = None,
        config: NixCodecConfig | None = None,
    ) -> None:
        """Initialize NixFileHandler.

        Args:
            file: Path to the Nix file
            touch: Whether to create the file if it doesn't exist (default: False)
            codec: Optional NixCodec instance to use (default: None)
            config: Optional NixCodecConfig for codec configuration (default: None)
        """
        super().__init__(file, mode="r+", encoding="utf-8", touch=touch)
        self._config: NixCodecConfig = config or NixCodecConfig()
        self._codec: NixCodec = codec or NixCodec(config=self._config)

    def set_codec(self, codec: NixCodec) -> None:
        """Set a custom NixCodec for the file handler.

        Args:
            codec: NixCodec instance to use for encoding/decoding
        """
        self._codec = codec

    def set_config(self, config: NixCodecConfig) -> None:
        """Set a custom NixCodecConfig and update the codec accordingly.

        Args:
            config: NixCodecConfig instance to use for codec configuration
        """
        self.update_config(**config.to_dict())

    def update_config(self, **kwargs: Any) -> None:
        """Update the NixCodecConfig with new parameters and refresh the codec.

        Updating the configuration here will implicitly update the codec and other
        dependent components to ensure consistency. This is how objects work in Python.

        Args:
            **kwargs: Configuration parameters to update in NixCodecConfig
        """
        self._config.update(**kwargs)

    def read(self, **kwargs) -> NixData | None:  # noqa: ARG002
        """Read and decode Nix file content.

        Returns:
            Decoded Python objects from the Nix file or None if the file is empty
        """
        handle: IO | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")

        with LockShared(handle):
            handle.seek(0)
            data: str = handle.read()
            if not data.strip():
                return None
            return self._codec.decode(data)

    def write(self, data: NixData, **kwargs) -> None:  # noqa: ARG002
        """Encode and write data to Nix file.

        Args:
            data: Python objects to encode and write to the file
        Raises:
            ValueError: If encoding fails
        """
        handle: IO | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        try:
            encoded_data: str = self._codec.encode(data)
        except Exception as e:
            raise ValueError(f"Failed to encode data to Nix format: {e}") from e
        with LockExclusive(handle):
            handle.seek(0)
            handle.truncate(0)
            handle.write(encoded_data)
            handle.flush()


__all__ = ["NixData", "NixFileHandler"]
