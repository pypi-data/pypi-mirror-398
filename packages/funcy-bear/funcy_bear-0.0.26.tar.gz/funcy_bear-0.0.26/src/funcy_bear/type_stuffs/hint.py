"""Utility functions and classes for type checking and type hinting."""

from typing import TYPE_CHECKING


def TypeHint[T](hint: type[T]) -> type[T]:  # noqa: N802
    """Add type hints from a specified class to a base class:

    >>> class Foo(TypeHint(Bar)):
    ...     pass

    This would add type hints from class ``Bar`` to class ``Foo``.

    Args:
        hint: The class to use for type hints.

    Returns:
        A base class with type hints from the specified class during
        type checking, otherwise a generic base class. We use a generic
        base class at runtime instead of object to avoid potential MRO
        conflicts and general generic support issues.
    """
    if TYPE_CHECKING:
        return hint  # This adds type hints for type checkers

    class _TypeHintBase: ...

    return _TypeHintBase
