from __future__ import annotations

from typing import Any, TypeGuard

from funcy_bear.sentinels import NOTSET

from .container_attrs import MinimalAttrs
from .provides import Provide
from .resources import Resource, Singleton

CONTAINER_ATTR = "{cls_name}_meta_"
BASE_CLASS_NAME = "DeclarativeContainer"


def is_resource(instance: Any) -> TypeGuard[Resource | Singleton]:
    """Check if a service is a Resource or Singleton."""
    return isinstance(instance, (Resource | Singleton))


class DeclarativeContainerMeta(type):
    """Metaclass that captures service declarations and makes the injection magic work.

    Uses MinimalAttrs to store metadata about resources and services that can be unique
    amongst subclasses.

    Attributes:
        __HAS__HOOK__ (bool): Indicates if the container has custom initialization logic.
    """

    __HAS__HOOK__: bool = False

    @property
    def container_name(cls) -> str:
        """Return the name of the container class."""
        return CONTAINER_ATTR.format(cls_name=cls.__name__)

    @property
    def attrs(cls) -> MinimalAttrs:
        """Return the container attributes."""
        a = object.__getattribute__(cls, cls.container_name)
        if a == NOTSET:
            raise AttributeError(f"'{cls.__name__}' has no attributes set.")
        return a

    @property
    def resources(cls) -> dict[str, Resource | Singleton]:
        """Return all resources defined in the container."""
        return cls.attrs.resources

    @property
    def services(cls) -> dict[str, Any]:
        """Return all services defined in the container."""
        return cls.attrs.services

    @property
    def service_types(cls) -> dict[str, Any]:
        """Return all service types defined in the container."""
        return cls.attrs.service_types

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        initialize: bool = True,
        start: bool = True,
    ) -> DeclarativeContainerMeta:
        """Create a new container class with provider magic.

        Args:
            name: The name of the class.
            bases: The base classes.
            namespace: The class namespace.
            initialize: Whether to initialize the container attributes.
                If False, the attributes will be set to NOTSET which is
                a sentinel indicating they are uninitialized.
            start: Whether to start the container after creation, if initialized.

        Returns:
            The new container class.
        """
        if initialize:
            attrs = MinimalAttrs(cls_name=name)
            names: dict[str, Any] = namespace.copy()
            attrs.set_resources(namespace, names)
            attrs.set_type_services(names)
            namespace[CONTAINER_ATTR.format(cls_name=name)] = attrs
        else:
            namespace[CONTAINER_ATTR.format(cls_name=name)] = NOTSET
        cls = super().__new__(mcs, name, bases, namespace)
        if initialize and start:
            # This is expected behavior, we added the start param as way to NOT start
            # during certain operations like subclassing for performance reasons.
            # Note: It is rather standard for DI containers to start automatically upon definition.
            cls.start()
        return cls

    def __getattr__(cls, name: str) -> Any:
        """Return a Provide instance for any service name or the actual provider object.

        Args:
            name: The name of the attribute.

        Returns:
            The provider object or a Provide instance or otherwise raises AttributeError.
        """
        if name == "__IS_CONTAINER__":
            return True
        attrs: Any = object.__getattribute__(cls, cls.container_name)

        if not attrs or attrs == NOTSET:
            raise AttributeError(f"'{cls.__name__}' has no attribute '{name}'")

        if attrs.name_map.get(name):
            return getattr(attrs, name)

        if name.lower() in attrs.resources or (name in attrs.service_types and not name.startswith("_")):
            return Provide(name.lower(), cls)
        raise AttributeError(f"'{cls.__name__}' has no attribute '{name}'")

    def __setattr__(cls, name: str, value: Any) -> None:
        """Set an attribute on the container class."""
        if name in cls.attrs.name_map:
            setattr(cls.attrs, name, value)
        super().__setattr__(name, value)
