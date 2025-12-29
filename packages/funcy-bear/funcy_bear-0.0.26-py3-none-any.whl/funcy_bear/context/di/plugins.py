"""Plugins for dependency injection tools."""

from collections import defaultdict
from collections.abc import Callable  # noqa: TC003
from functools import wraps
from typing import Any

from funcy_bear.protocols.general import Bindable
from funcy_bear.tools.names import Names
from funcy_bear.type_stuffs.validate import is_mapping, is_object

from .types import CollectionChoice, Params, Return, ReturnedCallable  # noqa: TC001
from .wiring import ParamsReturn, parse_params


class Getter[V](Bindable):
    """A tool for getting fields from a document."""

    doc: Any

    def bind(self, doc: Any, **kwargs) -> None:  # noqa: ARG002
        """Bind a document to the getter."""
        self.doc = doc

    def __call__(self, field: str, doc: Any | None = None) -> V:
        """Retrieve a field from the bound document.

        Args:
            field: The field name to retrieve.
            doc: An optional document to bind.

        Returns:
            The value of the specified field.
        """
        if doc is not None:
            self.bind(doc)
        if is_mapping(self.doc):
            return self.doc[field]
        if is_object(self.doc):
            return getattr(self.doc, field)
        return self.doc  # Individual value like an int, str, etc.


class Setter[V](Bindable):
    """A tool for setting fields on a document."""

    doc: Any

    def bind(self, doc: Any, **kwargs) -> None:  # noqa: ARG002
        """Bind a document to the setter."""
        self.doc = doc

    def __call__(self, field: str, value: V, doc: Any | None = None) -> V:
        """Set a field on the bound document.

        Args:
            field: The field name to set.
            value: The value to set.
            doc: An optional document to bind.
        """
        if doc is not None:
            self.bind(doc)
        if is_mapping(self.doc):
            self.doc[field] = value
            return value
        if is_object(self.doc):
            setattr(self.doc, field, value)
            return value
        self.bind(value)  # Individual value like an int, str, etc.
        return value  # We return the individual value


class Deleter(Bindable):
    """A tool for deleting fields from a document."""

    doc: Any

    def bind(self, doc: Any, **kwargs) -> None:  # noqa: ARG002
        """Bind a document to the deleter."""
        self.doc = doc

    def __call__(self, field: str, doc: Any | None = None) -> None:
        """Delete a field from the bound document."""
        if doc is not None:
            self.doc = doc
        if is_mapping(self.doc):
            del self.doc[field]  # type: ignore[index]
            return
        if is_object(self.doc):
            delattr(self.doc, field)
        # We don't bother deleting from individual values like int, str, etc.


class Factory(Bindable):
    """A factory tool for creating collections."""

    def bind(self, doc: Any, **kwargs) -> None:  # noqa: ARG002
        """Bind a document to the factory. No-op for Factory."""
        default: ReturnedCallable = default_factory(kwargs.pop("default_factory", "dict"))
        default = dict if default is None else default
        self._factory_override: Callable = default

    def __call__(self) -> Any:
        """Default factory function to create collections based on choice."""
        choice: CollectionChoice = "dict"
        if hasattr(self, "_factory_override"):
            return self._factory_override()
        return default_factory(choice=choice)


def default_factory(choice: CollectionChoice = "dict", **kwargs) -> ReturnedCallable:
    """Return a factory function based on the specified choice."""
    if factory := kwargs.pop("override", False):
        return factory
    match choice:
        case "list":
            return list
        case "set":
            return set
        case "dict":
            return dict
        case "defaultdict":
            return defaultdict
        case _:
            raise ValueError(f"Invalid choice: {choice}")


class ToolContext(Names):
    """A context that holds tool instances for document manipulation."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the ToolContext with the tools, passed in the container and kwargs."""
        super().__init__(**kwargs)


def inject_tools(**kws):  # type: ignore[reportGeneralTypeIssues]
    """Decorator that auto-injects tool dependencies, allowing for delayed execution."""

    def decorator(op_func: Callable[Params, Return]) -> Callable[Params, Return]:
        @wraps(op_func)
        def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Return:
            kwargs["__passed_kwargs__"] = kws
            returned: ParamsReturn = parse_params(op_func, *args, **kwargs)
            if returned.payload is not None:
                op_factory: Callable[..., Return] = returned.payload
                return op_factory(*returned.args, **returned.kwargs)
            return op_func(*returned.args, **returned.kwargs)

        return wrapper

    return decorator  # pyright: ignore[reportReturnType]
