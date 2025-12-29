from __future__ import annotations

from dataclasses import dataclass
from typing import NoReturn

from funcy_bear.tools.frozen_models import BaseHashValue, BaseNotCacheable

from ._common import OpType  # noqa: TC001 # Pydantic needs access


@dataclass(frozen=True, slots=True)
class HashValue(BaseHashValue):
    """A simple frozen model to hold a hash value for query caching."""

    op: OpType | None = None

    def combine(self, other: BaseHashValue, **kwargs) -> HashValue:
        """Combine multiple hash values into one."""
        return HashValue(value=[self, other], **kwargs)

    def __hash__(self) -> int:
        if not self.cacheable:
            raise TypeError("This HashValue is not cacheable")
        return self.get_hash()


@dataclass(frozen=True, slots=True)
class NotCacheable(HashValue, BaseNotCacheable):
    """A singleton representing a non-cacheable hash value, contains a frozen cacheable=False flag."""

    def __init__(self) -> None: ...

    def combine(self, other: BaseHashValue, **kwargs) -> NoReturn:  # noqa: ARG002
        raise TypeError("This object is not cacheable")

    def __hash__(self) -> int:
        raise TypeError("This HashValue is not cacheable")
