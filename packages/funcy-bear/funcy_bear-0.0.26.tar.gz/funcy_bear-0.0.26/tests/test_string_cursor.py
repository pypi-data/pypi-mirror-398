"""Tests for StringCursor class."""

import pytest

from funcy_bear.tools.string_cursor import StringCursor


class TestStringCursorInit:
    """Test StringCursor initialization."""

    def test_init_with_string(self) -> None:
        """Test initialization with a valid string."""
        cursor = StringCursor("hello")
        assert cursor.collection == "hello"
        assert cursor.index == 0

    def test_init_with_empty_string(self) -> None:
        """Test initialization with an empty string."""
        cursor = StringCursor("")
        assert cursor.collection == ""
        assert cursor.is_empty

    def test_init_with_non_string_raises_type_error(self) -> None:
        """Test that initialization with non-string raises TypeError."""
        with pytest.raises(TypeError, match="Expected str, got"):
            StringCursor(123)  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="Expected str, got"):
            StringCursor(["a", "b", "c"])  # type: ignore[arg-type]


class TestStringCursorCharComparison:
    """Test character comparison methods."""

    def test_is_char(self) -> None:
        """Test is_char method."""
        cursor = StringCursor("hello")
        assert cursor.is_char("h")
        assert not cursor.is_char("e")

        cursor.tick()
        assert cursor.is_char("e")
        assert not cursor.is_char("h")

    def test_prev_char_equals(self) -> None:
        """Test prev_char_equals method."""
        cursor = StringCursor("hello")
        cursor.set_index(2)  # At 'l'
        assert cursor.prev_char_equals("e")
        assert not cursor.prev_char_equals("h")

    def test_prev_char_equals_at_start(self) -> None:
        """Test prev_char_equals at start of string."""
        cursor = StringCursor("hello")
        # At index 0 with allow_negative=False (default), should return False
        assert not cursor.prev_char_equals("h")
        assert not cursor.prev_char_equals("e")

    def test_next_char_equals(self) -> None:
        """Test next_char_equals method."""
        cursor = StringCursor("hello")
        assert cursor.next_char_equals("e")
        cursor.tick()
        assert cursor.next_char_equals("l")

    def test_next_char_equals_at_end(self) -> None:
        """Test next_char_equals at end of string."""
        cursor = StringCursor("hello")
        cursor.tail()  # Move to 'o'
        # At end, peek(1) returns default value (empty string) since we're beyond bounds
        # even with constrained=False, there's no character beyond the end
        assert not cursor.next_char_equals("o")
        assert cursor.next_char_equals("")  # Default value is empty string

    def test_n_char_equals(self):
        """Test n_char_equals method with various offsets."""
        cursor = StringCursor("hello")
        cursor.set_index(1)  # At 'e'

        assert cursor.n_char_equals(0, "e")
        assert cursor.n_char_equals(1, "l")
        assert cursor.n_char_equals(2, "l")
        assert cursor.n_char_equals(-1, "h")
        assert not cursor.n_char_equals(1, "x")

        # Test negative offset at start with allow_negative=False
        cursor.set_index(0)
        assert not cursor.n_char_equals(-1, "h")  # Returns False, not clamped

    def test_head_equals(self) -> None:
        """Test head_equals method."""
        cursor = StringCursor("hello")
        assert cursor.head_equals("h")
        assert not cursor.head_equals("e")

        cursor.set_index(3)
        assert cursor.head_equals("h")  # Still first char

    def test_head_equals_empty_string(self) -> None:
        """Test head_equals on empty string."""
        cursor = StringCursor("")
        assert not cursor.head_equals("a")

    def test_tail_equals(self) -> None:
        """Test tail_equals method."""
        cursor = StringCursor("hello")
        assert cursor.tail_equals("o")
        assert not cursor.tail_equals("l")

        cursor.set_index(2)
        assert cursor.tail_equals("o")  # Still last char

    def test_tail_equals_empty_string(self) -> None:
        """Test tail_equals on empty string."""
        cursor = StringCursor("")
        assert not cursor.tail_equals("a")


class TestStringCursorMatchesAhead:
    """Test matches_ahead method."""

    def test_matches_ahead_single_char(self) -> None:
        """Test matching a single character ahead."""
        cursor = StringCursor("hello")
        assert cursor.matches_ahead("h")
        assert cursor.matches_ahead("he")
        assert not cursor.matches_ahead("x")

    def test_matches_ahead_full_string(self) -> None:
        """Test matching the entire string."""
        cursor = StringCursor("hello")
        assert cursor.matches_ahead("hello")
        assert not cursor.matches_ahead("hello!")

    def test_matches_ahead_from_middle(self) -> None:
        """Test matching from middle of string."""
        cursor = StringCursor("hello world")
        cursor.set_index(6)  # At 'w'
        assert cursor.matches_ahead("world")
        assert cursor.matches_ahead("w")
        assert not cursor.matches_ahead("hello")

    def test_matches_ahead_partial_match(self) -> None:
        """Test partial matches."""
        cursor = StringCursor("hello")
        cursor.set_index(1)  # At 'e'
        assert cursor.matches_ahead("ello")
        assert cursor.matches_ahead("el")
        assert not cursor.matches_ahead("hello")

    def test_matches_ahead_empty_string(self) -> None:
        """Test matching empty string."""
        cursor = StringCursor("hello")
        assert cursor.matches_ahead("")  # Empty string always matches

    def test_matches_ahead_beyond_end(self) -> None:
        """Test matching beyond string end."""
        cursor = StringCursor("hello")
        cursor.tail()  # At 'o'
        assert cursor.matches_ahead("o")
        assert not cursor.matches_ahead("oo")
        assert not cursor.matches_ahead("hello")

    def test_matches_ahead_exact_fit(self) -> None:
        """Test matching exactly to the end."""
        cursor = StringCursor("hello")
        cursor.set_index(3)  # At first 'l'
        assert cursor.matches_ahead("lo")
        assert not cursor.matches_ahead("loo")

    def test_matches_ahead_case_sensitive(self) -> None:
        """Test that matching is case-sensitive."""
        cursor = StringCursor("Hello")
        assert cursor.matches_ahead("Hello")
        assert not cursor.matches_ahead("hello")
        assert cursor.matches_ahead("H")
        assert not cursor.matches_ahead("h")


class TestStringCursorEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_single_character_string(self) -> None:
        """Test operations on single character string."""
        cursor = StringCursor("x")
        assert cursor.is_char("x")
        assert cursor.head_equals("x")
        assert cursor.tail_equals("x")
        assert cursor.matches_ahead("x")
        assert not cursor.matches_ahead("xy")

    def test_unicode_characters(self) -> None:
        """Test with unicode characters."""
        cursor = StringCursor("hello 🐻 world")
        cursor.set_index(6)  # At bear emoji
        assert cursor.is_char("🐻")
        assert cursor.matches_ahead("🐻 world")

    def test_special_characters(self) -> None:
        """Test with special characters."""
        cursor = StringCursor("hello\nworld\t!")
        assert cursor.matches_ahead("hello\n")
        cursor.set_index(6)
        assert cursor.is_char("w")
        assert cursor.matches_ahead("world\t!")

    def test_whitespace_handling(self):
        """Test with various whitespace."""
        cursor = StringCursor("  hello  ")
        assert cursor.is_char(" ")
        assert cursor.matches_ahead("  hello")
        cursor.tick()
        assert cursor.is_char(" ")

    def test_cursor_movement_with_comparisons(self):
        """Test combining cursor movement with comparisons."""
        cursor = StringCursor("abcdef")

        assert cursor.is_char("a")
        cursor.tick()
        assert cursor.is_char("b")
        assert cursor.prev_char_equals("a")
        assert cursor.next_char_equals("c")

        cursor.set_index(3)
        assert cursor.matches_ahead("def")
        cursor.tick()
        assert cursor.matches_ahead("ef")

    def test_repeated_characters(self):
        """Test with repeated characters."""
        cursor = StringCursor("aaaaaa")
        for i in range(6):
            cursor.set_index(i)
            assert cursor.is_char("a")
            assert cursor.head_equals("a")
            assert cursor.tail_equals("a")

    def test_all_methods_on_empty_string(self):
        """Test all comparison methods handle empty string gracefully."""
        cursor = StringCursor("")

        assert not cursor.is_char("a")
        assert not cursor.head_equals("a")
        assert not cursor.tail_equals("a")
        assert cursor.matches_ahead("")
        assert not cursor.matches_ahead("a")

        # These use peek which should handle empty collection
        assert not cursor.prev_char_equals("a")
        assert not cursor.next_char_equals("a")
        assert not cursor.n_char_equals(0, "a")


class TestStringCursorAllowNegative:
    """Test behavior when allow_negative is enabled."""

    def test_prev_char_equals_with_allow_negative(self):
        """Test prev_char_equals at start when allow_negative=True."""
        cursor = StringCursor("hello", allow_negative=True)
        # With allow_negative=True, should still return False at start
        # because there is no character before index 0
        assert not cursor.prev_char_equals("h")

    def test_n_char_equals_with_allow_negative(self):
        """Test n_char_equals with negative offsets when allow_negative=True."""
        cursor = StringCursor("hello", allow_negative=True)
        cursor.set_index(2)  # At 'l'

        assert cursor.n_char_equals(-1, "e")
        assert cursor.n_char_equals(-2, "h")

        # At start, negative offsets should still return False
        cursor.set_index(0)
        assert not cursor.n_char_equals(-1, "x")

    def test_tock_at_start_with_allow_negative(self):
        """Test tock at start of string when allow_negative=True."""
        cursor = StringCursor("hello", allow_negative=True)
        # tock() should allow negative index when allow_negative=True
        cursor.tock()
        assert cursor.index == -1

    def test_tock_at_start_without_allow_negative(self):
        """Test tock at start of string when allow_negative=False."""
        cursor = StringCursor("hello", allow_negative=False)
        # tock() should do nothing when at index 0 and allow_negative=False
        cursor.tock()
        assert cursor.index == 0


class TestStringCursorIntegration:
    """Integration tests combining multiple features."""

    def test_scanning_pattern(self):
        """Test a typical scanning pattern."""
        text = "The quick brown fox"
        cursor = StringCursor(text)

        # Scan for "quick"
        while cursor.index < cursor.size and not cursor.matches_ahead("quick"):
            cursor.tick()

        assert cursor.matches_ahead("quick")
        assert cursor.is_char("q")

    def test_parsing_tokens(self):
        """Test parsing-like operations."""
        cursor = StringCursor("name=value")

        # Find '='
        while not cursor.is_char("="):
            cursor.tick()

        assert cursor.prev_char_equals("e")
        assert cursor.next_char_equals("v")
        assert cursor.matches_ahead("=value")

    def test_boundary_checking(self):
        """Test operations near boundaries."""
        cursor = StringCursor("abc")

        # Start boundary
        assert cursor.is_char("a")
        assert cursor.head_equals("a")
        assert cursor.matches_ahead("abc")

        # End boundary
        cursor.tail()
        assert cursor.is_char("c")
        assert cursor.tail_equals("c")
        assert cursor.matches_ahead("c")
        assert not cursor.matches_ahead("cd")
