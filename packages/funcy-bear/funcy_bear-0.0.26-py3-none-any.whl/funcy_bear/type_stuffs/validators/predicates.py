"""Runtime predicates used across type validation helpers."""

from __future__ import annotations

from collections.abc import Callable, MutableMapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeGuard

from funcy_bear.constants.type_constants import ArrayLike, JSONLike, MappingExcludes, ObjExclude, SequenceExclude
from lazy_bear import LazyLoader

if TYPE_CHECKING:
    import ast
else:
    ast = LazyLoader("ast")


def is_truthy(value: Any) -> bool:
    """Check if a value is truthy.

    Args:
        value: The value to check.

    Returns:
        True if the value is truthy, else False.
    """
    return bool(value)


def is_falsy(value: Any) -> bool:
    """Check if a value is falsy.

    Args:
        value: The value to check.

    Returns:
        True if the value is falsy, else False.
    """
    return not bool(value)


def is_instance_of(obj: Any, types: type | tuple[type, ...]) -> bool:
    """Check if an object is an instance of the given type(s).

    Args:
        obj (Any): The object to check.
        types (type | tuple[type, ...]): The type or tuple of types to check against

    Returns:
        bool: True if obj is an instance of types, False otherwise.
    """
    return isinstance(obj, types)


def not_instance_of(obj: Any, types: type | tuple[type, ...]) -> bool:
    """Check if an object is not an instance of the given type(s).

    Args:
        obj (Any): The object to check.
        types (type | tuple[type, ...]): The type or tuple of types to check against

    Returns:
        bool: True if obj is not an instance of types, False otherwise.
    """
    return not isinstance(obj, types)


def isa(*types: type) -> Callable[..., bool]:
    """Create a checker function that checks if an object is an instance of the given type(s).

    Args:
        *types (type): The type(s) to check against.

    Returns:
        Callable[[Any], bool]: A function that takes an object and returns True if it is an instance of the given type(s).
    """

    def checker(obj: Any) -> bool:
        return isinstance(obj, types)

    return checker


def is_none(obj: Any) -> bool:
    """Check if an object is None.

    Args:
        obj (Any): The object to check.

    Returns:
        bool: True if obj is None, False otherwise.
    """
    return obj is None


def is_bool(obj: Any) -> bool:
    """Check if an object is a boolean.

    Args:
        obj (Any): The object to check.

    Returns:
        bool: True if obj is a boolean, False otherwise.
    """
    return isinstance(obj, bool)


def is_int(obj: Any, exclude_bool: bool = True) -> bool:
    """Check if an object is an integer.

    Args:
        obj (Any): The object to check.
        exclude_bool (bool): Whether to exclude booleans from being considered integers. Defaults to True.

    Returns:
        bool: True if obj is an integer, False otherwise.
    """
    if exclude_bool:
        return isinstance(obj, int) and not isinstance(obj, bool)
    return isinstance(obj, int)


def is_str(obj: Any) -> bool:
    """Check if an object is a string.

    Args:
        obj (Any): The object to check.

    Returns:
        bool: True if obj is a string, False otherwise.
    """
    return isinstance(obj, str)


def is_float(obj: Any) -> bool:
    """Check if an object is a float.

    Args:
        obj (Any): The object to check.

    Returns:
        bool: True if obj is a float, False otherwise.
    """
    return isinstance(obj, float)


def is_dict(obj: Any) -> bool:
    """Check if an object is a dictionary.

    Args:
        obj (Any): The object to check.

    Returns:
        bool: True if obj is a dictionary, False otherwise.
    """
    return isinstance(obj, dict)


def is_list(obj: Any) -> bool:
    """Check if an object is a list.

    Args:
        obj (Any): The object to check.

    Returns:
        bool: True if obj is a list, False otherwise.
    """
    return isinstance(obj, list)


def is_tuple(obj: Any) -> bool:
    """Check if an object is a tuple.

    Args:
        obj (Any): The object to check.

    Returns:
        bool: True if obj is a tuple, False otherwise.
    """
    return isinstance(obj, tuple)


def is_bytes(obj: Any) -> bool:
    """Check if an object is bytes.

    Args:
        obj (Any): The object to check.

    Returns:
        bool: True if obj is bytes, False otherwise.
    """
    return isinstance(obj, bytes)


def is_set(obj: Any) -> bool:
    """Check if an object is a set.

    Args:
        obj (Any): The object to check.

    Returns:
        bool: True if obj is a set, False otherwise.
    """
    return isinstance(obj, set)


def is_pathlib_path(obj: Any, exists: bool = False) -> TypeGuard[Path]:
    """Check if an object is a pathlib Path.

    Args:
        obj (Any): The object to check.
        exists (bool): Whether to check if the path exists. Defaults to False.

    Returns:
        bool: True if obj is a pathlib Path, False otherwise.
    """
    return isinstance(obj, Path) and (obj.exists() if exists else True)


def is_collection_type(value: Any) -> bool:
    """Check if a value is a collection type (list, tuple, set, dict), excluding strings.

    Args:
        value (Any): The value to check.

    Returns:
        bool: True if value is a collection type, False otherwise.
    """
    if isinstance(value, str):
        try:
            eval_value = ast.literal_eval(value)
            return isinstance(eval_value, (list | tuple | set | dict))
        except (ValueError, SyntaxError):
            return False
    return isinstance(value, (list, tuple, set, dict))


def is_json_like(instance: Any) -> TypeGuard[JSONLike]:
    """Check if an instance is JSON-like (dict or list).

    Args:
        instance (Any): The instance to check.

    Returns:
        bool: True if instance is JSON-like, False otherwise.
    """
    return isinstance(instance, (dict | list))


def is_array_like(instance: Any) -> TypeGuard[ArrayLike]:
    """Check if an instance is array-like (list, tuple, set).

    Args:
        instance (Any): The instance to check.

    Returns:
        bool: True if instance is array-like, False otherwise.
    """
    return isinstance(instance, (list | tuple | set))


def is_mapping(v: Any) -> TypeGuard[MutableMapping]:
    """Check if a document is a mapping type (like dict), excluding certain types.

    Args:
        v (Any): The value to check.

    Returns:
        bool: True if doc is a mapping type, False otherwise.
    """
    return isinstance(v, MutableMapping) or (not isinstance(v, MappingExcludes) and hasattr(v, "__getitem__"))


def is_object(v: Any) -> TypeGuard[object]:
    """Check if a value is an object, excluding certain types.

    Args:
        v (Any): The value to check.

    Returns:
        bool: True if v is an object, False otherwise.
    """
    return not isinstance(v, ObjExclude) and isinstance(v, object)


def is_sequence(v: Any) -> TypeGuard[Sequence]:
    """Check if a value is a sequence, excluding certain types.

    Args:
        v (Any): The value to check.

    Returns:
        bool: True if v is a sequence, False otherwise.
    """
    return isinstance(v, Sequence) and not isinstance(v, SequenceExclude)


__all__ = [
    "is_array_like",
    "is_bool",
    "is_bytes",
    "is_collection_type",
    "is_dict",
    "is_float",
    "is_instance_of",
    "is_int",
    "is_json_like",
    "is_list",
    "is_mapping",
    "is_none",
    "is_object",
    "is_pathlib_path",
    "is_sequence",
    "is_set",
    "is_str",
    "is_tuple",
    "isa",
    "not_instance_of",
]
