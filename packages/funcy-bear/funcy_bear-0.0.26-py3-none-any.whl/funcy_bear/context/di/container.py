"""A simple dependency injection container implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Self

from ._container_meta import DeclarativeContainerMeta, is_resource

if TYPE_CHECKING:
    from .resources import Resource, Singleton


class DeclarativeContainer(metaclass=DeclarativeContainerMeta, initialize=False):
    """A simple service container for dependency injection."""

    __HAS_HOOK__: ClassVar[bool] = False

    def __name__(self) -> str:
        """Return the name of the container class."""
        return self.__class__.__name__

    @classmethod
    def container_init(cls) -> None:
        """Add logic to this to extend container initialization."""
        cls.start()

    @classmethod
    def register(cls, name: str, instance: Any) -> None:
        """Register a service instance with a name and optional metadata."""
        cls.services[name.lower()] = instance

    @classmethod
    def get(cls, name: str) -> Any | None:
        """Get a registered service by name."""
        if name.lower() in cls.services:
            return cls.services[name.lower()]
        return None

    @classmethod
    def get_all(cls) -> dict[str, Any]:
        """Get all registered services."""
        return cls.services.copy()

    @classmethod
    def get_all_types(cls) -> dict[str, Any]:
        """Get all registered service types."""
        # ants: dict[str, Any] = get_annotations(cls)
        # for name, a in ants.items():
        #     if name.startswith("_"):
        #         continue
        #     if name.lower() not in cls.service_types:
        #         cls.service_types[name.lower()] = a
        return cls.service_types.copy()

    @classmethod
    def has(cls, name: str) -> bool:
        """Check if a service is registered."""
        return name.lower() in cls.services or hasattr(cls, name)

    @classmethod
    def override(cls, name: str, instance: Any) -> None:
        """Add an instance to the container using its class name as the key."""
        cls.attrs.services[name.lower()] = instance

    @classmethod
    def clear(cls) -> None:
        """Clear all registered services and metadata."""
        cls.attrs.services.clear()
        cls.attrs.resources.clear()

    @classmethod
    def start(cls) -> None:
        """Start all registered resources."""
        resources: dict[str, Singleton | Resource] = {k: v for k, v in cls.resources.items() if is_resource(v)}

        for name, resource in resources.items():
            instance: Any | None = resource.get()
            if instance is not None:
                cls.services[name] = instance

    @classmethod
    def on_inject(cls, **kwargs: Any) -> Any:
        """Hook for injection logic. Can be overridden."""

    @classmethod
    def stop(cls) -> None:
        """Should be overridden."""

    @classmethod
    def __enter__(cls) -> type[Self]:
        cls.start()
        return cls

    @classmethod
    def __exit__(cls, exc_type: object, exc: object, tb: object) -> None:
        cls.stop()
