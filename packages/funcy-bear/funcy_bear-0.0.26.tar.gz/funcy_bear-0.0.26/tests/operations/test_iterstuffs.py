from __future__ import annotations

from typing import Any

import pytest

from funcy_bear.ops.collections_ops.iter_stuffs import diff, freq, length, pairwise, window


def test_length_handles_sequences_and_iterators() -> None:
    assert length([1, 2, 3]) == 3
    assert length(x for x in range(4)) == 4


def test_freq_counts_occurrences() -> None:
    counts: dict[str, int] = freq(["apple", "banana", "apple", "orange", "banana", "apple"])
    assert counts == {"apple": 3, "banana": 2, "orange": 1}


def test_diff_identifies_mismatched_items() -> None:
    differences: list[tuple[Any, ...]] = list(diff([1, 2, 3], [1, 2, 4], [1, 3, 3]))
    assert differences == [(2, 2, 3), (3, 4, 3)]


def test_diff_with_default_fillvalue() -> None:
    differences = list(diff([1, 2], [1, 2, 3], default=0))
    assert differences == [(0, 3)]


def test_diff_requires_minimum_sequences() -> None:
    with pytest.raises(TypeError):
        list(diff([1]))


def test_pairwise_generates_adjacent_pairs() -> None:
    assert list(pairwise([1, 2, 3, 4])) == [(1, 2), (2, 3), (3, 4)]
    assert list(pairwise("hi")) == [("h", "i")]
    assert list(pairwise([1])) == []


def test_window_generates_overlapping_windows() -> None:
    assert list(window([1, 2, 3, 4, 5], 3)) == [(1, 2, 3), (2, 3, 4), (3, 4, 5)]


def test_window_size_validation() -> None:
    with pytest.raises(ValueError, match="Window size must be at least 1"):
        list(window([1, 2, 3], 0))


def test_window_smaller_sequence_returns_no_windows() -> None:
    assert list(window([1, 2], 3)) == []
