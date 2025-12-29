"""Utility type literals and type aliases."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, Sized
from os import PathLike
from pathlib import Path
from types import NoneType
from typing import Any, Literal, NoReturn, Protocol


class SupportsBool(Protocol):
    """Protocol for return values providing a dedicated truthiness hook."""

    def __bool__(self) -> bool: ...


class ArrayLike(ABC):
    """A protocol representing array-like structures (list, tuple, set)."""

    @abstractmethod
    def __iter__(self) -> Any: ...

    @classmethod
    @abstractmethod
    def __subclasshook__(cls, subclass: type) -> bool:
        return hasattr(subclass, "__iter__") and subclass in (list, tuple, set)


class JSONLike(ABC):
    """A protocol representing JSON-like structures (dict, list)."""

    @abstractmethod
    def __setitem__(self, key: Any, value: Any) -> None: ...

    @abstractmethod
    def get(self, key: Any, default: Any = None) -> Any:
        """Get a value by key with an optional default."""

    @classmethod
    @abstractmethod
    def __subclasshook__(cls, subclass: type) -> bool:
        return hasattr(subclass, "__setitem__") and subclass in (dict, list)


type LitInt = Literal["int"]
type LitFloat = Literal["float"]
type LitStr = Literal["str"]
type LitBool = Literal["bool"]
type LitList = Literal["list"]
type LitDict = Literal["dict"]
type LitTuple = Literal["tuple"]
type LitSet = Literal["set"]
type LitPath = Literal["path"]
type LitBytes = Literal["bytes"]

StringTypes = LitStr | LitInt | LitFloat | LitBool | LitList | LitDict | LitTuple | LitSet | LitPath | LitBytes

type StrPath = str | Path | PathLike

type LitFalse = Literal[False]
type LitTrue = Literal[True]

type OptInt = int | None
type OptFloat = float | None
type OptStr = str | None
type OptBool = bool | None

type OptStrList = list[str] | None
type OptStrDict = dict[str, str] | None

type NoReturnCall = Callable[..., NoReturn]
type SupportsTruthiness = SupportsBool | Sized
type TruthReturnedCall = Callable[..., SupportsTruthiness | bool]


ObjExclude = (
    int
    | float
    | str
    | bool
    | list
    | tuple
    | set
    | bytes
    | bytearray
    | memoryview
    | frozenset
    | Mapping
    | NoneType
    | complex
)
MappingExcludes = list | tuple | set | str | bytes | bytearray
SequenceExclude = Mapping | str | bytes | bytearray


__all__ = [
    "ArrayLike",
    "JSONLike",
    "LitBool",
    "LitBytes",
    "LitDict",
    "LitFalse",
    "LitFloat",
    "LitInt",
    "LitList",
    "LitPath",
    "LitSet",
    "LitStr",
    "LitTrue",
    "LitTuple",
    "MappingExcludes",
    "NoReturnCall",
    "ObjExclude",
    "OptBool",
    "OptFloat",
    "OptInt",
    "OptStr",
    "OptStrDict",
    "OptStrList",
    "SequenceExclude",
    "StrPath",
    "StringTypes",
    "SupportsTruthiness",
    "TruthReturnedCall",
]
