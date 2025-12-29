"""A module providing query classes and functions for querying data structures."""

from collections.abc import Callable  # noqa: TC003
from typing import Any, Literal, overload

from funcy_bear.type_stuffs.validate import is_mapping, is_object

from ._base import QueryBase, QueryInstance
from ._common import MISSING_VALUE, MissingValue, QueryTest, callable_test
from ._protocol import QueryProtocol
from .query_mapping import QueryMapping, where as where_mapping
from .query_object import QueryObject, where as where_object

QueryChoices = Literal["obj", "mapping"]


class QueryUnified(QueryBase):
    """A unified query class that can handle both object and mapping queries."""

    def _resolve_path_step(self, value: Any | None, part: str | Callable[..., Any]) -> Any:
        if value is None or isinstance(value, MissingValue):
            return value
        if isinstance(part, str):
            if is_mapping(value):
                return value.get(part, MISSING_VALUE)
            if is_object(value):
                return getattr(value, part, MISSING_VALUE)
            return MISSING_VALUE
        return part(value)


@overload
def query(choice: Literal["obj"]) -> type[QueryObject]: ...
@overload
def query(choice: Literal["mapping"]) -> type[QueryMapping]: ...


def query(choice: QueryChoices) -> type[QueryObject | QueryMapping]:
    """Get the query class based on the choice."""
    if choice == "obj":
        return QueryObject
    if choice == "mapping":
        return QueryMapping
    raise ValueError(f"Invalid query choice: {choice}")


@overload
def where(key: str, choice: Literal["obj"]) -> QueryObject: ...
@overload
def where(key: str, choice: Literal["mapping"]) -> QueryMapping: ...


def where(key: str, choice: QueryChoices) -> QueryObject | QueryMapping:
    """Get an instance of the query class based on the choice."""
    if choice == "obj":
        return where_object(key)
    if choice == "mapping":
        return where_mapping(key)
    raise ValueError(f"Invalid query choice: {choice}")


def where_obj(key: str) -> QueryObject:
    """A shorthand for ``Query('obj')[key]``

    Args:
        key (str): The key to query.

    Returns:
        QueryObject: A QueryObject instance with the specified key.
    """
    return where_object(key)


def where_map(key: str) -> QueryMapping:
    """A shorthand for ``Query('mapping')[key]``

    Args:
        key (str): The key to query.

    Returns:
        QueryMapping: A QueryMapping instance with the specified key.
    """
    return where_mapping(key)


__all__ = [
    "QueryChoices",
    "QueryInstance",
    "QueryMapping",
    "QueryObject",
    "QueryProtocol",
    "QueryTest",
    "QueryUnified",
    "callable_test",
    "query",
    "where",
    "where_map",
    "where_obj",
]
