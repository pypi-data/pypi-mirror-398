"""Helpers for working with generic types and validation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, get_args as _get_args

if TYPE_CHECKING:
    from funcy_bear.exceptions import ObjectTypeError


class TypeHelper[T]:
    """Utility wrapper offering common generic-introspection helpers."""

    def __init__(self, cls: type[T]) -> None:
        """Initialize with the class to wrap."""
        self.cls: type[T] = cls

    @property
    def orig_bases(self) -> tuple[type, ...]:
        """Get the original bases of the class.

        Returns:
            tuple[type, ...]: The original bases of the class.
        """
        if not hasattr(self.cls, "__orig_bases__"):
            raise AttributeError(f"Class {self.name} does not have __orig_bases__ attribute.")
        return getattr(self.cls, "__orig_bases__", ())

    @property
    def name(self) -> str:
        """Return the name of the class."""
        from funcy_bear.type_stuffs.builtin_tools import type_name  # noqa: PLC0415

        return type_name(self.cls)

    @property
    def args(self) -> tuple[Any, ...]:
        """Return generic arguments captured on the first orig base.

        Returns:
            tuple[Any, ...]: The generic arguments.
        """
        return _get_args(self.orig_bases[0])

    @property
    def mro(self) -> tuple[type, ...]:
        """Get the method resolution order (MRO) of the class.

        Returns:
            tuple[type, ...]: The MRO of the class.
        """
        return self.cls.__mro__

    @property
    def tp_count(self) -> int:
        """Return the number of type parameters captured.

        Returns:
            int: The number of type parameters.
        """
        return len(self.args)

    def get_type_param(self, index: int = 0) -> type:
        """Return the type parameter at the specified index."""
        args: tuple[Any, ...] = self.args
        if index < 0 or index >= len(args):
            raise IndexError(f"Index {index} is out of range for type parameters of class {self.name}.")
        return args[index]

    def validate_type(self, value: Any, exception: type[ObjectTypeError] | None = None) -> None:
        """Validate that the value is an instance of the wrapped class."""
        from funcy_bear.type_stuffs.builtin_tools import type_name  # noqa: PLC0415

        if not isinstance(value, self.cls):
            if exception is None:
                raise TypeError(f"Expected object of type {self.name}, but got {type_name(value)}.")
            raise exception(expected=self.cls, received=type(value))


def type_param(cls: type, index: int = 0) -> type:
    """Return the type parameter at the specified index for the given class."""
    return TypeHelper(cls).get_type_param(index=index)


def validate_type(value: Any, expected: type, exception: type[ObjectTypeError] | None = None) -> None:
    """Validate that the value is an instance of the expected type."""
    TypeHelper(expected).validate_type(value=value, exception=exception)


def num_type_params(cls: type) -> int:
    """Return the number of type parameters for the given class."""
    return TypeHelper(cls).tp_count


def all_same_type(*seq: Any) -> bool:
    """Check if all elements in the sequence are of the same type."""
    if not seq:
        raise ValueError("The sequence must contain at least one element.")
    first_type = type(seq[0])
    return all(isinstance(item, first_type) for item in seq[1:])


__all__ = [
    "TypeHelper",
    "all_same_type",
    "num_type_params",
    "type_param",
    "validate_type",
]
