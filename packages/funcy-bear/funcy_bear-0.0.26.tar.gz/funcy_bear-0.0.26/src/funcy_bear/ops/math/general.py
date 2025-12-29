"""Utility math functions for Bear Dereth."""

from typing import overload


def relative_norm(value: int, rel: float) -> float:
    """Normalize an integer value to a float between 0 and 1.

    Args:
        value (int): The integer value to normalize.
        rel (float): The relative maximum value for normalization.

    Returns:
        float: The normalized float value.
    """
    return value / rel


def normalize(v: int, mi: int, ma: int) -> float:
    """Normalize an integer value to a float between 0 and 1.

    Args:
        v (int): The integer value to normalize.
        mi (int): The minimum value for normalization.
        ma (int): The maximum value for normalization.

    Returns:
        float: The normalized float value.
    """
    if ma - mi == 0:
        raise ValueError("Maximum and minimum values cannot be the same.")
    return (v - mi) / (ma - mi)


@overload
def clamp(v: int, mi: int, ma: int) -> int: ...


@overload
def clamp(v: float, mi: float, ma: float) -> float: ...


def clamp(v: float, mi: float, ma: float) -> int | float:
    """Confirm that the value is within the specified range.

    Args:
        v (int | float): The value to confirm.
        mi (int | float): The minimum allowable value.
        ma (int | float): The maximum allowable value.

    Returns:
        int | float: The confirmed value.
    """
    return max(mi, min(v, ma))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b.

    Args:
        a (float): Start value.
        b (float): End value.
        t (float): Interpolation factor between 0.0 and 1.0.

    Returns:
        float: Interpolated value.
    """
    return a + (b - a) * clamp(t, 0.0, 1.0)


def inv_lerp(a: float, b: float, t: float) -> float:
    """Inverse linear interpolation between a and b.

    Args:
        a (float): Start value.
        b (float): End value.
        t (float): Value to interpolate.

    Returns:
        float: Interpolation factor between 0.0 and 1.0. If a == b, returns 0.0.
    """
    if a == b:
        return 0.0
    return clamp((t - a) / (b - a), 0.0, 1.0)


def remap(value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """Remap a value from one range to another.

    Args:
        value: The value to remap
        in_min: Input range minimum
        in_max: Input range maximum
        out_min: Output range minimum
        out_max: Output range maximum

    Returns:
        The remapped value
    """
    t: float = inv_lerp(in_min, in_max, value)
    return lerp(out_min, out_max, t)


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Smooth Hermite interpolation between 0 and 1.

    Smoother than linear interpolation - eases in and out.

    Args:
        edge0: Lower edge of the interpolation range
        edge1: Upper edge of the interpolation range
        x: The value to interpolate

    Returns:
        Smoothly interpolated value between 0 and 1
    """
    if edge0 == edge1:
        return 0.0
    t: float = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def sign(x: float) -> int:
    """Return the sign of a number.

    Args:
        x: The number to check

    Returns:
        -1 if negative, 0 if zero, 1 if positive
    """
    return 1 if x > 0 else -1 if x < 0 else 0


def map_range(value: float, in_range: tuple[float, float], out_range: tuple[float, float]) -> float:
    """Remap using tuple ranges for cleaner API.

    Args:
        value: Value to remap
        in_range: (min, max) input range
        out_range: (min, max) output range

    Returns:
        Remapped value
    """
    return remap(value, *in_range, *out_range)


@overload
def neg(v: int) -> int: ...


@overload
def neg(v: float) -> float: ...


def neg(v: float) -> float:
    """Represent a negative number.

    No matter if you pass in a positive or negative number, this will return the negative absolute value.

    Args:
        v: The number to represent as negative

    Returns:
        The negative absolute value of the input
    """
    return -abs(v)
