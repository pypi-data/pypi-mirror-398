from collections.abc import Callable  # noqa: TC003
from copy import deepcopy
from types import SimpleNamespace
from typing import Any

import pytest

import funcy_bear.api as ops


def make_docs(**values: Any) -> tuple[dict[str, Any], SimpleNamespace]:
    """Create a mapping and an object with the same initial values."""
    mapping: dict[str, Any] = {key: deepcopy(val) for key, val in values.items()}
    obj = SimpleNamespace(**{key: deepcopy(val) for key, val in values.items()})
    return mapping, obj


def apply_to_docs(transform: Callable[..., Any], **initial: Any) -> tuple[dict[str, Any], SimpleNamespace]:
    """Create docs, apply the transform to both, and return the results."""
    mapping, obj = make_docs(**initial)
    transform(mapping)
    transform(obj)
    return mapping, obj


@pytest.mark.parametrize(
    ("transform", "field", "initial", "expected"),
    [
        (ops.add("value", 5), "value", 10, 15),
        (ops.subtract("value", 3), "value", 10, 7),
        (ops.increment("value"), "value", 0, 1),
        (ops.decrement("value"), "value", 3, 2),
        (ops.multiply("value", 4), "value", 2, 8),
        (ops.div("value", 4, floor=False), "value", 10, 2.5),
        (ops.pow("value", 3), "value", 2, 8),
        (ops.mod("value", 3), "value", 10, 1),
        (ops.abs("value"), "value", -9, 9),
        (ops.clamp("value", 0, 5), "value", 10, 5),
        (ops.toggle("flag"), "flag", True, False),
    ],
)
def test_numeric_and_boolean_operations_apply_to_mapping_and_objects(
    transform: Callable[[Any], None],
    field: str,
    initial: Any,
    expected: Any,
) -> None:
    mapping, obj = apply_to_docs(transform, **{field: initial})
    print(mapping, obj, expected)
    if isinstance(expected, float):
        assert mapping[field] == pytest.approx(expected)
        assert getattr(obj, field) == pytest.approx(expected)
    else:
        assert mapping[field] == expected
        assert getattr(obj, field) == expected


def test_curried_return_values() -> None:
    starts: Callable[..., bool] = ops.starts_with("text", "Hello")
    ends: Callable[..., bool] = ops.ends_with("text", "World")
    mapping: dict[str, str] = {"text": "Hello, Funcy Bear World"}
    obj = SimpleNamespace(text="Hello, Funcy Bear World")
    value = "Hello, Funcy Bear World"  # test with individual value
    assert starts(mapping) is True
    assert ends(mapping) is True
    assert starts(obj) is True
    assert ends(obj) is True
    assert starts(value) is True
    assert ends(value) is True


def test_string_operations_apply_to_mapping_and_objects() -> None:
    mapping, obj = apply_to_docs(ops.upper("name"), name="alice")
    assert mapping["name"] == "ALICE"
    assert obj.name == "ALICE"

    mapping, obj = apply_to_docs(ops.lower("name"), name="ALICE")
    assert mapping["name"] == "alice"
    assert obj.name == "alice"

    mapping, obj = apply_to_docs(ops.replace("text", "world", "bear"), text="hello world")
    assert mapping["text"] == "hello bear"
    assert obj.text == "hello bear"


def test_format_operation_applies_to_both_doc_types() -> None:
    greeting = "Hello {name}"
    transform = ops.format("greeting", name="Ada")
    mapping: dict[str, str] = {"greeting": greeting}
    obj = SimpleNamespace(greeting=greeting)
    transform(mapping)
    transform(obj)
    assert mapping["greeting"] == "Hello Ada"
    assert obj.greeting == "Hello Ada"


def test_setter_and_delete_apply_to_both_doc_types() -> None:
    mapping, obj = apply_to_docs(ops.setter("status", "done"), status="pending")
    assert mapping["status"] == "done"
    assert obj.status == "done"

    mapping, obj = apply_to_docs(ops.delete("status"), status="stale")
    assert "status" not in mapping
    assert not hasattr(obj, "status")


def test_default_sets_missing_and_respects_existing() -> None:
    transform: Any = ops.default("fallback", "value", replace_none=False)

    map_missing, obj_missing = make_docs()
    transform(map_missing)
    transform(obj_missing)
    assert map_missing["fallback"] == "value"
    assert obj_missing.fallback == "value"

    map_existing, obj_existing = make_docs(fallback="present")
    transform(map_existing)
    transform(obj_existing)
    assert map_existing["fallback"] == "present"
    assert obj_existing.fallback == "present"


def test_default_replaces_none_when_requested() -> None:
    transform = ops.default("maybe", "value", replace_none=True)
    map_doc, obj_doc = make_docs(maybe=None)
    transform(map_doc)
    transform(obj_doc)
    assert map_doc["maybe"] == "value"
    assert obj_doc.maybe == "value"


def test_push_creates_list_for_missing_field() -> None:
    transform = ops.push("items", "a", index=-1)
    mapping = {}
    transform(mapping)
    obj = SimpleNamespace()
    transform(obj)
    assert mapping["items"] == ["a"]
    assert obj.items == ["a"]


def test_push_inserts_at_specific_index() -> None:
    mapping, obj = apply_to_docs(ops.push("items", "b", index=1), items=["a", "c"])
    assert mapping["items"] == ["a", "b", "c"]
    assert obj.items == ["a", "b", "c"]


def test_append_adds_item_to_end() -> None:
    mapping, obj = apply_to_docs(ops.append("items", 2), items=[1])
    assert mapping["items"] == [1, 2]
    assert obj.items == [1, 2]


def test_prepend_adds_item_to_start() -> None:
    mapping, obj = apply_to_docs(ops.prepend("items", 1), items=[2])
    assert mapping["items"] == [1, 2]
    assert obj.items == [1, 2]


def test_extend_adds_multiple_items() -> None:
    mapping, obj = apply_to_docs(ops.extend("items", [2, 3]), items=[1])
    assert mapping["items"] == [1, 2, 3]
    assert obj.items == [1, 2, 3]


def test_pop_removes_at_index() -> None:
    mapping, obj = apply_to_docs(ops.pop("items", index=1), items=[1, 2, 3])
    assert mapping["items"] == [1, 3]
    assert obj.items == [1, 3]


def test_if_else_executes_then_branch_for_positive_condition() -> None:
    mapping, obj = apply_to_docs(
        ops.if_else(
            "value",
            lambda v: v > 0,
            ops.add("value", 5),
            ops.subtract("value", 5),
        ),
        value=2,
    )
    assert mapping["value"] == 7
    assert obj.value == 7


def test_if_else_executes_otherwise_branch_for_negative_condition() -> None:
    mapping, obj = apply_to_docs(
        ops.if_else(
            "value",
            lambda v: v > 0,
            ops.add("value", 5),
            ops.subtract("value", 5),
        ),
        value=-2,
    )
    assert mapping["value"] == -7
    assert obj.value == -7
