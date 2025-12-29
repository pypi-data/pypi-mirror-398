"""A module for adding rich comparison methods to classes based on an attribute."""

from __future__ import annotations

from types import NotImplementedType  # noqa: TC003
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

PRIMITIVE_TYPES: tuple[type[str], type[int], type[float], type[bool]] = (str, int, float, bool)


def add_comparison_methods[T](attr: str) -> Callable[[type[T]], type[T]]:
    """Class decorator that adds rich comparison methods based on a specific attribute.

    This decorator adds __eq__, __ne__, __lt__, __gt__, __le__, __ge__, and __hash__ methods
    to a class, all of which delegate to the specified attribute. This allows instances
    of the decorated class to be compared with each other, as well as with primitive values
    that the attribute can be compared with.

    Args:
        attr: Name of the instance attribute to use for comparisons

    Returns:
        Class decorator function that adds comparison methods to a class

    Example:
        @add_comparison_methods('name')
        class Person:
            def __init__(self, name):
                self.name = name
    """

    def decorator(cls: type[T]) -> type[T]:
        def extract_comparable_value(self: object, other: Any) -> NotImplementedType | Any:  # noqa: ARG001
            """Helper to extract the comparable value from the other object."""
            if isinstance(other, PRIMITIVE_TYPES):
                return other

            if hasattr(other, attr):
                return getattr(other, attr)

            return NotImplemented

        def eq(self: object, other: Any) -> NotImplementedType | bool:
            """Equal comparison method (__eq__)."""
            other_val: NotImplementedType | Any = extract_comparable_value(self, other)
            if other_val is NotImplemented:
                return NotImplemented
            return getattr(self, attr) == other_val

        def ne(self: object, other: Any) -> NotImplementedType | bool:
            """Not equal comparison method (__ne__)."""
            other_val: NotImplementedType | Any = extract_comparable_value(self, other)
            if other_val is NotImplemented:
                return NotImplemented
            return getattr(self, attr) != other_val

        def lt(self: object, other: Any) -> NotImplementedType | bool:
            """Less than comparison method (__lt__)."""
            other_val: NotImplementedType | Any = extract_comparable_value(self, other)
            if other_val is NotImplemented:
                return NotImplemented
            return getattr(self, attr) < other_val

        def gt(self: object, other: Any) -> NotImplementedType | bool:
            """Greater than comparison method (__gt__)."""
            other_val: NotImplementedType | Any = extract_comparable_value(self, other)
            if other_val is NotImplemented:
                return NotImplemented
            return getattr(self, attr) > other_val

        def le(self: object, other: Any) -> NotImplementedType | bool:
            """Less than or equal comparison method (__le__)."""
            other_val: NotImplementedType | Any = extract_comparable_value(self, other)
            if other_val is NotImplemented:
                return NotImplemented
            return getattr(self, attr) <= other_val

        def ge(self: object, other: Any) -> NotImplementedType | bool:
            """Greater than or equal comparison method (__ge__)."""
            other_val: NotImplementedType | Any = extract_comparable_value(self, other)
            if other_val is NotImplemented:
                return NotImplemented
            return getattr(self, attr) >= other_val

        def hash_method(self: object) -> int:
            """Generate hash based on the attribute used for equality."""
            return hash(getattr(self, attr))

        cls.__eq__ = eq
        cls.__ne__ = ne
        cls.__lt__ = lt  # type: ignore[assignment]
        cls.__gt__ = gt  # type: ignore[assignment]
        cls.__le__ = le  # type: ignore[assignment]
        cls.__ge__ = ge  # type: ignore[assignment]
        cls.__hash__ = hash_method

        return cls

    return decorator


class ComparisonMethods[T]:
    """A way to get type hints for the added methods."""

    def __eq__(self, other: object) -> NotImplementedType | bool:
        return NotImplemented

    def __ne__(self, other: object) -> NotImplementedType | bool:
        return NotImplemented

    def __lt__(self, other: Any) -> NotImplementedType | bool:
        return NotImplemented

    def __gt__(self, other: Any) -> NotImplementedType | bool:
        return NotImplemented

    def __le__(self, other: Any) -> NotImplementedType | bool:
        return NotImplemented

    def __ge__(self, other: Any) -> NotImplementedType | bool:
        return NotImplemented

    def __hash__(self) -> int:
        return super().__hash__()
