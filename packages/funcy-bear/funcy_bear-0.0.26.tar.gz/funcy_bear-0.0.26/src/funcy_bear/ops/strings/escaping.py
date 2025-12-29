"""String escaping operations."""

from funcy_bear.constants import characters as ch
from funcy_bear.constants.escaping import FROM_ESCAPE_MAP, TO_ESCAPE_MAP
from funcy_bear.tools.string_cursor import StringCursor

ESCAPE_CHAR_SIZE = 2
"""The size of an escape character sequence, e.g., \n is 2 characters long."""


def return_escaped(c: str) -> str:
    """Return escaped character.

    Args:
        c: Character to escape
    Returns:
        Escaped character
    """
    if c not in TO_ESCAPE_MAP:
        return c
    return TO_ESCAPE_MAP[c]


def escape_string(s: str) -> str:
    """Escape a string.

    Args:
        s: String to escape
    Returns:
        Escaped string
    """
    return f"{ch.DOUBLE_QUOTE}{ch.EMPTY_STRING.join(return_escaped(c) for c in s)}{ch.DOUBLE_QUOTE}"


def return_unescaped(next_ch: str) -> str:
    """Return unescaped character.

    Args:
        next_ch: The character following the backslash
    Returns:
        The unescaped character
    """
    if next_ch not in FROM_ESCAPE_MAP:
        raise ValueError(f"Invalid escape sequence: \\{next_ch}")
    return FROM_ESCAPE_MAP[next_ch]


def unescape_string(s: str) -> str:
    r"""Unescape a string.

    Only valid escapes: \\, \", \n, \r, \t

    Args:
        s: String to unescape
    Returns:
        Unescaped string
    Raises:
        ValueError for invalid escape sequences.
    """
    result: list[str] = []
    cursor = StringCursor(s)
    while cursor.within_bounds:
        if cursor.is_char(ch.BACKSLASH):
            result.append(return_unescaped(cursor.peek(1)))
            cursor.move(ESCAPE_CHAR_SIZE)
        else:
            result.append(cursor.current)
            cursor.tick()
    return "".join(result)
