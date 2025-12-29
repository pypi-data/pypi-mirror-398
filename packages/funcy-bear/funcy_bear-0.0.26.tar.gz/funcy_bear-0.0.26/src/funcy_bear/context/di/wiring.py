"""Dependency injection wiring utilities."""

from __future__ import annotations

from functools import wraps
from inspect import Parameter
from typing import TYPE_CHECKING, Any, NamedTuple, ParamSpec, TypeVar

from ._param import ParamIntrospect
from .provides import Provide, Result

if TYPE_CHECKING:
    from collections.abc import Callable
    from inspect import BoundArguments, Parameter, Signature

    from .container import DeclarativeContainer

PASSED_KWARGS = "__passed_kwargs__"


def _provide_check(name: str, param: Parameter, kwargs: frozenset) -> bool:
    """Check if a parameter is of type Provide."""
    from funcy_bear.type_stuffs.introspection import isinstance_in_annotation, not_in_bound

    return isinstance_in_annotation(param, Provide, "default") and not_in_bound(kwargs, name)


def _get_provide_params(s: Signature, kwargs: frozenset) -> dict[str, Parameter]:
    """Get the parameters that are of type Provide."""
    return {n: p for n, p in s.parameters.items() if (_provide_check(n, p, kwargs))}


class ParamsReturn(NamedTuple):
    """Structure to hold parsed parameters."""

    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    payload: Any | None


class ParamsParser:
    """Parser for function parameters."""

    def __init__(
        self,
        sig: Signature,
        bound: BoundArguments,
        names: frozenset[str],
        params: dict[str, Parameter],
        func: Callable,
        **passed_kwargs: Any,
    ) -> None:
        """Initialize the ParamsParser."""
        # TODO: Need to handle multiple errors better
        self._result = Result()  # backup result in case there are other errors
        self.sig: Signature = sig
        self.bound: BoundArguments = bound
        self.names: frozenset[str] = names
        self.params: dict[str, Parameter] = params
        self.func: Callable[..., Any] = func
        self._container = None
        self._parsed: dict[str, Result] | None = None
        self._passed_kwargs: dict[str, Any] = passed_kwargs

    @property
    def container(self) -> type[DeclarativeContainer]:
        """Get the container from the first parameter."""
        if self._container is None:
            first_param: Parameter = next(iter(self.params.values()))
            self._container: Any = first_param.default.container
        return self._container

    @property
    def results(self) -> dict[str, Result]:
        """Get the introspected parameters."""
        if self._parsed is None:
            self._parsed = {name: ParamIntrospect.get(p, self.func) for name, p in self.params.items()}
        return self._parsed

    @property
    def has_hook(self) -> bool:
        """Check if the container has an injection hook."""
        return getattr(self.container, "__HAS_HOOK__", False)

    def do(self) -> ParamsReturn:
        """Introspect all parameters and check for a hook."""
        payload = None
        if not self.params:
            self.bound.apply_defaults()
            return ParamsReturn(args=self.bound.args, kwargs=self.bound.kwargs, payload=payload)

        for name, r in self.results.items():
            param: Parameter = self.params[name]
            if not r.success and r.exception is not None:
                param.default.result = r
            if r.success:
                self.bound.arguments[name] = r.instance
                self.container.override(name, r.instance)

        if self.has_hook:
            payload: Callable | None = self.container.on_inject(parser=self)

        self.bound.apply_defaults()
        return ParamsReturn(args=self.bound.args, kwargs=self.bound.kwargs, payload=payload)


def parse_params(func: Callable, *args, **kwargs) -> ParamsReturn:
    """Parse the parameters of a function."""
    from funcy_bear.type_stuffs.introspection import get_function_signature

    passed: dict[str, Any] = kwargs.pop(PASSED_KWARGS, {})
    s: Signature = get_function_signature(func)
    b: BoundArguments = s.bind_partial(*args, **kwargs)

    provided_names: frozenset[str] = frozenset(b.arguments.keys())
    params: dict[str, Parameter] = _get_provide_params(s=s, kwargs=provided_names)
    parser = ParamsParser(sig=s, bound=b, names=provided_names, params=params, func=func, **passed)
    return parser.do()


P = ParamSpec("P")
T = TypeVar("T")


def inject(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator that auto-injects dependencies"""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        bound: ParamsReturn = parse_params(func, *args, **kwargs)
        return func(*bound.args, **bound.kwargs)

    return wrapper


# ruff: noqa: PLC0415 UP047
