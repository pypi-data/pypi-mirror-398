"""Utility functions for dictionary operations."""

from __future__ import annotations

from typing import Any, Literal

from funcy_bear.injection import Provide, inject_tools
from funcy_bear.ops._di_containers import Factory, FactoryContainer

from .key_counts import KeyCounts

type ConflictResolutionChoice = Literal["error", "skip_last", "skip_first"]


def dict_verify(*dicts: dict[Any, Any]) -> None:
    """Verify that all arguments are dictionaries.

    Args:
        *dicts (dict): Dictionaries to verify.

    Raises:
        TypeError: If any argument is not a dictionary.
    """
    from funcy_bear.type_stuffs.validate import all_same_type  # noqa: PLC0415

    if not all_same_type(*dicts):
        raise TypeError("All arguments must be of the same type.")


@inject_tools(default_factory="dict")
def basic_merge[T](
    *dicts: dict[Any, T],
    factory: Factory = Provide[FactoryContainer.factory],
) -> dict[Any, T]:
    """Merge multiple dictionaries into one.

    Args:
        *dicts (dict): Dictionaries to merge.
        factory (Callable): Factory function to create the result dictionary,
            by default it is injected via DI but can be overridden by providing
            a factory parameter.

    Returns:
        dict: Merged dictionary.
    """
    dict_verify(*dicts)
    result: Any = factory()
    for d in dicts:
        result.update(d)
    return result


def key_counts(*d: dict[Any, Any]) -> KeyCounts:
    """Count occurrences of each key across multiple dictionaries, delineating the different dictionaries.

    Args:
        *d (dict): Dictionaries to count keys from.

    Returns:
        dict: A dictionary mapping each key to its occurrence count.

    Example:
        >>> key_counts({"a": 1, "b": 2}, {"b": 3, "c": 4})
        {'a': 1, 'b': 2, 'c': 1}
    """
    dict_verify(*d)
    counts = KeyCounts()
    for dictionary in d:
        for index, key in enumerate(dictionary):
            counts.plus(key, index, dictionary)
    return counts


def quick_dupe_check(*d: dict[Any, Any]) -> set[Any]:
    """Quickly check for duplicate keys across multiple dictionaries.

    Args:
        *d (dict): Dictionaries to check for duplicate keys.

    Returns:
        set: A set of duplicate keys found across the dictionaries.

    Example:
        >>> quick_dupe_check({"a": 1, "b": 2}, {"b": 3, "c": 4})
        {'b'}
    """
    seen_keys: set[Any] = set()
    dupes: set[Any] = set()
    for dicts in d:
        for k in dicts:
            if k in seen_keys:
                dupes.add(k)
            else:
                seen_keys.add(k)
    return dupes


def update_keys(d: dict[Any, Any], key_map: dict[Any, Any]) -> dict[Any, Any]:
    """Update keys in a dictionary based on a provided mapping.

    Args:
        d (dict): The original dictionary.
        key_map (dict): A mapping of old keys to new keys.

    Returns:
        dict: A new dictionary with updated keys.

    Example:
        >>> update_keys({"a": 1, "b": 2}, {"a": "alpha", "b": "beta"})
        {'alpha': 1, 'beta': 2}
    """
    dict_verify(d, key_map)
    return {key_map.get(k, k): v for k, v in d.items()}


def merge[T](
    *dicts: dict[Any, T],
    overwrite_keys: bool = True,
    conflict_choice: ConflictResolutionChoice = "error",
) -> dict[Any, T]:
    """Combine two dictionaries into one.

    Args:
        *dicts (dict[Any, T]): Dictionaries to combine.
        overwrite_keys (bool): If True, values from later dictionaries will overwrite those from earlier ones for duplicate keys. Defaults to True.
        conflict_choice (ConflictResolutionChoice): Strategy for handling key conflicts when overwrite_keys is False.
            - "error": Raise a ValueError on key conflict.
            - "skip_last": Keep the first occurrence, skip subsequent ones.
            - "skip_first": Keep the last occurrence, skip previous ones.

    Returns:
        dict[Any, T]: A new dictionary containing all items from both input dictionaries.

    Example:
        >>> combine_dicts({"a": 1, "b": 2}, {"b": 3, "c": 4})
        {'a': 1, 'b': 3, 'c': 4}
    """
    dict_verify(*dicts)
    if overwrite_keys:
        return basic_merge(*dicts)

    dupes: set[Any] = quick_dupe_check(*dicts)
    match conflict_choice:
        case "error":
            if dupes:
                raise ValueError(f"Key conflict detected for keys: {', '.join(str(k) for k in dupes)}")
        case "skip_last":
            return basic_merge(*reversed(dicts))
        case "skip_first":
            return basic_merge(*dicts)
    raise ValueError(f"Invalid conflict resolution choice: {conflict_choice}")
