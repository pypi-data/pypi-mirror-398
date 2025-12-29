from __future__ import annotations

from collections.abc import Collection  # noqa: TC003
import json

import pytest
from rich.text import Text  # noqa: TC002

from funcy_bear.type_stuffs.introspection._inspector import (
    DoInspect,
    ObjectKey,
    ObjectKeys,
    class_name,
    first_paragraph,
    get_formatted_doc,
    get_object_types_mro_as_strings,
    get_signature,
    is_object_one_of_types,
    single_line_docstring,
)


def sample_func(x: int) -> int:
    """Doc string"""
    return x + 1


class SampleClass:
    class_attr = 7

    def __init__(self) -> None:
        """A sample class."""
        self.instance_attr = "value"
        self._private = "hidden"

    def __dunder__(self) -> str:
        return "secret"

    def method(self) -> str:
        """A sample method."""
        return "ok"

    @property
    def prop(self) -> str:
        """A sample property."""
        return "prop-value"


@pytest.mark.parametrize(
    ("line", "expected"),
    [('"""only one line"""', True), ('  """multi', False), ("no quotes", False)],
)
def test_single_line_docstring(line: str, expected: bool) -> None:
    assert single_line_docstring(line) is expected


def test_object_key_for_function_metadata() -> None:
    ok = ObjectKey("sample_func", value=sample_func)

    assert ok.is_callable
    assert ok.is_function
    assert ok.return_annotation == "int"
    assert ok.parameters is not None
    assert set(ok.parameters.keys()) == {"x"}
    assert ok.parameters["x"].annotation == "int"
    assert ok.docs is not None
    assert ok.docs.plain == "Doc string"
    assert ok.text_signature is not None
    assert ok.text_signature.plain == "(x: int) -> int"

    serialized = json.loads(ok.to_json())
    assert serialized["name"] == "sample_func"
    assert serialized["parameters"] == {"x": "int"}
    assert serialized["signature"] == "(x: int) -> int"


def test_object_key_for_property_metadata() -> None:
    prop_key = ObjectKey("prop", value=SampleClass.prop)

    assert prop_key.is_property
    assert prop_key.text_signature is not None
    assert prop_key.text_signature.plain.startswith("(self)")
    assert prop_key.return_annotation == "str"
    assert prop_key.parameters is not None
    assert set(prop_key.parameters.keys()) == {"self"}


def test_object_key_builtin_and_attribute_handling() -> None:
    builtin_key = ObjectKey("len", value=len)
    attr_key = ObjectKey("instance_attr", value=123)

    assert builtin_key.is_builtin
    assert builtin_key.text_signature is None
    assert builtin_key.parameters is None

    assert attr_key.is_attribute
    assert not attr_key.is_callable


def test_object_key_source_strips_def_and_docstring() -> None:
    def with_doc() -> int:
        """Doc string with multiple lines.

        With three lines.
        """
        return 5

    ok = ObjectKey("with_doc", value=with_doc)
    assert ok.source is not None
    assert any("return 5" in line for line in ok.source)
    assert all('"""' not in line for line in ok.source)


def test_object_keys_filtering_and_update() -> None:
    keys: ObjectKeys = ObjectKeys.from_keys(["alpha", "_private", "__dunder__"])
    keys.filter_out_by_key(lambda k: k.startswith("_"))
    assert set(keys.keys()) == {"alpha"}

    keys.update_key("alpha", error=None, value=42)
    assert keys.get("alpha", strict=True).value == 42


def test_do_inspect_respects_private_and_dunder_flags() -> None:
    instance = SampleClass()

    inspector_default = DoInspect(instance)
    names_default: list[str] = inspector_default.obj_keys().keys()
    assert "_private" not in names_default
    assert "__dunder__" not in names_default

    inspector_all = DoInspect(instance, private=True, dunder=True)
    names_all: list[str] = inspector_all.obj_keys().keys()
    assert "_private" in names_all
    assert "__dunder__" in names_all


def test_do_inspect_signature_and_value() -> None:
    inspector_func = DoInspect(sample_func, value=False)
    assert inspector_func.signature is not None
    assert "sample_func" in inspector_func.signature.plain
    assert inspector_func.docs is not None
    assert "Doc string" in inspector_func.docs.plain

    inspector_literal = DoInspect(123)
    assert inspector_literal.value.plain == "123"


def test_do_inspect_help_full_doc() -> None:
    def doc_func() -> None:
        """Line one

        Line two
        """

    inspector = DoInspect(doc_func, help=True)
    assert inspector.docs is not None
    assert "Line two" in inspector.docs.plain


def test_do_inspect_value_suppressed_for_literal() -> None:
    inspector_literal = DoInspect("hello", value=False)
    assert inspector_literal.value.plain == ""


def test_get_formatted_doc_and_first_paragraph() -> None:
    def doc_func() -> None:
        """Line one

        Line two
        """

    assert get_formatted_doc(doc_func, help=False) == "Line one"
    docs: str | None = get_formatted_doc(doc_func, help=True)
    assert docs is not None
    assert "Line two" in docs
    assert first_paragraph("Para1\n\nPara2") == "Para1"


def test_get_signature_and_class_name_helpers() -> None:
    sig_text = get_signature("sample_func", sample_func)
    assert sig_text.plain.startswith("def sample_func")
    assert sig_text.plain.endswith(":")
    assert class_name(SampleClass()) == "SampleClass"


def test_mro_helpers() -> None:
    instance = SampleClass()
    mro_strings: Collection[str] = get_object_types_mro_as_strings(instance)
    assert any(part.endswith("SampleClass") for part in mro_strings)
    assert is_object_one_of_types(instance, {"builtins.object", *mro_strings})


def test_get_formatted_doc_none_docstring() -> None:
    def no_doc() -> None:
        return None

    no_doc.__doc__ = None
    assert get_formatted_doc(no_doc, help=False) is None


def test_object_key_handles_module_and_builtin_source() -> None:
    builtin_key = ObjectKey("len", value=len)
    module_key = ObjectKey("json_module", value=json)

    assert builtin_key.source is None
    assert module_key.is_module
    assert not module_key.is_attribute


def test_get_signature_error_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(obj: object) -> None:
        raise ValueError("no sig")

    monkeypatch.setattr("funcy_bear.type_stuffs.introspection._inspector.signature", boom)
    text_value_error: Text = get_signature("foo", sample_func)
    assert text_value_error.plain.endswith("(...)")

    def type_error(obj: object) -> None:
        raise TypeError("not callable")

    monkeypatch.setattr("funcy_bear.type_stuffs.introspection._inspector.signature", type_error)
    text_type_error: Text = get_signature("literal", 123)
    assert text_type_error.plain == "NONE"
