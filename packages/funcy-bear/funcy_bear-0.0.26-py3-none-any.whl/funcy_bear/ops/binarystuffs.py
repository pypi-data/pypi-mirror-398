"""Utility functions for working with binary integer types using ctypes."""

from ctypes import sizeof
from functools import cache

from funcy_bear.constants.binary_types import BITS_IN_BYTE, MIN_VALUE


@cache
def is_signed(ctype: type) -> bool:
    """Check if a ctypes integer type is signed."""
    try:
        return ctype(-1).value == -1
    except TypeError:
        return False


@cache
def to_bits(n: int) -> int:
    """Get the number of bits in n bytes."""
    return n * BITS_IN_BYTE


@cache
def get_int_info(ctype: type) -> tuple[int, int, bool]:
    """Get size in bytes and signedness of a ctypes integer type.

    Args:
        ctype: A ctypes integer type.

    Returns:
        A tuple of (size in bytes, number of bits, is signed).
    """
    size: int = sizeof(ctype)
    return size, to_bits(size), is_signed(ctype)


@cache
def shift_left(n: int) -> int:
    """1 << n_bits.

    Args:
        n: Number of bits to shift.

    Returns:
        The value of 1 << n.
    """
    return 1 << n


@cache
def shift_right(n: int) -> int:
    """1 >> n_bits.

    Args:
        n: Number of bits to shift.

    Returns:
        The value of 1 >> n.
    """
    return 1 >> n


@cache
def min_int(ctype: type | None = None, b: int | None = None, s: bool | None = None) -> int:
    """Get the minimum value of a ctypes integer type.

    Args:
        ctype: Optional ctypes integer type.
        b: Optional number of bits (overrides ctype).
        s: Optional signedness (overrides ctype).

    Returns:
        The minimum value.
    """
    if b is None or s is None:
        if ctype is None:
            raise ValueError("Either ctype or both b and s must be provided")
        _, b, s = get_int_info(ctype)
    return -(shift_left(b - 1)) if s else MIN_VALUE


@cache
def max_int(ctype: type | None = None, b: int | None = None, s: bool | None = None) -> int:
    """Get the maximum value of a ctypes integer type.

    Args:
        ctype: Optional ctypes integer type.
        b: Optional number of bits (overrides ctype).
        s: Optional signedness (overrides ctype).

    Returns:
        The maximum value.
    """
    if b is None or s is None:
        if ctype is None:
            raise ValueError("Either ctype or both b and s must be provided")
        _, b, s = get_int_info(ctype)
    return (shift_left(b - 1)) - 1 if s else (shift_left(b)) - 1


@cache
def bounds(ctype: type | None = None, b: int | None = None, s: bool | None = None) -> tuple[int, int]:
    """Get the (min, max) bounds of a ctypes integer type.

    Args:
        ctype: Optional ctypes integer type.
        b: Optional number of bits (overrides ctype).
        s: Optional signedness (overrides ctype).

    Returns:
        A tuple of (min, max) bounds.
    """
    return min_int(ctype, b, s), max_int(ctype, b, s)


@cache
def in_bounds(n: int, ctype: type | None = None, b: int | None = None, s: bool | None = None) -> bool:
    """Check if an integer is within the bounds of a ctypes integer type.

    Args:
        n: The integer to check.
        ctype: Optional ctypes integer type.
        b: Optional number of bits (overrides ctype).
        s: Optional signedness (overrides ctype).

    Returns:
        True if n is within bounds, else False.
    """
    lo, hi = bounds(ctype, b, s)
    return lo <= n <= hi


@cache
def is_int_type(n: int, ctype: type) -> bool:
    """Check if n is less than the maximum value of the given ctypes integer type.

    Args:
        n: The integer to check.
        ctype: The ctypes integer type.

    Returns:
        True if n is less than the maximum value, else False.
    """
    return n <= max_int(ctype)


@cache
def is_int_range(n: int, ctype: type) -> bool:
    """Check if n is within the bounds of the given ctypes integer type.

    Args:
        n: The integer to check.
        ctype: The ctypes integer type.

    Returns:
        True if n is within bounds, else False.
    """
    lo, hi = bounds(ctype)
    return lo <= n <= hi


def be_bytes(n: int, ctype: type) -> bytes:
    """Get big-endian bytes for an integer of the given ctypes type.

    Args:
        n: The integer to convert.
        ctype: The ctypes integer type.

    Returns:
        The big-endian bytes representation of n.
    """
    size, bits, signed = get_int_info(ctype)
    if in_bounds(n, ctype, bits, signed):
        return int(n).to_bytes(size, "big", signed=signed)
    raise OverflowError(f"value {n} out of {ctype.__name__} bounds")


def from_be_bytes(b: bytes, signed: bool) -> int:
    """Get integer from big-endian bytes.

    Args:
        b: The big-endian bytes.
        signed: Whether the integer is signed.

    Returns:
        The integer representation of the bytes.
    """
    return int.from_bytes(b, "big", signed=signed)
