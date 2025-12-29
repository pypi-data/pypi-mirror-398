"""An LRU (least-recently used) cache implementation.

A Cython based LRUCache with a doubly linked list and a hash map for O(1) access.
"""

from frozen_cub.lru_cache import LRUCache

__all__ = ["LRUCache"]
