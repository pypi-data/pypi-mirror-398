"""Type coercion utilities."""

from collections.abc import Callable  # noqa: TC003
from typing import Any

from funcy_bear.sentinels import NOT_FOUND
from funcy_bear.tools.dispatcher import Dispatcher
from funcy_bear.type_stuffs.validate import is_bool, is_bytes, is_float, is_int, is_str

from .func_stuffs import any_of

_to_int = Dispatcher(arg="value")


@_to_int.dispatcher()
def to_int(value: Any) -> int:
    """Convert a value to an integer."""
    raise TypeError(f"Unsupported type for to_int: {type(value)}")


@_to_int.register(any_of(is_int, is_float, is_str))
def _(value: Any) -> int:
    return int(value)


@_to_int.register(is_bytes)
def _(value: bytes) -> int:
    return int.from_bytes(value, "big")


_to_str = Dispatcher(arg="value")


@_to_str.dispatcher()
def format_default_value(value: Any) -> str:
    """Format a default value for string representation in code.

    Args:
        value (Any): The value to format.

    Returns:
        str: The formatted string representation of the value.
    """
    return repr(value)


@_to_str.register(is_str)
def _(value: str) -> str:
    return f'"{value}"'


@_to_str.register(any_of(is_int, is_float, is_bool))
def _(value: bool | float) -> str:
    return str(value)


def mini_dispatch(
    choices: dict[Callable[[Any], bool], Callable[..., Any]],
    otherwise: Callable | None = None,
) -> Callable[..., Any]:
    """A mini dispatcher function.

    A simplified version of a dispatcher that selects a function to apply
    based on a set of conditions.

    Example:
        def is_even(n):
            return n % 2 == 0

        def is_odd(n):
            return n % 2 == 1

        def handle_even(n):
            return f"{n} is even"

        def handle_odd(n):
            return f"{n} is odd"

        def handle_other(n):
            return f"{n} is neither even nor odd"

        choices = {
            is_even: handle_even,
            is_odd: handle_odd,
        }

        func = mini_dispatch(choices, handle_other)

        print(func(4))  # Output: "4 is even"
        print(func(7))  # Output: "7 is odd"
        print(func(3.5))  # Output: "3.5 is neither even nor odd"

    Args:
        choices: A dictionary mapping condition functions to their corresponding action functions.
        otherwise: A function to apply if no conditions match.

    Returns:
        A function that applies the first matching action function based on the conditions.
    """

    def wrapper(doc: Any) -> Any:
        for condition, func in choices.items():
            if condition(doc):
                return func(doc)
        return otherwise(doc) if otherwise else NOT_FOUND

    return wrapper


__all__ = ["to_int"]
