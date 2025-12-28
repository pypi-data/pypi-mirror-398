from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from functools import cached_property, partial
from pathlib import Path  # noqa: TC003
import statistics
from typing import TYPE_CHECKING, Any, Literal
from xml.etree.ElementTree import Element, ElementTree

from rich.color_triplet import ColorTriplet

from codec_cub.jsonl.file_handler import JSONLFileHandler
from codec_cub.jsons.file_handler import JSONFileHandler
from codec_cub.message_pack.file_handler import MsgPackFileHandler
from codec_cub.nix.file_handler import NixFileHandler
from codec_cub.text.file_handler import TextFileHandler
from codec_cub.toml.file_handler import TomlFileHandler, TomlWriteOpts
from codec_cub.toon.file_handler import ToonFileHandler
from codec_cub.xmls.file_handler import XMLFileHandler
from codec_cub.yamls.file_handler import YamlFileHandler

if TYPE_CHECKING:
    from codec_cub.general.base_file_handler import BaseFileHandler

Primitive = str | int | float | bool | None
CodecData = dict[str, dict[str, Primitive] | list[Primitive | dict[str, Primitive]] | Primitive]
Arrows = Literal["↓ ", "↑ ", ""]
DEFAULT_COLOR = ColorTriplet(255, 255, 255)


def touch(path: Path, exist_ok: bool = True) -> None:
    """Create the file at the given path if it does not exist."""
    if not path.exists():
        path.touch(exist_ok=exist_ok)


@dataclass
class _CodecRunner:
    """Internal helper describing how to profile one codec."""

    name: str
    path: Path
    ext: str | None = None
    _write_kwargs: dict[str, Any] | None = None
    _read_kwargs: dict[str, Any] | None = None
    _write_handler: Callable[..., BaseFileHandler] | None = None
    _read_handler: Callable[..., BaseFileHandler] | None = None
    _prepare: Callable[[CodecData], Any] | None = None
    _read_helper: Callable[[Any], Any] | None = None

    @cached_property
    def write_handler(self) -> BaseFileHandler:
        """Get the write handler."""
        if self._write_handler is None:
            raise ValueError("Write handler is not defined.")
        return self._write_handler(self.file_path)

    @cached_property
    def read_handler(self) -> BaseFileHandler:
        """Get the read handler."""
        if self._read_handler is None:
            raise ValueError("Read handler is not defined.")
        return self._read_handler(self.file_path)

    @property
    def size(self) -> int:
        """Get the size of the file used by the codec."""
        return self.file_path.stat().st_size if self.file_path.exists() else 0

    @property
    def extension(self) -> str:
        """Get the file extension used by the handlers."""
        return self.ext or self.name

    @property
    def file_path(self) -> Path:
        """Get the file path used by the handlers."""
        return self.path / f"{self.name}_codec.{self.extension}"

    @property
    def write_kwargs(self) -> dict[str, Any]:
        """Get the keyword arguments for the handlers."""
        return self._write_kwargs if self._write_kwargs is not None else {}

    @property
    def read_kwargs(self) -> dict[str, Any]:
        """Get the keyword arguments for the handlers."""
        return self._read_kwargs if self._read_kwargs is not None else {}

    def write(self, payload: Any) -> None:
        """Write data to the given path using this codec."""
        if self._write_handler is None:
            raise ValueError("Write handler is not defined.")

        self.write_handler.write(payload, **self.write_kwargs)

    def read(self) -> Any:
        """Read data from the given path using this codec."""
        if self._read_handler is None:
            raise ValueError("Read handler is not defined.")
        if self._read_helper:
            raw_value: Any = self.read_handler.read(**self.read_kwargs)
            return self._read_helper(raw_value)
        return self.read_handler.read(**self.read_kwargs)

    def prepare(self, data: CodecData) -> Any:
        """Prepare data for writing using this codec."""
        if self._prepare is None:
            raise ValueError("Prepare function is not defined.")
        return self._prepare(data)

    def close(self) -> None:
        """Close the file handlers."""
        if "write_handler" in self.__dict__:
            self.write_handler.close()
            self.__dict__.pop("write_handler")
        if "read_handler" in self.__dict__:
            self.read_handler.close()
            self.__dict__.pop("read_handler")


def _codec_definitions(base_dir: Path) -> dict[str, _CodecRunner]:
    import json  # noqa: PLC0415

    codecs: dict[str, _CodecRunner] = {}

    pass_through_partial = partial(lambda x: x)
    json_codec = _CodecRunner(
        name="json",
        path=base_dir,
        _write_handler=partial(JSONFileHandler, mode="r+", touch=True),
        _read_handler=partial(JSONFileHandler, mode="r+"),
        _prepare=pass_through_partial,
    )
    codecs[json_codec.name] = json_codec

    jsonl_codec = _CodecRunner(
        name="jsonl",
        path=base_dir,
        _write_handler=partial(JSONLFileHandler, touch=True),
        _read_handler=partial(JSONLFileHandler),
        _prepare=lambda data: [data],
    )
    codecs[jsonl_codec.name] = jsonl_codec

    yaml_codec = _CodecRunner(
        name="yaml",
        path=base_dir,
        ext="yml",
        _write_handler=partial(YamlFileHandler, touch=True),
        _read_handler=partial(YamlFileHandler),
        _prepare=pass_through_partial,
    )
    codecs[yaml_codec.name] = yaml_codec

    toml_codec = _CodecRunner(
        name="toml",
        path=base_dir,
        _write_handler=partial(TomlFileHandler, touch=True),
        _read_handler=partial(TomlFileHandler),
        _write_kwargs={"write_opts": TomlWriteOpts.CONVERT_NONE},
        _read_kwargs={"convert_none": TomlWriteOpts.CONVERT_NONE},
    )
    toml_codec._prepare = pass_through_partial
    codecs[toml_codec.name] = toml_codec

    nix_codec = _CodecRunner(
        name="nix",
        path=base_dir,
        _write_handler=partial(NixFileHandler, touch=True),
        _read_handler=partial(NixFileHandler),
        _prepare=pass_through_partial,
    )
    codecs[nix_codec.name] = nix_codec

    msgpack_codec = _CodecRunner(
        name="msgpack",
        path=base_dir,
        _write_handler=partial(MsgPackFileHandler, touch=True),
        _read_handler=partial(MsgPackFileHandler),
        _prepare=pass_through_partial,
    )
    codecs[msgpack_codec.name] = msgpack_codec

    toon_codec = _CodecRunner(
        name="toon",
        path=base_dir,
        _write_handler=partial(ToonFileHandler, touch=True),
        _read_handler=partial(ToonFileHandler),
        _prepare=pass_through_partial,
    )
    codecs[toon_codec.name] = toon_codec

    xml_codec = _CodecRunner(
        name="xml",
        path=base_dir,
        _write_handler=partial(XMLFileHandler, touch=True),
        _read_handler=partial(XMLFileHandler),
        _prepare=_dict_to_xml,
        _read_helper=_xml_to_dict,
    )
    codecs[xml_codec.name] = xml_codec

    text_codec = _CodecRunner(
        name="text",
        path=base_dir,
        ext="txt",
        _write_handler=partial(TextFileHandler, mode="w+", touch=True),
        _read_handler=partial(TextFileHandler, mode="r+"),
        _prepare=json.dumps,
        _read_helper=json.loads,
    )
    codecs[text_codec.name] = text_codec
    return codecs


ALL_CODECS: set[str] = {
    "json",
    "jsonl",
    "yaml",
    "toml",
    "nix",
    "msgpack",
    "toon",
    "xml",
    "text",
    "none",
}


@dataclass
class ProfileResult:
    """Timing information for a single codec."""

    name: str
    time_unit: str = "us"
    runs: int = 1
    total_write_seconds: float = 0.0
    total_read_seconds: float = 0.0
    write_times: list[float] = field(default_factory=list)
    read_times: list[float] = field(default_factory=list)

    _read_color: str = DEFAULT_COLOR.rgb
    _write_color: str = DEFAULT_COLOR.rgb
    _size_color: str = DEFAULT_COLOR.rgb

    size_bytes: int = 0
    error: str | None = None

    @cached_property
    def _time_multiplier(self) -> int:
        """Get the multiplier for converting seconds to the target unit."""
        return {"s": 1, "ms": 1000, "us": 1_000_000}[self.time_unit]

    @cached_property
    def _variance_multiplier(self) -> int:
        """Get the multiplier for converting variance to the target unit²."""
        return self._time_multiplier**2

    def _convert_time(self, t: float) -> float:
        """Convert time from seconds to configured unit."""
        return t * self._time_multiplier

    def _convert_variance(self, v: float) -> float:
        """Convert variance from seconds² to configured unit²."""
        return v * self._variance_multiplier

    @property
    def write_ms(self) -> float:
        """Get the write time in milliseconds."""
        return self.total_write_seconds * 1000

    @property
    def read_ms(self) -> float:
        """Get the read time in milliseconds."""
        return self.total_read_seconds * 1000

    @property
    def write_per_run_ms(self) -> float:
        """Get the average write time per run in milliseconds."""
        return (self.total_write_seconds / self.runs) * 1000

    @property
    def read_per_run_ms(self) -> float:
        """Get the average read time per run in milliseconds."""
        return (self.total_read_seconds / self.runs) * 1000

    @property
    def write_throughput_mbs(self) -> float:
        """Get write throughput in MB/s."""
        if self.total_write_seconds == 0:
            return 0.0
        return (self.size_bytes / 1024 / 1024) / (self.total_write_seconds / self.runs)

    @property
    def read_throughput_mbs(self) -> float:
        """Get read throughput in MB/s."""
        if self.total_read_seconds == 0:
            return 0.0
        return (self.size_bytes / 1024 / 1024) / (self.total_read_seconds / self.runs)

    @cached_property
    def write_avg(self) -> float:
        """Get the average write time per run."""
        return self._convert_time(self.total_write_seconds / self.runs)

    @cached_property
    def read_avg(self) -> float:
        """Get the average read time per run."""
        return self._convert_time(self.total_read_seconds / self.runs)

    @cached_property
    def write_min(self) -> float:
        """Get the minimum write time."""
        return self._convert_time(min(self.write_times)) if self.write_times else 0.0

    @cached_property
    def write_max(self) -> float:
        """Get the maximum write time."""
        return self._convert_time(max(self.write_times)) if self.write_times else 0.0

    @cached_property
    def read_min(self) -> float:
        """Get the minimum read time."""
        return self._convert_time(min(self.read_times)) if self.read_times else 0.0

    @cached_property
    def read_max(self) -> float:
        """Get the maximum read time."""
        return self._convert_time(max(self.read_times)) if self.read_times else 0.0

    @cached_property
    def write_median(self) -> float:
        """Get the median write time."""
        return self._convert_time(statistics.median(self.write_times)) if self.write_times else 0.0

    @cached_property
    def read_median(self) -> float:
        """Get the median read time."""
        return self._convert_time(statistics.median(self.read_times)) if self.read_times else 0.0

    @cached_property
    def write_std_dev(self) -> float:
        """Get the standard deviation of write times."""
        return self._convert_time(statistics.stdev(self.write_times)) if len(self.write_times) > 1 else 0.0

    @cached_property
    def read_std_dev(self) -> float:
        """Get the standard deviation of read times."""
        return self._convert_time(statistics.stdev(self.read_times)) if len(self.read_times) > 1 else 0.0

    @cached_property
    def write_variance(self) -> float:
        """Get the variance of write times."""
        return self._convert_variance(statistics.variance(self.write_times)) if len(self.write_times) > 1 else 0.0

    @cached_property
    def read_variance(self) -> float:
        """Get the variance of read times."""
        return self._convert_variance(statistics.variance(self.read_times)) if len(self.read_times) > 1 else 0.0

    @cached_property
    def slowest_reads(self) -> list[float]:
        """Get the slowest read times."""
        return sorted(self.read_times, reverse=True)[: max(1, len(self.read_times) // 25)]

    @cached_property
    def slowest_writes(self) -> list[float]:
        """Get the slowest write times."""
        return sorted(self.write_times, reverse=True)[: max(1, len(self.write_times) // 25)]

    @cached_property
    def fastest_reads(self) -> list[float]:
        """Get the fastest read times."""
        return sorted(self.read_times)[: max(1, len(self.read_times) // 25)]

    @cached_property
    def fastest_writes(self) -> list[float]:
        """Get the fastest write times."""
        return sorted(self.write_times)[: max(1, len(self.write_times) // 25)]


def _dict_to_xml(data: Mapping[str, Any] | list[Any] | Primitive, *, root: str = "root") -> ElementTree:
    root_element: Element = Element(root)
    _encode_xml_value(root_element, data)
    return ElementTree(root_element)


def _encode_xml_value(element: Element, value: Mapping[str, Any] | list[Any] | Primitive) -> None:
    if isinstance(value, Mapping):
        for key, val in value.items():
            child = Element(str(key))
            _encode_xml_value(child, val)
            element.append(child)
        return
    if isinstance(value, list):
        for item in value:
            child = Element("item")
            _encode_xml_value(child, item)
            element.append(child)
        return
    _encode_primitive(element, value)


def _prim(element: Element, types: str, value: str) -> None:
    element.set("type", types)
    element.text = value


def _encode_primitive(element: Element, value: Primitive) -> None:
    if value is None:
        return _prim(element, "none", "")
    if isinstance(value, bool):
        return _prim(element, "bool", "true" if value else "false")
    if isinstance(value, int):
        return _prim(element, "int", str(value))
    if isinstance(value, float):
        return _prim(element, "float", repr(value))
    return _prim(element, "str", str(value))


def _xml_to_dict(tree: ElementTree) -> Any:
    return _decode_xml_value(tree.getroot())  # pyright: ignore[reportArgumentType]


def _decode_xml_value(element: Element) -> Any:
    children: list[Element] = list(element)
    if not children:
        return _decode_primitive(element.text or "", element.get("type", "str"))
    if all(child.tag == "item" for child in children):
        return [_decode_xml_value(child) for child in children]
    return {child.tag: _decode_xml_value(child) for child in children}


def _decode_primitive(text: Any, value_type: str) -> Primitive:
    if value_type == "none":
        return None
    if value_type == "bool":
        return text.lower() == "true"
    if value_type == "int":
        return int(text)
    if value_type == "float":
        return float(text)
    return text


@dataclass
class SetupReturn:
    """Return value for setup functions."""

    codec_map: dict[str, _CodecRunner] = field(default_factory=dict)
    sample_data: CodecData = field(default_factory=dict)
    runs: int = 0
