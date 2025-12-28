"""Nix encoder implementation."""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal, DecimalTuple, InvalidOperation
from functools import lru_cache
import math
from typing import TYPE_CHECKING, Any, Final, cast

from codec_cub.common import Wrapper
from funcy_bear.constants import characters as ch
from funcy_bear.ops.func_stuffs import any_of, complement
from funcy_bear.ops.math import neg
from funcy_bear.ops.math.infinity import is_infinite
from funcy_bear.tools.dispatcher import Dispatcher
from funcy_bear.type_stuffs.validate import is_bool, is_float, is_int, is_list, is_mapping, is_none, is_str

if TYPE_CHECKING:
    from collections.abc import Mapping
    from types import NoneType

    from codec_cub.config import NixCodecConfig


UNDERSCORE: str = ch.UNDERSCORE
DASH: str = ch.DASH


@lru_cache(512)
def is_bare_identifier(s: str) -> bool:
    """Return True if s is a valid bare identifier in Nix.

    Args:
        s: The string to check.

    Returns:
        True if s is a valid bare identifier, False otherwise.
    """
    if not s:
        return False
    first: str = s[0]
    rest: str = s[1:]
    if not (first.isalpha() or first == ch.UNDERSCORE):
        return False
    return all(ch.isalnum() or ch in {UNDERSCORE, DASH} for ch in rest)


class _NixEncoder:
    def __init__(self, cfg: NixCodecConfig) -> None:
        self._cfg: NixCodecConfig = cfg
        self._in_array: bool = False

    def encode(self, obj: Any) -> str:
        return self._emit_value(obj, 0)

    def _emit_value(self, obj: Any, depth: int) -> str:
        return to_value(obj, encoder=self, depth=depth)

    def _emit_key(self, key: str) -> str:
        if is_bare_identifier(key):
            return key
        return to_string(key, encoder=self)

    def _indent(self, depth: int) -> str:
        return ch.SPACE * (self._cfg.indent_spaces * depth)

    def _is_atomic(self, x: Any) -> bool:
        return x is None or isinstance(x, (bool, int, float, str))

    def _is_inline_list(self, x: Any) -> bool:
        if not isinstance(x, list):
            return False
        return len(x) <= self._cfg.max_inline_list and all(self._is_atomic(item) for item in x)


encode = Dispatcher("obj")


@encode.dispatcher()
def to_value(obj: Any, encoder: _NixEncoder, depth: int) -> str:
    """Encode a Python object to Nix syntax string."""
    raise TypeError(f"Unsupported type for Nix encoding: {type(obj).__name__}")


@encode.register(any_of(is_none, is_infinite))
def to_null(obj: float | NoneType, encoder: _NixEncoder, depth: int) -> str:
    """Encode None as null in Nix."""
    return ch.NULL_LITERAL


@encode.register(is_bool)
def to_bool(obj: bool, encoder: _NixEncoder, depth: int) -> str:
    """Encode bool as true/false in Nix."""
    return ch.TRUE_LITERAL if obj else ch.FALSE_LITERAL


@encode.register(is_int)
def to_int(obj: int, encoder: _NixEncoder, depth: int) -> str:
    """Encode int as decimal in Nix."""
    return str(obj)


ZERO_QUOTE: Final = "0"
NEGATIVE_ZERO_QUOTE: Final = f"{ch.DASH}{ZERO_QUOTE}"


@lru_cache(512)
def is_nan(obj: Decimal) -> bool:
    """Check if Decimal is NaN."""
    return obj.is_nan()


@lru_cache(512)
def math_is_nan(obj: float) -> bool:
    """Check if float is NaN."""
    return math.isnan(obj)


@lru_cache(512)
def to_decimal_no_exponent(obj: float, encoder: _NixEncoder) -> Decimal:
    """Convert float to Decimal without exponent, respecting max_scale."""
    max_scale: int = encoder._cfg.float_scale
    try:
        dec = Decimal(repr(obj))
    except InvalidOperation:
        return Decimal(0)

    if is_nan(dec):
        return Decimal(0)

    quant: Decimal = Decimal(1).scaleb(neg(max_scale))
    normalized: Decimal = dec.quantize(quant, rounding=ROUND_HALF_EVEN).normalize()
    if normalized == Decimal(NEGATIVE_ZERO_QUOTE):
        return Decimal(0)
    norm_tuple: DecimalTuple = normalized.as_tuple()
    if abs(cast("int", norm_tuple.exponent)) > max_scale:
        return normalized.quantize(quant, rounding=ROUND_HALF_EVEN)
    return normalized


@encode.register(is_float, complement(is_infinite))
def to_float(obj: float, encoder: _NixEncoder, depth: int) -> str:
    """Encode float as decimal/no-exponent in Nix."""
    if math_is_nan(obj):
        return ch.NULL_LITERAL
    if obj == 0.0:
        return ZERO_QUOTE

    if obj.is_integer():
        return str(int(obj))

    dec: Decimal = to_decimal_no_exponent(obj, encoder)
    text: str = format(dec, F_LITERAL)
    if ch.DOT in text:
        text: str = text.rstrip(ZERO_QUOTE).rstrip(ch.DOT)
    return text or ZERO_QUOTE


N_LITERAL: Final = "n"
R_LITERAL: Final = "r"
T_LITERAL: Final = "t"
F_LITERAL: Final = "f"
ESCAPED_BACKSLASH: Final = f"{ch.BACKSLASH}{ch.BACKSLASH}"
"""Escaped backslash string."""
ESCAPED_DOUBLE_QUOTE: Final = f"{ch.BACKSLASH}{ch.DOUBLE_QUOTE}"
"""Escaped double quote string."""
ESCAPED_NEWLINE: Final = f"{ch.BACKSLASH}{N_LITERAL}"
"""Escaped newline string."""
ESCAPED_CARRIAGE: Final = f"{ch.BACKSLASH}{R_LITERAL}"
"""Escaped carriage return string."""
ESCAPED_TAB: Final = f"{ch.BACKSLASH}{T_LITERAL}"
"""Escaped tab string."""

ESCAPE_MEMBERS: set[str] = {ch.BACKSLASH, ch.DOUBLE_QUOTE, ch.NEWLINE, ch.CARRIAGE, ch.TAB}

TO_ESCAPE_MAP: dict[str, str] = {
    ch.BACKSLASH: ESCAPED_BACKSLASH,
    ch.DOUBLE_QUOTE: ESCAPED_DOUBLE_QUOTE,
    ch.NEWLINE: ESCAPED_NEWLINE,
    ch.CARRIAGE: ESCAPED_CARRIAGE,
    ch.TAB: ESCAPED_TAB,
}
"""Mapping of characters to their escape sequences."""


def return_escaped(c: str) -> str:
    """Return escaped character.

    Args:
        c: Character to escape
    Returns:
        Escaped character
    """
    if c not in ESCAPE_MEMBERS:
        return c
    return TO_ESCAPE_MAP[c]


@lru_cache(512)
def escape_string(s: str) -> str:
    """Escape a string.

    Args:
        s: String to escape
    Returns:
        Escaped string
    """
    return f"{ch.DOUBLE_QUOTE}{ch.EMPTY_STRING.join(return_escaped(c) for c in s)}{ch.DOUBLE_QUOTE}"


@encode.register(is_str)
def to_string(obj: str, encoder: _NixEncoder, depth: int = 0) -> str:
    """Encode str as "..." in Nix."""
    return escape_string(obj)


@encode.register(is_list)
def to_list(obj: list[Any], encoder: _NixEncoder, depth: int) -> str:
    """Encode list/tuple as [...] in Nix."""
    next_depth: int = depth + 1
    list_wrap = Wrapper(ch.LEFT_BRACKET, ch.RIGHT_BRACKET, sep=ch.SPACE)
    if encoder._is_inline_list(obj) or encoder._cfg.inline_lists:
        if not obj:
            return list_wrap.render()
        rendered: str = ch.SPACE.join(encoder._emit_value(x, next_depth) for x in obj)
        return list_wrap.append(rendered, ch.SPACE, ch.SPACE).render(sep=ch.EMPTY_STRING)

    was_in_array: bool = encoder._in_array
    encoder._in_array = True
    try:
        for x in obj:
            list_wrap.append(encoder._emit_value(x, next_depth), encoder._indent(next_depth))
        output: str = list_wrap.render(pre=encoder._indent(depth), sep=encoder._cfg.newline)
        return output
    finally:
        encoder._in_array = was_in_array


@encode.register(is_mapping)
def to_attrset(obj: Mapping[str, Any], encoder: _NixEncoder, depth: int) -> str:
    """Encode dict as {...} in Nix."""
    keys: list[str] = list(obj.keys())
    if encoder._cfg.sort_keys:
        keys.sort()
    next_depth: int = depth + 1
    dict_wrap = Wrapper(ch.LEFT_BRACE, ch.RIGHT_BRACE, ch.SPACE)
    end: str = ch.SEMICOLON if encoder._cfg.trailing_semicolon else ch.EMPTY_STRING

    if not keys:
        return dict_wrap.render()

    if encoder._cfg.inline_arrays and encoder._in_array:
        pairs: list[str] = []
        for k in keys:
            key_text: str = encoder._emit_key(k)
            value_text: str = encoder._emit_value(obj[k], next_depth)
            pairs.append(f"{key_text} {ch.EQUALS} {value_text}{end}")
        rendered: str = ch.SPACE.join(pairs)
        return dict_wrap.append(rendered, ch.SPACE, ch.SPACE).render(sep=ch.EMPTY_STRING)

    for k in keys:
        key_text: str = encoder._emit_key(k)
        value_text: str = encoder._emit_value(obj[k], next_depth)
        dict_wrap.append(f"{key_text} {ch.EQUALS} {value_text}{end}", pre=encoder._indent(next_depth))
    return dict_wrap.render(pre=encoder._indent(depth), sep=encoder._cfg.newline)


# ruff: noqa: ARG001
