"""A set of utility functions for type checking and conversion."""

import ast
from collections.abc import Callable  # noqa: TC003
from contextlib import suppress
from functools import lru_cache
from typing import Any

from funcy_bear.ops.value_stuffs import always_true
from funcy_bear.sentinels import CONTINUE

from .type_to_string import PossibleStrs, type_to_str


@lru_cache(maxsize=128)
def eval_to_native(
    v: Any,
    cond: Callable[..., bool] | None = None,
    *args,
    **kwargs,
) -> Any:
    """Uses ast.literal_eval to convert a string wrapped value to its native typ or string type.

    Args:
        value (Any): The value to convert.
        cond (Callable[[Any], bool]): A callable that takes a value and returns a bool, determining if the conversion is acceptable.
            If None, any successful conversion is accepted.
        args: Additional positional arguments to pass to the condition callable.
        kwargs: Additional keyword arguments to pass to the condition callable.

    Returns:
        Any: The converted value if successful and condition is met, otherwise the original value.
    """
    if cond is None:
        cond = always_true

    with suppress(Exception):
        evaluated: Any = ast.literal_eval(v)
        if cond(evaluated, *args, **kwargs):
            return evaluated
    return CONTINUE


def eval_to_type_str(
    value: Any,
    cond: Callable[..., bool] | None = None,
    *args,
    **kwargs,
) -> PossibleStrs | Any:
    """Uses ast.literal_eval to convert a string wrapped value to its native type and then to its string type.

    Args:
        value (Any): The value to convert.
        cond (Callable[[PossibleStrs], bool]): A callable that takes a PossibleStrs and returns a bool
    Returns:
        PossibleStrs | Any: The converted value as PossibleStrs if successful and condition is met, otherwise CONTINUE.
    """
    if cond is None:
        cond = always_true

    if isinstance(value, str):
        try:
            v: PossibleStrs = type_to_str(type(ast.literal_eval(value)))
            return v if cond(v, *args, **kwargs) else CONTINUE
        except (TypeError, ValueError, SyntaxError):
            return CONTINUE
    else:
        return type_to_str(type(value))
