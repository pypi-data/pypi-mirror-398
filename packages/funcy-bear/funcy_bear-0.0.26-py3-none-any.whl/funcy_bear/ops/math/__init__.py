"""A set of helper math functions."""

from funcy_bear.ops.math.general import (
    clamp,
    inv_lerp,
    lerp,
    map_range,
    neg,
    normalize,
    relative_norm,
    remap,
    sign,
    smoothstep,
)
from funcy_bear.ops.math.infinity import INFINITE

__all__ = [
    "INFINITE",
    "clamp",
    "inv_lerp",
    "lerp",
    "map_range",
    "neg",
    "normalize",
    "relative_norm",
    "remap",
    "sign",
    "smoothstep",
]
