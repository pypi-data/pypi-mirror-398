"""An AutoSort implementation."""

from __future__ import annotations

from collections.abc import Callable, Iterable, MutableSequence
from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

if TYPE_CHECKING:
    from bisect import bisect_left, bisect_right, insort

    from funcy_bear.ops.func_stuffs import identity
else:
    bisect_left, bisect_right, insort = lazy("bisect", "bisect_left", "bisect_right", "insort")
    identity = lazy("funcy_bear.ops.func_stuffs", "identity")


class AutoSort[T](MutableSequence):
    """An implementation of a sorted object list that maintains order on insertions."""

    __slots__: tuple = ("_key", "_list")

    def __init__(self, iterable: list[T] | None = None, key: Callable[[T], Any] = identity) -> None:
        """Initialize the AutoSort with an optional iterable and key function.

        Args:
            iterable (list[T] | None): An optional iterable to initialize the sorted list.
            key (Callable[[T], Any]): A function to extract a comparison key from each list
                element. Defaults to the identity function.
        """
        self._list: list[T] = []
        self._key: Callable[[T], Any] = key

        if iterable is not None:
            self.update(iterable=iterable)

    def update(self, iterable: Iterable[T]) -> None:
        """Update the sorted list with multiple values."""
        self._list.extend(iterable)
        self._list.sort(key=self._key)

    def extend(self, values: Iterable[T]) -> None:
        """Extend the sorted list with multiple values."""
        self._list.extend(values)
        self._list.sort(key=self._key)

    def insert(self, index: int, value: T) -> None:  # noqa: ARG002
        """Insert a value into the sorted list (ignores index)."""
        insort(self._list, value, key=self._key)

    def append(self, value: T) -> None:
        """Insert a value into the sorted list."""
        insort(self._list, value, key=self._key)

    def remove(self, value: T) -> None:
        """Remove a value from the sorted list."""
        self._list.remove(value)

    def bisect_left(self, value: T) -> int:
        """Find the insertion point for value in the sorted list to maintain order (left)."""
        return bisect_left(self._list, value, key=self._key)

    def bisect_right(self, value: T) -> int:
        """Find the insertion point for value in the sorted list to maintain order (right)."""
        return bisect_right(self._list, value, key=self._key)

    def pop_tail(self) -> T | None:
        """Pop and return the last item in the sorted list, or None if empty."""
        if self.empty:
            return None
        return self._list.pop()

    def pop_head(self) -> T | None:
        """Pop and return the first item in the sorted list, or None if empty."""
        if self.empty:
            return None
        return self._list.pop(0)

    def clear(self) -> None:
        """Clear the sorted list."""
        self._list.clear()

    @property
    def head(self) -> T | None:
        """Get the first item in the sorted list, or None if empty."""
        if self.empty:
            return None
        return self._list[0]

    @property
    def tail(self) -> T | None:
        """Get the last item in the sorted list, or None if empty."""
        if self.empty:
            return None
        return self._list[-1]

    @property
    def empty(self) -> bool:
        """Check if the sorted list is empty."""
        return len(self) == 0

    def __len__(self) -> int:
        """Get the length of the sorted list."""
        return len(self._list)

    def __bool__(self) -> bool:
        """Check if the sorted list is non-empty."""
        return not self.empty

    def __getitem__(self, index: int) -> T:  # type: ignore[override]
        """Get an item by index."""
        return self._list.__getitem__(index)

    def __setitem__(self, index: int, value: T) -> None:  # type: ignore[override]
        raise NotImplementedError("Setting items by index is not supported in AutoSort.")
        # del self._list[index]
        # insort(self._list, value, key=self._key)

    def __delitem__(self, index: int) -> None:  # type: ignore[override]
        """Delete an item by index."""
        raise NotImplementedError("Deleting items by index is not supported in AutoSort.")

    def get_all(self) -> list[T]:
        """Get the internal list."""
        return self._list


# if __name__ == "__main__":

#     def mod_2(x: int) -> int:
#     """Return x modulo 2."""
#     return x % 2


# def mod_4(x: int) -> int:
#     """Return x modulo 4."""
#     return x % 4
#     big_list: list[int] = list(range(2000))

#     reverse: AutoSort[int] = AutoSort[int](key=mod_2)
#     reverse.update(big_list)
#     full = reverse.get_all()
#     print(full[:10])
#     print(full[1990:2000])

#     b: AutoSort[int] = AutoSort[int](key=mod_4)
#     b.update(big_list)
#     full = b.get_all()
#     print(full[:10])
#     print(full[1990:2000])

# if __name__ == "__main__":
#     import timeit

#     from rich.console import Console
#     from rich.panel import Panel
#     from rich.table import Table

#     console = Console()
#     big_list: list[int] = list(range(0, 2000, 1))

#     RUNS = 10000

#     def test_update() -> None:
#         """Test update method with fresh AutoSort instance."""
#         a: AutoSort[int] = AutoSort[int]()
#         a.update(big_list)

#     def test_worse_update() -> None:
#         """Test worse_update method with fresh AutoSort instance."""
#         b: AutoSort[int] = AutoSort[int]()
#         b.worse_update(big_list)

#     def test_extend() -> None:
#         """Test extend method with fresh AutoSort instance."""
#         c: AutoSort[int] = AutoSort[int]()
#         c.extend(big_list)

#     # Benchmark update (extend + sort with local refs)
#     update_duration: float = timeit.timeit(
#         stmt="test_update()",
#         globals=globals(),
#         number=RUNS,
#     )
#     update_avg: float = update_duration / RUNS

#     # Benchmark worse_update (insort each item)
#     worse_duration: float = timeit.timeit(
#         stmt="test_worse_update()",
#         globals=globals(),
#         number=RUNS,
#     )
#     worse_avg: float = worse_duration / RUNS

#     # Benchmark extend (extend + sort without local refs)
#     extend_duration: float = timeit.timeit(
#         stmt="test_extend()",
#         globals=globals(),
#         number=RUNS,
#     )
#     extend_avg: float = extend_duration / RUNS

#     methods = {"update": update_avg, "extend": extend_avg, "worse_update": worse_avg}
#     fastest = min(methods, key=methods.get)  # type: ignore[arg-type]
#     slowest = max(methods, key=methods.get)  # type: ignore[arg-type]

#     diffs = {k: v - methods[fastest] for k, v in methods.items()}

#     table = Table(title=f"AutoSort Performance Benchmark: {RUNS}", show_lines=True)
#     table.add_column("Method", justify="left", style="cyan", no_wrap=True)
#     table.add_column("Avg Time (µs)", justify="right", style="magenta")
#     table.add_column("Diff from Fastest (µs)", justify="right", style="yellow")
#     table.add_column("Total Time (s)", justify="right", style="green")

#     for method, avg_time in methods.items():
#         table.add_row(method, f"{avg_time * 1000000:.6f}", f"{diffs[method] * 1000000:.6f}", f"{(avg_time * RUNS):.6f}")

#     speedup = methods[slowest] / methods[fastest]
#     panel = Panel.fit(
#         f"[bold green]Fastest:[/bold green] {fastest} ({methods[fastest] * 1000000:.6f} µs)\n"
#         # second fastest
#         f"[bold blue]Second Fastest:[/bold blue] "
#         f"{sorted(methods.items(), key=lambda x: x[1])[1][0]} "
#         f"({sorted(methods.items(), key=lambda x: x[1])[1][1] * 1000000:.6f} µs)\n"
#         f"[bold red]Slowest:[/bold red] {slowest} ({methods[slowest] * 1000000:.6f} µs)\n"
#         f"[bold yellow]Speedup:[/bold yellow] {speedup:.2f}x faster",
#         title="Summary",
#         border_style="blue",
#     )
#     console.print(table)
#     console.print(panel)
