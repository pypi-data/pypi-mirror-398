"""Constants associated binary types."""

from ctypes import (
    c_bool,
    c_char,
    c_double,
    c_float,
    c_int8,
    c_int16,
    c_int32,
    c_int64,
    c_ubyte,
    c_uint8,
    c_uint16,
    c_uint32,
    c_uint64,
    c_void_p,
)
from typing import Final

type Str_T = type[c_char]
type Int_T = type[c_int8 | c_int16 | c_int32 | c_int64 | c_uint8 | c_uint16 | c_uint32 | c_uint64]
type FLOAT_T = type[c_double | c_float]
type CType_Type = type[c_ubyte | c_bool | c_void_p] | Str_T | Int_T | FLOAT_T


class MetaStruct[T: CType_Type](type):
    """A metaclass for StructField to enforce c_type attribute."""

    c_type: T
    _info: tuple[int, int, bool] | None = None
    _bounds: tuple[int, int] | None = None

    @property
    def fmt(cls) -> str:
        """Get the format character for the ctypes type."""
        return str(cls.c_type._type_)

    @property
    def info(cls) -> tuple[int, int, bool]:
        """Get size in bytes, number of bits, and signedness of the ctypes type."""
        from funcy_bear.ops.binarystuffs import get_int_info  # noqa: PLC0415

        if cls._info is None:
            cls._info = get_int_info(cls.c_type)
        return cls._info

    @property
    def size(cls) -> int:
        """Get the size in bytes of the ctypes type."""
        return cls.info[0]

    @property
    def bits(cls) -> int:
        """Get number of bits of the ctypes type."""
        return cls.info[1]

    @property
    def signed(cls) -> bool:
        """Get signedness of the ctypes type."""
        return cls.info[2]

    @property
    def bounds(cls) -> tuple[int, int]:
        """Get the (low, high) bounds of the ctypes type."""
        from funcy_bear.ops.binarystuffs import bounds as bnds  # noqa: PLC0415

        if cls._bounds is None:
            _, bits, signed = cls.info
            cls._bounds = bnds(b=bits, s=signed)
        return cls._bounds

    @property
    def low(cls) -> int:
        """Get the low bound of the ctypes type."""
        return cls.bounds[0]

    @property
    def high(cls) -> int:
        """Get the high bound of the ctypes type."""
        return cls.bounds[1]


class StructField[T: CType_Type](metaclass=MetaStruct):
    """A class to represent a field in a C struct."""

    c_type: T


class CharField(StructField[type[c_char]]):
    """A class to represent a char field in a C struct."""

    c_type: type[c_char] = c_char


class UByteField(StructField[type[c_ubyte]]):
    """A class to represent an unsigned byte field in a C struct."""

    c_type: type[c_ubyte] = c_ubyte


class UINT8Field(StructField[type[c_uint8]]):
    """A class to represent an integer field in a C struct."""

    c_type: type[c_uint8] = c_uint8


class INT8Field(StructField[type[c_int8]]):
    """A class to represent an integer field in a C struct."""

    c_type: type[c_int8] = c_int8


class UINT16Field(StructField[type[c_uint16]]):
    """A class to represent an integer field in a C struct."""

    c_type: type[c_uint16] = c_uint16


class INT16Field(StructField[type[c_int16]]):
    """A class to represent an integer field in a C struct."""

    c_type: type[c_int16] = c_int16


class UINT32Field(StructField[type[c_uint32]]):
    """A class to represent an integer field in a C struct."""

    c_type: type[c_uint32] = c_uint32


class INT32Field(StructField[type[c_int32]]):
    """A class to represent an integer field in a C struct."""

    c_type: type[c_int32] = c_int32


class UINT64Field(StructField[type[c_uint64]]):
    """A class to represent an integer field in a C struct."""

    c_type: type[c_uint64] = c_uint64


class INT64Field(StructField[type[c_int64]]):
    """A class to represent an integer field in a C struct."""

    c_type: type[c_int64] = c_int64


class BoolField(StructField[type[c_bool]]):
    """A class to represent a boolean field in a C struct."""

    c_type: type[c_bool] = c_bool


class VoidPtrField(StructField[type[c_void_p]]):
    """A class to represent a void pointer field in a C struct."""

    c_type: type[c_void_p] = c_void_p


class DoubleField(StructField[type[c_double]]):
    """A class to represent a double field in a C struct."""

    c_type: type[c_double] = c_double


class FloatField(StructField[type[c_float]]):
    """A class to represent a float field in a C struct."""

    c_type: type[c_float] = c_float


CHAR = CharField  # "c" is a char type in C
UBYTE = UByteField  # "B" is an unsigned char type in C

UINT8 = UINT8Field  # "B" is an unsigned char type in C
UINT16 = UINT16Field  # "H" is an unsigned short type in C
UINT32 = UINT32Field  # "I" is an unsigned int type in C
UINT64 = UINT64Field  # "Q" is an unsigned long long type in C

INT8 = INT8Field  # "b" is a signed char type in C
INT16 = INT16Field  # "h" is a signed short type in C
INT32 = INT32Field  # "i" is a signed int type in C
INT64 = INT64Field  # "q" is a signed long long type in C

BOOL = BoolField  # "?" is a boolean type in C

STRING_TYPE: Final[tuple[str]] = (CHAR.fmt,)  # "c" is a char type in C
"""String type (char)."""

INT_TYPE: Final[tuple[str, ...]] = (
    UINT8.fmt,  # "B"
    UINT16.fmt,  # "H"
    UINT32.fmt,  # "I"
    UINT64.fmt,  # "Q"
    INT8.fmt,  # "b"
    INT16.fmt,  # "h"
    INT32.fmt,  # "i"
    INT64.fmt,  # "q"
)
"""Integer types (signed and unsigned)."""

FLOAT_TYPE: Final[tuple[str, ...]] = (
    FloatField.fmt,  # "f"
    DoubleField.fmt,  # "d"
)
"""Float types (float and double)."""

BYTE_TYPE: Final[tuple[str]] = (UBYTE.fmt,)  # "B" is an unsigned char type in C
"""Byte type (unsigned char)."""
VOID_TYPE: Final[tuple[str]] = (VoidPtrField.fmt,)  # "P" is a void pointer type in C
"""Void pointer type."""
BOOLEAN_TYPE: Final[tuple[str]] = (BOOL.fmt,)  # "?" is a boolean type in C
"""Boolean type."""

BITS_IN_BYTE: Final = 8
"""Number of bits in a byte."""
MIN_VALUE: Final = 0x00
"""Minimum hex value."""
MAX_VALUE: Final = 0xFF
"""Maximum hex value."""

INT8_MIN: Final[int] = INT8.low
"""Minimum value for INT8."""
INT16_MIN: Final[int] = INT16.low
"""Minimum value for INT16."""
INT32_MIN: Final[int] = INT32.low
"""Minimum value for INT32."""
INT64_MIN: Final[int] = INT64.low
"""Minimum value for INT64."""

INT8_MAX: Final[int] = INT8.high
"""Maximum value for INT8."""
INT16_MAX: Final[int] = INT16.high
"""Maximum value for INT16."""
INT32_MAX: Final[int] = INT32.high
"""Maximum value for INT32."""
INT64_MAX: Final[int] = INT64.high
"""Maximum value for INT64."""

UINT8_MIN: Final[int] = UINT8.low
"""Minimum value for UINT8."""
UINT16_MIN: Final[int] = UINT16.low
"""Minimum value for UINT16."""
UINT32_MIN: Final[int] = UINT32.low
"""Minimum value for UINT32."""
UINT64_MIN: Final[int] = UINT64.low
"""Minimum value for UINT64."""

UINT8_MAX: Final[int] = UINT8.high
"""Maximum value for UINT8."""
UINT16_MAX: Final[int] = UINT16.high
"""Maximum value for UINT16."""
UINT32_MAX: Final[int] = UINT32.high
"""Maximum value for UINT32."""
UINT64_MAX: Final[int] = UINT64.high
"""Maximum value for UINT64."""
