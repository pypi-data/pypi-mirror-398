from collections.abc import Callable  # noqa: TC003
from inspect import Parameter  # noqa: TC003
from types import GenericAlias, NoneType
from typing import Any, Self, TypeGuard

from funcy_bear.exceptions import CannotFindTypeError, CannotInstantiateObjectError

from .container import DeclarativeContainer  # noqa: TC001
from .provides import Result
from .resources import Resource, Singleton


class ParamIntrospect:
    """Scanner for a single function parameter."""

    def __init__(self, param: Parameter, func: Callable) -> None:
        """Initialize the parameter."""
        self.param: Parameter = param
        self.func: Callable[..., Any] = func
        self.result: Result = Result()

    @property
    def name(self) -> str:
        """Get the name of the parameter."""
        return self.param.name

    @property
    def container(self) -> type[DeclarativeContainer]:
        """Get the container from the parameter default."""
        return self.param.default.container

    @property
    def is_present(self) -> bool:
        """Check if the service is present in the container."""
        return self.container.has(self.name)

    @property
    def annotation(self) -> type | str:
        """Get the annotation of the parameter."""
        return self.param.annotation

    def is_singleton(self, service_type: type | None | str) -> TypeGuard[Singleton]:
        """Check if the service is a singleton."""
        return isinstance(service_type, Singleton)

    def is_resource(self, service_type: type | None | str) -> TypeGuard[Resource]:
        """Check if the service is a resource."""
        return isinstance(service_type, Resource)

    def _parsing(self) -> Result:
        """Alternative implementation showing annotation-first approach."""
        from funcy_bear.ops.value_stuffs import get_instance  # noqa: PLC0415

        """Step 1: Resolve what type we need to create"""
        resolved_type: type | None = self._resolve_to_concrete_type()
        if resolved_type is None:
            return self.result.fail(CannotFindTypeError(f"Could not resolve type for service '{self.name}'"))
        """Step 2: Check if we have a cached instance (optimization)"""
        if self.is_present:
            cached_instance: Any | None = self.container.get(self.name)
            service_instance: None | type = get_instance(cached_instance)
            if service_instance is not None:
                return Result(instance=service_instance, success=True)
        """Step 3: Create new instance from resolved type"""
        if service_instance := get_instance(resolved_type):
            return Result(instance=service_instance, success=True)
        """Step 4: Everything failed"""
        return Result(exception=CannotInstantiateObjectError(f"Could not create service '{self.name}'"), success=False)

    def _resolve_to_concrete_type(self) -> type | None:
        """Parse any annotation type into a concrete, instantiable type.

        This is the heart of the contract resolution - it handles:
        - Direct types: Console -> Console
        - String annotations: "Console" -> Console class from globals
        - Complex types: Union[A, B], Annotated[A, "meta"] -> A

        Returns: Result with the concrete type to instantiate, or error
        """
        from funcy_bear.type_stuffs.introspection import introspect_types  # noqa: PLC0415

        resolved_type: type | GenericAlias = introspect_types(self.param, self.func, default=NoneType)
        if resolved_type is not NoneType and isinstance(resolved_type, type):
            # TODO: Account for callables and other such insanity
            return resolved_type
        """Fallback: Try to get the instance directly from the container's type annotation."""
        instance: Any | None = self.container.get(self.name)
        if instance is not None:
            return type(instance)
        return None

    @classmethod
    def get(cls, param: Parameter, func: Callable) -> Result:
        """Work the parsing logic and return Metadata."""
        parser: Self = cls(param, func)
        try:
            return parser._parsing()
        except Exception as e:
            return Result(exception=e, success=False)
