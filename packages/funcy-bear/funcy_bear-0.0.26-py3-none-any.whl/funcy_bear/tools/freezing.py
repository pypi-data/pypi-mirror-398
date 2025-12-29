"""Utilities for making objects immutable and hashable.

Taken from Frozen Cub repo upgraded with Cython.
"""

from frozen_cub.frozen import FrozenDict, freeze

__all__ = ["FrozenDict", "freeze"]
