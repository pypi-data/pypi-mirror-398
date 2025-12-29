"""Tools for type coercion and conversion."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from types import NoneType
from typing import TYPE_CHECKING, Any

from funcy_bear.sentinels import NOTSET, MissingType
from funcy_bear.type_stuffs.validate import is_mapping, is_object
from lazy_bear import lazy

if TYPE_CHECKING:
    from collections.abc import Callable

    from frozen_cub.frozen import FrozenDict, freeze
else:
    FrozenDict, freeze = lazy("frozen_cub.frozen", "FrozenDict", "freeze")


STR_TO_TYPE: dict[str, type] = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "path": Path,
    "bytes": bytes,
    "set": set,
    "frozenset": frozenset,
    "none": NoneType,
    "nonetype": NoneType,
    "any": type[Any],
}


def coerce_to_type[T](v: Any, t: Callable[[Any], T]) -> T:
    """Coerce a value to the specified type if possible.

    Args:
        v (Any): The value to coerce.
        t (type): The type to which the value should be coerced.

    Returns:
        Any: The coerced value.

    Raises:
        ValueError: If the value cannot be coerced to the specified type.
    """
    try:
        return t(v)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Cannot coerce value {v} of type {type(v).__name__} to {t.__name__}.") from e


def value_to_type[T](container: Any, k: str, t: Callable[[Any], T], d: Any | MissingType = NOTSET) -> T:
    """Get a value from either a mapping or object and coerce it to the specified type if possible.

    Args:
        container (Mapping | object): The mapping or object from which to get the value.
        k (str): The key or attribute name of the value to get.
        t (type): The type to which the value should be coerced.
        d (Any, optional): The default value to use if the key is not found. Defaults to None.

    Returns:
        Any: The coerced value.

    Raises:
        ValueError: If the value cannot be coerced to the specified type.
    """
    if is_object(container):
        if not hasattr(container, k):
            if d is not NOTSET:
                return coerce_to_type(v=d, t=t)
            raise KeyError(f"Key {k} not found in object and no default provided.")
        return coerce_to_type(v=getattr(container, k), t=t)
    if is_mapping(container):
        if k not in container:
            if d is not NOTSET:
                return coerce_to_type(v=d, t=t)
            raise KeyError(f"Key {k} not found in mapping and no default provided.")
        return coerce_to_type(v=container[k], t=t)
    raise ValueError("Container must be a mapping or an object with attributes.")


class StrTypeHelper:
    """Helper class for string to type conversions."""

    def __init__(self, tp: str, d: type = NoneType, custom_map: dict | None = None) -> None:
        """Init with type, default, and a custom map, if any."""
        self.tp: str = tp.strip().lower()
        self.default: type = d
        self.custom_map: dict = custom_map or {}

    @property
    def type_map(self) -> dict[str, type]:
        """The combined map to use for type lookups."""
        return {**STR_TO_TYPE, **self.custom_map}

    def to_type(self) -> type:
        """Convert a string representation of a type to an actual type.

        Args:
            str_type (str): The string representation of the type.

        Returns:
            type: The corresponding Python type, or Any if not found.
        """
        return self.type_map.get(self.tp, type[Any] if self.default is NoneType else self.default)


@lru_cache(maxsize=128)
def cached_str_to_type(str_type: str, default: Any = NOTSET, custom_map: FrozenDict | None = None) -> type:
    """A cached version of str_to_type that only allows hashable inputs.

    Args:
        str_type (str): The string representation of the type.
        default (type, optional): The default type to return if the string is not found. Defaults to NOTSET.

    Returns:
        type: The corresponding Python type, or the default if not found.
    """
    if custom_map is None:
        return STR_TO_TYPE.get(str_type.strip().lower(), type[Any] if default is NOTSET else default)

    return StrTypeHelper(str_type, default, custom_map=custom_map).to_type()


def str_to_type(str_type: str, default: Any = NOTSET, custom_map: dict | None = None) -> type:
    """Convert a string representation of a type to an actual type.

    Args:
        str_type (str): The string representation of the type.
        default (type, optional): The default type to return if the string is not found. Defaults to NOTSET sentinel.
        custom_map (dict, optional): A custom mapping of string to type. Defaults to None.

    Returns:
        type: The corresponding Python type, or the default if not found.
    """
    if custom_map is None:
        return cached_str_to_type(str_type=str_type, default=default)

    return cached_str_to_type(str_type, default, custom_map=freeze(custom_map))


__all__ = [
    "STR_TO_TYPE",
    "StrTypeHelper",
    "cached_str_to_type",
    "coerce_to_type",
    "str_to_type",
    "value_to_type",
]
