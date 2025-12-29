from __future__ import annotations

from typing import Any

import pytest

from frozen_cub.frozen import FrozenDict, freeze
from frozen_cub.lru_cache import LRUCache


def test_lru_cache_respects_capacity_and_recency() -> None:
    cache: LRUCache[str, int] = LRUCache(capacity=2)
    cache.set("a", 1)
    cache.set("b", 2)

    # Access 'a' so it becomes most recently used
    assert cache.get("a") == 1

    cache.set("c", 3)  # Should evict 'b'

    assert "a" in cache
    assert "c" in cache
    assert "b" not in cache
    assert len(cache) == 2


def test_lru_cache_accepts_frozen_keys_from_freeze_helpers() -> None:
    cache: LRUCache[FrozenDict, str] = LRUCache(capacity=2)

    original: dict[str, Any] = {"alpha": [1, 2], "beta": {"nested": True}}
    key: FrozenDict = freeze(original)
    cache.set(key, "payload")

    # same structure, new object; freezing should normalize it to equivalent key
    equivalent_key: FrozenDict = freeze({"alpha": [1, 2], "beta": {"nested": True}})
    assert cache.get(equivalent_key) == "payload"

    cache.set(freeze({"alpha": [3]}), "other")
    assert len(cache) == 2


def test_lru_cache_get_with_default_and_missing_key() -> None:
    cache: LRUCache[str, int] = LRUCache(0)

    assert cache.get("missing") is None
    assert cache.get("missing", default=5) == 5

    cache.set("present", 42)
    assert cache["present"] == 42

    with pytest.raises(KeyError):
        _ = cache["absent"]


def test_lru_cache_rejects_unhashable_keys() -> None:
    cache: LRUCache[object, int] = LRUCache(0)

    with pytest.raises(TypeError):
        cache.set(["not", "hashable"], 1)  # type: ignore[list-item]


def test_lru_cache_delete_and_clear() -> None:
    cache: LRUCache[str, int] = LRUCache(0)
    cache["x"] = 10
    cache["y"] = 20

    del cache["x"]
    assert "x" not in cache
    assert len(cache) == 1

    cache.clear()
    assert len(cache) == 0
