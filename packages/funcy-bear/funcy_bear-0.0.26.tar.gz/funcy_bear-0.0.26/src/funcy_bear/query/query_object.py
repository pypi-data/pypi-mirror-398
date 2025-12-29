"""A module providing a query object implementation."""

from collections.abc import Callable  # noqa: TC003
from typing import Any

from ._base import QueryBase
from ._common import MISSING_VALUE, MissingValue


class QueryObject(QueryBase[object]):
    """A query object that can be instantiated."""

    def _resolve_path_step(
        self,
        value: object | Any,
        part: str | Callable[..., Any],
    ) -> Any:
        if value is None or isinstance(value, MissingValue):
            return value
        if isinstance(part, str):
            return getattr(value, part, MISSING_VALUE)
        return part(value)


def where(key: str) -> QueryObject:
    """Get an instance of the object query class."""
    return QueryObject()[key]
