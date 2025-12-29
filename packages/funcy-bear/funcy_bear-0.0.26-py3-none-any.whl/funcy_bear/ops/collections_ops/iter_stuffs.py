"""Itertools-like functions."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable, Collection, Generator, Iterable, Iterator, Sequence  # noqa: TC003
from functools import lru_cache
from itertools import filterfalse, zip_longest
from typing import TYPE_CHECKING, Any, NoReturn, overload

from funcy_bear.constants.type_constants import LitFalse, LitTrue  # noqa: TC001
from funcy_bear.ops.collections_ops.key_counts import KeyCounts
from funcy_bear.sentinels import NO_DEFAULT
from lazy_bear import lazy

if TYPE_CHECKING:
    from frozen_cub.frozen import freeze
else:
    freeze = lazy("frozen_cub.frozen", "freeze")

REQUIRED_NUM: int = 2


def length(seq: Collection | Sequence | Iterable) -> int:
    """Get the length of a sequence, or count items in an iterable.

    If the input has a __len__ method, it will be used to be lazy-evaluate the length.
    Otherwise, the function will iterate through the input to count the items.

    Args:
        seq (Sequence): The sequence or iterable to get the length of.

    Returns:
        int: The length of the sequence or count of items in the iterable.

    Example:
        >>> length([1, 2, 3, 4])
        4
        >>> length((x for x in range(5)))
        5
    """

    @lru_cache(maxsize=128)
    def cached_length(seq: Any) -> int:
        """Get the length of a sequence, or count items in an iterable, with caching."""
        return sum(1 for i in seq)

    if hasattr(seq, "__len__"):
        return len(seq)  # type: ignore[arg-type]
    try:
        return cached_length(seq)
    except TypeError:
        return cached_length(freeze(seq))


def freq(seq: Sequence) -> dict[str, int]:
    """Count the frequency of each item in a sequence.

    Args:
        seq (Sequence[str]): The sequence to count frequencies in.

    Returns:
        dict[str, int]: A dictionary mapping each item to its frequency.

    Example:
        >>> freq(["apple", "banana", "apple", "orange", "banana", "apple"])
        {'apple': 3, 'banana': 2, 'orange': 1}
    """
    d: defaultdict[str, int] = defaultdict(int)
    for item in seq:
        d[item] += 1
    return dict(d)


def is_iter(x: Sequence) -> bool:
    """Is x iterable?

    >>> is_iter([1, 2, 3])
    True
    >>> is_iter("abc")
    True
    >>> is_iter(5)
    False
    """
    try:
        iter(x)
        return True
    except TypeError:
        return False


def tail(seq: Sequence, n: int = 1) -> Generator[Any, Any]:
    """Generate the last n items from a sequence.

    Args:
        seq (Sequence): The sequence to get the tail from.
        n (int): The number of items to return from the end of the sequence. Defaults to 1.

    Yields:
        The last n items from the sequence.

    Example:
        >>> list(tail([1, 2, 3, 4, 5], 2))
        [4, 5]
        >>> list(tail("abcdef", 3))
        ['d', 'e', 'f']
    """
    if n < 1:
        raise ValueError("n must be at least 1")
    length_seq: int = length(seq)
    if length_seq < n:
        yield from seq
        return
    start: int = length_seq - n
    for i in range(start, length_seq):
        yield seq[i]


def head(seq: Sequence, n: int = 1) -> Generator[Any, Any]:
    """Generate the first n items from a sequence.

    Args:
        seq (Sequence): The sequence to get the head from.
        n (int): The number of items to return from the start of the sequence. Defaults to 1.

    Yields:
        The first n items from the sequence.

    Example:
        >>> list(head([1, 2, 3, 4, 5], 2))
        [1, 2]
        >>> list(head("abcdef", 3))
        ['a', 'b', 'c']
    """
    if n < 1:
        raise ValueError("n must be at least 1")
    length_seq: int = length(seq)
    if length_seq < n:
        yield from seq
        return
    for i in range(n):
        yield seq[i]


def drop(n: int, seq: Sequence) -> Generator[Any, Any]:
    """Generate items from a sequence, skipping the first n items.

    Args:
        n (int): The number of items to skip from the start of the sequence.
        seq (Sequence): The sequence to drop items from.

    Yields:
        Items from the sequence after skipping the first n items.

    Example:
        >>> list(drop(2, [1, 2, 3, 4, 5]))
        [3, 4, 5]
        >>> list(drop(3, "abcdef"))
        ['d', 'e', 'f']
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if length(seq) <= n:
        return
    for i in range(n, length(seq)):
        yield seq[i]


def keep[T](predicate: Callable, seq: Sequence[T]) -> filter[T]:
    """Return those items of sequence for which predicate(item) is True

    >>> def iseven(x):
    ...     return x % 2 == 0
    >>> list(keep(iseven, [1, 2, 3, 4]))
    [2, 4]
    """
    return filter(predicate, seq)


def first(seq: Sequence) -> Any:
    """Return the first item of a sequence, or None if the sequence is empty.

    >>> first([1, 2, 3])
    1
    >>> first([])
    None
    """
    return seq[0] if length(seq) > 0 else None


def last(seq: Sequence) -> Any:
    """Return the last item of a sequence, or None if the sequence is empty.

    >>> last([1, 2, 3])
    3
    >>> last([])
    None
    """
    return seq[-1] if length(seq) > 0 else None


def iterate(func: Callable, x: Sequence) -> Generator[Any, Any, NoReturn]:
    """Generate an infinite sequence by repeatedly applying a function.

    Args:
        func (Callable): The function to apply.
        x: The initial value.

    Yields:
        The next value in the sequence.

    Example:
        >>> def add_one(n):
        ...     return n + 1
        >>> it = iterate(add_one, 0)
        >>> [next(it) for _ in range(5)]
        [0, 1, 2, 3, 4]
    """
    while True:
        yield x
        x = func(x)


def apply(func: Callable, seq: Sequence, **kwargs) -> Generator[Any, Any]:
    """Apply a function to each item in a sequence, yielding the results.

    Args:
        func (Callable): The function to apply.
        seq (Sequence): The sequence of items to process.
        **kwargs: Additional keyword arguments to pass to the function.

    Yields:
        The result of applying the function to each item.

    Example:
        >>> def add(x, y=0):
        ...     return x + y
        >>> list(apply(add, [1, 2, 3], y=10))
        [11, 12, 13]
    """
    for item in seq:
        yield func(item, **kwargs)


def remove(predicate: Callable, seq: Sequence):
    """Return those items of sequence for which predicate(item) is False

    >>> def iseven(x):
    ...     return x % 2 == 0
    >>> list(remove(iseven, [1, 2, 3, 4]))
    [1, 3]
    """
    return filterfalse(predicate, seq)


def diff(*seqs, **kwargs) -> Generator[tuple[Any, ...], Any]:
    """Return those items that differ between sequences

    Args:
        *seqs: Two or more sequences to compare.
        **kwargs: Optional keyword arguments:
            - default: Value to use for missing items in shorter sequences (default: no_default).
            - key: Optional function to apply to each item before comparison (default: None).

    Yields:
        Tuples of items that differ between the sequences.

    Example:
        >>> list(diff([1, 2, 3], [1, 2, 4], [1, 3, 3]))
        [(2, 2, 3), (3, 4, 3)]
        >>> list(diff([1, 2], [1, 2, 3], default=0))
        [(0, 3)]
    """
    default: Any = kwargs.get("default", NO_DEFAULT)
    key: Any = kwargs.get("key")
    n: int = length(seqs)
    if n == 1 and isinstance(seqs[0], list):
        seqs = seqs[0]
        n = length(freeze(seqs))
    if n < REQUIRED_NUM:
        raise TypeError("Too few sequences given (min 2 required)")
    iters = zip(*seqs, strict=False) if default == NO_DEFAULT else zip_longest(*seqs, fillvalue=default)
    if key is None:
        for items in iters:
            if items.count(items[0]) != n:
                yield items
    else:
        for items in iters:
            vals: tuple[Any, ...] = tuple(map(key, items))
            if vals.count(vals[0]) != n:
                yield items


def dupes(*seqs) -> Generator[Any, Any]:
    """Yield items that appear more than once in the given sequences.

    Args:
        *seqs: One or more sequences to check for duplicates.

    Yields:
        Items that appear more than once in the sequences.

    Example:
        >>> list(dupes([1, 2, 3, 2, 4, 1]))
        [1, 2]
        >>> list(dupes("abca"))
        ['a']
    """
    seen: set[Any] = set()
    yielded: set[Any] = set()
    for item in seqs:
        if item in seen and item not in yielded:
            yielded.add(item)
            yield item
        else:
            seen.add(item)


def pairwise(seq: Sequence) -> Generator[tuple[Any, Any], Any]:
    """Generate pairs of consecutive items from a sequence.

    Args:
        seq (Sequence): The sequence to generate pairs from.

    Yields:
        Tuples of consecutive items.

    Example:
        >>> list(pairwise([1, 2, 3, 4]))
        [(1, 2), (2, 3), (3, 4)]
        >>> list(pairwise("hello"))
        [('h', 'e'), ('e', 'l'), ('l', 'l'), ('l', 'o')]
    """
    if length(seq) < REQUIRED_NUM:
        return
    a: Any = seq[0]
    for b in seq[1:]:
        yield (a, b)
        a = b


def window(seq: Sequence, size: int) -> Generator[tuple[Any, ...], Any]:
    """Generate overlapping windows of a specified size from a sequence.

    Args:
        seq (Sequence): The sequence to generate windows from.
        size (int): The size of each window.

    Yields:
        Tuples representing each window.

    Example:
        >>> list(window([1, 2, 3, 4, 5], 3))
        [(1, 2, 3), (2, 3, 4), (3, 4, 5)]
        >>> list(window("abcdef", 4))
        [('a', 'b', 'c', 'd'), ('b', 'c', 'd', 'e'), ('c', 'd', 'e', 'f')]
    """
    if size < 1:
        raise ValueError("Window size must be at least 1")
    if length(seq) < size:
        return
    it: Iterator[Any] = iter(seq)
    window_deque: deque[Any] = deque(maxlen=size)
    for r in range(size):
        window_deque.append(next(it))
    yield tuple(window_deque)
    for x in it:
        window_deque.append(x)
        yield tuple(window_deque)


def uniqueify[T](seq: Sequence[T]) -> list[T]:
    """Return a list of unique items from the sequence, preserving order.

    Args:
        seq (Sequence[T]): The sequence to process.

    Returns:
        list[T]: A list of unique items in the order they first appeared.
    """
    return list(dict.fromkeys(seq).keys())


def merge_lists[T](*lists: list[T] | tuple[T, ...], unique: bool = False) -> list[T]:
    """Combine multiple lists or tuples into one, with an option for uniqueness.

    Args:
        *lists (list[T] | tuple[T, ...]): Lists or tuples to merge.
        unique (bool): If True, only unique items will be kept. Defaults to False.

    Returns:
        list[T] | tuple[T, ...]: A new list or tuple containing all items from the input lists.

    Example:
        >>> merge_lists([1, 2], [3, 4])
        [1, 2, 3, 4]
    """
    result: list[T] = []
    for lst in lists:
        result.extend(lst)
    if unique:
        result = uniqueify(result)
    return result


@lru_cache(maxsize=128)
def merge_tuples[T](*tuples: tuple[T, ...], unique: bool = False) -> tuple[T, ...]:
    """Combine multiple tuples into one, with an option for uniqueness.

    Args:
        *tuples (tuple[T, ...]): Tuples to merge.
        unique (bool): If True, only unique items will be kept. Defaults to False.

    Returns:
        tuple[T, ...]: A new tuple containing all items from the input tuples.

    Example:
        >>> merge_tuples((1, 2), (3, 4))
        (1, 2, 3, 4)
    """
    return tuple(merge_lists(*tuples, unique=unique))


@overload
def merge_sets[T](*sets: set[T]) -> set[T]: ...


@overload
def merge_sets[T](*sets: frozenset[T]) -> frozenset[T]: ...


def merge_sets[T](*sets: set[T] | frozenset[T]) -> set[T] | frozenset[T]:
    """Combine multiple sets into one, converting frozensets to sets as needed.

    Args:
        *sets (set[T]): Sets to merge.

    Returns:
        set[T]: A new set containing all items from the input sets.

    Example:
        >>> merge_sets({1, 2}, {3, 4})
        {1, 2, 3, 4}
    """
    result: set[T] = set()
    for s in sets:
        result.update(s) if not isinstance(s, frozenset) else result.update(set(s))
    return result if isinstance(sets[0], set) else frozenset(result)


@overload
def merge[T: Any](*args: list[T], unique: bool) -> list[T]: ...


@overload
def merge[T: Any](*args: tuple[T, ...], unique: bool) -> tuple[T, ...]: ...


@overload
def merge[T: Any](*args: set[T], unique: bool) -> set[T]: ...


@overload
def merge[T: Any](*args: frozenset[T], unique: bool) -> frozenset[T]: ...


@overload
def merge[T: Any](*args: dict[Any, T], unique: bool) -> dict[Any, T]: ...


def merge[T: Any](*args, unique: bool = False) -> list[T] | tuple[T, ...] | set[T] | frozenset[T] | dict[Any, T]:
    """Merge multiple collections of the same type into one.

    Args:
        *args (Collection[T]): Collections to merge.
        unique (bool): If True, only unique items will be kept (applicable to lists and tuples). Defaults to False.

    Returns:
        Collection[T]: A new collection containing all items from the input collections.

    Raises:
        TypeError: If input collections are of different types or unsupported types.

    Example:
        >>> merge([1, 2], [3, 4])
        [1, 2, 3, 4]
        >>> merge((1, 2), (3, 4))
        (1, 2, 3, 4)
        >>> merge({1, 2}, {3, 4})
        {1, 2, 3, 4}
    """
    from funcy_bear.ops.collections_ops.dict_stuffs import merge as merge_dict
    from funcy_bear.type_stuffs.conversions import PossibleStrs, type_to_str

    if not args:
        raise ValueError("At least one collection is required to merge.")

    all_types: set[PossibleStrs] = {type_to_str(type(arg)) for arg in args}

    if len(all_types) != 1:
        raise TypeError(f"All collections must be of the same type, got: {all_types}")

    _type: PossibleStrs = next(iter(all_types))

    match _type:
        case "list" | "tuple":
            return merge_lists(*args, unique=unique) if _type == "list" else merge_tuples(*args, unique=unique)
        case "set" | "frozenset":
            return merge_sets(*args)
        case "dict":
            return merge_dict(*args)
        case _:
            raise TypeError(f"Unsupported collection type: {_type}")
    return []


def key_counts(*c) -> KeyCounts:
    """Count occurrences of each key across multiple collections, delineating the different collections.

    This includes dictionaries, sets, lists, and tuples.

    Args:
        *c (Collection): collections to count keys from.

    Returns:
        KeyCounts: A KeyCounts object mapping each key to its occurrence count.

    Example:
        >>> key_counts([1, 2, 3], {2, 3, 4}, (3, 4, 5))
        KeyCounts with counts for keys 1, 2, 3, 4, 5 including a report on duplicates.
    """
    counts = KeyCounts()
    for collection in c:
        for index, key in enumerate(collection):
            counts.plus(key, index, collection)
    return counts


def extract_gen(gen: Generator) -> list:
    """Extract all items from a generator into a list.

    Args:
        gen (Generator): The generator to extract items from.

    Returns:
        list: A list containing all items from the generator.

    return list(gen)
    """
    return list(gen)


@overload
def pop_iter[T](seq: Sequence[T], n: int = 0, remainder: LitFalse = False) -> T: ...
@overload
def pop_iter[T](seq: Sequence[T], n: int, remainder: LitTrue) -> tuple[T, Iterable[T]]: ...
def pop_iter[T](seq: Sequence[T], n: int = 0, remainder: bool = True) -> tuple[T, Iterable[T]] | T:
    """Pop an item at the nth index from an iterable and return the remainder.

    Args:
        seq: The iterable to pop from.
        n: The index at which to pop the item.
        remainder: Whether to return the remainder of the iterable.

    Returns:
        tuple[Any, Iterable] | Any: The popped item and the remainder of the iterable, or just the popped item if remainder is False.
    """
    if not seq:
        raise IndexError("Cannot pop from an empty sequence")

    if n < 0:
        n = len(seq) + n

    if n < 0 or n >= len(seq):
        raise IndexError("Index out of bounds")

    popped = seq[n]
    if remainder:
        return popped, (item for i, item in enumerate(seq) if i != n)
    return popped


# ruff: noqa: B007 PLC0415
