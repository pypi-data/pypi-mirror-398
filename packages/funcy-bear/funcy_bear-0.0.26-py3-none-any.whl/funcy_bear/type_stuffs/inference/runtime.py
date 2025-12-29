"""Utilities for inferring string values to their respective types.

This might be useful in serialization/deserialization scenarios, config parsing, or
any situation where types need to be inferred from string representations.
"""

from __future__ import annotations

from contextlib import suppress
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, overload

from funcy_bear.sentinels import CONTINUE
from funcy_bear.type_stuffs.builtin_tools import type_name
from funcy_bear.type_stuffs.conversions import PossibleStrs, eval_to_native, eval_to_type_str, type_to_str
from funcy_bear.type_stuffs.validate import (
    all_same_type,
    is_collection_type,
    is_dict,
    is_instance_of,
    is_list,
    is_set,
    is_str,
    is_tuple,
)
from funcy_bear.type_stuffs.validators.predicates import is_falsy
from lazy_bear import lazy

if TYPE_CHECKING:
    from frozen_cub.dispatcher import Dispatcher
    from frozen_cub.frozen import freeze
else:
    Dispatcher = lazy("frozen_cub.dispatcher", "Dispatcher")
    freeze = lazy("frozen_cub.frozen", "freeze")

ACCEPTABLE_TYPE_STRS: tuple[str, ...] = ("bool", "int", "float", "bytes", "list", "dict", "tuple", "set", "NoneType")
ACCEPTABLE_TYPES: tuple[type, ...] = (int, float, bool, list, dict, tuple, set, bytes)


class Inference:
    """Class to find the inner type of array-like structures."""

    def __init__(
        self,
        value: Any | None = None,
        path_as_str: bool = False,
        arb_types_allowed: bool = False,
    ) -> None:
        """Initialize with a value to infer its type."""
        self._value: Any | None = value
        self.path_as_str: bool = path_as_str
        self.arb_types_allowed: bool = arb_types_allowed

    def infer_type(self, v: Any | None = None, prime_types_only: bool = False) -> str:
        """Infer the type of the value and return it as a string."""
        if v is not None:
            self.value = v
        value: str = self._infer_type(prime_types_only=prime_types_only)
        self.reset()
        return value

    def _infer_type(self, prime_types_only: bool = False) -> str:
        """Infer the inner type of an array-like structure (list, tuple, set)."""
        self.value = to_inferred_type(self.value, prime_types_only, self)
        return self.value

    def reset(self) -> None:
        """Reset the stored value to None."""
        self._value = None

    @property
    def value(self) -> Any:
        """Get the current value."""
        if self._value is None:
            raise ValueError("Value has already been consumed.")
        return self._value

    @value.setter
    def value(self, new_value: Any | None) -> None:
        """Set a new value."""
        self._value = new_value

    @property
    def all_value_types(self) -> set[str]:
        """Get a set of all unique types in the collection."""
        if not is_collection_type(self.value):
            return set()
        if isinstance(self.value, dict):
            return {str_type(v) for v in self.value.values()}
        return {str_type(v) for v in self.value}

    def __len__(self) -> int:
        """Get the length of the collection if applicable, otherwise 0."""
        return len(self.value) if hasattr(self.value, "__len__") else 0


infer = Dispatcher(arg="value")


@infer.dispatcher()
def to_inferred_type(value: Any, prime_types_only: bool, infer: Inference) -> str:
    """Default inference for types not specifically handled."""
    try:
        return type_to_str(type(value))
    except Exception:
        return "Any"


@infer.register(is_str)
def _is_str(value: str, prime_types_only: bool, infer: Inference) -> str:
    value_eval: Any = eval_to_native(value, is_instance_of, types=ACCEPTABLE_TYPES)
    if str_to_bool(value, as_str=True) == "bool":
        return "bool"
    if path_check(value, path_as_str=False):
        return "path"
    if value_eval is CONTINUE:
        return str_type(value)
    return to_inferred_type(value_eval, prime_types_only, infer)


@infer.register(is_collection_type, is_falsy)
def _empty_collection(value: Any, prime_types_only: bool, infer: Inference) -> str:
    return type_to_str(type(value))


@infer.register(is_tuple)
def _is_tuple(value: tuple, prime_types_only: bool, infer: Inference) -> str:
    if prime_types_only:
        return "tuple"
    if not value or (len(infer) == 1 and value == ...):
        return type_brackets("tuple", "Any")
    type_values: set[str] = {type_to_str(type(v)) for v in value}
    if len(type_values) == 1 and len(value) == 1:
        return type_brackets("tuple", next(iter(type_values)))
    if len(type_values) == 1 and len(value) > 1:
        return type_brackets("tuple", f"{type_to_str(type(value[0]))}, ...")
    return type_brackets("tuple", ", ".join(sorted(type_values)))


@infer.register(is_list)
def _is_list(value: list, prime_types_only: bool, infer: Inference) -> str:
    if prime_types_only:
        return "list"
    if all_same_type(*value):
        return type_brackets("list", f"{type_to_str(type(value[0]))}")
    type_values: set[str] = {type_to_str(type(v)) for v in value}
    if len(type_values) == 1:
        return type_brackets("list", next(iter(type_values)))
    return type_brackets("list", " | ".join(sorted(type_values)))


@infer.register(is_set)
def _is_set(value: set, prime_types_only: bool, infer: Inference) -> str:
    if prime_types_only:
        return "set"
    type_values: set[str] = {type_to_str(type(v)) for v in value}
    if len(type_values) == 1:
        return type_brackets("set", f"{type_to_str(type(next(iter(value))))}")
    return type_brackets("set", " | ".join(sorted(type_values)))


@infer.register(is_dict)
def _is_dict(value: dict, prime_types_only: bool, infer: Inference) -> str:
    if prime_types_only:
        return "dict"
    dict_key: set[str] = {type_name(k) for k in value}
    key_type: str = type_name(next(iter(value))) if len(dict_key) == 1 else "Any"
    type_values: set[str] = {type_to_str(type(v)) for v in value.values()}
    if len(type_values) == 1:
        val: Any = next(iter(value.values()))
        return type_brackets("dict", f"{key_type}, {type_to_str(type(val))}")
    return type_brackets("dict", f"{key_type}, {' | '.join(sorted(type_values))}")


def type_brackets(t: str, s: str) -> str:
    """Helper to format type strings."""
    return f"{t}[{s}]"


def path_check(value: str, path_as_str: bool) -> bool:
    """Check if a string represents a valid filesystem path."""
    with suppress(Exception):
        if not path_as_str:
            return Path(value).exists()
    return False


@lru_cache(maxsize=128)
def str_type(value: str) -> str:
    """Infer the type of a str wrapped value and return it as a string.

    Args:
        value(str): The value to infer the type of that is wrapped in a str.

    Returns:
        A string representing the inferred type.
    """
    from funcy_bear.api import if_in_list

    string_value: PossibleStrs = eval_to_type_str(value, if_in_list, lst=freeze(ACCEPTABLE_TYPE_STRS))
    if string_value is not CONTINUE:
        return string_value
    return "str"


@lru_cache(maxsize=128)
def infer_type(
    value: str | Any,
    path_as_str: bool = False,
    arb_types_allowed: bool = False,
    prime_types_only: bool = False,
) -> str:
    """Infer the type of a str wrapped value and return it as a string.

    Args:
        value (str): The value to infer the type of that is wrapped in a str.
        path_as_str (bool): Whether to treat valid filesystem paths as strings. Defaults to False.

    Returns:
        str: A string representing the inferred type.
    """
    return Inference(
        value,
        path_as_str=path_as_str,
        arb_types_allowed=arb_types_allowed,
    ).infer_type(prime_types_only=prime_types_only)


@overload
def str_to_bool(val: str, as_str: Literal[True]) -> str: ...


@overload
def str_to_bool(val: str, as_str: Literal[False] = False) -> bool: ...


@lru_cache(maxsize=128)
def str_to_bool(val: str, as_str: bool = False) -> bool | str:
    """Check if a string represents a boolean value, either returning a bool or the string "bool".

    Returns:
        bool: The boolean value.
    """
    value: Any = eval_to_native(str(val).title(), lambda x: isinstance(x, bool))
    if as_str and value is not CONTINUE:
        return "bool"
    return bool(value is not CONTINUE and value)


# ruff: noqa: PLC0415 ARG001


__all__ = ["Inference", "infer_type", "str_to_bool"]
