"""LRU (Least Recently Used) cache tools and decorators.

This is basically just the functools.lru_cache but with modern type hints
and some minor improvements.
"""

from collections.abc import Callable  # noqa: TC003
from functools import partial, update_wrapper
from threading import RLock
from typing import Any, Final, NamedTuple, ParamSpec, TypeVar


class _CacheInfo(NamedTuple):
    """Cache information tuple."""

    hits: int
    misses: int
    maxsize: int | None
    currsize: int


KwdMark: Final = (object(),)
FastTypes: Final = {int, str}

TupleFactory: Callable[..., tuple] = partial(tuple)
TypeFactory: Callable[..., type] = partial(type)
Length: Callable[[Any], int] = partial(len)


def _make_key(
    args: tuple[Any, ...],
    kwds: dict[str, Any],
    typed: bool,
    kwd_mark: tuple[object] = KwdMark,
    fasttypes: set[type] = FastTypes,
    tup: Callable[..., tuple] = TupleFactory,
    ty: Callable[..., type] = TypeFactory,
    length: Callable[[Any], int] = Length,
) -> Any:
    """Make a cache key from optionally typed positional and keyword arguments

    The key is constructed in a way that is flat as possible rather than
    as a nested structure that would take more memory.

    If there is only a single argument and its data type is known to cache
    its hash value, then that argument is returned without a wrapper.  This
    saves space and improves lookup speed.

    Args:
        args (Any): Positional arguments.
        kwds (dict[str, Any]): Keyword arguments.
        typed (bool): Whether to include argument types in the key.
        kwd_mark (tuple[object], optional): A marker to separate positional and keyword arguments. Defaults to KwdMark.
        fasttypes (set[type], optional): A set of types that are fast to hash. Defaults to FastTypes.
        tup (_type_, optional): The tuple constructor. Defaults to tuple.
        ty (_type_, optional): The type constructor. Defaults to type.
        length (Callable[[Any], int], optional): The length function. Defaults to len.
    """
    # All of code below relies on kwds preserving the order input by the user.
    # Formerly, we sorted() the kwds before looping.  The new way is *much*
    # faster; however, it means that f(x=1, y=2) will now be treated as a
    # distinct call from f(y=2, x=1) which will be cached separately.
    key = args
    if kwds:
        key += kwd_mark
        for item in kwds.items():
            key += item
    if typed:
        key += tup(ty(v) for v in args)
        if kwds:
            key += tup(ty(v) for v in kwds.values())
    elif length(key) == 1 and ty(key[0]) in fasttypes:
        return key[0]
    return key


T = TypeVar("T")
P = ParamSpec("P")


def lru_cache(
    maxsize: int | Callable[..., Any] | Any = 128, typed: bool = False
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Least-recently-used cache decorator.

    If *maxsize* is set to None, the LRU features are disabled and the cache
    can grow without bound.

    If *typed* is True, arguments of different types will be cached separately.
    For example, f(decimal.Decimal("3.0")) and f(3.0) will be treated as
    distinct calls with distinct results. Some types such as str and int may
    be cached separately even when typed is false.

    Arguments to the cached function must be hashable.

    View the cache statistics named tuple (hits, misses, maxsize, currsize)
    with f.cache_info().  Clear the cache and statistics with f.cache_clear().
    Access the underlying function with f.__wrapped__.

    See:  https://en.wikipedia.org/wiki/Cache_replacement_policies#Least_recently_used_(LRU)

    """
    # Users should only access the lru_cache through its public API:
    #       cache_info, cache_clear, and f.__wrapped__
    # The internals of the lru_cache are encapsulated for thread safety and
    # to allow the implementation to change (including a possible C version).

    if isinstance(maxsize, int):
        # Negative maxsize is treated as 0
        maxsize = max(maxsize, 0)

    elif callable(maxsize) and isinstance(typed, bool):
        # The user_function was passed in directly via the maxsize argument
        user_function, maxsize = maxsize, 128
        wrapper = _lru_cache_wrapper(user_function, maxsize, typed, _CacheInfo)
        wrapper.cache_parameters = lambda: {"maxsize": maxsize, "typed": typed}  # pyright: ignore[reportFunctionMemberAccess]
        return update_wrapper(wrapper, user_function)  # pyright: ignore[reportReturnType]

    elif maxsize is not None:
        raise TypeError("Expected first argument to be an integer, a callable, or None")

    def decorating_function(user_function: Callable[P, T]) -> Callable[P, T]:
        """Return a wrapper function for caching."""
        wrapper: Callable[P, T] = _lru_cache_wrapper(user_function, maxsize, typed, _CacheInfo)
        wrapper.cache_parameters = lambda: {"maxsize": maxsize, "typed": typed}  # pyright: ignore[reportFunctionMemberAccess]
        return update_wrapper(wrapper, user_function)

    return decorating_function


def _lru_cache_wrapper(
    user_function: Callable[P, T],
    maxsize: int | None,
    typed: bool,
    c_info: Callable[..., _CacheInfo],
) -> Callable[P, T]:
    # Constants shared by all lru cache instances:
    sentinel = object()  # unique object used to signal cache misses
    make_key: Callable[..., Any] = _make_key  # build a key from the function arguments
    PREV = 0
    NEXT = 1
    KEY = 2
    RESULT = 3

    cache: dict = {}
    hits: int = 0
    misses: int = 0
    full = False
    cache_get: Callable[..., Any] = cache.get  # bound method to lookup a key or return None
    cache_len: Callable[[], int] = cache.__len__  # get cache size without calling len()
    lock = RLock()  # because linked list updates aren't thread safe
    root = []  # root of the circular doubly linked list
    root[:] = [root, root, None, None]  # initialize by pointing to self

    if maxsize == 0:

        def wrapper(*args, **kwds) -> T:
            """A wrapper function for no caching."""
            # No caching -- just a statistics update
            nonlocal misses

            misses += 1
            return user_function(*args, **kwds)

    elif maxsize is None:

        def wrapper(*args, **kwds) -> T:
            """A wrapper function for unbounded caching."""
            # Simple caching without ordering or size limit
            nonlocal hits, misses

            key: Any = make_key(args, kwds, typed)
            result: Any = cache_get(key, sentinel)
            if result is not sentinel:
                hits += 1
                return result
            misses += 1
            result = user_function(*args, **kwds)
            cache[key] = result
            return result

    else:

        def wrapper(*args, **kwds) -> T:
            """A wrapper function for bounded LRU caching."""
            # Size limited caching that tracks accesses by recency
            nonlocal root, hits, misses, full

            key: Any = make_key(args, kwds, typed)

            with lock:
                link: Any = cache_get(key)
                if link is not None:
                    # Move the link to the front of the circular queue
                    link_prev, link_next, _, result = link
                    link_prev[NEXT] = link_next
                    link_next[PREV] = link_prev
                    last = root[PREV]
                    last[NEXT] = root[PREV] = link
                    link[PREV] = last
                    link[NEXT] = root
                    hits += 1
                    return result
                misses += 1

            result: T = user_function(*args, **kwds)

            with lock:
                if key in cache:
                    # Getting here means that this same key was added to the
                    # cache while the lock was released.  Since the link
                    # update is already done, we need only return the
                    # computed result and update the count of misses.
                    ...

                elif full:
                    # Use the old root to store the new key and result.
                    oldroot = root
                    oldroot[KEY] = key
                    oldroot[RESULT] = result

                    # Empty the oldest link and make it the new root.
                    # Keep a reference to the old key and old result to
                    # prevent their ref counts from going to zero during the
                    # update. That will prevent potentially arbitrary object
                    # clean-up code (i.e. __del__) from running while we're
                    # still adjusting the links.
                    root = oldroot[NEXT]
                    oldkey = root[KEY]
                    _ = root[RESULT]
                    root[KEY] = root[RESULT] = None

                    # Now update the cache dictionary.
                    del cache[oldkey]

                    # Save the potentially reentrant cache[key] assignment
                    # for last, after the root and links have been put in
                    # a consistent state.
                    cache[key] = oldroot

                else:
                    # Put result in a new link at the front of the queue.
                    last = root[PREV]
                    link = [last, root, key, result]
                    last[NEXT] = root[PREV] = cache[key] = link

                    # Use the cache_len bound method instead of the len() function
                    # which could potentially be wrapped in an lru_cache itself.
                    full: bool = cache_len() >= maxsize

            return result

    def cache_info() -> Any:
        """Report cache statistics"""
        with lock:
            return c_info(hits, misses, maxsize, cache_len())

    def cache_clear() -> None:
        """Clear the cache and cache statistics"""
        nonlocal hits, misses, full

        with lock:
            cache.clear()
            root[:] = [root, root, None, None]
            hits = misses = 0
            full = False

    wrapper.cache_info = cache_info  # pyright: ignore[reportFunctionMemberAccess]
    wrapper.cache_clear = cache_clear  # pyright: ignore[reportFunctionMemberAccess]
    return wrapper


def cache(user_function: Callable[P, T], /) -> Callable[P, T]:
    """Simple lightweight unbounded cache.  Sometimes called "memoize"."""
    return lru_cache(maxsize=None)(user_function)


# ruff: noqa: UP047 N806

__all__ = ["cache", "lru_cache"]
