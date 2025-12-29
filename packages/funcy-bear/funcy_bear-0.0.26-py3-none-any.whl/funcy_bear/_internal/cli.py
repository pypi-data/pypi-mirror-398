from __future__ import annotations

from argparse import ArgumentParser, Namespace
import sys

from funcy_bear.context.arg_helpers import args_inject

from ._exit_code import ExitCode
from ._info import METADATA, VALID_BUMP_TYPES, BumpType, Version
from .debug import _print_debug_info


def _debug_info() -> ExitCode:  # pragma: no cover
    """CLI command to print debug information."""
    _print_debug_info()
    return ExitCode.SUCCESS


def _bump(b: BumpType) -> ExitCode:  # pragma: no cover
    """Bump the version of the current package.

    Args:
        b: The type of bump ("major", "minor", or "patch").

    Returns:
        An ExitCode indicating success or failure.
    """
    if b not in VALID_BUMP_TYPES:
        print(f"Invalid argument '{b}'. Use one of: {', '.join(VALID_BUMP_TYPES)}.")
        return ExitCode.FAILURE
    try:
        new_version: Version = METADATA.version_tuple.new_version(b)
        print(str(new_version))
        return ExitCode.SUCCESS
    except ValueError:
        print(f"Invalid version tuple: {METADATA.version_tuple}")
        return ExitCode.FAILURE


def _version(name: bool = False) -> ExitCode:  # pragma: no cover
    """CLI command to get the current version of the package."""
    print(f"{METADATA.name} {METADATA.version}" if name else METADATA.version)
    return ExitCode.SUCCESS


def _to_args(args: list[str]) -> Namespace:  # pragma: no cover
    """Convert a list of arguments into a Namespace object."""
    parser = ArgumentParser(prog=METADATA.name, description="Lazy Bear CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("debug", help="Print debug information")
    version_parser: ArgumentParser = subparsers.add_parser("version", help="Get the current version")
    version_parser.add_argument("--name", action="store_true", help="Include the package name in the output")
    bump_parser: ArgumentParser = subparsers.add_parser("bump", help="Bump the version of the package")
    bump_parser.add_argument("bump_type", choices=["major", "minor", "patch"], help="Type of version bump")
    return parser.parse_args(args)


@args_inject(process=_to_args)
def main(args: Namespace) -> ExitCode:
    """Entry point for the CLI application.

    This function is executed when you type `lazy_bear` or `python -m lazy_bear`.

    Parameters:
        args: Arguments passed from the command line.

    Returns:
        An exit code.
    """
    command: str = args.command
    match command:
        case "debug":
            return _debug_info()
        case "version":
            return _version(name=args.name)
        case "bump":
            return _bump(args.bump_type)
        case _:  # pragma: no cover
            print(f"Unknown command: {command}", file=sys.stderr)
            return ExitCode.FAILURE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
