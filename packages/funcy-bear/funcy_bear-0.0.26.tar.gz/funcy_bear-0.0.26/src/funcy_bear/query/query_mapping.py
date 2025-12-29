"""A module providing a query implementation for mappings."""

from collections.abc import Callable, Mapping
from typing import Any

from ._base import QueryBase
from ._common import MISSING_VALUE, MissingValue


class QueryMapping(QueryBase[Mapping]):
    """A query object that uses mappings (like dicts)."""

    def _resolve_path_step(
        self,
        value: Mapping | Any,
        part: str | Callable[..., Any],
    ) -> Any:
        if value is None or isinstance(value, MissingValue):
            return value
        if isinstance(part, str):
            return value.get(part, MISSING_VALUE)
        return part(value)


def where(key: str) -> QueryMapping:
    """Get an instance of the mapping query class."""
    return QueryMapping()[key]
