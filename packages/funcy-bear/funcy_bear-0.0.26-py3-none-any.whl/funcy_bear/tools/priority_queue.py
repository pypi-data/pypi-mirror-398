"""A simple priority queue implementation using a heap."""

from collections.abc import Iterator  # noqa: TC003
from threading import RLock
from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

if TYPE_CHECKING:
    from heapq import heapify, heappop, heappush, nsmallest
else:
    heapify, heappop, heappush, nsmallest = lazy("heapq", "heapify", "heappop", "heappush", "nsmallest")


class PriorityQueue[QueueType: Any]:
    """A simple priority queue implementation using a heap."""

    def __init__(self) -> None:
        """A simple priority queue implementation using a heap."""
        self._lock = RLock()
        self._elements: list[QueueType] = []

    def put(self, item: QueueType) -> None:
        """Add an item to the queue."""
        with self._lock:
            heappush(self._elements, item)

    def get(self) -> QueueType:
        """Remove and return the highest priority item from the queue."""
        if self.not_empty():
            with self._lock:
                return heappop(self._elements)
        raise IndexError("get from empty priority queue")

    def peek(self) -> QueueType:
        """Return the highest priority item without removing it."""
        if self.not_empty():
            with self._lock:
                return self._elements[0]
        raise IndexError("peek from empty priority queue")

    def empty(self) -> bool:
        """Check if the queue is empty."""
        with self._lock:
            return not self._elements

    def not_empty(self) -> bool:
        """Check if the queue is not empty."""
        with self._lock:
            return bool(self._elements)

    def clear(self) -> None:
        """Clear all items from the queue."""
        with self._lock:
            self._elements.clear()

    def sort(self) -> None:
        """Sort the queue in place."""
        with self._lock:
            heapify(self._elements)

    def sorted_items(self) -> Iterator[QueueType]:
        """Return items in priority order without modifying the queue."""
        with self._lock:
            return iter(nsmallest(len(self._elements), self._elements))

    def remove_element(self, key: str, value: Any) -> bool:
        """Remove an item from the queue based on a key-value pair.

        Args:
            key (str): The attribute name to match.
            value (Any): The value to match against the attribute.

        Returns:
            bool: True if an item was removed, False otherwise.
        """
        if self.empty():
            return False

        with self._lock:
            try:
                item_to_remove: QueueType = next(item for item in self._elements if getattr(item, key, None) == value)
                self._elements.remove(item_to_remove)
                heapify(self._elements)
                return True
            except StopIteration:
                return False
            except ValueError:
                return False

    @property
    def size(self) -> int:
        """Get the number of items in the queue."""
        with self._lock:
            return len(self._elements)

    def __len__(self) -> int:
        with self._lock:
            return len(self._elements)

    def __bool__(self) -> bool:
        with self._lock:
            return bool(self._elements)

    def __iter__(self) -> Iterator[QueueType]:
        """Iterate over items in priority order (destructive)."""
        with self._lock:
            while self._elements:
                yield heappop(self._elements)

    def __repr__(self) -> str:
        return f"PriorityQueue({self._elements})"
