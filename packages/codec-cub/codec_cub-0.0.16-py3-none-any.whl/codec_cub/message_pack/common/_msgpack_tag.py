from __future__ import annotations

from collections.abc import Callable  # noqa: TC003
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Self

from funcy_bear.constants.binary_types import CHAR, INT8, INT16, INT32, INT64, UINT8, UINT16, UINT32, UINT64
from funcy_bear.rich_enums.base_value import BaseValue
from funcy_bear.rich_enums.int_enum import RichIntEnum
from funcy_bear.rich_enums.variable_enum import VariableType
from funcy_bear.sentinels import MissingType


@dataclass
class MetaTag(VariableType):
    """A VariableType for MessagePack tag metadata.

    Delegates size/bounds information to StructField types from binary_types.
    """

    parser: Callable[[str], int] = int
    description: str = ""
    ctype: type = MissingType
    literal: Any = MissingType
    data_ctype: bool = False

    def in_range(self, n: int) -> bool:
        """Check if n is within the bounds of the ctype."""
        if self.ctype is MissingType:
            return False
        return self.low <= n <= self.high

    def be_bytes(self, n: int) -> bytes:
        """Get big-endian bytes for an integer of this ctype."""
        if self.ctype is MissingType:
            return b""
        return int(n).to_bytes(self.size, "big", signed=self.signed)

    @cached_property
    def size(self) -> int:
        """Get size in bytes of the ctype (delegates to StructField.size)."""
        if self.ctype is MissingType:
            return 0
        return self.ctype.size

    @cached_property
    def bits(self) -> int:
        """Get number of bits of the ctype (delegates to StructField.bits)."""
        if self.ctype is MissingType:
            return 0
        return self.ctype.bits

    @cached_property
    def signed(self) -> bool:
        """Get signedness of the ctype (delegates to StructField.signed)."""
        if self.ctype is MissingType:
            return False
        return self.ctype.signed

    @cached_property
    def low(self) -> int:
        """Get the low bound of the ctype (delegates to StructField.bounds)."""
        if self.ctype is MissingType:
            return 0
        return self.ctype.bounds[0]

    @cached_property
    def high(self) -> int:
        """Get the high bound of the ctype (delegates to StructField.bounds)."""
        if self.ctype is MissingType:
            return 0
        return self.ctype.bounds[1]

    @cached_property
    def is_literal(self) -> bool:
        """Check if this tag has no payload (i.e., only the tag byte itself) with literal value."""
        return self.ctype == CHAR and self.literal is not MissingType


@dataclass(frozen=True)
class V(BaseValue[int, MetaTag]):
    """A frozen class for holding constant variable values."""

    value: int
    meta: MetaTag
    text: str = ""

    def __getattr__(self, item: str) -> Any:
        """Allow access to attributes directly from the model."""
        if item == "size":
            return self.meta.size
        if item == "literal":
            return self.meta.literal
        if hasattr(self.meta, item):
            return getattr(self.meta, item)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")


class VariableIntEnum(RichIntEnum):
    """Base class for Enums with variable values."""

    meta: Any
    low: int
    high: int

    def __new__(cls, value: V) -> Self:
        """Create a new enum member with the given VarValue."""
        obj: Self = int.__new__(cls, value.value)
        obj._value_ = value.value
        obj.text = value.text or ""
        obj.meta = value
        obj.low = value.meta.low
        obj.high = value.meta.high
        return obj

    def __int__(self) -> int:
        """Return the integer value of the enum."""
        return self.value


class Tag(MetaTag.Hint(), VariableIntEnum):
    """MessagePack tags (spec constants).

    Note:
        The `MetaTag.Hint()` pattern is used to graft type hints onto the enum class without runtime inheritance.
        This allows static type checkers to recognize the `meta` attribute on enum members, while at runtime
        only `VariableIntEnum` is inherited. This approach avoids runtime conflicts and ensures maintainability
        for those unfamiliar with conditional typing patterns.
    """

    meta: MetaTag
    """Meta type for Tag enum members."""

    # These fields will be set with CHAR to explain they are a single byte for the tag itself but no payload.
    NIL = V(0xC0, meta=MetaTag(description="nil value", literal=None, ctype=CHAR))
    FALSE = V(0xC2, meta=MetaTag(description="boolean false", literal=False, ctype=CHAR))
    TRUE = V(0xC3, meta=MetaTag(description="boolean true", literal=True, ctype=CHAR))

    # These fields will have ctype to indicate the size of the length field following the tag.
    BIN8 = V(0xC4, meta=MetaTag(description="binary data (8-bit length)", ctype=UINT8))
    BIN16 = V(0xC5, meta=MetaTag(description="binary data (16-bit length)", ctype=UINT16))
    BIN32 = V(0xC6, meta=MetaTag(description="binary data (32-bit length)", ctype=UINT32))
    FLOAT64 = V(0xCB, meta=MetaTag(description="64-bit floating point number", ctype=UINT64))
    STR8 = V(0xD9, meta=MetaTag(description="string (8-bit length)", ctype=UINT8))
    STR16 = V(0xDA, meta=MetaTag(description="string (16-bit length)", ctype=UINT16))
    STR32 = V(0xDB, meta=MetaTag(description="string (32-bit length)", ctype=UINT32))
    ARRAY16 = V(0xDC, meta=MetaTag(description="array (16-bit length)", ctype=UINT16))
    ARRAY32 = V(0xDD, meta=MetaTag(description="array (32-bit length)", ctype=UINT32))
    MAP16 = V(0xDE, meta=MetaTag(description="map (16-bit length)", ctype=UINT16))
    MAP32 = V(0xDF, meta=MetaTag(description="map (32-bit length)", ctype=UINT32))

    # All of the integers here will use their ctype to indicate the size and signedness of the integer payload following the tag.
    UINT8 = V(0xCC, meta=MetaTag(description="unsigned integer (8-bit)", ctype=UINT8, data_ctype=True))
    UINT16 = V(0xCD, meta=MetaTag(description="unsigned integer (16-bit)", ctype=UINT16, data_ctype=True))
    UINT32 = V(0xCE, meta=MetaTag(description="unsigned integer (32-bit)", ctype=UINT32, data_ctype=True))
    UINT64 = V(0xCF, meta=MetaTag(description="unsigned integer (64-bit)", ctype=UINT64, data_ctype=True))
    INT8 = V(0xD0, meta=MetaTag(description="signed integer (8-bit)", ctype=INT8, data_ctype=True))
    INT16 = V(0xD1, meta=MetaTag(description="signed integer (16-bit)", ctype=INT16, data_ctype=True))
    INT32 = V(0xD2, meta=MetaTag(description="signed integer (32-bit)", ctype=INT32, data_ctype=True))
    INT64 = V(0xD3, meta=MetaTag(description="signed integer (64-bit)", ctype=INT64, data_ctype=True))


LITERAL_TYPES: tuple[Tag, ...] = (Tag.NIL, Tag.TRUE, Tag.FALSE)
INT_TYPES: tuple[Tag, ...] = (Tag.UINT8, Tag.UINT16, Tag.UINT32, Tag.UINT64, Tag.INT8, Tag.INT16, Tag.INT32, Tag.INT64)
STR_TYPES: tuple[Tag, ...] = (Tag.STR8, Tag.STR16, Tag.STR32)
BIN_TYPES: tuple[Tag, ...] = (Tag.BIN8, Tag.BIN16, Tag.BIN32)
ARRAY_TYPES: tuple[Tag, ...] = (Tag.ARRAY16, Tag.ARRAY32)
MAP_TYPES: tuple[Tag, ...] = (Tag.MAP16, Tag.MAP32)
