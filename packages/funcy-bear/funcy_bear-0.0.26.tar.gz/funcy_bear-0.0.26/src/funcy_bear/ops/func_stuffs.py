"""Functions that operate on functions, this is considered experimental."""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from inspect import isclass, ismodule

    from funcy_bear.type_stuffs.validate import is_mapping, is_object
else:
    isclass, ismodule = lazy("inspect", "isclass", "ismodule")
    is_mapping, is_object = lazy("funcy_bear.type_stuffs.validate", "is_mapping", "is_object")


def identity[T](x: T) -> T:
    """Return the input value unchanged.

    Args:
        x (T): The input value.

    Returns:
        T: The same input value.
    """
    return x


def is_ident(x: Any, value: Any) -> bool:
    """Check if the input value is identical to the typed value.

    Args:
        x (Any): The input value to check.
        value (Any): The value to compare against.

    Returns:
        bool: True if the input value is identical to the instance value, False otherwise.
    """
    return x is value


def compose(*funcs: Callable) -> Callable:
    """Compose multiple functions into a single function.

    Args:
        *funcs (Callable): Functions to compose. The functions are applied
            from right to left.

    Returns:
        Callable: A new function that is the composition of the input functions.
    """
    if not funcs:
        return identity

    def composed(x: Any) -> Any:
        """Apply the composed functions to the input value."""
        for f in reversed(funcs):
            x = f(x)
        return x

    return composed


def const[T](value: T, *_, **__) -> Callable[..., T]:
    """Create a constant function that always returns the given value.

    Use this when you just need the value to be returned by a function, but
    don't care about the arguments. If you want to have more control over
    the arguments, use the `Const` class directly.

    Args:
        value (Any): The value to be returned by the constant function.

    Returns:
        Callable[..., Any]: A function that takes any arguments and returns the specified value.
    """

    def constant_function(*_: Any, **__: Any) -> T:
        """Return the constant value, ignoring any arguments."""
        return value

    return constant_function


def pipe(value: Any, *funcs: Callable) -> Any:
    """Pipe a value through a series of functions.

    Args:
        value (Any): The initial value to be processed.
        *funcs (Callable): Functions to apply to the value in sequence.

    Returns:
        Any: The final result after applying all functions.
    """
    for func in funcs:
        value = func(value)
    return value


def complement(f: Callable[[Any], bool]) -> Callable[[Any], bool]:
    """Return the complement of a predicate function.

    Args:
        f (Callable[[Any], bool]): A predicate function that returns a boolean value.

    Returns:
        Callable[[Any], bool]: A new function that returns the opposite boolean value of the input function.
    """

    def complemented(*args: Any, **kwargs: Any) -> bool:
        return not f(*args, **kwargs)

    return complemented


def has_attr(obj: object, attr: str) -> bool:
    """Check if an object has a specific attribute.

    Args:
        obj (Any): The object to check.
        attr (str): The name of the attribute to check for.

    Returns:
        bool: True if the object has the specified attribute, False otherwise.
    """
    return hasattr(obj, attr)


def has_all_attrs(obj: object, attrs: Sequence[str]) -> bool:
    """Check if an object has all specified attributes.

    Args:
        obj (Any): The object to check.
        attrs (list[str]): A list of attribute names to check for.

    Returns:
        bool: True if the object has all specified attributes, False otherwise.
    """
    return all(hasattr(obj, attr) for attr in attrs)


def has_attrs(seq: object, attrs: Sequence[str], true_only: bool = False) -> dict[str, bool]:
    """Check if an object has all specified attributes.

    Args:
        obj (Any): The object to check.
        attrs (list[str]): A list of attribute names to check for.

    Returns:
        dict[str, bool]: A dictionary mapping each attribute name to a boolean indicating its presence.
    """
    out: dict[str, bool] = {attr: hasattr(seq, attr) for attr in attrs}
    if true_only:
        out = {k: v for k, v in out.items() if v}
    return out


def if_in_list(item: Any, lst: list | tuple) -> bool:
    """Check if an item is in a collection (list, tuple, or set).

    Args:
        item: The item to check for.
        lst: The collection to check within.

    Returns:
        bool: True if the item is in the collection, False otherwise.
    """
    return item in lst


def any_of(*conditions: Callable[..., bool]) -> Callable[..., bool]:
    """Return a function that checks if any of the given conditions are True.

    Args:
        *conditions (Callable[..., bool]): A variable number of predicate functions.

    Returns:
        Callable[..., bool]: A function that returns True if any condition is True.
    """

    def checker(*args: Any, **kwargs: Any) -> bool:
        return any(condition(*args, **kwargs) for condition in conditions)

    return checker


def all_of(*conditions: Callable[..., bool]) -> Callable[..., bool]:
    """Return a function that checks if all of the given conditions are True.

    Args:
        *conditions (Callable[..., bool]): A variable number of predicate functions.

    Returns:
        Callable[..., bool]: A function that returns True if all conditions are True.
    """

    def checker(*args: Any, **kwargs: Any) -> bool:
        return all(condition(*args, **kwargs) for condition in conditions)

    return checker


def none_of(*conditions: Callable[..., bool]) -> Callable[..., bool]:
    """Return a function that checks if none of the given conditions are True.

    Args:
        *conditions (Callable[..., bool]): A variable number of predicate functions.

    Returns:
        Callable[..., bool]: A function that returns True if none of the conditions are True.
    """

    def checker(*args: Any, **kwargs: Any) -> bool:
        return not any(condition(*args, **kwargs) for condition in conditions)

    return checker


def one_of(*conditions: Callable[..., bool]) -> Callable[..., bool]:
    """Return a function that checks if exactly one of the given conditions is True.

    Args:
        *conditions (Callable[..., bool]): A variable number of predicate functions.

    Returns:
        Callable[..., bool]: A function that returns True if exactly one condition is True.
    """

    def checker(*args: Any, **kwargs: Any) -> bool:
        return sum(1 for condition in conditions if condition(*args, **kwargs)) == 1

    return checker


@cache
def n_in_range(n: int, low: int, high: int) -> bool:
    """Check if n is within the inclusive range [low, high].

    Args:
        n: The value to check.
        low: The lower bound of the range.
        high: The upper bound of the range.

    Returns:
        True if n is within the range, else False.
    """
    return low <= n <= high


@cache
def less_than_max(n: int, n_max: int) -> bool:
    """Check if n is less than or equal to n_max.

    Args:
        n: The value to check.
        n_max: The maximum bound.

    Returns:
        True if n is less than or equal to n_max, else False.
    """
    return n <= n_max


def a_or_b(a: Callable, b: Callable, otherwise: Callable | None = None) -> Callable[..., Any]:
    """Return a function that applies either a or b based on the type of the document.

    Depends on whether the document is a mapping or an object.

    Args:
        a: Function to apply if the document is a mapping.
        b: Function to apply if the document is an object.
        otherwise: Function to apply if neither condition is met.

    Returns:
        A function that applies either a or b based on the document type.
    """
    choices: dict[Callable[[Any], bool], Callable[..., Any]] = {is_mapping: a, is_object: b}
    from funcy_bear.ops.dispatch import mini_dispatch  # noqa: PLC0415

    return mini_dispatch(choices, otherwise)


def monkey[T](cls: T, name: str | None = None) -> Callable[..., T]:
    """Monkey patches class or module by adding to it decorated function.

    Anything overwritten could be accessed via .original attribute of decorated object.

    Example:
        class MyClass:
            def greet(self):
                return "Hello"

        @monkey(MyClass)
        def greet(self):
            return "Hi there!"

        obj = MyClass()
        print(obj.greet())  # Output: Hi there!
        print(obj.greet.original(obj))  # Output: Hello

    Args:
        cls: The class or module to monkey patch.
        name: Optional name for the function being added. If not provided, the original function's
            name will be used.

    Returns:
        A decorator that adds the decorated function to the specified class or module.
    """
    from funcy_bear.ops.strings.string_stuffs import cut_prefix  # noqa: PLC0415

    if not (isclass(cls) or ismodule(cls)):
        raise TypeError("Attempting to monkey patch non-class and non-module")

    def decorator(value: Any) -> Any:
        func: Any = getattr(value, "fget", value)  # Support properties
        func_name: str = name or cut_prefix(s=func.__name__, prefix=f"{cls.__name__}__")

        func.__name__ = func_name
        func.original = getattr(cls, func_name, None)

        setattr(cls, func_name, value)
        return value

    return decorator


__all__ = [
    "a_or_b",
    "all_of",
    "any_of",
    "complement",
    "compose",
    "const",
    "has_attrs",
    "identity",
    "if_in_list",
    "less_than_max",
    "n_in_range",
    "none_of",
    "pipe",
]
