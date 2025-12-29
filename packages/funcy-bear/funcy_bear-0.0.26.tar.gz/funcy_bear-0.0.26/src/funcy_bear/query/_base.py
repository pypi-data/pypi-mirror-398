"""A general-purpose query system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Self

from lazy_bear import LazyLoader

from ._common import MissingValue, callable_test
from ._hash_value import HashValue, NotCacheable
from ._protocol import QueryProtocol

if TYPE_CHECKING:
    from collections.abc import Callable
    import re

    from ._common import OpType, QueryTest
else:
    re = LazyLoader("re")


class QueryInstance[T](QueryProtocol):
    """A manifestation of a query operation."""

    def __init__(self, test: QueryTest, hash_val: HashValue | None) -> None:
        """Initialize the query instance."""
        self._test = test
        self._hash: HashValue = hash_val if hash_val is not None else NotCacheable()

    @property
    def is_cacheable(self) -> bool:
        """Check if this object is cacheable."""
        return self._hash.cacheable

    def combine(self, op: OpType, other: QueryInstance) -> HashValue:
        """Combine multiple hash values into one."""
        if not other.is_cacheable or not self.is_cacheable:
            return NotCacheable()
        return self._hash.combine(op=op, other=other._hash)

    def __call__(self, value: T) -> bool:
        """Call the test function with the provided value."""
        return callable_test(self._test)(value)

    def __hash__(self) -> int:
        return hash(self._hash)

    def __repr__(self) -> str:
        return f"Query({self._hash})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, QueryInstance):
            return self._hash == other._hash

        return False

    def __and__(self, other: QueryInstance) -> QueryInstance:
        return QueryInstance(lambda value: self(value) and other(value), self.combine("and", other))

    def __or__(self, other: QueryInstance) -> QueryInstance:
        return QueryInstance(lambda value: self(value) or other(value), self.combine("or", other))

    def __invert__(self) -> QueryInstance:
        return QueryInstance(lambda value: not self(value), HashValue(op="not", value=[self._hash]))


class QueryBase[T](QueryInstance[T], ABC):
    """Lightweight Query class that builds query paths dynamically.

    Now with frozen data structure support for better hashing and immutability.
    """

    def __init__(self) -> None:
        """Initialize the Query object."""
        self._path: tuple[str | Callable, ...] = ()

        def no_test(*_, **__) -> bool:
            raise RuntimeError("Empty query was evaluated")

        super().__init__(test=no_test, hash_val=HashValue(op=None, value=[None]))

    def __hash__(self) -> int:
        return super().__hash__()

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"

    def __getattr__(self, key: str) -> Self:
        """Build nested path for attribute access like Query().user.name"""
        query: Self = type(self)()
        query._path = (*self._path, key)
        query._hash = HashValue(op="path", value=[*self._path, key]) if self.is_cacheable else NotCacheable()
        return query

    def __getitem__(self, key: str) -> Self:
        """Build nested path for item access like Query()["user"]["name"]"""
        return self.__getattr__(key)

    @abstractmethod
    def _resolve_path_step(self, value: T | None, part: str | Callable) -> Any:
        """Resolve a single step in the query path."""

    def _get_test(self, test: QueryTest, hash_val: HashValue, allow_empty_path: bool = False) -> QueryInstance:
        """Generate a query based on a test function that first resolves the query path.

        Args:
            test (QueryCheck): A callable that takes a single argument and returns a boolean.
            hash_val (tuple): A tuple representing the hash value for caching.
            allow_empty_path (bool): Whether to allow an empty path. Defaults to False.

        Returns:
            QueryInstance: A query instance that applies the test to the resolved path value.
        """
        if not self._path and not allow_empty_path:
            raise ValueError("Query has no path")

        def runner(value: T) -> bool:
            try:
                for part in self._path:
                    value = self._resolve_path_step(value, part)
            except (KeyError, TypeError):
                return False
            else:
                return test(value)

        hash_val = hash_val if self.is_cacheable else HashValue.not_cacheable()
        return QueryInstance(lambda value: runner(value), hash_val)

    def __eq__(self, value: Any) -> QueryInstance:  # type: ignore[override] # noqa: PYI032
        """Create equality test callable."""
        return self._get_test(lambda record: record == value, hash_val=HashValue(op="==", value=[*self._path, value]))

    def __ne__(self, value: Any) -> QueryInstance:  # type: ignore[override] # noqa: PYI032
        """Create not-equal test callable."""
        return self._get_test(lambda record: record != value, hash_val=HashValue(op="!=", value=[*self._path, value]))

    def __gt__(self, value: Any) -> QueryInstance:
        """Create greater-than test callable."""
        return self._get_test(
            lambda record: record is not None and record > value, hash_val=HashValue(op=">", value=[*self._path, value])
        )

    def __lt__(self, value: Any) -> QueryInstance:
        """Create less-than test callable."""
        return self._get_test(
            lambda record: record is not None and record < value, hash_val=HashValue(op="<", value=[*self._path, value])
        )

    def __ge__(self, value: Any) -> QueryInstance:
        """Create greater-than-or-equal test callable."""
        return self._get_test(
            lambda record: record is not None and record >= value,
            hash_val=HashValue(op=">=", value=[*self._path, value]),
        )

    def __le__(self, value: Any) -> QueryInstance:
        """Create less-than-or-equal test callable."""
        return self._get_test(
            lambda record: record is not None and record <= value,
            hash_val=HashValue(op="<=", value=[*self._path, value]),
        )

    def exists(self) -> QueryInstance:
        """Create exists test callable."""
        return self._get_test(
            test=lambda record: not isinstance(record, MissingValue),
            hash_val=HashValue(op="exists", value=[*self._path]),
            allow_empty_path=True,
        )

    def matches(self, regex: str, flags: int = 0) -> QueryInstance:
        """Create a regex match test callable."""

        def regex_test(record: Any) -> bool:
            if not isinstance(record, str):
                return False
            return re.match(regex, record, flags) is not None

        return self._get_test(regex_test, hash_val=HashValue(op="matches", value=[*self._path, regex, flags]))

    def search(self, regex: str, flags: int = 0) -> QueryInstance:
        """Create a regex search test callable."""

        def regex_test(record: Any) -> bool:
            if not isinstance(record, str):
                return False
            return re.search(regex, record, flags) is not None

        return self._get_test(regex_test, hash_val=HashValue(op="search", value=[*self._path, regex, flags]))

    def all(self, condition: QueryInstance | list[Any]) -> QueryInstance:
        """Create a test callable that checks if all elements in a list satisfy a condition.

        Args:
            condition (QueryInstance | list[Any]): A callable condition or a list of values to check
                for membership.

        Returns:
            QueryInstance: A query instance that checks if all elements satisfy the condition.
        """
        if callable(condition):

            def test(value) -> bool:  # noqa: ANN001
                return hasattr(value, "__iter__") and all(condition(e) for e in value)

        else:

            def test(value) -> bool:  # noqa: ANN001
                return hasattr(value, "__iter__") and all(e in value for e in condition)

        return self._get_test(lambda record: test(record), hash_val=HashValue(op="all", value=[*self._path, condition]))
