"""A module defining a class to represent positive infinity."""

from __future__ import annotations

import math
import sys
from typing import Any, Final, Self, final

MAX_SIZE: Final = sys.maxsize


def is_infinite(obj: Any) -> bool:
    """Check if an obj is infinite (positive or negative).

    Args:
        obj: The obj to check.

    Returns:
        bool: True if the obj is infinite, False otherwise.
    """
    return isinstance(obj, float) and math.isinf(obj)


@final
class Infinity(int):
    """A class representing positive infinity."""

    def __new__(cls) -> Self:
        """Create a new instance of Infinity."""
        return super().__new__(cls, MAX_SIZE)

    def __init__(self) -> None:
        """Initialize the Infinity instance."""
        self.inf = float("inf")

    def __hash__(self) -> int:
        """Return the hash of Infinity."""
        return hash(self.inf)

    def __repr__(self) -> str:
        """Return the string representation of Infinity."""
        return "Infinity"

    def __str__(self) -> str:
        """Return the string representation of Infinity."""
        return "Infinity"

    def __gt__(self, other: Any) -> bool:
        """Infinity is greater than any other value."""
        if isinstance(other, (int, float)):
            return True
        return NotImplemented

    def __lt__(self, other: Any) -> bool:
        """Infinity is not less than any other value."""
        if isinstance(other, (int, float)):
            return False
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        """Infinity is only equal to itself."""
        return isinstance(other, Infinity)

    def __ne__(self, other: object) -> bool:
        """Infinity is not equal to any other value except itself."""
        return not self.__eq__(other)

    def __le__(self, other: Any) -> bool:
        """Infinity is not less than or equal to any other value except itself."""
        if isinstance(other, (int, float)):
            return False
        return NotImplemented

    def __ge__(self, other: Any) -> bool:
        """Infinity is greater than or equal to any other value."""
        if isinstance(other, (int, float)):
            return True
        return NotImplemented

    def __add__(self, other: Any) -> float:  # type: ignore[override]
        """Adding anything to Infinity results in Infinity."""
        if isinstance(other, (int, float)):
            return self.inf
        return NotImplemented

    def __sub__(self, other: Any) -> float:  # type: ignore[override]
        """Subtracting anything from Infinity results in Infinity."""
        if isinstance(other, (int, float)):
            return self.inf
        return NotImplemented

    def __mul__(self, other: Any) -> float:  # type: ignore[override]
        """Multiplying Infinity by a positive number results in Infinity."""
        if isinstance(other, (int, float)) and other > 0:
            return self.inf
        if isinstance(other, (int, float)) and other < 0:
            raise ValueError("Multiplying Infinity by a negative number is undefined.")
        return NotImplemented

    def __truediv__(self, other: Any) -> float:
        """Dividing Infinity by a positive number results in Infinity."""
        if isinstance(other, (int, float)) and other > 0:
            return self.inf
        if isinstance(other, (int, float)) and other < 0:
            raise ValueError("Dividing Infinity by a negative number is undefined.")
        return NotImplemented

    def __rtruediv__(self, other: Any) -> float:
        """Dividing a number by Infinity results in 0."""
        if isinstance(other, (int, float)):
            return 0.0
        return NotImplemented

    def __int__(self) -> int:
        """Return the integer representation of Infinity."""
        return MAX_SIZE

    def __float__(self) -> float:
        """Return the float representation of Infinity."""
        return self.inf


INFINITE: Final = Infinity()
