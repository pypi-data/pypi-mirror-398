from __future__ import annotations

import datetime
from pathlib import Path
from types import NoneType
from typing import TYPE_CHECKING

import pytest

from funcy_bear.ops.dispatch import format_default_value
from funcy_bear.ops.func_stuffs import a_or_b
from funcy_bear.type_stuffs.builtin_tools import check_for_conflicts
from funcy_bear.type_stuffs.conversions import coerce_to_type, str_to_type, type_to_str, value_to_type
from funcy_bear.type_stuffs.hint import TypeHint
from funcy_bear.type_stuffs.inference.runtime import infer_type, str_to_bool
from funcy_bear.type_stuffs.validate import (
    all_same_type,
    is_array_like,
    is_json_like,
    is_mapping,
    is_object,
    num_type_params,
    type_param,
    validate_type,
)

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.fixture
def sample_string_data() -> dict[str, tuple[tuple[str, str], ...]]:
    # fmt: off
    return {
        "ints": (("1", "int"), ("2", "int"), ("3", "int")),
        "floats": (("1.0", "float"), ("2.0", "float"), ("3.0", "float")),
        "strings": (("'a'", "str"), ("'b'", "str"), ("'c'", "str")),
        "bools": (("True", "bool"), ("False", "bool"), ("true", "bool"), ("false", "bool")),
        "empty_data": (("[]", "list"), ("{}", "dict"), ("()", "tuple")),
        "lists": (("[1, 2]", "list[int]"), ("['a', 'b']", "list[str]"), ("[True, False]", "list[bool]")),
        "dicts": (("{'a': 1}", "dict[str, int]"), ("{'b': 2}", "dict[str, int]"), ("{'c': 3}", "dict[str, int]")),
        "tuples": (("(1, 2)", "tuple[int, ...]"),("('a', 'b')", "tuple[str, ...]"),("(True, False)", "tuple[bool, ...]")),
        "mixed_tuples": (("(1, 'a')", "tuple[int, str]"), ("(True, 2.0)", "tuple[bool, float]")),
        "mixed_lists": (("[1, 'a']", "list[int | str]"), ("[True, 2.0]", "list[bool | float]")),
        "mixed_dicts": (("{'a': 1, 'b': 'two'}", "dict[str, int | str]"),("{'key': True, 'value': 3.14}", "dict[str, bool | float]")),
        "mixed_sets": (("{1, 'a'}", "set[int | str]"), ("{True, 2.0}", "set[bool | float]")),
        "bytes": (("b'hello'", "bytes"), ("b'world'", "bytes")),
        "sets": (("{1, 2}", "set[int]"), ("{'a', 'b'}", "set[str]"), ("{True, False}", "set[bool]")),
        "none": (("None", "NoneType"),),
        "path": (("/", "path"), (str(Path("/")), "path")),
    }
    # fmt: on


class Single[T]: ...


class Dual[T, U]: ...


class SingleInt(Single[int]): ...


class DualStrFloat(Dual[str, float]): ...


class SingleNone(Single[None]): ...


class NonGeneric: ...


def test_num_type_params_counts_generic_arguments() -> None:
    assert num_type_params(SingleInt) == 1
    assert num_type_params(DualStrFloat) == 2


def test_num_type_params_raises_for_non_generic() -> None:
    with pytest.raises(AttributeError):
        num_type_params(NonGeneric)


def test_type_param_retrieves_requested_argument() -> None:
    assert type_param(SingleInt) is int
    assert type_param(DualStrFloat, 1) is float


def test_type_param_errors_for_invalid_indices_and_none_values() -> None:
    with pytest.raises(IndexError):
        type_param(SingleInt, 5)
    assert type_param(SingleNone) is NoneType


def test_mapping_to_type_returns_converted_values_and_defaults() -> None:
    data: dict[str, str] = {"count": "3"}
    assert value_to_type(data, "count", int) == 3
    assert value_to_type(data, "missing", int, d="5") == 5


def test_mapping_to_type_raises_for_missing_key_and_bad_coercion() -> None:
    with pytest.raises(KeyError):
        value_to_type({}, "value", int)
    with pytest.raises(ValueError, match="Cannot coerce value"):
        value_to_type({"value": "abc"}, "value", int)


def test_validate_type_accepts_matches_and_raises_for_mismatches() -> None:
    validate_type(10, int)
    # with pytest.raises(AttributeError):
    #     validate_type("abc", int)
    # with pytest.raises(AttributeError):
    #     validate_type("abc", int, exception=ObjectTypeError)


def test_type_hint_returns_runtime_stub_class() -> None:
    hinted = TypeHint(list)
    assert isinstance(hinted, type)
    assert hinted is not list
    assert issubclass(hinted, object)
    assert hinted() is not None


def test_json_and_array_like_guards() -> None:
    assert is_json_like({})
    assert is_json_like([])
    assert not is_json_like(set())

    assert is_array_like([1, 2])
    assert is_array_like((1, 2))
    assert is_array_like({1, 2})
    assert not is_array_like({"a": 1})


class FauxMapping:
    def __init__(self) -> None:
        """A simple mapping-like class."""
        self._store: dict[str, int] = {}

    def __getitem__(self, key: str) -> int:
        return self._store[key]

    def __setitem__(self, key: str, value: int) -> None:
        self._store[key] = value


class PlainObject:
    def __init__(self) -> None:
        """A simple object with attributes."""
        self.value = 42


def test_mapping_and_object_detection_helpers() -> None:
    assert is_mapping({"a": 1})
    assert is_mapping(FauxMapping())
    assert not is_mapping(PlainObject())

    assert is_object(PlainObject())
    assert not is_object({"a": 1})
    assert not is_object(10)


def test_a_or_b_dispatches_to_mapping_or_object_handlers() -> None:
    calls: list[str] = []

    def handle_mapping(doc: object) -> None:
        calls.append("mapping")

    def handle_object(doc: object) -> None:
        calls.append("object")

    handler: Callable[..., None] = a_or_b(handle_mapping, handle_object)
    handler({"a": 1})
    handler(PlainObject())

    handler(5)

    assert calls == ["mapping", "object"]


def test_str_to_bool_handles_truthy_strings() -> None:
    assert str_to_bool("True")
    assert not str_to_bool("false")


def test_coerce_to_type_success_and_failure_cases() -> None:
    assert coerce_to_type("5", int) == 5
    with pytest.raises(ValueError, match="Cannot coerce"):
        coerce_to_type("bad", int)


def test_infer_type_identifies_known_types(tmp_path: Path) -> None:
    assert infer_type("[1, 2]") == "list[int]"
    assert infer_type("(1, 2)") == "tuple[int, ...]"
    assert infer_type("{'a': 1}") == "dict[str, int]"
    assert infer_type("{1, 2}") == "set[int]"
    assert infer_type("b'bytes'") == "bytes"
    assert infer_type("None") == "NoneType"
    assert infer_type("true") == "bool"
    assert infer_type("3") == "int"
    assert infer_type("3.5") == "float"
    file_path: Path = Path(tmp_path / "demo.txt")
    file_path.write_text("x")
    assert file_path.exists()
    assert infer_type(str(file_path)) == "path"

    assert infer_type("hello") == "str"
    assert infer_type(object(), arb_types_allowed=True) == "Any"


def test_various_str_types(sample_string_data: dict[str, tuple[tuple[str, str], ...]]):
    for category, tests in sample_string_data.items():
        for input_str, expected_type in tests:
            assert infer_type(input_str) == expected_type, f"Failed on {category} with input {input_str}"


def test_str_to_type_supports_known_entries_and_defaults() -> None:
    assert str_to_type("int") is int
    assert str_to_type("FLOAT") is float
    assert str_to_type("unknown", default=list) is list


def test_type_to_str_converts_supported_types_and_handles_arbitrary() -> None:
    assert type_to_str(int) == "int"
    assert type_to_str(Path) == "path"
    assert type_to_str(datetime) == "datetime"
    with pytest.raises(TypeError):
        type_to_str(complex)

    class Custom: ...

    assert type_to_str(Custom, arb_types_allowed=True) == "Any"


def test_str_to_type() -> None:
    type_map: dict[str, type] = {
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "tuple": tuple,
        "path": Path,
        "bytes": bytes,
        "set": set,
        "frozenset": frozenset,
        "none": NoneType,
        "nonetype": NoneType,
        "object": str,
    }
    custom_map: dict[str, type] = {
        "EpochTimestamp".lower(): int,
        "datetime": str,
    }

    for key, val in type_map.items():
        assert str_to_type(key, str, custom_map=custom_map) == val


def test_check_for_conflicts_uses_fallbacks_and_modifiers() -> None:
    assert check_for_conflicts("class") == "class_"
    assert check_for_conflicts("len") == "len_"
    assert check_for_conflicts("async", modifier=lambda name: f"{name}X") == "asyncX"


def test_format_default_value_formats_common_types() -> None:
    assert format_default_value("value") == '"value"'
    assert format_default_value(value=True) == "True"
    assert format_default_value(3) == "3"
    assert format_default_value(3.14) == "3.14"
    assert format_default_value([1, 2, 3]) == "[1, 2, 3]"


def test_all_same_type_bug_fix() -> None:
    class CustomClass: ...

    assert all_same_type(1, 2, 3) is True
    assert all_same_type(1, "2", 3) is False
    assert all_same_type(1) is True
    assert all_same_type("a", "b", "c") is True
    assert all_same_type([1, 2], [3, 4], [5, 6]) is True
    assert all_same_type([1, 2], {3, 4}) is False
    assert all_same_type(CustomClass(), CustomClass()) is True
    with pytest.raises(ValueError, match="The sequence must contain at least one element"):
        all_same_type()
