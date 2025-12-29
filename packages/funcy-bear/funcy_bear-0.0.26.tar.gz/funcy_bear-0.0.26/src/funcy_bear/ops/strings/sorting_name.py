"""Functions for converting names to sorting names."""

import re
from string import ascii_letters, digits

ROMAN_CONVERSIONS: list[tuple[str, str]] = [
    ("X", "10"),
    ("IX", "09"),
    ("VIII", "08"),
    ("VII", "07"),
    ("VI", "06"),
    ("V", "05"),
    ("IV", "04"),
    ("III", "03"),
    ("II", "02"),
    ("I", "01"),
]


DEFAULT_FILTERED_WORDS: list[str] = ["The ", "A ", "An "]
ALLOWED_CHARS: str = ascii_letters + digits + " "


class SortingNameTool:
    """A tool for converting unnormalized names to sorting names."""

    def __init__(
        self,
        name: str,
        filtered_words: list[str] | None = None,
        roman: bool = False,
        article_filter: bool = True,
        alphanum: bool = False,
        sortable_nums: bool = True,
    ) -> None:
        """Initialize the SortingNameTool with a name.

        Args:
            name (str): The original name.
            roman (bool, optional): Whether to handle Roman numerals. Defaults to False.
            article_filter (bool, optional): Whether to filter out common articles("The", "A", "An"). Defaults to True.
            alphanum (bool, optional): Whether to remove non-alphanumeric characters. Defaults to False.
            sortable_nums (bool, optional): Whether to make numbers sortable. Defaults to True.
            filtered_words (list[str] | None, optional): Additional words to filter out. Defaults to None.
        """
        self.name: str = name
        self.roman: bool = roman
        self.article_filter: bool = article_filter
        self.alphanum: bool = alphanum
        self.sortable_nums: bool = sortable_nums

        filtered: list[str] = filtered_words if filtered_words is not None else []
        self.filtered_words: tuple[str, ...] = (*DEFAULT_FILTERED_WORDS, *filtered)

    @staticmethod
    def word_filter(name: str, filtered_words: tuple[str, ...]) -> str:
        """Remove common prefixes from a name.

        Args:
            name (str): The original name.
            filtered_words (tuple[str]): List of common prefixes to remove.

        Returns:
            str: The name without common prefixes.
        """
        for prefix in filtered_words:
            if name.startswith(prefix):
                name = name[len(prefix) :]
                break
        return name

    @staticmethod
    def roman_convert(og: str) -> str:
        """Convert Roman numerals at word boundaries to numbers.

        Args:
            og (str): The original string.

        Returns:
            str: The converted sorting string.
        """
        converted: str = og
        for roman, number in ROMAN_CONVERSIONS:
            # Use word boundaries to match Roman numerals properly
            # \b ensures we match whole "words" not parts of other text
            pattern: str = rf"\b{roman}\b"
            if re.search(pattern, converted):
                converted = re.sub(pattern, number, converted)
                break
        return converted

    @staticmethod
    def alpha_filter(og: str) -> str:
        """Remove non-alphanumeric characters from a string.

        Args:
            og (str): The original string.

        Returns:
            str: The alphanumeric-only string.
        """
        return "".join(char for char in og if char in ALLOWED_CHARS)

    @staticmethod
    def make_sortable_nums(og: str) -> str:
        """Make numbers in a string sortable by padding them with leading zeros.

        Args:
            og (str): The original string.

        Returns:
            str: The string with sortable numbers.
        """
        stack: list[str] = []
        current_num: str = ""
        for char in og:
            if char.isdigit():
                current_num += char
            else:
                if current_num:
                    stack.append(current_num.zfill(2))
                    current_num = ""
                stack.append(char)
        if current_num:
            stack.append(current_num.zfill(2))
        return "".join(stack)

    def sorting_name(self) -> str:
        """Generate a sorting name based on the initialized parameters.

        Returns:
            str: The generated sorting name.
        """
        name: str = self.name
        if self.article_filter:
            name = self.word_filter(name, self.filtered_words)
        if self.alphanum:
            name = self.alpha_filter(name)
        if self.roman:
            name = self.roman_convert(name)
        if self.sortable_nums:
            name = self.make_sortable_nums(name)
        return name


def sorting_name(
    name: str,
    filtered_words: list[str] | None = None,
    roman: bool = False,
    article_filter: bool = True,
    alphanum: bool = False,
    sortable_nums: bool = True,
) -> str:
    """Generate a sorting name from a name.

    Args:
        name (str): The original name.
        roman (bool, optional): Whether to handle Roman numerals. Defaults to False.
        article_filter (bool, optional): Whether to filter out common articles. Defaults to True.
        alphanum (bool, optional): Whether to remove non-alphanumeric characters. Defaults to False.
        sortable_nums (bool, optional): Whether to make numbers sortable. Defaults to True.

    Returns:
        str: The generated sorting name.
    """
    tool = SortingNameTool(
        name=name,
        filtered_words=filtered_words,
        roman=roman,
        article_filter=article_filter,
        alphanum=alphanum,
        sortable_nums=sortable_nums,
    )
    return tool.sorting_name()


# if __name__ == "__main__":
#     examples: list[str] = [
#         "The Legend of Zelda",
#         "A Tale of Two Cities",
#         "Final Fantasy VII",
#         "Super Mario Bros. 3",
#         "Xenoblade Chronicles 2",
#         "Resident Evil IV",
#         "Halo 2: Anniversary",
#         "Call of Duty: Modern Warfare 3",
#         "The Witcher 3: Wild Hunt",
#         "Assassin's Creed II",
#         "God of War III",
#         "Metal Gear Solid V: The Phantom Pain",
#         "The Elder Scrolls V: Skyrim",
#         "Red Dead Redemption II",
#         "Mass Effect 2",
#         "BioShock Infinite",
#         "Dark Souls III",
#         "Dragon Age: Inquisition",
#         "Fallout 4",
#         "The Last of Us Part II",
#     ]

#     for example in examples:
#         print(f"Original: {example}")
#         print(f"Sorted:   {sorting_name(example, roman=True, alphanum=True)}")
#         print()
