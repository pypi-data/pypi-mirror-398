"""A utility class to merge multiple lists into one, with options for string representation."""

from collections.abc import Iterator  # noqa: TC003
from typing import Self


class ListMerge[T]:
    """Merge multiple lists into one, with options for string representation."""

    @classmethod
    def merge_items(cls, *args: list[T], unique: bool = False) -> list[T]:
        """Merge multiple lists into one.

        Args:
            *args (list[T]): Lists to combine.
            unique (bool): If True, only unique items will be kept. Defaults to False.

        Returns:
            list[T]: The merged list.
        """
        from funcy_bear.ops.collections_ops.iter_stuffs import merge_lists  # noqa: PLC0415

        return merge_lists(*args, unique=unique)

    def __init__(self, *args: list[T], unique: bool = False) -> None:
        """Merge multiple lists into one.

        Args:
            *args (list[T]): Lists to combine.
            unique (bool): If True, only unique items will be kept. Defaults to False.
        """
        self._merged: list[T] = self.merge_items(*args, unique=unique) if args else []
        self.unique: bool = unique

    @property
    def merged(self) -> list[T]:
        """Return the merged list."""
        return self._merged

    def add(self, items: list[T]) -> Self:
        """Add a list of items to be merged later."""
        self._merged = self.merge_items(self._merged, items, unique=self.unique)
        return self

    def merge(self, *args: list[T], unique: bool | None = None) -> list[T]:
        """Combine additional lists into the existing merged list.

        Meant to be used last, after any delayed adds.

        Args:
            *args (list[T]): Lists to combine.
        """
        _unique: bool = self.unique if unique is None else unique
        self._merged = self.merge_items(self._merged, *args, unique=_unique)
        return self.merged

    def as_list(self) -> list[T]:
        """Return the merged list.

        Meant to be used last, after any delayed adds when you have nothing else to merge.
        """
        return self.merged

    def as_string(self, sep: str = "\n") -> str:
        """Return the merged list as a string, joined by the specified separator."""
        return sep.join(map(str, self.merged))

    def __repr__(self) -> str:
        return f"ListMerge(merged={self.merged}, unique={self.unique})"

    def __str__(self) -> str:
        return self.as_string()

    def __len__(self) -> int:
        return len(self.merged)

    def __iter__(self) -> Iterator[T]:
        return iter(self.merged)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None: ...
