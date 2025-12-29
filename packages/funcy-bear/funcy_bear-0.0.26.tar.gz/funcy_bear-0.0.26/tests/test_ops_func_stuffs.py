from __future__ import annotations

import types
from typing import TYPE_CHECKING

import pytest

from funcy_bear.ops.func_stuffs import monkey

if TYPE_CHECKING:
    from collections.abc import Callable


class Sample:
    def greet(self) -> str:
        """Return a greeting string."""
        return "original"


def test_monkey_patches_class_and_preserves_original() -> None:
    original: Callable[..., str] = Sample.greet

    @monkey(Sample)
    def Sample__greet(self: Sample) -> str:  # noqa: N802
        return "patched"

    try:
        inst = Sample()
        assert inst.greet() == "patched"
        assert inst.greet.original(inst) == "original"  # pyright: ignore[reportAttributeAccessIssue]
    finally:
        Sample.greet = original  # type: ignore[assignment]


def test_monkey_patches_module_with_custom_name() -> None:
    module = types.ModuleType("fake_mod")

    @monkey(module, name="shout")
    def _shout() -> str:
        return "roar"

    try:
        assert module.shout() == "roar"
        assert module.shout.original is None
    finally:
        delattr(module, "shout")


def test_monkey_rejects_non_class_or_module() -> None:
    with pytest.raises(TypeError):
        monkey(object())  # type: ignore[arg-type]
