"""Tests for ToolContainer and tool service injection."""

from collections.abc import Callable  # noqa: TC003
from typing import Any

from funcy_bear.injection import (
    Deleter,
    Getter,
    Provide,
    Setter,
    Singleton,
    ToolContainer as _ToolContainer,
    ToolContext,
    inject_tools,
)

ToolContainer = _ToolContainer.value


class ToolContain(ToolContainer):
    """A subclass of ToolContainer to test inheritance behavior."""

    getter: Singleton[Getter] = Singleton(Getter)
    setter: Singleton[Setter] = Singleton(Setter)
    deleter: Singleton[Deleter] = Singleton(Deleter)
    ctx: Singleton[ToolContext] = Singleton(ToolContext, getter=getter, setter=setter, deleter=deleter)


def test_tool_container_services_inject() -> None:
    """Verify that ToolContainer services can be injected via Provide."""

    @inject_tools()
    def delete(field: str, deleter: Deleter = Provide[ToolContain.deleter]) -> Callable[[dict], Callable[[str], None]]:  # type: ignore[return]
        """Delete a given field from the document.

        Args:
            field: The field to delete.
        """
        deleter(field)

    @inject_tools()
    def add(
        field: str,
        n: int,
        getter: Getter = Provide[ToolContain.getter],
        setter: Setter = Provide[ToolContain.setter],
    ) -> Callable[[dict], Callable[[str, int], None]]:  # type: ignore[return]
        """Add ``n`` to a given field in the document.

        Args:
            field: The field to add to.
            n: The amount to add.
        """
        attr: Any = getter(field)
        if isinstance(attr, (int | float)):
            setter(field, attr + n)

    test_dict: dict[str, int] = {"a": 1, "b": 2, "c": 3}

    del_a = delete("a")
    # assert isinstance(del_a, Callable)
    del_a(test_dict)

    assert "a" not in test_dict
    add_to_b = add("b", 5)
    assert callable(add_to_b), "add_to_b should be callable"
    add_to_b(test_dict)
    assert test_dict["b"] == 7


def test_tool_context_available_in_container():
    """Verify that ToolContext is registered in ToolContainer."""
    ctx: ToolContext | None = ToolContain.get("ctx")
    assert ctx is not None
    assert isinstance(ctx, ToolContext)
