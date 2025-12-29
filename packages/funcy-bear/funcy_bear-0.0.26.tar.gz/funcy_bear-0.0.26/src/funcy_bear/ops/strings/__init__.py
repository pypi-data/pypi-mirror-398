"""Various string operations."""

from .manipulation import to_camel, to_kebab, to_pascal, to_screaming_snake, to_snake
from .sorting_name import SortingNameTool
from .string_stuffs import add_indent, cut_prefix, cut_suffix, join, to_lines

__all__ = [
    "SortingNameTool",
    "add_indent",
    "cut_prefix",
    "cut_suffix",
    "join",
    "to_camel",
    "to_kebab",
    "to_lines",
    "to_pascal",
    "to_screaming_snake",
    "to_snake",
]
