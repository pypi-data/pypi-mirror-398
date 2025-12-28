"""TOON decoder implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple

from codec_cub.toon.constants import CLOSE_BRACKET, COLON, DOUBLE_QUOTE, LIST_ITEM_PREFIX, OPEN_BRACKET, SPACE, TAB
from codec_cub.toon.header_parser import parse_array_header
from codec_cub.toon.indentation_tracker import IndentationTracker, LineInfo
from codec_cub.toon.primitive_parser import parse_primitive
from codec_cub.toon.quote_scanner import QuoteAwareScanner
from funcy_bear.ops.strings.escaping import unescape_string
from funcy_bear.ops.strings.manipulation import extract

if TYPE_CHECKING:
    from codec_cub.config import ToonCodecConfig


class KeyValuePair(NamedTuple):
    """Representation of a key-value pair."""

    key: str
    value: Any


class ToonDecoder:
    """Decode TOON format to Python objects per specification v2.0."""

    def __init__(self, config: ToonCodecConfig) -> None:
        """Initialize decoder with configuration."""
        self._cfg: ToonCodecConfig = config
        self._tracker: IndentationTracker | None = None

    @property
    def tracker(self) -> IndentationTracker:
        """Get the current indentation tracker."""
        if self._tracker is None:
            raise RuntimeError("Tracker not initialized - decode() must be called first")
        return self._tracker

    def decode(self, text: str) -> Any:
        """Decode a TOON string to Python object.

        Args:
            text: TOON formatted string

        Returns:
            Python object (dict, list, or primitive)
        """
        lines: list[str] = text.split(self._cfg.newline)
        depths: list[int] = [self._compute_depth(line) for line in lines]

        while lines and not lines[-1].strip():  # Per §12: trailing newlines are accepted
            lines.pop()
            depths.pop()

        if not lines or all(not line.strip() for line in lines):
            # Per §5: empty document decodes to empty object
            return {}

        self._tracker = IndentationTracker(lines, depths)
        return self._detect_root_form()

    def _compute_depth(self, line: str) -> int:
        """Compute indentation depth for a line."""
        if not line or not line.strip():
            return 0

        leading_spaces: int = len(line) - len(line.lstrip(SPACE))

        if self._cfg.strict:
            if leading_spaces % self._cfg.indent_spaces != 0:
                raise ValueError(
                    f"Invalid indentation: {leading_spaces} spaces (must be multiple of {self._cfg.indent_spaces})"
                )
            indent_part: str = line[: leading_spaces if leading_spaces > 0 else 0]
            if TAB in indent_part:
                raise ValueError("Tabs are not allowed in indentation")

        return leading_spaces // self._cfg.indent_spaces

    def _detect_root_form(self) -> Any:
        """Detect root form per §5."""
        first_line: str | None = None
        first_line_idx: int | None = None
        while self.tracker.has_more():
            line: LineInfo = self.tracker.peek()
            if line.text.strip():
                first_line = line.text.strip()
                first_line_idx = self.tracker.current_index
                break
            self.tracker.consume()

        if first_line is None or first_line_idx is None:
            return {}

        # Per §5: "[N]:" at start = root array, "key[N]:" = keyed array in object
        if self._is_array_header(first_line) and COLON in first_line and first_line.startswith("["):
            self.tracker.current_index = first_line_idx
            self.tracker.consume()
            return self._parse_array_at_depth(0, first_line)

        self.tracker.reset()
        non_empty_count = 0
        while self.tracker.has_more():
            line: LineInfo = self.tracker.peek()
            if line.text.strip():
                non_empty_count += 1
            self.tracker.consume()

        if (non_empty_count == 1 and COLON not in first_line) or first_line.startswith(DOUBLE_QUOTE):
            return self._parse_primitive_token(first_line)

        self.tracker.reset()
        return self._parse_object_at_depth(0)

    def _is_array_header(self, line: str) -> bool:
        """Check if line looks like an array header."""
        return OPEN_BRACKET in line and CLOSE_BRACKET in line

    def _parse_object_at_depth(self, depth: int) -> dict[str, Any]:
        """Parse an object starting at current index."""
        obj: dict[Any, Any] = {}

        while self.tracker.has_more():
            line: LineInfo = self.tracker.peek()
            if not line.text.strip():  # Skip blank lines outside arrays (§12)
                self.tracker.consume()
                continue
            if line.depth < depth:  # If depth decreased, we're done with this object
                break
            if line.depth > depth:  # Skip lines deeper than current depth
                self.tracker.consume()
                continue
            stripped: str = line.text.strip()
            if self._is_array_header(stripped) and COLON in stripped:
                obj_kv: KeyValuePair = self._parse_keyed_array_line(stripped, depth)
                obj[obj_kv.key] = obj_kv.value
                continue

            if COLON not in stripped:
                self.tracker.consume()
                continue

            kv: KeyValuePair = self._parse_key_value_line(stripped, depth)
            obj[kv.key] = kv.value
        return obj

    def _parse_key_value_line(self, stripped: str, depth: int) -> KeyValuePair:
        """Parse a key: value line.

        Args:
            stripped: Line content stripped of leading/trailing whitespace
            depth: Current indentation depth
        Returns:
            Tuple of (key, value)
        """
        scanner = QuoteAwareScanner(stripped)
        colon_idx: int = scanner.find_unquoted(COLON)
        if colon_idx == -1:
            msg: str = f"Missing colon in key-value line: {stripped}"
            raise ValueError(msg)
        key_part: str = stripped[:colon_idx]
        value_part: str = stripped[colon_idx + 1 :].lstrip()
        key: str = self._parse_key(key_part)
        if not value_part:
            self.tracker.consume()
            nested_obj: dict[str, Any] = self._parse_object_at_depth(depth + 1)
            return KeyValuePair(key, nested_obj)
        self.tracker.consume()
        value: Any = self._parse_primitive_token(value_part)
        return KeyValuePair(key, value)

    def _parse_key(self, key_str: str) -> str:
        """Parse a key (quoted or unquoted)."""
        min_quoted_length = 2
        key_str = key_str.strip()
        if key_str.startswith(DOUBLE_QUOTE):
            if not key_str.endswith(DOUBLE_QUOTE) or len(key_str) < min_quoted_length:
                msg: str = f"Unterminated quoted key: {key_str}"
                raise ValueError(msg)
            inner: str = extract(key_str)
            return unescape_string(inner)
        return key_str

    def _parse_keyed_array_line(self, stripped: str, depth: int) -> KeyValuePair:
        """Parse a line with key and array header: key[N]:...

        Args:
            stripped: Line content stripped of leading/trailing whitespace
            depth: Current indentation depth

        Returns:
            Tuple of (key, array value)
        """
        bracket_start: int = stripped.index("[")
        key_part: str = stripped[:bracket_start]
        rest: str = stripped[bracket_start:]
        key: str = self._parse_key(key_part)
        self.tracker.consume()
        array_value: list[Any] = self._parse_array_at_depth(depth, rest)
        return KeyValuePair(key, array_value)

    def _parse_array_at_depth(self, depth: int, header_line: str) -> list[Any]:
        """Parse an array given its header line."""
        headers: tuple[int, str, list[str]] = parse_array_header(header_line)
        length: int = headers[0]
        delimiter: str = headers[1]
        field_names: list[str] = headers[2]
        colon_idx: int = header_line.index(COLON)
        after_colon: str = header_line[colon_idx + 1 :].lstrip()
        if after_colon:
            values: list[Any] = self._parse_delimited_values(after_colon, delimiter)
            if self._cfg.strict and len(values) != length:
                raise ValueError(f"Array length mismatch: expected {length}, got {len(values)}")
            return values
        if field_names:
            return self._parse_tabular_rows(depth, length, delimiter, field_names)
        return self._parse_expanded_list(depth, length)

    def _parse_delimited_keys(self, content: str, delimiter: str) -> list[str]:
        """Parse delimiter-separated keys."""
        scanner = QuoteAwareScanner(content)
        tokens: list[str] = scanner.split_by(delimiter)
        return [self._parse_key(token) for token in tokens]

    def _parse_tabular_rows(
        self,
        depth: int,
        length: int,
        delimiter: str,
        field_names: list[str],
    ) -> list[dict[str, Any]]:
        """Parse tabular array rows.

        Args:
            depth: Current indentation depth
            length: Expected number of rows
            delimiter: Delimiter used in rows
            field_names: List of field names for each column

        Returns:
            List of row objects as dictionaries
        """
        rows: list[Any] = []
        row_depth: int = depth + 1

        while self.tracker.has_more():
            line: LineInfo = self.tracker.peek()
            if not line.text.strip():
                if self._cfg.strict:
                    raise ValueError("Blank lines not allowed inside tabular rows")
                self.tracker.consume()
                continue
            if line.depth < row_depth:
                break
            if line.depth > row_depth:
                self.tracker.consume()
                continue
            stripped: str = line.text.strip()
            if self._is_row_end(stripped, delimiter):
                break
            values: list[Any] = self._parse_delimited_values(stripped, delimiter)
            if self._cfg.strict and len(values) != len(field_names):
                msg: str = f"Row width mismatch: expected {len(field_names)}, got {len(values)}"
                raise ValueError(msg)

            row_obj: dict[str, Any | None] = {
                field_names[i]: values[i] if i < len(values) else None for i in range(len(field_names))
            }
            rows.append(row_obj)
            self.tracker.consume()

        if self._cfg.strict and len(rows) != length:
            raise ValueError(f"Tabular row count mismatch: expected {length}, got {len(rows)}")
        return rows

    def _is_row_end(self, stripped: str, delimiter: str) -> bool:
        """Check if line marks end of tabular rows per §9.3: disambiguate rows vs key-value using unquoted positions."""
        scanner = QuoteAwareScanner(stripped)
        delim_pos: int = scanner.find_unquoted(delimiter)
        colon_pos: int = scanner.find_unquoted(COLON)
        if (colon_pos == -1 and delim_pos == -1) or (delim_pos != -1 and colon_pos == -1):
            return False
        if colon_pos != -1 and delim_pos == -1:
            return True
        return colon_pos < delim_pos

    def _parse_expanded_list(self, depth: int, length: int) -> list[Any]:
        """Parse expanded list items."""
        if self._tracker is None:
            raise RuntimeError("Tracker not initialized - decode() must be called first")
        items: list[Any] = []
        item_depth: int = depth + 1
        while self._tracker.has_more():
            line: LineInfo = self._tracker.peek()
            if not line.text.strip():
                if self._cfg.strict:
                    raise ValueError("Blank lines not allowed inside array items")
                self._tracker.consume()
                continue
            if line.depth < item_depth:
                break
            if line.depth > item_depth:
                self._tracker.consume()
                continue
            stripped: str = line.text.strip()
            if not stripped.startswith(LIST_ITEM_PREFIX):
                break
            after_marker: str = stripped[len(LIST_ITEM_PREFIX) :]
            item_value: Any = self._parse_list_item(after_marker, item_depth)
            items.append(item_value)

        if self._cfg.strict and len(items) != length:
            raise ValueError(f"List item count mismatch: expected {length}, got {len(items)}")
        return items

    def _parse_list_item(self, after_marker: str, item_depth: int) -> Any:
        """Parse a single list item after the '- ' marker."""
        if not after_marker:
            self.tracker.consume()
            return {}
        if self._is_array_header(after_marker) and COLON in after_marker:
            self.tracker.consume()
            return self._parse_array_at_depth(item_depth, after_marker)
        if COLON in after_marker:
            self.tracker.consume()
            return self._parse_object_item(after_marker, item_depth)
        self.tracker.consume()
        return self._parse_primitive_token(after_marker)

    def _parse_object_item(self, first_field_line: str, item_depth: int) -> dict[str, Any]:
        """Parse an object that starts on a list item line per §10."""
        obj = {}

        scanner = QuoteAwareScanner(first_field_line)
        colon_idx: int = scanner.find_unquoted(COLON)
        if colon_idx == -1:
            raise ValueError(f"Missing colon in object field: {first_field_line}")

        key_part: str = first_field_line[:colon_idx]
        value_part: str = first_field_line[colon_idx + 1 :].lstrip()

        key: str = self._parse_key(key_part)

        if self._is_array_header(first_field_line):
            array_value = self._parse_array_at_depth(item_depth, first_field_line[colon_idx:])
            obj[key] = array_value
        elif not value_part:
            nested_obj: dict[str, Any] = self._parse_object_at_depth(item_depth + 1)
            obj[key] = nested_obj
        else:
            obj[key] = self._parse_primitive_token(value_part)

        sibling_depth: int = item_depth + 1
        while self.tracker.has_more():
            line: LineInfo = self.tracker.peek()
            if not line.text.strip() or (line.depth > sibling_depth):
                self.tracker.consume()
                continue
            if line.depth < sibling_depth:
                break
            stripped: str = line.text.strip()
            if stripped.startswith(LIST_ITEM_PREFIX):
                break
            if self._is_array_header(stripped) and COLON in stripped:
                kv: KeyValuePair = self._parse_keyed_array_line(stripped, sibling_depth)
                obj[kv.key] = kv.value
                continue
            if COLON not in stripped:
                self.tracker.consume()
                continue
            obj_kv: KeyValuePair = self._parse_key_value_line(stripped, sibling_depth)
            obj[obj_kv.key] = obj_kv.value
        return obj

    def _parse_delimited_values(self, text: str, delimiter: str) -> list[Any]:
        """Parse delimiter-separated primitive values."""
        scanner = QuoteAwareScanner(text)
        tokens: list[str] = scanner.split_by(delimiter)
        return [self._parse_primitive_token(token) for token in tokens]

    def _parse_primitive_token(self, token: str) -> Any:
        """Parse a primitive token per §4 and §7.4."""
        return parse_primitive(token)
