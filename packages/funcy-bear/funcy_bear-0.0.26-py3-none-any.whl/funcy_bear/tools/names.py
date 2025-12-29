"""A simple namespace-like class for storing attributes."""

from __future__ import annotations

from collections.abc import Iterator  # noqa: TC003
from typing import TYPE_CHECKING, Any, Self, overload

from lazy_bear import lazy

if TYPE_CHECKING:
    import copy

    from frozen_cub.frozen import freeze
    from funcy_bear.constants.type_constants import LitFalse, LitTrue
else:
    copy = lazy("copy")  # type: ignore[assignment]
    freeze = lazy("frozen_cub.frozen", "freeze")  # type: ignore[assignment]


class Names[Value: Any = Any]:
    """A simple object for storing attributes.

    The key for the internal dictionary has to be a string
    since we want to access attributes via dot notation.

    Example:
        >>> ns = Names()
        >>> ns.foo = "bar"
        or
        >>> ns.add("foo", "bar")
        >>> print(ns.foo)
        bar
        >>> print(ns)
        Names(foo='bar')
    """

    def __init__(self, **kwargs) -> None:
        """Initialize the Names class with optional attributes."""
        self._root: dict[str, Value] = {}
        for key, value in kwargs.items():
            self.add(key, value)  # pyright: ignore[reportArgumentType]

    def add(self, k: str, v: Value) -> None:
        """Add or update an attribute in the Namespace."""
        self._root[k] = v

    def set(self, k: str, v: Value) -> None:
        """Set an attribute in the Namespace (alias for add)."""
        self.add(k, v)

    @overload
    def get(self, k: str, d: Any = None, strict: LitFalse = False) -> Value | None: ...

    @overload
    def get(self, k: str, d: Any = None, strict: LitTrue = True) -> Value: ...

    def get(self, k: str, d: Any = None, strict: bool = False) -> Value | None:
        """Get an attribute from the Namespace, returning default if not found.

        Args:
            k: Attribute name
            d: Default value if attribute not found (default: None)
            strict: If True, raise KeyError if attribute not found (default: False)
                This allows to avoid dealing with None values if desired.
        """
        if strict and k not in self._root:
            raise KeyError(f"'Namespace' object has no attribute '{k}'")
        return self._root.get(k, d)

    def has(self, k: str) -> bool:
        """Check if the Namespace has a given attribute."""
        return k in self._root

    def size(self) -> int:
        """Return the number of attributes in the Namespace."""
        return len(self._root)

    def keys(self) -> list[str]:
        """Return a list of attribute names in the Namespace."""
        return list(self._root.keys())

    def values(self) -> list[Value]:
        """Return a list of attribute values in the Namespace."""
        return list(self._root.values())

    def items(self) -> list[tuple[str, Value]]:
        """Return a list of attribute name-value pairs in the Namespace."""
        return list(self._root.items())

    def remove(self, k: str) -> None:
        """Remove an attribute from the Namespace."""
        if self.has(k):
            del self._root[k]

    def clear(self) -> None:
        """Clear all attributes from the Namespace."""
        self._root.clear()

    def __getattr__(self, k: str) -> Value:
        if k in self._root:
            value: Value = self._root[k]
            return value
        raise AttributeError(f"'Namespace' object has no attribute '{k}'")

    def __setattr__(self, k: str, v: Value) -> None:
        if k == "_root":
            super().__setattr__(k, v)
        else:
            self._root[k] = v

    def __getitem__(self, k: str) -> Value:
        return self._root[k]

    def __setitem__(self, k: str, v: Value) -> None:
        self._root[k] = v

    def __delitem__(self, k: str) -> None:
        if k in self._root:
            del self._root[k]

    def __contains__(self, k: str) -> bool:
        return k in self._root

    def __delattr__(self, k: str) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        if k in self._root:
            del self._root[k]

    def __iter__(self) -> Iterator[tuple[str, Value]]:
        yield from self._root.items()

    def __next__(self) -> tuple[str, Value]:
        return next(iter(self))

    def __len__(self) -> int:
        return len(self._root)

    def __bool__(self) -> bool:
        return bool(self._root)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:  # type: ignore[ARG001]
        pass

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Names):
            return self._root == other._root
        if isinstance(other, dict):
            return self._root == other
        return False

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __or__(self, other: Names[Value] | object) -> Names[Value]:
        if isinstance(other, Names):
            combined: dict[str, Any] = self._root.copy()
            combined.update(other._root)
            return Names(**combined)
        if isinstance(other, dict):
            combined = self._root.copy()
            combined.update(other)
            return Names(**combined)
        return NotImplemented

    def __and__(self, other: Names[Value] | object) -> Names[Value]:
        if isinstance(other, Names):
            common: dict[str, Value] = {k: v for k, v in self._root.items() if k in other._root and other.get(k) == v}
            return Names(**common)
        if isinstance(other, dict):
            common = {k: v for k, v in self._root.items() if k in other and other[k] == v}
            return Names(**common)
        return NotImplemented

    def __xor__(self, other: Names[Value] | object) -> Names[Value]:
        if isinstance(other, Names):
            diff: dict[str, Value] = {k: v for k, v in self._root.items() if k not in other._root or other.get(k) != v}
            diff.update({k: v for k, v in other._root.items() if k not in self._root or self._root[k] != v})
            return Names(**diff)
        if isinstance(other, dict):
            diff = {k: v for k, v in self._root.items() if k not in other or other[k] != v}
            diff.update({k: v for k, v in other.items() if k not in self._root or self._root[k] != v})
            return Names(**diff)
        return NotImplemented

    def __ior__(self, other: Names[Value] | object) -> Self:
        if isinstance(other, Names):
            self._root.update(other._root)
            return self
        if isinstance(other, dict):
            self._root.update(other)
            return self
        return NotImplemented

    def __iand__(self, other: Names[Value] | object) -> Self:
        if isinstance(other, Names):
            self._root = {k: v for k, v in self._root.items() if k in other._root and other.get(k) == v}
            return self
        if isinstance(other, dict):
            self._root = {k: v for k, v in self._root.items() if k in other and other[k] == v}
            return self
        return NotImplemented

    def __ixor__(self, other: Names[Value] | object) -> Self:
        if isinstance(other, Names):
            new_root: dict[str, Value] = {
                k: v for k, v in self._root.items() if k not in other._root or other.get(k) != v
            }
            new_root.update({k: v for k, v in other._root.items() if k not in self._root or self._root[k] != v})
            self._root = new_root
            return self
        if isinstance(other, dict):
            new_root = {k: v for k, v in self._root.items() if k not in other or other[k] != v}
            new_root.update({k: v for k, v in other.items() if k not in self._root or self._root[k] != v})
            self._root = new_root
            return self
        return NotImplemented

    def __copy__(self) -> Names[Value]:
        root_copy: dict[str, Value] = self._root.copy()
        return Names(**root_copy)

    def __deepcopy__(self, memo: dict[Any, Any] | None = None) -> Names[Value]:
        root_deepcopy: dict[str, Value] = copy.deepcopy(self._root, memo)
        return Names(**root_deepcopy)

    def __hash__(self) -> int:
        return hash(freeze(self._root))

    def __repr__(self) -> str:
        attrs: str = ", ".join(f"{k}={v!r}" for k, v in self._root.items())
        return f"{self.__class__.__name__}({attrs})"

    def __str__(self) -> str:
        return self.__repr__()
