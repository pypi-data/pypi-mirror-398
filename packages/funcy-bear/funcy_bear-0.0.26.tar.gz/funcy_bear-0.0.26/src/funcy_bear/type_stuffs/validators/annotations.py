"""Predicates focused on typing annotations and generics."""

from __future__ import annotations

from types import GenericAlias
from typing import Any, TypeGuard


def is_typed(annotation: str | type) -> bool:
    """Check if the annotation is a concrete type (not 'Any')."""
    return isinstance(annotation, type) and annotation is not Any


def is_generic_alias(annotation: Any) -> TypeGuard[GenericAlias]:
    """Check if the annotation is a GenericAlias."""
    return isinstance(annotation, GenericAlias)


def is_annotated(annotation: Any) -> bool:
    """Check if the annotation is an Annotated type."""
    return str(type(annotation)).endswith("<class 'typing._AnnotatedAlias'>")


def is_union(annotation: Any) -> bool:
    """Check if the annotation is a Union type."""
    return str(type(annotation)).endswith("<class 'typing._UnionGenericAlias'>")


def is_generic_callable(annotation: Any) -> bool:
    """Check if the annotation is a generic Callable type."""
    return str(type(annotation)).endswith("<class 'collections.abc._CallableGenericAlias'>")


def is_not_generic(annotation: Any) -> bool:
    """Check if the annotation is not a generic type."""
    return not is_union(annotation) and not is_annotated(annotation) and not is_generic_alias(annotation)


__all__ = [
    "is_annotated",
    "is_generic_alias",
    "is_generic_callable",
    "is_not_generic",
    "is_typed",
    "is_union",
]
