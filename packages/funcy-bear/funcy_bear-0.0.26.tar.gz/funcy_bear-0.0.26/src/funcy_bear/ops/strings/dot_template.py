"""A templating system with support for nested dictionary keys with the internal Template class."""

from string import Template
from typing import TYPE_CHECKING, Any

from funcy_bear.sentinels import SentinelDict
from lazy_bear import lazy

if TYPE_CHECKING:
    from collections import ChainMap
    from collections.abc import Mapping
    from queue import SimpleQueue
    import re
else:
    re = lazy("re")
    ChainMap = lazy("collections", "ChainMap")
    SimpleQueue = lazy("queue", "SimpleQueue")
    Mapping = lazy("collections.abc", "Mapping")

_sentinel_dict: SentinelDict = SentinelDict()


class DotTemplate(Template):
    """An alternative Template class that checks nested dictionaries for keys in format strings."""

    delimiter = "$"

    def safe_substitute(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        mapping: dict = _sentinel_dict,
        unique_keys: set[str] | None = None,
        queue: SimpleQueue | None = None,
        /,
        **kws,
    ) -> str:
        """Perform a safe substitution, checking nested dictionaries for keys.

        Args:
            mapping: The mapping to use for substitution, defaults to a sentinel to use kws.
            unique_keys: An optional set of unique keys to improve performance.
            queue: An optional SimpleQueue to use for flattening nested dictionaries.
            **kwds: Additional keyword arguments to include in the mapping.

        Returns:
            The resulting string after substitution.
        """
        local_cache: dict | ChainMap = mapping if mapping is not _sentinel_dict else ChainMap(kws, mapping)
        has_nested: bool = has_nested_dicts(local_cache)

        def flatten() -> dict[str, Any]:
            local_queue: SimpleQueue = queue or SimpleQueue()
            flat_cache: dict[str, Any] = {}
            local_queue.put(local_cache)
            while local_queue:
                current: dict[str, Any] = local_queue.get()
                for key, value in current.items():
                    if isinstance(value, dict):
                        local_queue.put(value)
                    if unique_keys is None or key in unique_keys:
                        flat_cache[key] = value
            return flat_cache

        if has_nested:
            local_cache = flatten()

        def convert(mo: re.Match[str]) -> str:
            named: str | None = mo.group("named")
            if named is not None:
                if named in local_cache:
                    return str(local_cache[named])
                return mo.group(0)
            braced: str | None = mo.group("braced")
            if braced is not None:
                if braced in local_cache:
                    return str(local_cache[braced])
                return mo.group(0)
            raise ValueError("Unrecognized named group in pattern", self.pattern)

        return self.pattern.sub(convert, self.template)


def cache_unique(t: Template) -> set[str]:
    """Extract the keys used in the format string.

    Args:
        fmt: The format string.

    Returns:
        A set of keys used in the format string.
    """
    keys: set[str] = set()
    for match in t.pattern.finditer(t.template):
        named: str | None = match.group("named") or match.group("braced")
        if named is not None:
            keys.add(named)
    return keys


def has_nested_dicts(mapping: Mapping) -> bool:
    """Quick check if dict contains any nested dicts."""
    return any(isinstance(v, dict) for v in mapping.values())
