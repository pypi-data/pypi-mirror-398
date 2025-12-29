"""Sentinel values for various purposes."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final, Self, final

from singleton_base import SingletonBase

if TYPE_CHECKING:
    from funcy_bear.constants.type_constants import LitFalse


class Nullish(SingletonBase):
    """A sentinel value to indicate a null value, no default, or exit signal.

    Similar to a `None` type but distinct for configuration and control flow
    that might handle `None` as a valid value.

    Can be subclassed for specific sentinel types like `NO_DEFAULT`,
    `EXIT_SIGNAL`, `CONTINUE`, and `NOTSET`.

    All instances and subclasses of `Nullish` will be treated as equal to each other.
    """

    _name: str = "Nullish"

    def value(self) -> None:
        """Return None to indicate no default value."""
        return None  # noqa: RET501

    def __getitem__(self, key: object) -> Nullish:
        return self

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Nullish)

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Nullish)

    def __bool__(self) -> LitFalse:
        return False

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash("__nullish__")

    def __str__(self) -> str:
        return f"<{self._name}>"


def ad_hoc_sentinel(name: str) -> Nullish:
    """Create an ad-hoc sentinel value with the given name.

    Args:
        name: The name of the sentinel.

    Returns:
        A new Nullish sentinel instance with the specified name.
    """

    class AdHocSentinel(Nullish):
        _name: str = name

    return AdHocSentinel()


@final
class NoDefaultType(Nullish):
    """A sentinel value to indicate no default value."""

    _name: str = "NoDefault"


NO_DEFAULT: Final = NoDefaultType()
"""A sentinel value to indicate no default value."""


@final
class ExitSignalType(Nullish):
    """A sentinel value to indicate an exit signal."""

    _name: str = "ExitSignal"


EXIT_SIGNAL: Final = ExitSignalType()
"""A sentinel value to indicate an exit signal."""


@final
class ContinueType(Nullish):
    """A sentinel value to indicate continuation in an iteration or process."""

    _name: str = "Continue"


CONTINUE: Final = ContinueType()
"""A sentinel value to indicate continuation in an iteration or process."""


@final
class NotSetType(Nullish):
    """A sentinel value to indicate a value is not set."""

    _name: str = "NotSet"


NOTSET: Final = NotSetType()
"""A sentinel value to indicate a value is not set."""
UNSET: Final = NOTSET
"""Alias for NOTSET sentinel value."""
NOT_INIT: Final = NOTSET
"""Alias for NOTSET sentinel value."""


@final
class MissingType(Nullish):
    """A sentinel value to indicate a missing value."""

    _name: str = "Missing"


MISSING: Final = MissingType()
"""A sentinel value to indicate a missing value."""
UNDEFINED: Final = MISSING
"""Alias for MISSING sentinel value."""
NOT_FOUND: Final = MISSING
"""Alias for MISSING sentinel value."""


@final
class MemoryPath(Path):
    """A sentinel Path representing in-memory storage."""

    def __new__(cls, *_, **__) -> Self:
        """Create a new MemoryPath instance."""
        return super().__new__(cls, ":memory:")


IN_MEMORY: Final = MemoryPath()


@final
class SentinelDict(dict):
    """A sentinel dictionary to indicate a special case."""

    def __bool__(self) -> LitFalse:
        return False


@final
class SentinelTuple(tuple):
    """A sentinel tuple to indicate a special case."""

    def __bool__(self) -> LitFalse:
        return False


@final
class EndOfFileType(Nullish, bytes):
    """A sentinel value to indicate end of file."""

    _name: str = "EndOfFile"

    def __new__(cls) -> Self:
        """Create a new EndOfFileType instance with a null byte."""
        return super().__new__(cls, b"\x00")


EOF: Final = EndOfFileType()
"""A sentinel value to indicate end of file."""

__all__ = [
    "CONTINUE",
    "EXIT_SIGNAL",
    "IN_MEMORY",
    "MISSING",
    "NOTSET",
    "NOT_FOUND",
    "NOT_INIT",
    "NO_DEFAULT",
    "UNDEFINED",
    "UNSET",
    "MemoryPath",
    "Nullish",
    "SentinelDict",
    "ad_hoc_sentinel",
]
