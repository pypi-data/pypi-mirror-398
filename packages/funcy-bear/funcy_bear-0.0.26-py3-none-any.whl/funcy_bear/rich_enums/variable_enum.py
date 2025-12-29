"""A class for holding constant variable values of various types within an enum."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from .base_value import BaseValue
from .int_enum import RichIntEnum
from .str_enum import RichStrEnum

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class VariableType[T]:
    """A base class for variable metadata types."""

    parser: Callable[[str], T]  # Function to parse the variable value
    description: str  # Description of the variable
    required: bool = False  # Whether the variable is required
    default: Any = None  # Default value if not provided

    @classmethod
    def _name(cls) -> str:
        """Get the name of the variable type."""
        return f"{cls.__name__}Hint"

    @classmethod
    def Hint(cls) -> type:  # noqa: N802
        """Convert this to a class that has all the attributes but does not inherit from VariableType."""
        from funcy_bear.type_stuffs.hint import TypeHint  # noqa: PLC0415

        return TypeHint(type(f"{cls._name()}", (), dict(cls.__annotations__.items())))


@dataclass(frozen=True)
class VarValue[V, T](BaseValue[V, T]):
    """A frozen class for holding constant variable values."""

    value: V
    meta: T
    text: str = ""

    def __getattr__(self, item: str) -> Any:
        """Allow access to attributes directly from the model."""
        if hasattr(self.meta, item):
            return getattr(self.meta, item)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")


class VariableEnum(RichStrEnum):
    """Base class for Enums with variable values."""

    meta: Any

    def __new__(cls, value: VarValue) -> Self:
        """Create a new enum member with the given VarValue."""
        obj: Self = str.__new__(cls, value.value)
        obj._value_ = value.value
        obj.text = value.text or ""
        obj.meta = value
        return obj

    def __getattr__(self, item: str) -> Any:
        """Allow access to metadata attributes directly from the enum member."""
        if self.meta and hasattr(self.meta, item):
            return getattr(self.meta, item)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    def __str__(self) -> str:
        """Return a string representation of the enum."""
        return self.value


class VariableIntEnum(RichIntEnum):
    """Base class for Enums with variable values."""

    meta: Any

    def __new__(cls, value: VarValue) -> Self:
        """Create a new enum member with the given VarValue."""
        obj: Self = int.__new__(cls, value.value)
        obj._value_ = value.value
        obj.text = value.text or ""
        obj.meta = value
        return obj

    def __getattr__(self, item: str) -> Any:
        """Allow access to metadata attributes directly from the enum member."""
        if self.meta and hasattr(self.meta, item):
            return getattr(self.meta, item)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    def __int__(self) -> int:
        """Return the integer value of the enum."""
        return self.value
