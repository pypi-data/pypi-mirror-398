"""Constants for common characters used in formatting and code generation."""

from enum import StrEnum
from typing import Final

SPACE: Final[str] = " "
INDENT: Final[str] = SPACE * 4
NEWLINE: Final[str] = "\n"
CARRIAGE: Final[str] = "\r"
BACKSLASH: Final[str] = "\\"
TRIPLE_QUOTE: Final[str] = '"""'
SINGLE_TRIPLE_QUOTE: Final[str] = "'''"
EMPTY_STRING: Final[str] = ""

LEFT_BRACE: Final[str] = "{"
RIGHT_BRACE: Final[str] = "}"
LEFT_PAREN: Final[str] = "("
RIGHT_PAREN: Final[str] = ")"
LEFT_BRACKET: Final[str] = "["
RIGHT_BRACKET: Final[str] = "]"

COMMA: Final[str] = ","
COLON: Final[str] = ":"
SEMICOLON: Final[str] = ";"
DOT: Final[str] = "."
EQUALS: Final[str] = "="
DOUBLE_QUOTE: Final[str] = '"'
SINGLE_QUOTE: Final[str] = "'"

HASH: Final[str] = "#"
TAB: Final[str] = "\t"
UNDERSCORE: Final[str] = "_"
DASH: Final[str] = "-"
PIPE: Final[str] = "|"
AMPERSAND: Final[str] = "&"
AT: Final[str] = "@"

ARROW: Final[str] = "->"
ASTERISK: Final[str] = "*"
DOUBLE_ASTERISK: Final[str] = ASTERISK * 2
PLUS: Final[str] = "+"
FORWARD_SLASH: Final[str] = "/"
PERCENT: Final[str] = "%"
CARET: Final[str] = "^"
TILDE: Final[str] = "~"
EXCLAMATION: Final[str] = "!"
QUESTION: Final[str] = "?"
LESS_THAN: Final[str] = "<"
GREATER_THAN: Final[str] = ">"
DOLLAR: Final[str] = "$"
LIST_ITEM_MARKER: Final[str] = "-"
LIST_ITEM_PREFIX: Final[str] = "- "

NULL_LITERAL: Final[str] = "null"
TRUE_LITERAL: Final[str] = "true"
FALSE_LITERAL: Final[str] = "false"
ELLIPSIS: Final[str] = "..."


class ControlCharacter(StrEnum):
    """Enumeration of control characters."""

    NEWLINE = "\n"
    CARRIAGE_RETURN = "\r"
    TAB = "\t"
    SPACE = " "


class BracketCharacter(StrEnum):
    """Enumeration of bracket/brace/parenthesis characters."""

    LEFT_BRACE = "{"
    RIGHT_BRACE = "}"
    LEFT_PAREN = "("
    RIGHT_PAREN = ")"
    LEFT_BRACKET = "["
    RIGHT_BRACKET = "]"


class QuoteCharacter(StrEnum):
    """Enumeration of quote characters."""

    SINGLE_QUOTE = "'"
    DOUBLE_QUOTE = '"'
    BACKSLASH = "\\"


class PunctuationCharacter(StrEnum):
    """Enumeration of punctuation characters."""

    COMMA = ","
    COLON = ":"
    SEMICOLON = ";"
    DOT = "."
    EQUALS = "="
    HASH = "#"
    UNDERSCORE = "_"
    DASH = "-"
    PIPE = "|"
    AMPERSAND = "&"
    AT = "@"
    ASTERISK = "*"
    PLUS = "+"
    FORWARD_SLASH = "/"
    PERCENT = "%"
    CARET = "^"
    TILDE = "~"
    EXCLAMATION = "!"
    QUESTION = "?"
    LESS_THAN = "<"
    GREATER_THAN = ">"
    DOLLAR = "$"
    ELLIPSIS = "..."


class LiteralCharacter(StrEnum):
    """Enumeration of literal string values."""

    NULL_LITERAL = "null"
    TRUE_LITERAL = "true"
    FALSE_LITERAL = "false"


__all__ = [
    "AMPERSAND",
    "ASTERISK",
    "AT",
    "BACKSLASH",
    "CARET",
    "CARRIAGE",
    "COLON",
    "COMMA",
    "DASH",
    "DOLLAR",
    "DOT",
    "DOUBLE_QUOTE",
    "ELLIPSIS",
    "EQUALS",
    "EXCLAMATION",
    "FALSE_LITERAL",
    "FORWARD_SLASH",
    "GREATER_THAN",
    "HASH",
    "INDENT",
    "LEFT_BRACE",
    "LEFT_BRACKET",
    "LEFT_PAREN",
    "LESS_THAN",
    "LIST_ITEM_MARKER",
    "LIST_ITEM_PREFIX",
    "NEWLINE",
    "NULL_LITERAL",
    "PERCENT",
    "PIPE",
    "PLUS",
    "QUESTION",
    "RIGHT_BRACE",
    "RIGHT_BRACKET",
    "RIGHT_PAREN",
    "SEMICOLON",
    "SINGLE_QUOTE",
    "SINGLE_TRIPLE_QUOTE",
    "SPACE",
    "TAB",
    "TILDE",
    "TRIPLE_QUOTE",
    "TRUE_LITERAL",
    "UNDERSCORE",
    "BracketCharacter",
    "ControlCharacter",
    "LiteralCharacter",
    "PunctuationCharacter",
    "QuoteCharacter",
]
