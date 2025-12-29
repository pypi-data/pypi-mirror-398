"""A collection of generally useful protocols."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class FrozenClass(Protocol):
    """A protocol for frozen (immutable) classes."""

    __frozen__: bool


@runtime_checkable
class Bindable(Protocol):
    """A protocol for objects that can bind documents."""

    def bind(self, doc: Any, **kwargs) -> None:
        """Bind a document to the object."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the object with the given arguments."""


@runtime_checkable
class CollectionProtocol(Protocol):
    """A protocol for collections that support len() and indexing."""

    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> Any: ...
    def __setitem__(self, index: int, value: Any) -> None: ...
    def pop(self) -> Any: ...
    def remove(self, item: Any) -> None: ...
    def get(self, index: int) -> Any: ...
    def copy(self) -> Any: ...
    def clear(self) -> None: ...
    def join(self, d: str) -> str: ...


class FileHandlerProtocol[T](Protocol):
    """Basic protocol for file handlers."""

    def read(self, **kwargs) -> T:
        """Return parsed records from the file (format-specific in subclass)."""
        raise NotImplementedError

    def write(self, data: T, **kwargs) -> None:
        """Replace file contents with `data` (format-specific in subclass)."""
        raise NotImplementedError

    def clear(self) -> None:
        """Clear the file contents using an exclusive lock."""
        raise NotImplementedError

    @property
    def closed(self) -> bool:
        """Check if the file handle is closed."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the file handle if open."""
        raise NotImplementedError

    def flush(self) -> None:
        """Flush the file handle if open."""
        raise NotImplementedError


@runtime_checkable
class PathInfo(Protocol):
    """A protocol for path-like objects."""

    def exists(self, *, follow_symlinks: bool = True) -> bool: ...
    def is_dir(self, *, follow_symlinks: bool = True) -> bool: ...
    def is_file(self, *, follow_symlinks: bool = True) -> bool: ...
    def is_symlink(self) -> bool: ...


# ruff: noqa: D102
