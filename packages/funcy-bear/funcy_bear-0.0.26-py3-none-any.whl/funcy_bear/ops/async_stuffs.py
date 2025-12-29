"""Helper functions and classes for managing asynchronous operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from lazy_bear import lazy

if TYPE_CHECKING:
    import asyncio
    from asyncio import AbstractEventLoop, Task
    from collections.abc import Awaitable, Callable, Coroutine
    from contextlib import suppress
    from dataclasses import dataclass
    from functools import lru_cache, wraps
    import inspect
    import time
else:
    asyncio = lazy("asyncio")
    inspect = lazy("inspect")
    time = lazy("time")
    suppress = lazy("contextlib", "suppress")
    dataclass = lazy("dataclasses", "dataclass")
    lru_cache, wraps = lazy("functools", "lru_cache", "wraps")


@lru_cache(maxsize=128)
def is_async(func: Callable) -> bool:
    """Check if a function is asynchronous.

    Args:
        func (Callable): The function/method to check.

    Returns:
        bool: True if the function is asynchronous, False otherwise.
    """
    return inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(func) or inspect.isasyncgen(func)


def syncify[**P, T](func: Callable[P, Awaitable[T]]) -> Callable[P, T]:
    """This simple decorator converts an async function into a sync function.

    Args:
        func: An async function to convert to sync

    Returns:
        A sync function with the same signature and return type
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return asyncio.run(cast("Coroutine", func(*args, **kwargs)))
        except Exception as e:
            raise e from None

    return wrapper


@dataclass(slots=True)
class AsyncResponseModel[T]:
    """A model to handle asynchronous operations with a function and its arguments.

    Args:
        before_loop (bool): Indicates if the function was called before entering an async loop.
        loop (AbstractEventLoop | None): The event loop to run the task.
        task (Task | None): The asyncio task to be executed.
        result (T | None): The result of the completed task.
    """

    before_loop: bool = False
    loop: AbstractEventLoop | None = None
    task: Task | None = None
    result: T | None = None

    @property
    def done(self) -> bool:
        """Check if the task is completed."""
        return self.task is not None and self.task.done()

    def get_result(self) -> T:
        """Get the result of the completed task."""
        if not self.task:
            raise ValueError("No task available")
        if not self.task.done():
            raise ValueError("Task not completed yet")
        if self.result is None:
            self.result = self.task.result()
        return self.result if self.result is not None else self.task.result()

    def conditional_result(self, timeout: float = 10.0) -> T:
        """Get the result of the task, running the event loop if necessary."""
        if self.loop and self.task and not self.before_loop:
            self.loop.run_until_complete(self.task)
        start_time: float = time.monotonic()
        while not self.done:
            if time.monotonic() - start_time > timeout:
                raise TimeoutError("Task timed out")
            time.sleep(0.1)
        return self.get_result()

    def run(self) -> None:
        """Run the event loop until the task is complete if not in a running loop."""
        if self.loop and self.task and not self.before_loop:
            self.loop.run_until_complete(self.task)


def is_async_loop() -> bool:
    """Check if the current context is already in an async loop.

    Returns:
        bool: True if an async loop is running, False otherwise.
    """
    loop: AbstractEventLoop | None = None
    with suppress(RuntimeError):
        loop = asyncio.get_running_loop()
    return loop.is_running() if loop else False


def get_async_loop() -> AbstractEventLoop:
    """Get the current event loop, creating one if it doesn't exist.

    Returns:
        AbstractEventLoop: The current or newly created event loop.
    """
    if is_async_loop():
        return asyncio.get_event_loop()
    loop: AbstractEventLoop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


def create_async_task[T](
    func: Callable,
    my_loop: AbstractEventLoop | None = None,
    *args,
    **kwargs,
) -> AsyncResponseModel:
    """Create an asyncio task for a given function.

    Args:
        func (Callable): The function to run asynchronously.
        my_loop (AbstractEventLoop | None): An optional event loop to use.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        AsyncResponseModel: A model containing the event loop and task.
    """
    before_loop: bool = is_async_loop()
    loop: AbstractEventLoop = my_loop or get_async_loop()
    task: Task[T] = loop.create_task(func(*args, **kwargs))
    return AsyncResponseModel(loop=loop, task=task, before_loop=before_loop)


__all__ = ["AsyncResponseModel", "create_async_task", "get_async_loop", "is_async", "is_async_loop", "syncify"]
