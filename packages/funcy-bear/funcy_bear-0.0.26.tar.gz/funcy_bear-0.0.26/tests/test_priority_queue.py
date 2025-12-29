from __future__ import annotations

from dataclasses import dataclass

import pytest

from funcy_bear.tools.priority_queue import PriorityQueue


def test_priority_queue_orders_items_by_priority() -> None:
    queue: PriorityQueue[int] = PriorityQueue()
    queue.put(5)
    queue.put(1)
    queue.put(3)

    assert queue.peek() == 1
    assert len(queue) == 3

    assert queue.get() == 1
    assert queue.get() == 3
    assert queue.get() == 5

    assert queue.empty()

    with pytest.raises(IndexError):
        queue.get()


def test_priority_queue_iteration_drains_in_order() -> None:
    queue: PriorityQueue[int] = PriorityQueue()
    for value in [4, 2, 9]:
        queue.put(value)

    assert list(queue) == [2, 4, 9]
    assert queue.empty()


@dataclass(order=True)
class Task:
    priority: int
    name: str


def test_priority_queue_remove_element_by_attribute() -> None:
    queue: PriorityQueue[Task] = PriorityQueue()
    queue.put(Task(2, "beta"))
    queue.put(Task(1, "alpha"))
    queue.put(Task(3, "gamma"))

    removed = queue.remove_element("name", "beta")
    assert removed is True
    assert queue.peek().name == "alpha"

    # Attempt to remove a non-existent key should safely return False
    assert queue.remove_element("name", "missing") is False

    # Removing from empty queue should also return False
    queue.clear()
    assert queue.remove_element("name", "alpha") is False
