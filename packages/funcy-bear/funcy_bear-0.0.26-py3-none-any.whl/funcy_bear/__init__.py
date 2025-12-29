"""Funcy Bear: A collection of functional programming utilities."""

from funcy_bear._internal.cli import METADATA, main

__version__: str = METADATA.version

__all__: list[str] = ["METADATA", "__version__", "main"]
