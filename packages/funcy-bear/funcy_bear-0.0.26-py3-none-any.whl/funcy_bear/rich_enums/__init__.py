"""A set of rich enums for various purposes."""

from .int_enum import IntValue, RichIntEnum
from .str_enum import RichStrEnum, StrValue
from .variable_enum import VariableEnum, VariableType, VarValue

__all__ = [
    "IntValue",
    "RichIntEnum",
    "RichStrEnum",
    "StrValue",
    "VarValue",
    "VariableEnum",
    "VariableType",
]
