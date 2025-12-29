# funcy_bear.query

Path-based querying utilities that work across both dict-like mappings and
attribute-driven objects. Inspired by TinyDB-style query syntax, these helpers
compose nested lookups with logical operations and hash-based caching.

## Core Concepts
- `QueryBase`: Base class that records a path (e.g., `.user.name` or `["user"]`)
  and builds test functions.
- `QueryObject` / `QueryMapping`: Concrete implementations that resolve path
  segments via `getattr` or `dict.get`.
- `QueryInstance`: Wraps a callable predicate and a `HashValue` used for cache
  identity. Supports `&`, `|`, and `~` for logical composition.
- `QueryUnified`: Hybrid query that inspects both objects and mappings by
  picking getters at runtime.
- `HashValue`: Immutable token capturing the structure/arguments of a query
  (or a `NotCacheable` sentinel when hashing isn’t safe).

Import shortcuts:
```python
from funcy_bear.query import where_obj, where_map, QueryObject, QueryMapping
```

---

## Building Queries

```python
from funcy_bear.query import where_obj, where_map

User = type("User", (), {})
user = User()
user.profile = {"nickname": "bear", "followers": 42}

q_obj = where_obj("profile").nickname == "bear"
q_map = where_map("profile").followers > 10

assert q_obj(user) is True
assert q_map(user.__dict__) is True
```

Queries are lazy: attribute/item access appends to the path, and comparisons
create `QueryInstance` objects. Use `exists()`, `matches(regex)`, `search`,
`all(condition)` for richer predicates.

---

## Composing Logic

```python
profile = {"nickname": "bear", "followers": 42}

is_bear = where_map("nickname") == "bear"
is_popular = where_map("followers") >= 40

bear_and_popular = is_bear & is_popular
bear_or_popular = is_bear | is_popular

assert bear_and_popular(profile)
assert bear_or_popular(profile)
assert (~is_popular)(profile) is False
```

Logical operators generate new `QueryInstance` objects, combining hash tokens so
queries can be cached or deduplicated. If any branch is non-cacheable (e.g.,
due to dynamic callables), the combined hash is marked `NotCacheable`.

---

## Using Callables & Custom Steps

```python
from funcy_bear.query import where_map

def is_even(value: int) -> bool:
    return value % 2 == 0

q = where_map("numbers")(lambda seq: seq[0]).all(is_even)
assert q({"numbers": [[2, 4], [1, 3]]}) is True
```

- Passing a callable in the path (`Q("numbers")(lambda seq: seq[0])`) injects
  custom traversal logic.
- `.all(condition)` supports either a list of expected values or a nested
  `QueryInstance`.

---

## Unified Queries

`QueryUnified` bridges the gap between mappings and objects by checking the
runtime value type at each path segment. Handy when mixed data structures are
present:

```python
from funcy_bear.query import QueryUnified

q = QueryUnified().profile.nickname == "Bear"

assert q({"profile": {"nickname": "Bear"}})

class Profile: nickname = "Bear"
class User: profile = Profile()
assert q(User())
```

---

## Tips
- For mapping-heavy data, prefer `where_map` so the intent is explicit.
- Combine queries with enums or constants to avoid stringly-typed paths.
- Leverage hashing to memoize expensive query evaluations; check `is_cacheable`
  before storing in caches.
- `MissingValue` sentinel ensures comparisons behave predictably when a path
  doesn’t exist (e.g., `.exists()`).

Query boldly, Bear! 🐻🔍✨
