"""All constants for MessagePack fix families.

| Family        | Base  | Classify Mask  | Bits  | Range       | Pass Test `(byte & mask) == base`|
|---------------|-------|----------------|-------|-------------|----------------------------------|
| pos fixint    | 0x00  | 0x80           | 7     | 0..127      | 0x7F & 0x80 = 0                  |
| neg fixint    | 0xE0  | 0xE0           | 5     | -32..-1     | 0xE2 & 0xE0 = 0xE0               |
| fixstr        | 0xA0  | 0xE0           | 5     | len 0-31    | 0xA5 & 0xE0 = 0xA0               |
| fixarray      | 0x90  | 0xF0           | 4     | len 0-15    | 0x93 & 0xF0 = 0x90               |
| fixmap        | 0x80  | 0xF0           | 4     | len 0-15    | 0x8F & 0xF0 = 0x80               |
"""

from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Final, Self

from funcy_bear.constants.binary_types import MIN_VALUE
from funcy_bear.ops.binarystuffs import shift_left
from funcy_bear.ops.math import neg
from funcy_bear.rich_enums.base_value import BaseValue
from funcy_bear.rich_enums.int_enum import RichIntEnum
from funcy_bear.rich_enums.variable_enum import VariableType

# Family      | Base  | Classify Mask | Bits         | Range        | Pass Test `(byte & mask) == base`
# Pos FIXINT  | 0x00  | 0x80          | 7            | 0..127       | 0x7F & 0x80 = 0
POS_FIX_BASE = 0x00
"""Base byte for positive fixint family."""
POS_FIXINT_CMASK: Final = 0x80
"""Mask for identifying positive fixint family (top bit == 0)."""
POS_FIXINT_BITS: Final = 7
"""Number of bits used for data in positive fixint."""
POS_FIXINT_MIN: Final = 0
"""Minimum value for positive fixint."""
POS_FIXINT_MAX: Final = 127
"""Maximum value for positive fixint."""
POS_FIXINT_MASK: Final = shift_left(POS_FIXINT_BITS) - 1
"""Mask for extracting data bits from positive fixint."""


# Family      | Base  | Classify Mask | Bits         | Range        | Pass Test `(byte & mask) == base`
# Neg FIXINT  | 0xE0  | 0xE0          | 5            | -32..-1      | 0xE2 & 0xE0 = 0xE0
NEG_FIX_BASE = 0xE0
"""Base byte for negative fixint family."""
NEG_FIXINT_CMASK: Final = 0xE0
"""Mask for identifying negative fixint family (top three bits == 111)."""
NEG_FIXINT_BITS: Final = 5
"""Number of bits used for data in negative fixint."""
NEG_FIXINT_MIN: Final = neg(32)
"""Minimum value for negative fixint."""
NEG_FIXINT_MAX: Final = neg(1)
"""Maximum value for negative fixint."""
NEG_FIXINT_MASK: Final = shift_left(NEG_FIXINT_BITS) - 1
"""Mask for extracting magnitude bits from negative fixint."""

# Family     | Base  | Classify Mask | Bits         | Range        | Pass Test `(byte & mask) == base`
# FixSTR     | 0xA0  | 0xE0          | 5            | len 0-31     | 0xA5 & 0xE0 = 0xA0
FIXSTR_BASE = 0xA0
"""Base byte for fixstr family."""
FIXSTR_CMASK: Final = 0xE0
"""Mask for identifying fixstr family (top three bits == 101)."""
FIXSTR_LEN_BITS: Final = 5
"""Number of bits used for length in fixstr."""
FIXSTR_MAX_LEN: Final = 31
"""Maximum length for fixstr family."""
FIXSTR_MASK: Final = 0x1F
"""Mask for extracting length bits from fixstr."""

# Family     | Base  | Classify Mask | Bits         | Range        | Pass Test `(byte & mask) == base`
# FixARRAY   | 0x90  | 0xF0          | 4            | len 0-15     | 0x93 & 0xF0 = 0x90
FIXARRAY_BASE = 0x90
"""Base byte for fixarray family."""
FIXARRAY_CMASK: Final = 0xF0
"""Mask for identifying fixarray family (top nibble == 1001)."""
FIXARRAY_LEN_BITS: Final = 4
"""Number of bits used for length in fixarray."""
FIXARRAY_MAX_LEN: Final = 15
"""Maximum length for fixarray family."""
FIXARRAY_MASK: Final = 0x0F
"""Mask for extracting length bits from fixarray."""


# Family     | Base  | Classify Mask | Bits         | Range        | Pass Test `(byte & mask) == base`
# FixMAP     | 0x80  | 0xF0          | 4            | len 0-15     | 0x8F & 0xF0 = 0x80
FIXMAP_BASE = 0x80
"""Base byte for fixmap family."""
FIXMAP_CMASK: Final = 0xF0
"""Mask for identifying fixmap family (top nibble == 1000)."""
FIXMAP_LEN_BITS: Final = 4
"""Number of bits used for length in fixmap."""
FIXMAP_MAX_LEN: Final = 15
"""Maximum length for fixmap family."""
FIXMAP_MASK: Final = 0x0F
"""Mask for extracting length bits from fixmap."""


@dataclass(slots=True)
class FixTag(VariableType):
    """Metadata for MessagePack fix family tags."""

    base: int = 0
    classify_mask: int = 0  # Mask for matching: (byte & classify_mask) == base
    extract_mask: int = 0  # Mask for extracting data: byte & extract_mask
    description: str = ""
    parser: Callable[[str], int] = int
    low: int = 0
    high: int = 255

    def matches(self, byte: int) -> bool:
        """Check if this byte belongs to this fix family."""
        return (byte & self.classify_mask) == self.base

    def extract_length(self, byte: int) -> int:
        """Extract the embedded length from the byte."""
        return byte & self.extract_mask

    def in_range(self, n: int) -> bool:
        """Check if n is within the bounds of this IntData."""
        return self.low <= n <= self.high


def fix_matches(byte: int, enum: FixTag) -> bool:
    """Check if this byte belongs to the given fix family."""
    return (byte & enum.classify_mask) == enum.base


@dataclass(frozen=True)
class V(BaseValue[int, FixTag]):
    value: int
    meta: FixTag
    text: str = ""

    @cached_property
    def matches(self) -> Callable[[int], bool]:
        """Get a function that checks if a byte matches this fix tag."""

        def matcher(byte: int) -> bool:
            return (byte & self.meta.classify_mask) == self.meta.base

        return matcher

    @cached_property
    def extract_length(self) -> Callable[[int], int]:
        """Get a function that extracts length from a byte for this fix tag."""

        def extractor(byte: int) -> int:
            return byte & self.meta.extract_mask

        return extractor

    @cached_property
    def high(self) -> int:
        """Get the high bound from the meta."""
        return self.meta.high

    @cached_property
    def low(self) -> int:
        """Get the low bound from the meta."""
        return self.meta.low

    @cached_property
    def base(self) -> int:
        """Get the base from the meta."""
        return self.meta.base

    @cached_property
    def extract_mask(self) -> int:
        """Get the extract_mask from the meta."""
        return self.meta.extract_mask


class VariableIntEnum(RichIntEnum):
    meta: Any
    base: int
    classify_mask: int
    low: int
    high: int

    def __new__(cls, value: V) -> Self:
        """Create a new enum member with the given VarValue."""
        obj: Self = int.__new__(cls, value.value)
        obj._value_ = value.value
        obj.text = value.text or ""
        obj.meta = value
        obj.base = value.meta.base
        obj.classify_mask = value.meta.classify_mask
        obj.low = value.meta.low
        obj.high = value.meta.high
        return obj

    def __int__(self) -> int:
        """Return the integer value of the enum."""
        return self.value


_PosInt = FixTag(
    base=POS_FIX_BASE,
    classify_mask=POS_FIXINT_CMASK,
    extract_mask=POS_FIXINT_MASK,
    low=POS_FIXINT_MIN,
    high=POS_FIXINT_MAX,
    description="pos fixint family",
)
_NegInt = FixTag(
    base=NEG_FIX_BASE,
    classify_mask=NEG_FIXINT_CMASK,
    extract_mask=NEG_FIXINT_MASK,
    low=NEG_FIXINT_MIN,
    high=NEG_FIXINT_MAX,
    description="neg fixint family",
)
_FixStr = FixTag(
    base=FIXSTR_BASE,
    classify_mask=FIXSTR_CMASK,
    extract_mask=FIXSTR_MASK,
    low=MIN_VALUE,
    high=FIXSTR_MAX_LEN,
    description="fixstr family",
)
_FixArray = FixTag(
    base=FIXARRAY_BASE,
    classify_mask=FIXARRAY_CMASK,
    extract_mask=FIXARRAY_MASK,
    low=MIN_VALUE,
    high=FIXARRAY_MAX_LEN,
    description="fixarray family",
)
_FixMap = FixTag(
    base=FIXMAP_BASE,
    classify_mask=FIXMAP_CMASK,
    extract_mask=FIXMAP_MASK,
    low=MIN_VALUE,
    high=FIXMAP_MAX_LEN,
    description="fixmap family",
)


class FixFamily(FixTag.Hint(), VariableIntEnum):
    """MessagePack fix family tags."""

    meta: FixTag
    """Meta type for FixFamily enum members."""

    FIXMAP = V(FIXMAP_BASE, meta=_FixMap)
    FIXARRAY = V(FIXARRAY_BASE, meta=_FixArray)
    FIXSTR = V(FIXSTR_BASE, meta=_FixStr)
    POS_FIXINT = V(POS_FIX_BASE, meta=_PosInt)
    NEG_FIXINT = V(NEG_FIX_BASE, meta=_NegInt)


POS_FIXINT = FixFamily.POS_FIXINT
NEG_FIXINT = FixFamily.NEG_FIXINT
FIXINTS: tuple[FixFamily, ...] = (POS_FIXINT, NEG_FIXINT)
