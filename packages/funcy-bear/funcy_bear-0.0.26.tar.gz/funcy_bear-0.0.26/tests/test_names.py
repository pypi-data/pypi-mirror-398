from __future__ import annotations

import copy

import pytest

from funcy_bear.tools.names import Names


def test_names_basic_attribute_and_mapping_behaviour() -> None:
    ns = Names(foo=1, bar=2)

    assert ns.foo == 1
    assert ns["bar"] == 2
    assert ns.get("missing") is None

    ns.add("baz", 3)
    assert ns.baz == 3
    assert ns.size() == 3

    assert "foo" in ns
    del ns["foo"]
    assert "foo" not in ns


def test_names_boolean_and_iteration() -> None:
    ns = Names()
    assert not ns

    ns.add("alpha", 10)
    assert bool(ns)
    assert list(iter(ns)) == [("alpha", 10)]


def test_names_set_operations_and_hash() -> None:
    ns1 = Names(alpha=1, beta=2)
    ns2 = Names(beta=2, gamma=3)

    union = ns1 | ns2
    assert isinstance(union, Names)
    assert union.get("alpha") == 1
    assert union.get("gamma") == 3

    intersection = ns1 & ns2
    assert intersection == Names(beta=2)

    symmetric = ns1 ^ ns2
    assert symmetric == Names(alpha=1, gamma=3)

    ns1 |= {"delta": 4}
    assert ns1.delta == 4

    ns1 &= {"delta": 4, "beta": 2}
    assert ns1 == {"delta": 4, "beta": 2}

    ns1 ^= {"epsilon": 5}
    assert ns1 == {"delta": 4, "beta": 2, "epsilon": 5}

    # Hash consistency
    ns_copy = Names(**ns1._root)  # pyright: ignore[reportPrivateUsage]
    assert hash(ns1) == hash(ns_copy)


def test_names_copy_and_deepcopy() -> None:
    ns = Names(alpha=[1, 2])
    ns_copy = copy.copy(ns)
    ns_deepcopy = copy.deepcopy(ns)

    assert ns_copy == ns
    assert ns_deepcopy == ns

    # Mutate originals and ensure deep copy stays independent
    ns.alpha.append(3)
    assert ns_copy.alpha == [1, 2, 3]
    assert ns_deepcopy.alpha == [1, 2]


def test_names_get_with_strict_mode() -> None:
    ns = Names(foo=42)

    # Normal get with default
    assert ns.get("missing", "default") == "default"
    assert ns.get("foo") == 42

    with pytest.raises(KeyError):
        ns.get("missing", strict=True)


def test_names_attribute_vs_dict_access() -> None:
    ns = Names()

    # Set via attribute
    ns.foo = 123
    assert ns["foo"] == 123

    # Set via dict
    ns["bar"] = 456
    assert ns.bar == 456

    # Delete via attribute
    del ns.foo
    assert "foo" not in ns

    # Delete via dict
    del ns["bar"]
    assert "bar" not in ns


def test_names_with_none_values() -> None:
    ns = Names(foo=None, bar=42)

    assert ns.foo is None
    assert ns.get("foo") is None
    assert ns.has("foo")
    assert "foo" in ns


def test_names_empty_operations() -> None:
    empty = Names()
    ns = Names(foo=1)

    # Empty operations
    assert empty | ns == ns
    assert ns | empty == ns
    assert empty & ns == Names()
    assert empty ^ ns == ns

    # Empty boolean
    assert not empty
    assert bool(ns)
