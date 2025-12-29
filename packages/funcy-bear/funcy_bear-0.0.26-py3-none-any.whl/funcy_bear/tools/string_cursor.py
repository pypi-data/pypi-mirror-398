"""String cursor for scanning through a string one character at a time."""

from funcy_bear.ops.math.general import neg

# TODO: Update this will Cython version at some point


class StringCursor:
    """Cursor for scanning through a string one character at a time."""

    def __init__(self, text: str = "", *, allow_negative: bool = False) -> None:
        """Initialize cursor with text to scan."""
        if not isinstance(text, str):
            raise TypeError(f"Expected str, got {type(text).__name__}")
        self._text: str = text
        self.index: int = 0
        self.allow_neg: bool = allow_negative

    @property
    def collection(self) -> str:
        """Get the entire text being scanned."""
        return self._text

    @property
    def head_value(self) -> str:
        """Get the first character in the text."""
        return self._text[0]

    @property
    def tail_value(self) -> str:
        """Get the last character in the text."""
        return self._text[-1]

    @property
    def not_empty(self) -> bool:
        """Check if the text is not empty."""
        return self.size > 0

    @property
    def current(self) -> str:
        """Get the current character at the cursor's index."""
        if 0 <= self.index < len(self._text):
            return self._text[self.index]
        raise IndexError("Cursor index out of bounds")

    def move(self, offset: int) -> None:
        """Move the cursor by a given offset.

        Args:
            offset: Number of positions to move the cursor
        """
        self._move(offset)

    def _move(self, offset: int) -> None:
        new_index: int = self.index + offset
        if not self.allow_neg and new_index < 0:
            self.index = 0
        elif new_index > len(self._text):
            self.index = len(self._text)
        else:
            self.index = new_index

    def peek(self, offset: int) -> str:
        """Peek at character at offset from current index.

        Args:
            offset: Offset from current index
        Returns:
            Character at offset, or None if out of bounds
        """
        target_index: int = self.index + offset
        if 0 <= target_index < self.size:
            return self._text[target_index]
        return ""

    def set_index(self, new_index: int) -> None:
        """Set the cursor's index to a new value.

        Args:
            new_index: The new index to set the cursor to
        """
        if not self.allow_neg and new_index < 0:
            self.index = 0
        elif new_index > self.size:
            self.index = self.size
        else:
            self.index = new_index

    def tick(self) -> None:
        """Move the cursor forward by one."""
        self._move(1)

    def tock(self) -> None:
        """Move the cursor backward by one."""
        if not self.allow_neg and self.index == 0:
            return
        self._move(neg(1))

    def prev_char_equals(self, s: str) -> bool:
        """Check if previous character equals target character.

        Args:
            s: Target character to compare
        Returns:
            True if previous character equals s
        """
        if not self.allow_neg and self.index == 0:
            return False
        return self.peek(-1) == s

    def next_char_equals(self, s: str) -> bool:
        """Check if next character equals target character.

        Args:
            s: Target character to compare
        Returns:
            True if next character equals s
        """
        return self.peek(1) == s

    def is_char(self, s: str) -> bool:
        """Check if current character equals target character.

        Args:
            s: Target character to compare
        Returns:
            True if current character equals s
        """
        return self.peek(0) == s

    def head(self) -> None:
        """Set index to the first character in the text."""
        self.index = 0

    def tail(self) -> None:
        """Set index to the last character in the text."""
        self.index = self.size - 1

    def n_char_equals(self, o: int, s: str) -> bool:
        """Check if character at offset equals target character.

        Args:
            o: Offset from current index
            s: Target character to compare

        Returns:
            True if character at offset equals s
        """
        if not self.allow_neg and self.index + o < 0:
            return False
        return self.peek(o) == s

    def head_equals(self, s: str) -> bool:
        """Check if the first character in the text equals target character.

        Args:
            s: Target character to compare
        Returns:
            True if first character equals s
        """
        return self.head_value == s if self.not_empty else False

    def tail_equals(self, s: str) -> bool:
        """Check if the last character in the text equals target character.

        Args:
            s: Target character to compare
        Returns:
            True if last character equals s
        """
        return self.tail_value == s if self.not_empty else False

    def matches_ahead(self, s: str) -> bool:
        """Check if string ahead matches target.

        Args:
            s: Target string to compare
        Returns:
            True if string ahead matches s
        Raises:
            IndexError: If there are not enough characters ahead to match
        """
        if self.index + len(s) > self.size:
            return False
        return self._text[self.index : self.index + len(s)] == s

    @property
    def within_bounds(self) -> bool:
        """Check if the cursor is within the bounds of the text."""
        if self.allow_neg:
            return self.index < self.size
        return 0 <= self.index < self.size

    @property
    def is_empty(self) -> bool:
        """Check if the text is empty."""
        return self.size == 0

    @property
    def size(self) -> int:
        """Get the size of the text."""
        return len(self._text)
