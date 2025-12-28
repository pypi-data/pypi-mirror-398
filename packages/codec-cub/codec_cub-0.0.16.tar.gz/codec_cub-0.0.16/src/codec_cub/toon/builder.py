"""TOON builder API for manual structure control.

Provides wrappers and functions to force specific encoding formats,
particularly useful for database records where optional fields may be missing
but tabular format is still desired.

Usage Guidelines:
    - Use tabular() when rows have inconsistent fields but you want tabular format
    - Use Tabular.from_rows() to auto-detect all fields from row union
    - Use Tabular.detect() to check if data qualifies for automatic tabular format
    - Let auto-detection work for uniform arrays (no wrapper needed)

Example:
    >>> from codec_cub.toon.builder import tabular, toon_dumps
    >>>
    >>> data = {
    ...     "users": tabular(
    ...         rows=[{"id": 1, "name": "Bear"}, {"id": 2}],
    ...         fields=["id", "name"],
    ...         fill_missing=True,
    ...     )
    ... }
    >>> print(toon_dumps(data))
    users[2]{id,name}:
      1,Bear
      2,null
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from codec_cub.toon.encoder import ToonEncoder
from codec_cub.toon.utils import (
    build_array_header,
    encode_key,
    encode_primitive,
    get_delimiter_char,
    is_primitive_array,
)
from funcy_bear.constants.characters import SPACE

if TYPE_CHECKING:
    from codec_cub.config import ToonCodecConfig


@dataclass(slots=True, frozen=True)
class Tabular:
    """Wrapper to force tabular encoding for a list of dicts.

    When the encoder encounters this wrapper, it will use the specified
    fields to produce tabular format regardless of whether all rows
    have matching keys.

    Also serves as the result type for tabular detection, replacing the
    previous TabularArray NamedTuple.

    Attributes:
        rows: List of dictionaries to encode as tabular rows.
        fields: Field names defining column order.
        fill_missing: If True (default), missing fields are encoded as null.
            If False, raises ValueError for missing fields.
    """

    rows: list[dict[str, Any]]
    fields: list[str]
    fill_missing: bool = True

    @property
    def is_tabular(self) -> bool:
        """Check if this represents a valid tabular array (has fields)."""
        return len(self.fields) > 0

    @classmethod
    def nulled(cls) -> Self:
        """Create an empty/null result indicating non-tabular data."""
        return cls(rows=[], fields=[])

    @classmethod
    def detect(cls, items: list[Any]) -> Self:
        """Detect if array qualifies for tabular format per §9.3.

        Returns a Tabular with is_tabular=True if all items are dicts with
        identical keys containing only primitive values. Otherwise returns
        a nulled Tabular.

        We check the first item per the spec, then verify all others match.

        Args:
            items: List of items to analyze

        Returns:
            Tabular instance (check is_tabular property for result)
        """
        if not items or not all(isinstance(item, dict) for item in items) or not items[0]:
            return cls.nulled()

        item_dicts: list[dict[str, Any]] = items
        first_keys: set[str] = set(item_dicts[0].keys())

        for item in item_dicts[1:]:
            if set(item.keys()) != first_keys:
                return cls.nulled()

        for item in item_dicts:
            for value in item.values():
                if isinstance(value, (dict, list)):
                    return cls.nulled()

        return cls(rows=items, fields=list(item_dicts[0].keys()))

    @classmethod
    def from_rows(
        cls,
        rows: list[dict[str, Any]],
        fill_missing: bool = True,
    ) -> Self:
        """Create Tabular with fields auto-detected as union of all row keys.

        Args:
            rows: List of dictionaries
            fill_missing: If True (default), missing fields become null during encoding

        Returns:
            Tabular instance with fields from union of all keys
        """
        if not rows:
            return cls(rows=[], fields=[])

        all_fields: set[str] = set()
        for row in rows:
            all_fields.update(row.keys())

        return cls(rows=rows, fields=sorted(all_fields), fill_missing=fill_missing)


def tabular(
    rows: list[dict[str, Any]],
    fields: list[str],
    fill_missing: bool = True,
) -> Tabular:
    """Create a Tabular wrapper for forced tabular encoding.

    Args:
        rows: List of dictionaries to encode.
        fields: Field names defining column order.
        fill_missing: If True (default), missing fields become null.
            If False, raises ValueError for missing fields.

    Returns:
        Tabular wrapper instance.

    Example:
        >>> wrapper = tabular(
        ...     [{"a": 1}, {"a": 2, "b": 3}], fields=["a", "b"], fill_missing=True
        ... )
        >>> wrapper.fill_missing
        True
    """
    return Tabular(rows=rows, fields=fields, fill_missing=fill_missing)


def toon_dumps(data: Any, config: ToonCodecConfig | None = None) -> str:
    r"""Encode data to TOON string with wrapper awareness.

    Like tomlkit.dumps(), this function builds a TOON string from
    structured data. It recognizes Tabular wrappers and forces
    tabular format for those arrays.

    Args:
        data: Python object to encode (dict, list, or primitive).
        config: Optional ToonCodecConfig for encoding options.

    Returns:
        TOON formatted string.

    Example:
        >>> from codec_cub.toon.builder import tabular, toon_dumps
        >>> data = {"items": tabular([{"x": 1}], fields=["x"])}
        >>> toon_dumps(data)
        'items[1]{x}:\n  1'
    """
    from codec_cub.config import ToonCodecConfig  # noqa: PLC0415

    cfg: ToonCodecConfig = config if config is not None else ToonCodecConfig()
    builder = _ToonBuilder(cfg)
    return builder.build(data)


class _ToonBuilder:
    """Internal builder that handles Tabular wrappers during encoding."""

    def __init__(self, config: ToonCodecConfig) -> None:
        self._cfg: ToonCodecConfig = config
        self._encoder = ToonEncoder(config)
        self._lines: list[str] = []

    def build(self, data: Any) -> str:
        """Build TOON string from data, handling wrappers."""
        if isinstance(data, dict):
            self._build_object(data, depth=0)
            return self._cfg.newline.join(self._lines)
        return self._encoder.encode(data)

    def _indent(self, depth: int) -> str:
        """Get indentation string for depth."""
        return SPACE * (depth * self._cfg.indent_spaces)

    def _add_line(self, content: str, depth: int = 0) -> None:
        """Add a line with indentation."""
        self._lines.append(f"{self._indent(depth)}{content}")

    def _encode_tabular_rows(
        self,
        rows: list[dict[str, Any]],
        fields: list[str],
        fill_missing: bool = True,
    ) -> list[str]:
        """Encode tabular rows to TOON value strings.

        Args:
            rows: List of dicts to encode
            fields: Field names defining column order
            fill_missing: If True, missing fields become "null". If False, raises ValueError.

        Returns:
            List of encoded row strings (delimiter-separated values)
        """
        result: list[str] = []
        for row in rows:
            row_values: list[str] = []
            for field in fields:
                if field in row:
                    row_values.append(encode_primitive(row[field], self._cfg.delimiter))
                elif fill_missing:
                    row_values.append("null")
                else:
                    raise ValueError(f"Field '{field}' missing from row and fill_missing=False")
            result.append(self._cfg.delimiter.join(row_values))
        return result

    def _build_object(self, obj: dict[str, Any], depth: int) -> None:
        """Build object (dict) handling any Tabular wrappers in values."""
        for key, value in obj.items():
            encoded_key: str = encode_key(key)
            self._build_key_value(encoded_key, value, depth)

    def _build_key_value(self, key: str, value: Any, depth: int) -> None:
        """Build a key-value pair, detecting wrappers."""
        if isinstance(value, Tabular):
            self._build_tabular(key, value, depth)
        elif isinstance(value, dict):
            self._add_line(f"{key}:", depth)
            if value:
                self._build_object(value, depth + 1)
        elif isinstance(value, list):
            self._build_array(key, value, depth)
        else:
            primitive: str = encode_primitive(value, self._cfg.delimiter)
            self._add_line(f"{key}: {primitive}", depth)

    def _build_tabular(self, key: str, wrapper: Tabular, depth: int) -> None:
        """Build a forced tabular array from Tabular wrapper."""
        rows: list[dict[str, Any]] = wrapper.rows
        fields: list[str] = wrapper.fields
        length: int = len(rows)
        delim_char: str = get_delimiter_char(self._cfg.delimiter)

        if not rows:
            self._add_line(build_array_header(key, 0, [], self._cfg.delimiter, delim_char), depth)
            return

        header: str = build_array_header(key, length, fields, self._cfg.delimiter, delim_char)
        self._add_line(header, depth)

        for row_str in self._encode_tabular_rows(rows, fields, wrapper.fill_missing):
            self._add_line(row_str, depth + 1)

    def _build_array(self, key: str, items: list[Any], depth: int) -> None:
        """Build a regular array (delegates to encoder logic)."""
        length: int = len(items)
        delim_char: str = get_delimiter_char(self._cfg.delimiter)

        if is_primitive_array(items):
            if not items:
                self._add_line(build_array_header(key, 0, [], self._cfg.delimiter, delim_char), depth)
            else:
                values = self._cfg.delimiter.join(encode_primitive(v, self._cfg.delimiter) for v in items)
                self._add_line(
                    f"{build_array_header(key, length, [], self._cfg.delimiter, delim_char)} {values}", depth
                )
        elif all(isinstance(item, dict) for item in items) and items:  # empty lists would pass all() check
            self._build_dict_array(key, items, depth)
        else:
            self._add_line(build_array_header(key, length, [], self._cfg.delimiter, delim_char), depth)
            for item in items:
                self._build_list_item(item, depth + 1)

    def _build_dict_array(
        self,
        key: str,
        items: list[dict[str, Any]],
        depth: int,
    ) -> None:
        """Build array of dicts - try tabular detection, fallback to expanded.

        # Tabular.detect() guarantees all items have identical keys matching detected fields
        """
        detected: Tabular = Tabular.detect(items)
        length: int = len(items)
        delim_char: str = get_delimiter_char(self._cfg.delimiter)

        if detected.is_tabular:
            header: str = build_array_header(key, length, detected.fields, self._cfg.delimiter, delim_char)
            self._add_line(header, depth)

            for row_str in self._encode_tabular_rows(items, detected.fields, fill_missing=False):
                self._add_line(row_str, depth + 1)
        else:
            self._add_line(build_array_header(key, length, [], self._cfg.delimiter, delim_char), depth)
            for item in items:
                self._build_list_item(item, depth + 1)

    def _build_list_item(self, item: Any, depth: int) -> None:
        """Build a list item with '- ' prefix."""
        if not isinstance(item, (dict, list)):
            self._add_line(f"- {encode_primitive(item, self._cfg.delimiter)}", depth)
        elif isinstance(item, dict):
            if not item:
                self._add_line("-", depth)
            else:
                # TOON list item syntax: first key shares line with "- " prefix,
                # remaining keys are indented on subsequent lines
                keys: list[str] = list(item.keys())
                first_key: str = keys[0]
                first_value: Any = item[first_key]
                encoded_first_key: str = encode_key(first_key)

                if not isinstance(first_value, (dict, list)):
                    prim: str = encode_primitive(first_value, self._cfg.delimiter)
                    self._add_line(f"- {encoded_first_key}: {prim}", depth)
                else:
                    self._add_line(f"- {encoded_first_key}:", depth)
                    if isinstance(first_value, dict) and first_value:
                        self._build_object(first_value, depth + 2)
                    elif isinstance(first_value, list):
                        self._build_array(encoded_first_key, first_value, depth + 1)

                for rest_key in keys[1:]:
                    self._build_key_value(encode_key(rest_key), item[rest_key], depth + 1)
        elif isinstance(item, list):
            length: int = len(item)
            delim_char: str = get_delimiter_char(self._cfg.delimiter)
            if is_primitive_array(item):
                if not item:
                    self._add_line(f"- {build_array_header(None, length, [], self._cfg.delimiter, delim_char)}", depth)
                else:
                    values: str = self._cfg.delimiter.join(encode_primitive(v, self._cfg.delimiter) for v in item)
                    self._add_line(
                        f"- {build_array_header(None, length, [], self._cfg.delimiter, delim_char)} {values}", depth
                    )
            else:
                self._add_line(f"- {build_array_header(None, length, [], self._cfg.delimiter, delim_char)}", depth)
                for nested in item:
                    self._build_list_item(nested, depth + 1)


__all__ = ["Tabular", "tabular", "toon_dumps"]
