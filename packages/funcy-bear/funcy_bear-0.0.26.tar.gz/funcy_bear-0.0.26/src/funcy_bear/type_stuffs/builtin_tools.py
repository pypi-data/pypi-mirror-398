"""Utilities for handling Python built-in types and keywords."""

import builtins as _builtins
from collections.abc import Callable  # noqa: TC003
import keyword as _keyword
from types import NoneType


def type_name(tp: str | type) -> str:
    """Get the name of a type, handling built-in types and keywords appropriately.

    Args:
        tp (type): The type to get the name of.

    Returns:
        str: The name of the type.
    """
    if isinstance(tp, str):
        tp = type(tp)
    if tp in (str, int, float, bool, list, dict, tuple, set, NoneType):
        return tp.__name__
    if hasattr(tp, "__name__"):
        name: str = tp.__name__
        if name in dir(_builtins) or _keyword.iskeyword(name):
            return f"{tp.__module__}.{name}"
        return name
    return str(tp)


def check_for_conflicts(
    name: str,
    modifier: Callable | None = None,
    fallback: str = "{name}_",
) -> str:
    """Check if a name conflicts with Python built-ins or keywords.

    If there is a conflict, append an underscore to the name.

    Args:
        name (str): The name to check.
        modifier (Callable | None): Optional function to modify the name if there is a conflict.
        fallback (str): The format string to use if there is a conflict and no modifier is provided.

    Returns:
        str: The original name or the name with an appended underscore if there was a conflict.
    """
    if _keyword.iskeyword(name) or hasattr(_builtins, name):
        name = modifier(name) if modifier else fallback.format(name=name)
    return name
