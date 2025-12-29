"""A utility to create slugs from strings."""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, Literal, overload

from funcy_bear.constants import characters as ch
from funcy_bear.constants.type_constants import LitFalse, LitTrue  # noqa: TC001
from funcy_bear.ops.collections_ops.iter_stuffs import pop_iter
from lazy_bear import LazyLoader

if TYPE_CHECKING:
    import json
    import re
    import unicodedata
else:
    re = LazyLoader("re")
    json = LazyLoader("json")
    unicodedata = LazyLoader("unicodedata")


def join_dicts(data: list[dict], sep: str = ch.NEWLINE) -> str:
    """Join a list of dictionaries into a single string with each dictionary serialized as JSON.

    Might use this with JSONL files.

    Args:
        data (list[dict]): List of dictionaries to join.
        sep (str): Separator to use between items. Defaults to newline.

    Returns:
        str: The joined string.
    """
    return sep.join(ln if isinstance(ln, str) else json.dumps(ln, ensure_ascii=False) for ln in data)


def slugify(value: str, sep: str = ch.DASH) -> str:
    """Return an ASCII slug for ``value``.

    Args:
        value: String to normalize.
        sep: Character used to replace whitespace and punctuation.

    Returns:
        A sluggified version of ``value``.
    """
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", ch.EMPTY_STRING, value.lower())
    return re.sub(r"[-_\s]+", sep, value).strip("-_")


CaseChoices = Literal["snake", "kebab", "camel", "pascal", "screaming_snake"]


class CaseConverter:
    """String casing utilities."""

    @cached_property
    def _cts_pattern(self) -> re.Pattern[str]:
        """Regex pattern to convert camelCase to snake_case.

        Returns:
            Compiled regex pattern for camelCase to snake_case conversion.
        """
        return re.compile(
            r"""
                (?<=[a-z])      # preceded by lowercase
                (?=[A-Z])       # followed by uppercase
                |               # OR
                (?<=[A-Z])      # preceded by lowercase
                (?=[A-Z][a-z])  # followed by uppercase, then lowercase
            """,
            re.X,
        )

    def camel_to_snake(self, value: str) -> str:
        """Convert a camelCase string to snake_case.

        Args:
            value: The camelCase string to convert.

        Returns:
            The converted snake_case string.
        """
        return self._cts_pattern.sub(ch.UNDERSCORE, value).lower()

    def snake_to_pascal(self, value: str) -> str:
        """Convert a snake_case string to PascalCase.

        Args:
            value: The snake_case string to convert.

        Returns:
            The converted PascalCase string.
        """
        return "".join(word.capitalize() for word in value.split(ch.UNDERSCORE))

    def snake_to_kebab(self, value: str) -> str:
        """Convert a snake_case string to kebab-case.

        Args:
            value: The snake_case string to convert.

        Returns:
            The converted kebab-case string.
        """
        return value.replace(ch.UNDERSCORE, ch.DASH)

    def _normalized_case(self, value: str) -> str:
        current_case: str = detect_case(value)
        if current_case in {"camel", "pascal"}:
            return self.camel_to_snake(value)
        if current_case == "kebab":
            return value.replace(ch.DASH, ch.UNDERSCORE)
        if current_case == "screaming_snake":
            return value.lower()
        if current_case == "snake":
            return value
        return value

    def convert_to(self, value: str, target_case: CaseChoices) -> str:
        """Convert a string to the target case format, auto-detecting the source format.

        Args:
            value: The string to convert.
            target_case: The target case format ('snake', 'kebab', 'camel', 'pascal').

        Returns:
            The converted string.

        Raises:
            ValueError: If the target case is not supported.
        """
        normalized: str = self._normalized_case(value)
        match target_case:
            case "snake":
                return normalized
            case "kebab":
                return normalized.replace(ch.UNDERSCORE, ch.DASH)
            case "camel":
                words: list[str] = normalized.split(ch.UNDERSCORE)
                first, rest = pop_iter(words)
                return first + "".join(word.capitalize() for word in rest)
            case "pascal":
                return self.snake_to_pascal(normalized)
            case "screaming_snake":
                return normalized.upper()
            case _:
                raise ValueError(f"Unsupported target case: {target_case}")


def detect_case(value: str) -> str:
    """Detect the casing format of a string.

    Args:
        value: The string to analyze.

    Returns:
        The detected case format: 'snake', 'kebab', 'camel', 'pascal', 'screaming_snake', or 'unknown'.
    """
    if not value:
        return "unknown"
    has_underscores: bool = ch.UNDERSCORE in value
    has_dashes: bool = ch.DASH in value
    has_uppercase: bool = any(c.isupper() for c in value)
    has_lowercase: bool = any(c.islower() for c in value)
    starts_with_upper: bool = first_item(value).isupper()
    has_spaces: bool = ch.SPACE in value
    if has_spaces:
        return "unknown"
    if has_underscores and has_uppercase and not has_lowercase:
        return "screaming_snake"
    if has_underscores and not has_uppercase:
        return "snake"
    if has_dashes and not has_uppercase:
        return "kebab"
    if starts_with_upper and has_uppercase and has_lowercase and not has_underscores and not has_dashes:
        return "pascal"
    if not starts_with_upper and has_uppercase and has_lowercase and not has_underscores and not has_dashes:
        return "camel"
    return "unknown"


def to_snake(value: str) -> str:
    """Convert a string to snake_case.

    Args:
        value: The string to convert.

    Returns:
        The converted snake_case string.
    """
    return CaseConverter().convert_to(value, "snake")


def to_kebab(value: str) -> str:
    """Convert a string to kebab-case.

    Args:
        value: The string to convert.

    Returns:
        The converted kebab-case string.
    """
    return CaseConverter().convert_to(value, "kebab")


def to_camel(value: str) -> str:
    """Convert a string to camelCase.

    Args:
        value: The string to convert.

    Returns:
        The converted camelCase string.
    """
    return CaseConverter().convert_to(value, "camel")


def to_pascal(value: str) -> str:
    """Convert a string to PascalCase.

    Args:
        value: The string to convert.

    Returns:
        The converted PascalCase string.
    """
    return CaseConverter().convert_to(value, "pascal")


def to_screaming_snake(value: str) -> str:
    """Convert a string to SCREAMING_SNAKE_CASE.

    Args:
        value: The string to convert.

    Returns:
        The converted SCREAMING_SNAKE_CASE string.
    """
    return CaseConverter().convert_to(value, "screaming_snake")


def convert_case(value: str, target_case: CaseChoices) -> str:
    """Convert a string to the target case format, auto-detecting the source format.

    Args:
        value: The string to convert.
        target_case: The target case format ('snake', 'kebab', 'camel', 'pascal', 'screaming_snake').

    Returns:
        The converted string.
    """
    return CaseConverter().convert_to(value, target_case)


def truncate(
    value: str,
    max_length: int,
    suffix: str = ch.ELLIPSIS,
    word_boundary: bool = False,
) -> str:
    """Truncate string to max_length, adding suffix if truncated.

    Args:
        value: String to truncate.
        max_length: Maximum length including suffix.
        suffix: String to append when truncated (default "...").
        word_boundary: If True, truncate at word boundary to avoid cutting words,
            raises a silly error if no spaces are found.

    Returns:
        Truncated string with suffix, or original string if no truncation needed.

    Examples:
        >>> truncate("Hello world", 8)
        'Hello...'
        >>> truncate("Hello world", 8, word_boundary=True)
        'Hello...'
    """
    if len(value) <= max_length:
        return value
    truncate_at: int = max_length - len(suffix)
    if truncate_at <= 0:
        return suffix[:max_length]
    if word_boundary and ch.SPACE not in value:
        raise ValueError("Cannot truncate at word boundary: no spaces found in the string.")
    if word_boundary:
        truncated: str = value[:truncate_at]
        last_space: int = truncated.rfind(ch.SPACE)
        if last_space > 0:
            truncated = truncated[:last_space]
        return join(truncated, suffix)
    return join(value[:truncate_at], suffix)


def first_item(s: Any) -> str:
    """Extract the first member.

    Args:
        s: A list or similar iterable
    Returns:
        The first member of the iterable
    """
    return pop(s, remainder=False)


@overload
def pop(s: str, n: int = 0, remainder: LitFalse = False) -> str: ...
@overload
def pop(s: str, n: int, remainder: LitTrue) -> tuple[str, str]: ...
def pop(s: str, n: int = 0, remainder: bool = True) -> tuple[str, str] | str:
    """Pop characters at the nth index from a string and return the remainder.

    Args:
        s: The string to pop from.
        n: The index at which to pop characters.
        remainder: Whether to return the remainder of the string.

    Returns:
        A tuple containing the popped character and the remainder of the string.
    """
    if n < 0 or n >= len(s):
        raise ValueError("Invalid index")
    if not remainder:
        return s[n]
    return s[n], join(s[:n], s[n + 1 :])


def extract(t: str) -> str:
    """Remove the first and last character from a string.

    Args:
        t: The string to extract from
    Returns:
        The string without the first and last character
    """
    return t[1:-1]


def quoted(s: object) -> str:
    """Return the string wrapped in double quotes.

    Args:
        s: The string to quote.

    Returns:
        The quoted string.
    """
    return join(ch.DOUBLE_QUOTE, s, ch.DOUBLE_QUOTE)


def bracketed(s: object) -> str:
    """Return the string wrapped in square brackets.

    Args:
        s: The string to bracket.

    Returns:
        The bracketed string.
    """
    return join(ch.LEFT_BRACKET, s, ch.RIGHT_BRACKET)


def braced(s: object) -> str:
    """Return the string wrapped in braces.

    Args:
        s: The string to brace.

    Returns:
        The braced string.
    """
    return f"{ch.LEFT_BRACE}{s}{ch.RIGHT_BRACE}"


def paren(s: object) -> str:
    """Return the string wrapped in parentheses.

    Args:
        s: The string to parenthesize.

    Returns:
        The parenthesized string.
    """
    return join(ch.LEFT_PAREN, s, ch.RIGHT_PAREN)


def piped(*segs: object) -> str:
    """Join segments with pipe character.

    Args:
        *segs: The segments to join.

    Returns:
        The joined string.
    """
    return join(*segs, sep=ch.PIPE)


def get_asterisks(arg: bool = False, kwarg: bool = False) -> str:
    """Get the appropriate asterisk prefix for function arguments.

    Args:
        arg: Whether it's a single asterisk argument.
        kwarg: Whether it's a double asterisk argument.

    Returns:
        The asterisk prefix as a string.
    """
    return ch.ASTERISK if arg else ch.DOUBLE_ASTERISK if kwarg else ch.EMPTY_STRING


def join(*segments: object, depth: int | None = None, indent: str | None = None, sep: str = "") -> str:
    """Concatenate segments with indentation at specified depth.

    Args:
        *segments: The string segments to join.
        depth: The indentation depth (number of indents).
        indent: Custom indent string. If None, uses default indent.
        sep: Separator to use between segments.

    Returns:
        The joined string with indentation.
    """
    _indent: str = ch.INDENT * depth if depth is not None else (indent if indent is not None else ch.EMPTY_STRING)
    return f"{_indent}{sep.join(segments)}"  # pyright: ignore[reportArgumentType]


__all__ = [
    "CaseConverter",
    "braced",
    "bracketed",
    "convert_case",
    "detect_case",
    "extract",
    "first_item",
    "get_asterisks",
    "join",
    "join_dicts",
    "paren",
    "piped",
    "quoted",
    "slugify",
    "to_camel",
    "to_kebab",
    "to_pascal",
    "to_screaming_snake",
    "to_snake",
    "truncate",
]

# if __name__ == "__main__":
#     # Example usage
#     original = "exampleStringForConversionWithVariousThings"

#     testing = "this_is_a_test_string"

#     print("To Pascal (from snake):", to_pascal(value=original))

#     print("To Screaming Snake:", to_screaming_snake(original))
#     print("Detected Case:", detect_case(original))
#     print("Truncated:", truncate(original, 30))

#     print("Original:", original)
#     print("Slugified:", slugify(original))
#     print("To Snake:", to_snake(original))
#     print("To Kebab:", to_kebab(original))
#     print("To Camel:", to_camel(original))
#     print("To Pascal:", to_pascal(original))
