from collections.abc import Callable
from typing import Literal, TypeVar

from singleton_base import SingletonBase

InputType = TypeVar("InputType")
"""A generic type variable for input types."""

QueryTest = Callable[[InputType], bool]
"""A type alias for a callable that takes an input and returns a boolean."""

OpType = Literal["path", "==", "!=", ">", "<", ">=", "<=", "exists", "and", "or", "not", "matches", "all", "search"]
"""A type alias for the supported query operation types."""


def callable_test(value: QueryTest) -> QueryTest:
    """Create a callable that checks for equality with the given value."""
    return value


class MissingValue(SingletonBase):
    """A sentinel class to represent a missing value in queries."""

    def __lt__(self, other: object) -> bool:
        return False

    def __le__(self, other: object) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MissingValue)

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, MissingValue)

    def __gt__(self, other: object) -> bool:
        return False

    def __ge__(self, other: object) -> bool:
        return False

    def __hash__(self) -> int:
        return hash("MissingValue")

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "MISSING"


MISSING_VALUE = MissingValue()
"""A singleton instance of MissingValue to be used as a sentinel."""
