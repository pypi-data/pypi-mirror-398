"""A collection of curried operations that can be applied to fields in a document.

This applies to all functions found in this module:
- They are curried functions that operate on fields within a document (mapping or object or even
    individual value in most cases).
- They use dependency injection to get the necessary tools (Getter, Setter, Deleter).
- They return curried functions that take a field name and other parameters, and return a function
    that takes a document and performs the operation.
"""

from collections.abc import Callable  # noqa: TC003
from contextlib import suppress
from operator import abs as _abs, mod as _mod, not_ as invert, pow as _pow
from typing import Any

from funcy_bear.injection import Deleter, Getter, Provide, Setter, inject_tools
from funcy_bear.ops._di_containers import CurryingContainer, FactoryContainer
from funcy_bear.ops.math import clamp as _clamp, neg


@inject_tools()
def delete(
    field: str,
    deleter: Deleter = Provide[CurryingContainer.deleter],
) -> Callable[..., None]:
    """Delete a given field from the document.

    Args:
        field: The field to delete.
    """
    deleter(field)
    return None  # pyright: ignore[reportReturnType]


@inject_tools()
def add(
    field: str = "",
    n: int = 0,
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., int | float]:
    """Add ``n`` to a given field in the document.

    Args:
        field: The field to add to.
        n: The amount to add.

    Returns:
        The new value after addition.
    """
    attr: Any = getter(field)
    return setter(field, attr + n) if isinstance(attr, (int | float)) else attr


@inject_tools()
def subtract(
    field: str = "",
    n: int = 0,
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., int | float]:
    """Subtract ``n`` to a given field in the document.

    Args:
        field: The field to subtract from.
        n: The amount to subtract.

    Returns:
        The new value after subtraction.
    """
    attr: Any = getter(field)
    return setter(field, attr - n) if isinstance(attr, (int | float)) else attr


@inject_tools()
def increment(
    field: str = "",
    value: int = 1,
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., int | float]:
    """Increment a given field by 1.

    Args:
        field: The field to increment.
        value: The amount to increment by. Default is 1.

    Returns:
        The new value after incrementing or the original value if not numeric.
    """
    attr: Any = getter(field)
    return setter(field, attr + value) if isinstance(attr, (int | float)) else attr


@inject_tools()
def decrement(
    field: str = "",
    value: int = 1,
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., int | float]:
    """Decrement a given field in the document by 1.

    Args:
        field: The field to decrement.
        value: The amount to decrement by. Default is 1.

    Returns:
        The new value after decrementing or the original value if not numeric.
    """
    attr: Any = getter(field)
    return setter(field, attr + neg(value)) if isinstance(attr, (int | float)) else attr


@inject_tools()
def multiply(
    field: str = "",
    n: int = 0,
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., int | float]:
    """Multiply a given field in the document by n.

    Args:
        field: The field to multiply.
        n: The amount to multiply by.
    """
    attr: Any = getter(field)
    return setter(field, attr * n) if isinstance(attr, (int | float)) else attr


@inject_tools()
def div(
    field: str = "",
    n: int = 1,
    floor: bool = False,
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., int | float]:
    """Divide a given field in the document by n.

    Args:
        field: The field to divide.
        n: The amount to divide by. Must not be zero
        floor: If True, use floor division.
    """
    attr: Any = getter(field)
    if isinstance(attr, (int | float)) and n != 0:
        return setter(field, attr // n) if floor else setter(field, attr / n)
    return attr  # pyright: ignore[reportReturnType]


@inject_tools()
def setter(
    field: str = "",
    v: Any | None = None,
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., Any]:
    """Set a given field to ``val``.

    Args:
        field: The field to set.
        v: The value to set the field to.
    """
    return setter(field, v)


@inject_tools()
def if_else(
    field: str,
    cond: Callable[[Any], bool] | tuple[Callable[..., bool], ...],
    then: Callable[..., Any],
    otherwise: Callable[..., Any],
    getter: Getter = Provide[FactoryContainer.getter],
) -> Callable[..., Callable[[Any], Any]]:
    """Apply one of two operations based on the value of a field in the document.

    Args:
        field: The field to check.
        cond: A callable that takes the field's value and returns a boolean.
        then: The operation to apply if the condition is true.
        otherwise: The operation to apply if the condition is false

    Returns:
        A curried function that takes a document and applies the appropriate operation.
    """
    conditions: Callable[[Any], bool] | tuple[Callable[..., bool], ...] = cond
    if callable(conditions):
        conditions = (conditions,)

    def transform(doc: Any) -> Any:
        if all(c(getter(field, doc)) for c in conditions):
            return then(doc)
        return otherwise(doc)

    return transform  # pyright: ignore[reportReturnType]


@inject_tools()
def swapcase(
    field: str = "",
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., str]:
    """Swap the case of a string field.

    Args:
        field: The field to swap case.
    """
    attr: Any = getter(field)
    return setter(field, attr.swapcase()) if isinstance(attr, str) else attr


@inject_tools()
def upper(
    field: str = "",
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., str]:
    """Convert a string field to uppercase.

    Args:
        field: The field to convert.
    """
    attr: Any = getter(field)
    return setter(field, attr.upper()) if isinstance(attr, str) else attr


@inject_tools()
def lower(
    field: str = "",
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., str]:
    """Convert a string field to lowercase.

    Args:
        field: The field to convert.

    Returns:
        The lowercased string.
    """
    attr: Any = getter(field)
    return setter(field, attr.lower()) if isinstance(attr, str) else attr


@inject_tools()
def replace(
    field: str = "",
    old: str = "",
    new: str = "",
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., str]:
    """Replace occurrences of a substring in a string field.

    Args:
        field: The field to modify.
        old: The substring to replace.
        new: The substring to replace with.
    """
    attr: Any = getter(field)
    return setter(field, attr.replace(old, new)) if isinstance(attr, str) else attr


@inject_tools()
def format(
    field: str = "",
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
    **kwargs: Any,
) -> Callable[..., Any]:
    """Format a string field using the provided arguments.

    Args:
        field: The field to format.
        **kwargs: Keyword arguments for formatting.
    """
    attr = getter(field)
    if isinstance(attr, str) and kwargs.get("kwargs") and isinstance(kwargs["kwargs"], dict):
        extracted: Any = kwargs.pop("kwargs")
        attr: str = attr.format(**extracted)
        return setter(field, attr)
    return setter(field, attr.format(**kwargs))


@inject_tools()
def pow(
    field: str = "",
    n: int = 0,
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., int | float]:
    """Raise a given field in the document to the power of n.

    Args:
        field: The field to exponentiate.
        n: The exponent to raise the field to, default is 2.

    Returns:
        The new value after exponentiation.
    """
    attr: Any = getter(field)
    if isinstance(attr, (int | float)) and n != 0:
        return setter(field, _pow(attr, n))
    return attr  # pyright: ignore[reportReturnType]


@inject_tools()
def clamp(
    field: str = "",
    min_value: int = 0,
    max_value: int = 100,
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., int | float]:
    """Clamp a given field in the document to be within min_value and max_value.

    Args:
        field: The field to clamp.
        min_value: The minimum value to clamp to.
        max_value: The maximum value to clamp to.

    Returns:
        The clamped value.
    """
    attr: Any = getter(field)
    return setter(field, _clamp(attr, min_value, max_value)) if isinstance(attr, (int | float)) else attr


@inject_tools()
def mod(
    field: str = "",
    n: int = 0,
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., int | float]:
    """Modulus a given field in the document by n.

    Args:
        field: The field to modulus
        n: The amount to modulus by.
    """
    attr: Any = getter(field)
    return setter(field, _mod(attr, n)) if isinstance(attr, (int | float)) and n != 0 else attr  # pyright: ignore[reportReturnType]


@inject_tools()
def toggle(
    field: str = "",
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., bool]:
    """Toggle a boolean field.

    Args:
        field: The field to toggle.
    """
    attr: Any = getter(field)
    return setter(field, invert(attr)) if isinstance(attr, bool) else attr


@inject_tools()
def abs(
    field: str = "",
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., int | float]:
    """Set a field to its absolute value.

    Args:
        field: The field to set.
    """
    attr: Any = getter(field)
    return setter(field, _abs(attr)) if isinstance(attr, (int | float)) else attr


@inject_tools()
def default(
    field: str,
    v: Any,
    replace_none: bool,
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., None]:
    """Set a field to a default value if it does not exist.

    Args:
        field: The field to set.
        v: The default value to set the field to.
        replace_none: If True, also replace None values.
    """
    try:
        current: Any = getter(field)
        if replace_none and current is None:
            setter(field, v)
    except (KeyError, AttributeError):
        setter(field, v)
    return None  # pyright: ignore[reportReturnType]


@inject_tools()
def push(
    field: str,
    v: Any,
    index: int,
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., None]:
    """Push a value to a list field in the document at a specific index.

    Args:
        field: The field to push to.
        v: The value to push.
        index: The index to insert the value at. Defaults to -1 (the end of the list).
    """
    try:
        attr: Any = getter(field)
    except (KeyError, AttributeError):
        attr = setter(field, [])

    if isinstance(attr, list):
        attr.append(v) if index == -1 or index >= len(attr) else attr.insert(index, v)
    return None  # pyright: ignore[reportReturnType]


@inject_tools()
def append(
    field: str,
    v: Any,
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., None]:
    """Append a value to a list field in the document.

    Args:
        field: The field to append to.
        v: The value to append.
    """
    try:
        attr: Any = getter(field)
    except (KeyError, AttributeError):
        attr = setter(field, [])

    if isinstance(attr, list):
        attr.append(v)
    return None  # pyright: ignore[reportReturnType]


@inject_tools()
def prepend(
    field: str,
    v: Any,
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., None]:
    """Prepend a value to a list field in the document.

    Args:
        field: The field to prepend to.
        v: The value to prepend.
    """
    try:
        attr: Any = getter(field)
    except (KeyError, AttributeError):
        attr = setter(field, [])
    if isinstance(attr, list):
        attr.insert(0, v)
    return None  # pyright: ignore[reportReturnType]


@inject_tools()
def extend(
    field: str,
    vals: list,
    getter: Getter = Provide[CurryingContainer.getter],
    setter: Setter = Provide[CurryingContainer.setter],
) -> Callable[..., None]:
    """Extend a list field in the document with another list.

    Args:
        field: The field to extend.
        vals: The list of values to extend with.
    """
    try:
        attr = getter(field)
    except (KeyError, AttributeError):
        setter(field, [])
        attr: list[Any] = []

    if isinstance(attr, list):
        attr.extend(vals)
    return None  # pyright: ignore[reportReturnType]


@inject_tools()
def pop(
    field: str = "",
    index: int = -1,
    strict: bool = False,
    getter: Getter = Provide[CurryingContainer.getter],
) -> Callable[..., Any]:
    """Pop a value from a list field in the document.

    Args:
        field: The field to pop from.
        index: The index to pop. Defaults to -1 (the last item).
        strict: If True, raise an IndexError if the index is out of range.

    Returns:
        The popped value, or None if the operation failed.
    """
    with suppress(IndexError, KeyError, AttributeError):
        attr: Any = getter(field)
        if isinstance(attr, list) and -len(attr) <= index < len(attr):
            return attr.pop(index)
    if strict:
        raise IndexError(f"Index {index} out of range for field '{field}'")
    return None  # pyright: ignore[reportReturnType]


@inject_tools()
def starts_with(
    field: str = "",
    prefix: str | tuple[str, ...] = "",
    getter: Getter = Provide[CurryingContainer.getter],
) -> Callable[..., bool]:
    """Check if a string field starts with a given prefix.

    Args:
        field: The field to check.
        prefix: The prefix to check for.

    Returns:
        bool: True if the field starts with the prefix, False otherwise.
    """
    attr: Any = getter(field)
    return attr.startswith(prefix) if isinstance(attr, str) else False  # pyright: ignore[reportReturnType]


@inject_tools()
def ends_with(
    field: str = "",
    suffix: str | tuple[str, ...] = "",
    getter: Getter = Provide[CurryingContainer.getter],
) -> Callable[..., bool]:
    """Check if a string field ends with a given suffix.

    Args:
        field: The field to check.
        suffix: The suffix to check for.

    Returns:
        bool: True if the field ends with the suffix, False otherwise.
    """
    attr: Any = getter(field)
    return attr.endswith(suffix) if isinstance(attr, str) else False  # pyright: ignore[reportReturnType]


if __name__ == "__main__":
    data = {"text": "Hello, Funcy Bear World"}
    starts = starts_with("text", "Hello")
