"""Container attributes for dependency injection containers."""

from dataclasses import dataclass, field
from typing import Any, TypeGuard

from .resources import Resource, Singleton

_ATTR_PATTERN = "_{attr}_{cls_name}"


def has_service_name(instance: Any) -> TypeGuard[Resource | Singleton]:
    """Check if a service is a Resource or Singleton and has a service_name attribute."""
    return isinstance(instance, (Resource | Singleton)) and hasattr(instance, "service_name")


def get_attr_name(cls: Any, attr: str) -> str:
    """Get the class-specific attribute name."""
    return _ATTR_PATTERN.format(attr=attr, cls_name=cls.cls_name)


@dataclass(slots=True)
class MinimalAttrs:
    """Minimal attributes for the container."""

    cls_name: str
    """The name of the container class."""
    name_map: dict[str, str | bool] = field(default_factory=dict)
    """Quick way to search attributes on MinimalAttrs."""
    resources: dict[str, Resource | Singleton] = field(default_factory=dict)
    """Resources defined in the container."""
    services: dict[str, Any] = field(default_factory=dict)
    """The extracted services defined in the container, usually instances."""
    service_types: dict[str, type] = field(default_factory=dict)
    """A backup way to be able to instantiate services based on their type annotations."""

    def _setup_name_map(self) -> None:
        """Setup the name map for the attributes."""
        self.name_map: dict[str, str | bool] = {
            "resources": get_attr_name(self, "resources"),
            "services": get_attr_name(self, "services"),
            "service_types": get_attr_name(self, "service_types"),
        }

    def __post_init__(self) -> None:
        """Post-initialization to setup the name map."""
        self._setup_name_map()

    def set_resources(self, og: dict[str, Any], cp: dict[str, Any]) -> None:
        """Set the resources for the container."""
        for attr_name, attr_value in cp.items():
            if attr_name.startswith("_"):
                continue
            if isinstance(attr_value, classmethod):
                continue
            if has_service_name(attr_value) and attr_value.service_name is None:
                attr_value.service_name = attr_name.lower()
            self.resources[attr_name.lower()] = attr_value
            del og[attr_name]

    def set_type_services(self, names: dict[str, Any]) -> None:
        """Set the service types for the container."""
        try:
            if a_func := names.get("__annotate_func__"):
                from annotationlib import Format  # noqa: PLC0415

                ants: dict[str, Any] = a_func(Format.VALUE)
            else:
                ants = names.get("__annotations__", {})
        except Exception:
            # raise RuntimeError("Failed to retrieve annotations for service types.") from e
            ants = {}
        for service_name, service_type in ants.items():
            if not service_name.startswith("_"):
                self.service_types[service_name.lower()] = service_type
