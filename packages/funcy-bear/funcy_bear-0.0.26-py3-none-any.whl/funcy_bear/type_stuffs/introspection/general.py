"""General introspection utilities."""

from __future__ import annotations

from contextlib import suppress
from functools import lru_cache
import inspect
from inspect import BoundArguments, Parameter, Signature
from types import GenericAlias, NoneType
from typing import TYPE_CHECKING, Any, Literal, cast, get_type_hints

from ._helpers import ParamWrapper

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType


@lru_cache(maxsize=256)
def get_function_signature(func: Callable) -> Signature:
    """Get the signature of a function, cached for performance.

    Args:
        func: The function to inspect.

    Returns:
        The Signature object representing the function's signature.
    """
    return inspect.signature(func)


@lru_cache(maxsize=256)
def find_type_hints(name: str, func: Callable) -> Any | None:
    """Get the type hint for a given parameter name in a function, cached for performance.

    Args:
        name: The name of the parameter to look up.
        func: The function to inspect.

    Returns:
        The type hint for the parameter, or None if not found.
    """
    type_hints: dict[str, Any] = get_type_hints(func, globalns=func.__globals__)
    return type_hints.get(name)


def not_in_bound(b: BoundArguments | frozenset, p: str) -> bool:
    """Check if a parameter is already bound in the given BoundArguments.

    You can also pass a frozenset of argument names for faster repeated checks.

    Args:
        b: The BoundArguments to check, or a frozenset of argument names.
        p: The name of the parameter to check.

    Returns:
        True if the parameter is not in the bound arguments, False otherwise.
    """

    @lru_cache(maxsize=256)
    def inner(b: frozenset, p: str) -> bool:
        return p not in b

    if isinstance(b, frozenset):
        return inner(b, p)
    return p not in b.arguments


Locations = Literal["annotation", "default"]


@lru_cache(maxsize=256)
def type_in_annotation(
    param: Parameter,
    valid_types: tuple[type, ...] | frozenset[type],
    location: Locations = "annotation",
) -> bool:
    """Check if a parameter's annotation matches any of the valid types.

    Args:
        param: The parameter to check.
        valid_types: A set of valid types to check against.
        location: Where to check the type ('annotation' or 'default').

    Returns:
        True if the parameter's annotation is in the valid types, False otherwise.
    """
    if location == "default":
        return param.default in valid_types
    return param.annotation in valid_types


@lru_cache(maxsize=256)
def isinstance_in_annotation(param: Parameter, valid_types: type | tuple[type, ...], location: Locations) -> bool:
    """Check if a parameter's annotation is an instance of any of the valid types.

    Args:
        param: The parameter to check.
        valid_types: A type or tuple of types to check against.
        location: Where to check the type ('annotation' or 'default').

    Returns:
        True if the parameter's annotation is an instance of the valid types, False otherwise.
    """
    target: Any
    if location == "annotation":
        target = param.annotation
    elif location == "default":
        target = param.default
    return isinstance(target, valid_types)


def resolve_string_to_type(name: str, f: Callable) -> type | None:
    """Helper to resolve string type names to actual types.

    This function attempts to resolve a type name given as a string to an actual type object. It checks:
    1. If the type is defined in the function's type hints.
    2. If the type is defined in the module where the function is defined.
    3. If the type is defined in the function's global scope.

    Args:
        name: The name of the type to resolve.
        f: The function whose context is used for resolution.

    Returns:
        The resolved type if found, otherwise None.
    """
    with suppress(NameError, AttributeError, KeyError, TypeError):
        resolved_type: Any | None = find_type_hints(name, f)
        if resolved_type is not None:
            return resolved_type
    with suppress(KeyError, AttributeError, TypeError):
        module: ModuleType | None = inspect.getmodule(f)
        if module is not None:
            module_type: Any | None = module.__dict__.get(name)
            if module_type is not None and isinstance(module_type, type):
                return module_type
    with suppress(KeyError, AttributeError, TypeError):
        global_type: Any | None = f.__globals__.get(name)
        if global_type is not None and isinstance(global_type, type):
            return global_type
    return None


def introspect_types(param: Parameter | ParamWrapper, func: Callable, default: type = NoneType) -> type | GenericAlias:
    """Post-initialization to resolve type hints.

    1. If the annotation is already a type, return it.
    2. If the annotation is a string, attempt to resolve it to a type via the name and not the annotation.
    3. If the annotation is a generic with type arguments, attempt to resolve the first type argument recursively.
    4. If all else fails, return the provided default type.

    Args:
        param: The Parameter object from inspect.
        func: The function being inspected.
        default: The default type to return if resolution fails, defaults to NoneType.

    Returns:
        The resolved type.
    """
    if isinstance(param, Parameter):
        param = ParamWrapper(param)

    if param.is_typed:  # Annotation is already a type
        return cast("type", param.annotation)

    if param.is_generic_callable:  # Generic Callable, return as-is
        return cast("GenericAlias", param.annotation)

    if param.is_str:  # We need to resolve via the arg string
        resolved: type | None = resolve_string_to_type(param.name, func)
        param.from_annotation(resolved) if resolved is not None else param
        if resolved is not None and not param.args:
            return resolved
    if param.origin is not None and param.args:  # Unwrap generics
        return introspect_types(param.unwrap_first(), func, default=default)
    return default
