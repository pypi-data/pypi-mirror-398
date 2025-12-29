"""Types for the dependency injection system."""

from collections.abc import Callable
from typing import Literal, NamedTuple, ParamSpec, TypeVar

type CollectionChoice = Literal["list", "set", "dict", "defaultdict"]
type ReturnedCallable = Callable[..., dict | list | set | Callable]

Item = TypeVar("Item", bound=dict | object)
Return = TypeVar("Return")
Params = ParamSpec("Params")


class TearDownCallback(NamedTuple):
    """Information about a registered teardown callback."""

    priority: float
    name: str
    callback: Callable[[], None]
