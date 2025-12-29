"""A set of plugin containers for dependency injection."""

from collections.abc import Callable  # noqa: TC003
from queue import PriorityQueue
from typing import TYPE_CHECKING, Any, ClassVar

from funcy_bear.protocols.general import Bindable

from .container import DeclarativeContainer
from .types import Item, Params, Return, TearDownCallback

if TYPE_CHECKING:
    from .wiring import ParamsParser


class LifecycleContainer(DeclarativeContainer, initialize=False):
    """Mixin to add teardown functionality to DeclarativeContainer classes."""

    __HAS_HOOK__: ClassVar[bool] = False

    teardown_callbacks: PriorityQueue[TearDownCallback]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Initialize the teardown callbacks priority queue for the subclass."""
        super().container_init()
        cls.teardown_callbacks = PriorityQueue[TearDownCallback]()

    @classmethod
    def get_all_shutdowns(cls) -> dict[str, Any]:
        """Return all services that have a shutdown method.

        This allows us to always know that these services have a valid shutdown method.

        Returns:
            dict[str, Any]: A dictionary of service names to service instances that have a shutdown method
            that are considered valid shutdown services.
        """
        return {k: v for k, v in cls.services.items() if hasattr(v, "shutdown") and callable(v.shutdown)}

    @classmethod
    def register_teardown(cls, name: str, callback: Callable[[], None], priority: float = float("inf")) -> None:
        """Register a callback to be executed during shutdown.

        Args:
            name (str): The name of the teardown callback.
            callback (Callable[[], None]): The callback function to be executed during shutdown.
            priority (float, optional): The priority of the callback. Lower values indicate higher priority.
                Defaults to float('inf') indicating lowest priority.

        Example:
            -------
            ```python
            class AppContainer(DeclarativeContainer):
                db: Database


            db = Database()
            AppContainer.register("db", db)
            AppContainer.register_teardown(lambda: db.close())
            AppContainer.shutdown()
        ```
        """
        if not callable(callback):
            return
        callback_info = TearDownCallback(priority=float(priority), name=name, callback=callback)
        cls.teardown_callbacks.put(callback_info)

    @classmethod
    def shutdown(cls) -> None:
        """Shutdown services and execute registered teardown callbacks."""
        while cls.teardown_callbacks:
            callback_info: TearDownCallback = cls.teardown_callbacks.get()
            if callable(callback_info.callback):
                callback_info.callback()
        cls.clear()
        cls.teardown_callbacks.clear()


class FactoryContainerBase(DeclarativeContainer, initialize=False):
    """Container for factory services used in field operations."""

    __HAS_HOOK__: ClassVar[bool] = True

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Ensure subclasses initialize the container."""
        super().container_init()

    @classmethod
    def on_inject(cls, **kwargs) -> None:
        """Hook for injection logic - passes kwargs to bindable factories."""
        parser: ParamsParser | None = kwargs.pop("parser", None)
        if parser is None:
            return

        passed_kwargs: dict[str, Any] = parser._passed_kwargs

        for result in parser.results.values():
            if isinstance(result.instance, Bindable):
                result.instance.bind(None, **passed_kwargs)


class ToolContainer(DeclarativeContainer, initialize=False):
    """Container for tool services used in field operations."""

    __HAS_HOOK__: ClassVar[bool] = True

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Ensure subclasses initialize the container."""
        super().container_init()

    @classmethod
    def on_inject(cls, **kwargs) -> Callable[Params, Callable[[Item], Return]]:  # pyright: ignore[reportInvalidTypeVarUse, reportIncompatibleMethodOverride]
        """Hook for injection logic - returns a curried function that waits for doc."""
        parser: ParamsParser | None = kwargs.pop("parser", None)
        if parser is None:
            return None  # pyright: ignore[reportReturnType]

        passed_kwargs: dict[str, Any] = parser._passed_kwargs
        func: Callable[..., Any] = parser.func

        def op_factory(*_: Params.args, **__: Params.kwargs) -> Callable[[Item], Return]:
            """Outer function captures base arguments for the operation."""

            def transform(doc: Item) -> Return:
                """Inner function receives the document and executes with injected services."""
                for result in parser.results.values():
                    if isinstance(result.instance, Bindable):
                        result.instance.bind(doc, **passed_kwargs)
                parser.bound.apply_defaults()
                return func(*parser.bound.args, **parser.bound.kwargs)

            return transform

        return op_factory


__all__ = ["LifecycleContainer", "ToolContainer"]
