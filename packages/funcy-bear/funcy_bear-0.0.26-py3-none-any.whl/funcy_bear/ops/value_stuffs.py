"""Utilities for general values and their handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeGuard

from lazy_bear import lazy

if TYPE_CHECKING:
    from collections.abc import Mapping
    from inspect import isclass

    from funcy_bear.constants.type_constants import LitFalse, LitTrue
else:
    isclass = lazy("inspect", "isclass")


def not_equal_value(obj: Any, value: Any | tuple[Any, ...]) -> bool:
    """Check if an object is not equal to a specific value or any value in a tuple.

    Args:
        obj: The object to check.
        value: The value or tuple of values to compare against.

    Returns:
        bool: True if the object is not equal to the value(s), False otherwise.
    """
    if isinstance(value, tuple):
        return obj not in value
    return obj != value


def equal_value(obj: Any, value: Any | tuple[Any, ...]) -> bool:
    """Check if an object is equal to a specific value or any value in a tuple.

    Args:
        obj: The object to check.
        value: The value or tuple of values to compare against.

    Returns:
        bool: True if the object is equal to the value(s), False otherwise.
    """
    if isinstance(value, tuple):
        return obj in value
    return obj == value


def get_instance(obj: type | Any) -> Any | None:
    """Get an instance of a class or return the object itself if it's not a class.

    Args:
        service (Any): The service class or instance.
    """
    try:
        if isclass(obj):
            return obj()
        return obj
    except Exception:
        return None


def has_exception(e: Exception | None) -> TypeGuard[Exception]:
    """Check if an exception is present.

    Args:
        e: The exception to check
    Returns:
        True if an exception is present, False otherwise
    """
    return e is not None


def always_true(*_, **__) -> LitTrue:
    """A function that always returns True."""
    return True


def always_false(*_, **__) -> LitFalse:
    """A function that always returns False."""
    return False


def has_nested_dicts(mapping: Mapping) -> bool:
    """Quick check if dict contains any nested dicts.

    Args:
        mapping: The mapping to check.

    Returns:
        True if any value in the mapping is a dict, False otherwise.
    """
    return any(isinstance(v, dict) for v in mapping.values())
