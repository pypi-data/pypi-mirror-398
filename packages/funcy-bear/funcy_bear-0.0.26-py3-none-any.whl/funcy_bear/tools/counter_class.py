"""A simple counter class that can be used to track state transitions."""

from __future__ import annotations

from itertools import count as counter
from typing import Any, Self


class Counter:
    """A simple counter class that can be used to track state transitions."""

    def __init__(self, start: int = 0) -> None:
        """Initialize the Counter."""
        self.start: int = start
        self.count: int = 0
        self._counter: counter | None = None

    @property
    def counter(self) -> counter:
        """Get the internal counter generator."""
        if self._counter is None:
            self._counter = counter(self.start)
        return self._counter

    @counter.setter
    def counter(self, value: counter) -> None:
        """Set the internal counter generator."""
        self._counter = value

    def get(self, before: bool = False, after: bool = False) -> int:
        """Get the current value of the counter.

        Args:
            before (bool): If True, increment the counter before getting the value.
            after (bool): If True, increment the counter after getting the value.
        """
        if before:
            self.tick()
            return self.count
        if after:
            current_value: int = self.count
            self.tick()
            return current_value
        return self.count

    def _set(self, value: int) -> None:
        """Set the counter to a specific value without validation."""
        self.counter = counter(value)
        self.count: int = next(self.counter)

    def set(self, value: int) -> Self:
        """Set the counter to a specific value.

        Args:
            value (int): The value to set the counter to. Must be non-negative and not
                            less than the current counter value.
        """
        if value < 0:
            raise ValueError("Counter value cannot be negative.")
        if value < self.count:
            raise ValueError("Cannot set counter to a value less than the current counter value.")
        self._set(value)
        return self

    def tick(self) -> int:
        """Increment the counter and return the new value."""
        self.count = next(self.counter)
        return self.count

    def clone(self) -> Counter:
        """Return a copy of the current Counter instance."""
        return Counter(start=self.count)

    def reset(self, value: int = -1) -> None:
        """Reset the counter to the start value or a specific value.

        Args:
            value (int): The value to reset the counter to. If -1, resets to the start value.
        """
        if value == -1:
            value = self.start
        self._set(value)

    def __copy__(self) -> Counter:
        """Return a shallow copy of the current Counter instance."""
        return self.clone()

    def __next__(self) -> int:
        """Return the next counter value."""
        return self.tick()

    def __iter__(self) -> Any:
        """Return the iterator for the counter."""
        return self

    def __add__(self, other: int) -> int:
        """Add an integer to the current counter value."""
        return self.count + other

    def __radd__(self, other: int) -> int:
        """Add an integer to the current counter value (reversed)."""
        return self.count + other

    def __sub__(self, other: int) -> int:
        raise NotImplementedError("Subtraction is not supported for Counter.")

    def __rsub__(self, other: int) -> int:
        raise NotImplementedError("Subtraction is not supported for Counter.")

    def __lt__(self, other: int) -> bool:
        """Check if the counter is less than another integer."""
        return self.count < other

    def __le__(self, other: int) -> bool:
        """Check if the counter is less than or equal to another integer."""
        return self.count <= other

    def __eq__(self, other: object) -> bool:
        """Check equality with another integer."""
        return self.count == other

    def __gt__(self, other: int) -> bool:
        """Check if the counter is greater than another integer."""
        return self.count > other

    def __ge__(self, other: int) -> bool:
        """Check if the counter is greater than or equal to another integer."""
        return self.count >= other

    def __hash__(self) -> int:
        """Return the hash of the current counter value."""
        return hash(self.count)

    def __bool__(self) -> bool:
        """Return True if the current counter value is non-zero."""
        return self.count != 0

    def __int__(self) -> int:
        """Return the current counter value as an integer."""
        return self.count

    def __index__(self) -> int:
        """Return the current counter value for indexing."""
        return self.count

    def __repr__(self) -> str:
        """Return a string representation of the counter."""
        return f"Counter(start={self.start}, count={self.count})"

    def __str__(self) -> str:
        """Return the string representation of the current counter value."""
        return str(self.count)


__all__ = ["Counter"]
