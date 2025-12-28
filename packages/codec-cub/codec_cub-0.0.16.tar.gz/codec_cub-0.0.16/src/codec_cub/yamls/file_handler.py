"""YAML file handler for Bear Dereth."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import IO, TYPE_CHECKING, Any, Self

from yaml import Dumper, FullLoader, YAMLError, dump, load as yaml_load, safe_dump, safe_load

from codec_cub.general.base_file_handler import BaseFileHandler
from codec_cub.general.file_lock import LockExclusive, LockShared


class FlowDict(dict[str, Any]):
    """Dict subclass that renders in YAML flow style {key: value}."""


class CustomDumper(Dumper):
    """Custom YAML dumper with specific formatting options.

    Primarily to allow you to have non-flow style for the majority
    of the YAML, but flow style for specific elements.
    """


CustomDumper.add_representer(
    FlowDict,
    lambda dumper, data: dumper.represent_mapping(
        "tag:yaml.org,2002:map",
        data,
        flow_style=True,
    ),
)


if TYPE_CHECKING:
    from pathlib import Path

YamlData = dict[str, Any]


@dataclass(slots=True)
class YamlConfig:
    safe_mode: bool = True
    """Best practice is to use safe mode to avoid code execution risks but user can opt into unsafe mode."""
    default_flow_style: bool = False
    """Use block (False) or flow (True) style for YAML formatting."""
    sort_keys: bool = False
    """Whether to sort keys on dump."""
    indent: int = 2
    """Number of spaces for indentation."""
    width: int | None = None
    """Preferred line width; None means no limit."""
    allow_unicode: bool = True
    """Allow Unicode characters in output."""
    Dumper: type[CustomDumper] = CustomDumper
    """YAML Dumper class to use."""
    custom_dumper: bool = True
    """Use CustomDumper to support FlowDict."""

    def model_dump(self, exclude: set[str] | None = None, exclude_none: bool = False) -> dict[str, Any]:
        data: dict[str, Any] = asdict(self)
        if exclude_none:
            data = {k: v for k, v in data.items() if v is not None}
        if exclude:
            for key in exclude:
                data.pop(key, None)
        return data


class YamlFileHandler(BaseFileHandler[YamlData]):
    """YAML file handler with safe defaults and formatting options."""

    def __init__(
        self,
        file: Path | str,
        encoding: str = "utf-8",
        safe_mode: bool = True,
        flow_style: bool = False,
        sort_keys: bool = False,
        indent: int = 2,
        width: int | None = None,
        touch: bool = False,
    ) -> None:
        """Initialize the YAML file handler.

        Args:
            path: Path to the YAML file
            encoding: File encoding (default: "utf-8")
            safe_mode: Use safe_load/safe_dump (default: True, recommended)
            flow_style: Use block (False) or flow (True) style (default: False)
            sort_keys: Whether to sort keys on dump (default: False)
            indent: Number of spaces for indentation (default: 2)
            width: Preferred line width (default: None, no limit)
            touch: Whether to create the file if it doesn't exist (default: False)

        Raises:
            ImportError: If PyYAML is not installed
        """
        super().__init__(file, mode="r+", encoding=encoding, touch=touch)
        self.opts = YamlConfig(
            safe_mode=safe_mode,
            default_flow_style=flow_style,
            sort_keys=sort_keys,
            indent=indent,
            width=width,
        )

    def _get_options(self, exclude: set[str] | None = None, exclude_none: bool = False, **kwargs) -> dict[str, Any]:
        """Get YAML dump options as dictionary.

        Args:
            exclude: Set of option names to exclude
            exclude_none: Whether to exclude options with None values
        Returns:
            Dictionary of YAML dump options
        """
        options: dict[str, Any] = self.opts.model_dump(exclude=exclude, exclude_none=exclude_none)
        options.update(kwargs)
        return options

    def read(self, **_) -> dict[str, Any]:
        """Read and parse YAML file.

        Returns:
            Parsed YAML data as dictionary

        Raises:
            yaml.YAMLError: If file contains invalid YAML
            ValueError: If file cannot be read
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        with LockShared(handle):
            handle.seek(0)
            if self.opts.safe_mode:
                data: YamlData = safe_load(handle)
            else:
                # User can opt into unsafe loading if they understand the risks
                data = yaml_load(handle, Loader=FullLoader)  # noqa: S506
            return data or {}

    def write(self, data: YamlData, **kwargs) -> None:
        """Write data as YAML to file.

        Args:
            data: Data to serialize as YAML (must be dict-like)

        Raises:
            yaml.YAMLError: If data cannot be YAML serialized
            ValueError: If file cannot be written
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")

        if not self.opts.safe_mode and self.opts.custom_dumper:
            options: dict[str, Any] = self._get_options(exclude={"safe_mode", "custom_dumper"}, **kwargs)
        else:
            options = self._get_options(exclude={"safe_mode", "custom_dumper", "Dumper"}, **kwargs)

        with LockExclusive(handle):
            try:
                handle.seek(0)
                handle.truncate(0)
                if self.opts.safe_mode:
                    safe_dump(data, handle, **options)
                else:
                    dump(data, handle, **options)
            except YAMLError as e:
                raise ValueError(f"Cannot serialize data to YAML: {e}") from e
            except Exception as e:
                raise ValueError(f"Error writing YAML file {self.file}: {e}") from e

    def to_string(self, data: YamlData | None = None, **kwargs) -> str:
        """Convert data to YAML string without writing to file.

        Args:
            data: Data to serialize (uses cached data if None)

        Returns:
            YAML formatted string

        Raises:
            ValueError: If data cannot be serialized
        """
        to_serialize: YamlData = data if data is not None else self.read()

        if not self.opts.safe_mode and self.opts.custom_dumper:
            options: dict[str, Any] = self._get_options(exclude={"safe_mode", "custom_dumper"}, **kwargs)
        else:
            options: dict[str, Any] = self._get_options(exclude={"safe_mode", "custom_dumper", "Dumper"}, **kwargs)

        try:
            if self.opts.safe_mode:
                return safe_dump(to_serialize, **options)
            return dump(to_serialize, **options)
        except YAMLError as e:
            raise ValueError(f"Cannot serialize data to YAML string: {e}") from e

    def __enter__(self) -> Self:
        """Enter context manager."""
        self.read()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Exit context manager."""
        self.close()


__all__ = ["FlowDict", "YamlData", "YamlFileHandler"]
