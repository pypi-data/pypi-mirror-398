"""Classes for various operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable
    from inspect import Signature


class Currying:
    """Generalized currying that plays nice with functools.partial."""

    def __init__(self, func: Any, *args: Any, **kwargs: Any) -> None:
        """Initialize the Curry object."""
        from funcy_bear.type_stuffs.introspection import get_function_signature  # noqa: PLC0415

        if hasattr(func, "func") and hasattr(func, "args"):
            base_func: Callable = func.func
            base_args: tuple = getattr(func, "args", ())
            base_kwargs: dict = getattr(func, "keywords", {}) or getattr(func, "kwargs", {})

            self.func: Callable = base_func
            self.args: tuple = base_args + args
            self.kwargs: dict = base_kwargs | kwargs
        else:
            self.func = func
            self.args = args
            self.kwargs = kwargs

        self.sig: Signature = get_function_signature(self.func)

    def __call__(self, *new_args: Any, **new_kwargs: Any) -> Any:
        """Call the curried function with additional arguments."""
        combined_args: tuple = self.args + new_args
        combined_kwargs: dict = self.kwargs | new_kwargs
        if self.is_fully_curried:
            return self.func(*combined_args, **combined_kwargs)
        return Currying(self.func, *combined_args, **combined_kwargs)

    @property
    def is_fully_curried(self) -> bool:
        """Check if the function has been fully curried."""
        try:
            self.sig.bind(*self.args, **self.kwargs)
            return True
        except TypeError:
            return False

    def __repr__(self) -> str:
        return f"Curry({self.func.__name__}, args={self.args}, kwargs={self.kwargs})"
