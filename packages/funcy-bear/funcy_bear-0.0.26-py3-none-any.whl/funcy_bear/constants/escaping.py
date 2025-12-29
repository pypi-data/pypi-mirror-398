"""Constants related to escaping characters in strings."""

from typing import Final

from funcy_bear.constants import characters as ch

N_LITERAL: Final = "n"
R_LITERAL: Final = "r"
T_LITERAL: Final = "t"
E_LITERAL: Final = "e"
F_LITERAL: Final = "f"
ZERO_QUOTE: Final = "0"
COMMA_SPACE: Final = f"{ch.COMMA} "

NEGATIVE_ZERO_QUOTE: Final = f"{ch.DASH}{ZERO_QUOTE}"

ESCAPED_BACKSLASH: Final = f"{ch.BACKSLASH}{ch.BACKSLASH}"
"""Escaped backslash string."""
ESCAPED_DOUBLE_QUOTE: Final = f"{ch.BACKSLASH}{ch.DOUBLE_QUOTE}"
"""Escaped double quote string."""
ESCAPED_NEWLINE: Final = f"{ch.BACKSLASH}{N_LITERAL}"
"""Escaped newline string."""
ESCAPED_CARRIAGE: Final = f"{ch.BACKSLASH}{R_LITERAL}"
"""Escaped carriage return string."""
ESCAPED_TAB: Final = f"{ch.BACKSLASH}{T_LITERAL}"


TO_ESCAPE_MAP: dict[str, str] = {
    ch.BACKSLASH: ESCAPED_BACKSLASH,
    ch.DOUBLE_QUOTE: ESCAPED_DOUBLE_QUOTE,
    ch.NEWLINE: ESCAPED_NEWLINE,
    ch.CARRIAGE: ESCAPED_CARRIAGE,
    ch.TAB: ESCAPED_TAB,
}
"""Mapping of characters to their escape sequences."""


FROM_ESCAPE_MAP: dict[str, str] = {
    ch.BACKSLASH: ch.BACKSLASH,
    ch.DOUBLE_QUOTE: ch.DOUBLE_QUOTE,
    N_LITERAL: ch.NEWLINE,
    R_LITERAL: ch.CARRIAGE,
    T_LITERAL: ch.TAB,
}
"""Mapping of escape sequences to their characters."""
