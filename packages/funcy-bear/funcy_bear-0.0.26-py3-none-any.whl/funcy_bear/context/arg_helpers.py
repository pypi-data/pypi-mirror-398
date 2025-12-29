"""Helper functions and decorators for handling command line arguments in functions."""

from collections.abc import Callable  # noqa: TC003
from typing import TYPE_CHECKING, Annotated

from lazy_bear import lazy

if TYPE_CHECKING:
    from functools import wraps
    from inspect import BoundArguments, Signature
    import sys

    from funcy_bear.type_stuffs.introspection import get_function_signature
else:
    sys = lazy("sys")
    wraps = lazy("functools", "wraps")
    get_function_signature = lazy("funcy_bear.type_stuffs.introspection", "get_function_signature")

ArgsType = Annotated[list[str] | None, "ArgsType: A list of command line arguments or None to use sys.argv[1:]"]
"""A type alias for when command line arguments may be passed in or None to use sys.argv[1:]."""
CLIArgsType = Annotated[list[str], "CLIArgsType: A list of command line arguments specifically for CLI usage"]
"""A type alias for when command line arguments are expected to be passed in."""


def to_argv(args: ArgsType = None) -> list[str]:
    """A simple function to return command line arguments or a provided list of arguments.

    Args:
        args (list[str] | None): A list of arguments to return. If None, it will return sys.argv[1:].

    Returns:
        list[str]: The list of command line arguments.
    """
    return sys.argv[1:] if args is None else args


def args_parse[R](
    param_name: str = "args",
    handler: Callable[[], list[str]] = to_argv,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """A decorator to inject raw command line arguments as list[str].

    This decorator injects sys.argv[1:] (or custom handler result) into the specified
    parameter if it's not already provided when calling the function.

    Args:
        param_name: The name of the parameter to inject arguments into
        handler: Function to retrieve arguments (defaults to sys.argv[1:])

    Example:
        ```python
        @args_parse()
        def my_command(args: list[str]) -> None:
            print(f"Args: {args}")
        ```
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> R:
            sig: Signature = get_function_signature(func)
            if param_name in sig.parameters and param_name not in kwargs:
                bound: BoundArguments = sig.bind_partial(*args, **kwargs)
                if param_name not in bound.arguments:
                    bound.arguments[param_name] = handler()
                return func(*bound.args, **bound.kwargs)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def args_inject[R, ProcessedT](
    param_name: str = "args",
    handler: Callable[[], list[str]] = to_argv,
    *,
    process: Callable[[list[str]], ProcessedT],
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """A decorator to inject processed command line arguments.

    This decorator retrieves command line arguments, processes them through the provided
    function, and injects the result into the specified parameter.

    Args:
        param_name: The name of the parameter to inject processed arguments into
        handler: Function to retrieve raw arguments (defaults to sys.argv[1:])
        process: Function to process the raw arguments - its return type determines
                the type of the injected parameter

    Example:
        ```python
        def parse_args(args: list[str]) -> Namespace:
            parser = ArgumentParser()
            parser.add_argument("--name")
            return parser.parse_args(args)


        @args_inject(process=parse_args)
        def my_command(args: Namespace) -> None:
            print(f"Name: {args.name}")
        ```
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> R:
            sig: Signature = get_function_signature(func)
            if param_name in sig.parameters and param_name not in kwargs:
                bound: BoundArguments = sig.bind_partial(*args, **kwargs)
                raw_args: list[str] = bound.arguments[param_name] if param_name in bound.arguments else handler()
                processed_args: ProcessedT = process(raw_args)
                bound.arguments[param_name] = processed_args
                return func(*bound.args, **bound.kwargs)
            return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["ArgsType", "CLIArgsType", "args_inject", "args_parse"]
