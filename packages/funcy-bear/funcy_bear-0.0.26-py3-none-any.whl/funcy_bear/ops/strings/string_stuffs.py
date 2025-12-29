"""String manipulation utilities."""

from funcy_bear.constants.characters import INDENT


def add_indent(s: str, level: int = 1, sep: str = "\n") -> str:
    """Add indentation to each line of the given string.

    Args:
        s: The original string.
        level: The number of indentation levels to add (default is 1).
        sep: The separator used to split lines (default is newline).

    Returns:
        The string with added indentation.
    """
    indent: str = INDENT * level
    return sep.join(f"{indent}{line}" if line.strip() else line for line in s.split(sep))


def join(
    lines: list[str],
    prefix: str = "",
    suffix: str = "",
    sep: str = "",
) -> str:
    """Join lines into a single string with optional prefix and suffix.

    Args:
        lines: A list of string lines to join.
        prefix: An optional prefix to add at the beginning.
        suffix: An optional suffix to add at the end.
        sep: An optional separator to use between lines.

    Returns:
        A single string with the lines joined, prefixed, and suffixed.
    """
    return f"{prefix}{sep.join(lines)}{suffix}"


def to_lines(raw: str) -> list[str]:
    """Return a list of non-empty, stripped lines from the raw data.

    Args:
        raw: The raw string data to be processed.

    Returns:
        A list of non-empty, stripped lines.
    """
    return [line for line in raw.strip().splitlines() if line.strip()]


def cut_prefix(s: str, prefix: str) -> str:
    """Cuts prefix from given string if it's present.

    Args:
        s: The original string.
        prefix: The prefix to cut.

    Returns:
        The string without the prefix if it was present, otherwise the original string.
    """
    return s[len(prefix) :] if s.startswith(prefix) else s


def cut_suffix(s: str, suffix: str) -> str:
    """Cuts suffix from given string if it's present.

    Args:
        s: The original string.
        suffix: The suffix to cut.

    Returns:
        The string without the suffix if it was present, otherwise the original string.
    """
    if not suffix:
        return s
    return s[: -len(suffix)] if s.endswith(suffix) else s


__all__ = [
    "add_indent",
    "cut_prefix",
    "cut_suffix",
    "join",
    "to_lines",
]
