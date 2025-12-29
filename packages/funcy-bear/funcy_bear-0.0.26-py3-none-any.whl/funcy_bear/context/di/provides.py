"""A module for dependency injection providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Self

from .resources import Resource, Singleton

if TYPE_CHECKING:
    from types import ModuleType

    from .container import DeclarativeContainer


@dataclass(slots=True)
class Result:
    """Result for a service."""

    exception: Exception | None = None
    instance: Any | None = None
    success: bool = True

    def successful(self, instance: Any) -> Self:
        """Set the result as a success with the given instance."""
        self.instance = instance
        return self

    def fail(self, e: Exception) -> Self:
        """Set the result as a failure with the given exception."""
        self.exception = e
        self.success = False
        return self

    @property
    def error(self) -> str:
        """Extract the exception as a string."""
        return str(self.exception) if self.exception is not None else ""


class Provider[T: DeclarativeContainer]:
    """Marker for a service to be injected."""

    __IS_MARKER__: bool = True

    _container: ClassVar[type[T] | T | None] = None  # pyright: ignore[reportGeneralTypeIssues]

    @classmethod
    def has_container(cls) -> bool:
        """Check if a container has been set."""
        return cls._container is not None

    @classmethod
    def set_container(cls, container: type[T] | type) -> None:
        """Set the container class for this provider."""
        cls._container = container

    @classmethod
    def get_container(cls) -> type[T] | T:
        """Get the container class for this provider."""
        if cls._container is None:
            container: type[T] = get_container_from_sys()  # pyright: ignore[reportAssignmentType]
            cls._container = container
        return cls._container

    def __init__(self, service_name: str, container: type[T] | T | None = None) -> None:
        """Marker for a service to be injected."""
        self.service_name: str = service_name
        self.container: DeclarativeContainer | type[T] | T = container or self.get_container()

    @classmethod
    def __class_getitem__(cls, item: Any) -> Self:
        """Return a Provide instance for the given item."""
        if isinstance(item, cls) and hasattr(item, "service_name") and not isinstance(item, (Resource | Singleton)):
            return item
        if isinstance(item, (Resource | Singleton)) and hasattr(item, "service_name") and item.service_name:
            return cls(item.service_name, cls.get_container())
        if hasattr(item, "__name__"):
            name: str = item.__name__  # pyright: ignore[reportAttributeAccessIssue]
            return cls(name.lower())
        if isinstance(item, str):
            return cls(item)
        return cls(str(item))  # Try to extract service name from the item

    def __repr__(self) -> str:
        return f"Provide(service_name={self.service_name}, container={self.container.__name__ or 'None'})"


class Provide(Provider):
    """Alias for Provider to simplify usage."""


def get_container_from_sys() -> type[DeclarativeContainer]:
    """Get the DeclarativeContainer subclass defined in the current modules.

    This should basically never be run because we get the container in most cases,
    I wasn't able to find a case where this is actually needed, but it's here just in case.

    We ignore the DeclarativeContainer because users should never use the base class directly.

    Returns:
        The DeclarativeContainer subclass found in the current modules.
    """
    from inspect import isclass  # noqa: PLC0415
    import sys  # noqa: PLC0415

    from .container import DeclarativeContainer  # noqa: PLC0415

    mod_copy: dict[str, ModuleType] = sys.modules.copy()
    for mod in mod_copy.values():
        for attr_name in dir(mod):
            attr: Any = getattr(mod, attr_name)
            if not isclass(attr):
                continue
            if attr is DeclarativeContainer:
                continue
            if not issubclass(attr, DeclarativeContainer):
                continue
            if getattr(attr, "__IS_CONTAINER__", False):
                return attr
    raise RuntimeError("No DeclarativeContainer subclass found in current modules.")
