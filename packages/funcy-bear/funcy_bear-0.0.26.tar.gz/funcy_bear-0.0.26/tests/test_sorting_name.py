"""Tests for sorting_name module."""

from funcy_bear.ops.strings.sorting_name import SortingNameTool, sorting_name


class TestWordFilter:
    """Test word_filter static method."""

    def test_filter_the(self):
        """Test filtering 'The' prefix."""
        result: str = SortingNameTool.word_filter("The Matrix", ("The ",))
        assert result == "Matrix"

    def test_filter_a(self):
        """Test filtering 'A' prefix."""
        result: str = SortingNameTool.word_filter("A New Hope", ("A ",))
        assert result == "New Hope"

    def test_filter_an(self):
        """Test filtering 'An' prefix."""
        result: str = SortingNameTool.word_filter("An American Tail", ("An ",))
        assert result == "American Tail"

    def test_no_match(self):
        """Test no filtering when prefix doesn't match."""
        result: str = SortingNameTool.word_filter("Star Wars", ("The ",))
        assert result == "Star Wars"

    def test_first_match_only(self):
        """Test only first matching prefix is removed."""
        result: str = SortingNameTool.word_filter("The The Band", ("The ", "A "))
        assert result == "The Band"


class TestRomanConvert:
    """Test roman_convert static method."""

    def test_roman_numeral_ending(self):
        """Test converting Roman numerals at end."""
        assert SortingNameTool.roman_convert("Part III") == "Part 03"
        assert SortingNameTool.roman_convert("Chapter VII") == "Chapter 07"
        assert SortingNameTool.roman_convert("Episode X") == "Episode 10"

    def test_roman_numeral_middle(self):
        """Test converting Roman numerals in middle."""
        assert SortingNameTool.roman_convert("Part II Extended") == "Part 02 Extended"
        assert SortingNameTool.roman_convert("Chapter V Special") == "Chapter 05 Special"

    def test_no_roman_numerals(self):
        """Test no conversion when no Roman numerals."""
        assert SortingNameTool.roman_convert("Part 3") == "Part 3"
        assert SortingNameTool.roman_convert("Something") == "Something"

    def test_complex_roman_numerals(self):
        """Test complex Roman numeral patterns."""
        # These should match patterns in ROMAN_CONVERSIONS
        assert SortingNameTool.roman_convert("Episode VIII") == "Episode 08"
        assert SortingNameTool.roman_convert("Part VI") == "Part 06"


class TestAlphaFilter:
    """Test alpha_filter static method."""

    def test_remove_punctuation(self) -> None:
        """Test removing punctuation."""
        assert SortingNameTool.alpha_filter("Hello, World!") == "Hello World"
        assert SortingNameTool.alpha_filter("Test: 123") == "Test 123"

    def test_keep_alphanumeric(self) -> None:
        """Test keeping alphanumeric characters."""
        assert SortingNameTool.alpha_filter("Test123") == "Test123"
        assert SortingNameTool.alpha_filter("ABC 456") == "ABC 456"

    def test_remove_special_chars(self) -> None:
        """Test removing special characters."""
        assert SortingNameTool.alpha_filter("Test@#$%") == "Test"
        assert SortingNameTool.alpha_filter("Hello(World)") == "HelloWorld"


class TestMakeSortableNums:
    """Test make_sortable_nums static method."""

    def test_single_digit_padding(self) -> None:
        """Test padding single digits."""
        assert SortingNameTool.make_sortable_nums("Part 3") == "Part 03"
        assert SortingNameTool.make_sortable_nums("Chapter 5") == "Chapter 05"

    def test_double_digit_no_padding(self) -> None:
        """Test double digits don't get padded."""
        assert SortingNameTool.make_sortable_nums("Part 10") == "Part 10"
        assert SortingNameTool.make_sortable_nums("Chapter 25") == "Chapter 25"

    def test_multiple_numbers(self) -> None:
        """Test multiple numbers in string."""
        assert SortingNameTool.make_sortable_nums("Season 2 Episode 3") == "Season 02 Episode 03"

    def test_no_numbers(self) -> None:
        """Test string with no numbers."""
        assert SortingNameTool.make_sortable_nums("Hello World") == "Hello World"

    def test_number_at_end(self) -> None:
        """Test number at end of string."""
        assert SortingNameTool.make_sortable_nums("Version 5") == "Version 05"


class TestSortingNameToolInit:
    """Test SortingNameTool initialization."""

    def test_default_initialization(self) -> None:
        """Test default parameter values."""
        tool = SortingNameTool("Test Name")
        assert tool.name == "Test Name"
        assert tool.roman is False
        assert tool.article_filter is True
        assert tool.alphanum is False
        assert tool.sortable_nums is True

    def test_custom_parameters(self) -> None:
        """Test custom parameter values."""
        tool = SortingNameTool(
            "Test Name",
            roman=True,
            article_filter=False,
            alphanum=True,
            sortable_nums=False,
        )
        assert tool.roman is True
        assert tool.article_filter is False
        assert tool.alphanum is True
        assert tool.sortable_nums is False

    def test_filtered_words_default(self) -> None:
        """Test default filtered words."""
        tool = SortingNameTool("Test Name")
        assert "The " in tool.filtered_words
        assert "A " in tool.filtered_words
        assert "An " in tool.filtered_words

    def test_filtered_words_custom(self) -> None:
        """Test custom filtered words."""
        tool = SortingNameTool("Test Name", filtered_words=["Custom "])
        assert "Custom " in tool.filtered_words
        assert "The " in tool.filtered_words  # Defaults still included


class TestSortingNameToolMethod:
    """Test SortingNameTool.sorting_name method."""

    def test_article_filter_only(self) -> None:
        """Test with only article filter."""
        tool = SortingNameTool(
            "The Matrix",
            article_filter=True,
            alphanum=False,
            roman=False,
            sortable_nums=False,
        )
        assert tool.sorting_name() == "Matrix"

    def test_alphanum_only(self) -> None:
        """Test with only alphanum filter."""
        tool = SortingNameTool(
            "Hello, World!",
            article_filter=False,
            alphanum=True,
            roman=False,
            sortable_nums=False,
        )
        assert tool.sorting_name() == "Hello World"

    def test_roman_only(self) -> None:
        """Test with only Roman numeral conversion."""
        tool = SortingNameTool(
            "Part III",
            article_filter=False,
            alphanum=False,
            roman=True,
            sortable_nums=False,
        )
        assert tool.sorting_name() == "Part 03"

    def test_sortable_nums_only(self) -> None:
        """Test with only sortable numbers."""
        tool = SortingNameTool(
            "Chapter 5",
            article_filter=False,
            alphanum=False,
            roman=False,
            sortable_nums=True,
        )
        assert tool.sorting_name() == "Chapter 05"

    def test_all_filters_combined(self) -> None:
        """Test with all filters enabled."""
        tool = SortingNameTool(
            "The Legend: Part III",
            article_filter=True,
            alphanum=True,
            roman=True,
            sortable_nums=True,
        )
        result: str = tool.sorting_name()
        assert not result.startswith("The ")
        assert ":" not in result
        assert "03" in result


class TestSortingNameFunction:
    """Test sorting_name convenience function."""

    def test_basic_usage(self) -> None:
        """Test basic function usage."""
        result: str = sorting_name("The Matrix")
        assert result == "Matrix"

    def test_with_roman(self) -> None:
        """Test with Roman numeral handling."""
        result: str = sorting_name("Final Fantasy VII", roman=True)
        assert "07" in result

    def test_with_alphanum(self) -> None:
        """Test with alphanumeric filter."""
        result: str = sorting_name("Hello, World!", alphanum=True)
        assert "," not in result

    def test_disable_article_filter(self) -> None:
        """Test disabling article filter."""
        result: str = sorting_name("The Matrix", article_filter=False)
        assert result == "The Matrix"

    def test_disable_sortable_nums(self) -> None:
        """Test disabling sortable numbers."""
        result: str = sorting_name("Part 3", sortable_nums=False)
        assert result == "Part 3"

    def test_custom_filtered_words(self) -> None:
        """Test custom filtered words."""
        result: str = sorting_name("My Title", filtered_words=["My "])
        assert result == "Title"


class TestRealWorldExamples:
    """Test real-world examples."""

    def test_video_game_titles(self):
        """Test sorting video game titles."""
        assert sorting_name("The Legend of Zelda", roman=True) == "Legend of Zelda"
        assert sorting_name("Final Fantasy VII", roman=True) == "Final Fantasy 07"
        assert sorting_name("The Witcher 3", roman=True) == "Witcher 03"

    def test_movie_titles(self):
        """Test sorting movie titles."""
        assert sorting_name("The Matrix") == "Matrix"
        assert sorting_name("A New Hope") == "New Hope"
        # Test a movie with Roman numerals that works with the conversion list
        result = sorting_name("Rocky III", roman=True)
        assert "03" in result

    def test_book_titles(self):
        """Test sorting book titles."""
        assert sorting_name("The Great Gatsby") == "Great Gatsby"
        assert sorting_name("A Tale of Two Cities") == "Tale of Two Cities"

    def test_series_with_numbers(self):
        """Test series with numbers."""
        assert sorting_name("Season 2 Episode 5") == "Season 02 Episode 05"
        assert sorting_name("Volume 3") == "Volume 03"
