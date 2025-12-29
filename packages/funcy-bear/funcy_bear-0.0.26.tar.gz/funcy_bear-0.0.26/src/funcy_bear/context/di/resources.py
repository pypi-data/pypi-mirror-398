"""A module for dependency injection resources."""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Generator
from functools import cached_property
from threading import RLock
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from collections.abc import Callable


class _Resource[T](metaclass=ABCMeta):
    obj: T | None
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    _service_name: str | None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self._service_name = None
        self.kwargs = kwargs
        self.obj = None

    @abstractmethod
    def init(self, *args: Any, **kwargs: Any) -> T | None: ...

    @property
    def service_name(self) -> str | None:
        if self._service_name is not None:
            return self._service_name
        if self.obj is not None and hasattr(self.obj, "__name__") and isinstance(self.obj, type):
            return self.obj.__name__.lower()
        if hasattr(self.obj, "__class__") and hasattr(self.obj.__class__, "__name__"):
            return self.obj.__class__.__name__.lower()
        return None

    @service_name.setter
    def service_name(self, value: str | None) -> None:
        self._service_name = value

    def shutdown(self, resource: T | None) -> None: ...  # noqa: B027

    def __enter__(self) -> T | None:
        self.obj = obj = self.init(*self.args, **self.kwargs)
        return obj

    def __exit__(self, *exc_info: object) -> None:
        self.shutdown(self.obj)
        self.obj = None


class Singleton[T](_Resource[T]):
    """A base class for singleton classes"""

    def __init__(self, c: type[T] | Callable[..., T], /, *args, **kwargs) -> None:
        """Initialize the singleton with the given class or callable."""
        self._obj: type[T] | Callable[..., T] = c
        self._args: tuple[Any, ...] = args
        self._service_name: str | None = None
        self._kwargs: dict[str, Any] = kwargs
        self._lock: RLock = RLock()

    @property
    def service_name(self) -> str | None:
        """Get or set the service name for this singleton."""
        if self._service_name is not None:
            return self._service_name
        if hasattr(self._obj, "__name__"):
            return self._obj.__name__.lower()
        return None

    @service_name.setter
    def service_name(self, value: str | None) -> None:
        self._service_name = value

    @cached_property
    def instance(self) -> T:
        """Get the singleton instance, creating it if it doesn't exist."""
        return self._obj(*self._args, **self._kwargs)

    def init(self, *args: Any, **kwargs: Any) -> T:
        """Initialize the singleton instance with the given arguments."""
        with self._lock:
            if not self.has_instance():
                self._args = args
                self._kwargs = kwargs
            return self.instance

    def has_instance(self) -> bool:
        """Return ``True`` if the singleton instance has been initialized.

        Returns:
            bool: ``True`` if the instance exists, ``False`` otherwise.
        """
        return hasattr(self, "instance")

    def reset_instance(self, _: Any | None = None) -> None:
        """Reset the singleton instance to allow re-initialization.

        Uses a lock to ensure thread safety.
        """
        with self._lock:
            if self.has_instance():
                del self.instance

    def get(self) -> T:
        """Get the singleton instance, initializing it if necessary."""
        with self._lock:
            if self.has_instance():
                return self.instance
            return self.instance

    def __getattr__(self, item: str) -> Any:
        """Delegate attribute access to the singleton instance."""
        return getattr(self.get(), item)

    def shutdown(self, resource: T | None = None) -> None:
        """Shutdown the singleton by resetting its instance."""
        self.reset_instance(resource)

    @classmethod
    def from_instance(cls, value: T) -> Self:
        """Create a Singleton from an existing instance."""
        obj: Self = cls.__new__(cls)
        obj._obj = lambda: value
        obj._args = ()
        obj._kwargs = {}
        return obj


class ContextManagerType(ABCMeta):
    """A type that represents a context manager."""

    def __instancecheck__(cls, instance: object) -> bool:
        return hasattr(instance, "__enter__") and hasattr(instance, "__exit__")

    @abstractmethod
    def __enter__(cls) -> Any: ...
    @abstractmethod
    def __exit__(cls, exc_type: object, exc_value: object, traceback: object) -> None: ...


class Resource[T](_Resource[T]):
    """A resource class that handles both regular functions and context managers.

    Can handle:
    1. Regular functions that return a resource
    2. Context managers (objects with __enter__/__exit__)
    3. Generator-based context managers (from @contextmanager decorator)

    Example:
        @contextmanager
        def database_connection():
            conn = sqlite3.connect("db.sqlite")
            try:
                yield conn
            finally:
                conn.close()

        # Usage in container:
        database: Connection = Resource(database_connection, *args)
    """

    def __init__(self, f: Callable[..., T], *args, **kwargs: Any) -> None:
        """Initialize the Resource with a factory function."""
        super().__init__(*args, **kwargs)
        self.factory_func: Callable[..., T] = f
        self._resource = None
        self._exit_func = None
        self._initialized = False

    @property
    def service_name(self) -> str | None:
        """Get or set the service name for this resource."""
        if self._service_name is not None:
            return self._service_name
        if hasattr(self.factory_func, "__name__"):
            return self.factory_func.__name__.lower()
        return None

    @service_name.setter
    def service_name(self, value: str | None) -> None:
        self._service_name = value

    def init(self, *args: Any, **kwargs: Any) -> T | None:
        """Initialize the resource, handling both regular functions and context managers."""
        resolved_args, resolved_kwargs = self._resolve_args(*args, **kwargs)
        result: T = self.factory_func(*resolved_args, **resolved_kwargs)
        if hasattr(result, "__enter__") and hasattr(result, "__exit__"):
            res: ContextManagerType = result  # type: ignore[assignment]
            self._resource = res.__enter__()
            self.obj = self._resource
            self._exit_func = res.__exit__
            self._initialized = True
            return self._resource
        if hasattr(result, "__next__") and isinstance(result, Generator):
            self._context_manager = result
            try:
                return next(result)
            except StopIteration:
                return None
        return result

    def get(self) -> T | None:
        """Get the resource by initializing it directly (for injection)."""
        if self._initialized:
            return self.obj
        return self.init(*self.args, **self.kwargs)

    def shutdown(self, resource: T | None = None) -> None:  # noqa: ARG002
        """Shutdown the resource using captured exit method or generator cleanup."""
        if self._exit_func is not None:
            try:
                self._exit_func(None, None, None)
            finally:
                self._exit_func = None
        if self._context_manager is not None and isinstance(self._context_manager, Generator):
            try:
                next(self._context_manager)
            except StopIteration:
                pass
            finally:
                self._context_manager = None

    @staticmethod
    def _resolve_args(*args, **kwargs) -> tuple[tuple[Any, ...], dict[str, Any]]:
        """Resolve any provider arguments before calling the factory function."""
        resolved_args = []
        resolved_kwargs = {}
        for arg in args:
            if isinstance(arg, Resource | Singleton):
                resolved_args.append(arg.get())
            else:
                resolved_args.append(arg)
        for key, value in kwargs.items():
            if isinstance(value, Resource | Singleton):
                resolved_kwargs[key] = value.get()
            else:
                resolved_kwargs[key] = value
        return tuple(resolved_args), resolved_kwargs
