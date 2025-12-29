"""Utilities for converting Python types to string representations."""

from collections.abc import Sequence  # noqa: TC003
import datetime
from pathlib import Path
from types import NoneType
from typing import Literal

PossibleStrs = Literal[
    "str",
    "int",
    "float",
    "bool",
    "list",
    "dict",
    "tuple",
    "path",
    "bytes",
    "set",
    "frozenset",
    "datetime",
    "NoneType",
    "Any",
]

TYPE_MAP: dict[type, PossibleStrs] = {
    str: "str",
    bool: "bool",
    int: "int",
    float: "float",
    list: "list",
    dict: "dict",
    tuple: "tuple",
    Path: "path",
    bytes: "bytes",
    set: "set",
    frozenset: "frozenset",
    datetime: "datetime",
    NoneType: "NoneType",
}


def type_to_str(tp: type, arb_types_allowed: bool = False) -> PossibleStrs:
    """Convert a Python type to its string representation.

    Args:
        tp (type): The Python type to convert.
        arb_types_allowed (bool): Whether to allow arbitrary types. Defaults to False.

    Returns:
        str: The string representation of the type.
    """
    matching: str | None = TYPE_MAP.get(tp)
    if matching is None and not arb_types_allowed:
        raise TypeError(f"Type {tp} is not supported.")
    return matching or "Any"


class CollectionCheck[T]:
    """Check a collection in various ways."""

    def __init__(self, collection: Sequence[T]) -> None:
        """Initialize with a collection."""
        self.collection: Sequence[T] = collection
        self.types: list[PossibleStrs] = [type_to_str(type(item), arb_types_allowed=True) for item in collection]

    @property
    def unique_types(self) -> set[PossibleStrs]:
        """Get unique types in the collection."""
        return set(self.types)
