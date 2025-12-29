"""Generally useful tools like data structures, caching, and freezing."""

from typing import TYPE_CHECKING

from lazy_bear import lazy

if TYPE_CHECKING:
    from frozen_cub.dispatcher import Dispatcher
    from frozen_cub.frozen import FrozenDict, freeze
    from frozen_cub.lru_cache import LRUCache
    from funcy_bear.tools.gradient import ColorGradient, DefaultColorConfig
    from funcy_bear.tools.names import Names
    from funcy_bear.tools.priority_queue import PriorityQueue
    from funcy_bear.tools.string_cursor import StringCursor
else:
    Dispatcher = lazy("frozen_cub.dispatcher", "Dispatcher")
    FrozenDict, freeze = lazy("frozen_cub.frozen", "FrozenDict", "freeze")
    LRUCache = lazy("frozen_cub.lru_cache", "LRUCache")
    ColorGradient, DefaultColorConfig = lazy("funcy_bear.tools.gradient", "ColorGradient", "DefaultColorConfig")
    Names = lazy("funcy_bear.tools.names", "Names")
    StringCursor = lazy("funcy_bear.tools.string_cursor", "StringCursor")
    PriorityQueue = lazy("funcy_bear.tools.priority_queue", "PriorityQueue")

__all__ = [
    "ColorGradient",
    "DefaultColorConfig",
    "Dispatcher",
    "FrozenDict",
    "LRUCache",
    "Names",
    "PriorityQueue",
    "StringCursor",
    "freeze",
]
