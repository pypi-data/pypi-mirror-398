from functools import partial

import pytest

from funcy_bear.ops.func_stuffs import complement, const, if_in_list
from funcy_bear.ops.value_stuffs import always_false, always_true
from funcy_bear.tools.dispatcher import Dispatcher


def test_dispatcher_routes_matching_keyword_handler() -> None:
    dispatcher = Dispatcher()

    @dispatcher.register(lambda obj: obj == "hello")
    def handle(obj: str) -> str:
        return f"greetings {obj}"

    @dispatcher.dispatcher()
    def process(*, obj: str) -> str:
        return f"default {obj}"

    assert process(obj="hello") == "greetings hello"
    assert process(obj="world") == "default world"


def test_dispatcher_routes_matching_positional_handler() -> None:
    dispatcher = Dispatcher(arg="value")

    @dispatcher.register(lambda value: value == 1)
    def handle(value: int, flag: bool = False) -> str:
        return f"handled {value} {flag}"

    @dispatcher.dispatcher()
    def process(value: int, flag: bool = False) -> str:
        return f"default {value} {flag}"

    assert process(1, flag=True) == "handled 1 True"
    assert process(2) == "default 2 False"


def test_dispatcher_falls_back_when_no_handler_matches() -> None:
    dispatcher = Dispatcher()

    @dispatcher.register(lambda obj: obj == "special")
    def handle(obj: str) -> str:
        return f"handled {obj}"

    @dispatcher.dispatcher()
    def process(*, obj: str) -> str:
        return f"default {obj}"

    assert process(obj="ordinary") == "default ordinary"


def test_dispatcher_handles_missing_argument_via_original_function() -> None:
    dispatcher = Dispatcher()

    @dispatcher.register(lambda obj: obj == "value")
    def handle(obj: str) -> str:
        return f"handled {obj}"

    @dispatcher.dispatcher()
    def process(obj: str = "fallback") -> str:
        return f"default {obj}"

    assert process() == "default fallback"


def test_dispatcher_applies_and_overrides_registered_kwargs() -> None:
    dispatcher = Dispatcher()

    captured: dict[str, tuple[str, str]] = {}

    @dispatcher.register(lambda obj: obj == "special", action="registered")
    def handle(obj: str, *, action: str) -> str:
        captured[obj] = ("handle", action)
        return f"{obj}:{action}"

    @dispatcher.dispatcher()
    def process(*, obj: str, action: str = "call") -> str:
        captured[obj] = ("process", action)
        return f"{obj}:{action}"

    assert process(obj="special") == "special:registered"
    assert captured["special"] == ("handle", "registered")

    assert process(obj="special", action="override") == "special:override"
    assert captured["special"] == ("handle", "override")


def test_dispatcher_requires_all_conditions_to_pass() -> None:
    dispatcher = Dispatcher()

    @dispatcher.register(lambda obj: isinstance(obj, int), lambda obj: obj > 0)
    def handle(obj: int) -> str:
        return f"positive {obj}"

    @dispatcher.dispatcher()
    def process(*, obj: object) -> str:
        return f"default {obj}"

    assert process(obj=10) == "positive 10"
    assert process(obj=-5) == "default -5"
    assert process(obj="10") == "default 10"


def test_dispatcher_uses_first_matching_handler() -> None:
    dispatcher = Dispatcher()

    @dispatcher.register(lambda obj: True)
    def first(obj: str) -> str:
        return "first"

    @dispatcher.register(lambda obj: True)
    def second(obj: str) -> str:
        return "second"

    @dispatcher.dispatcher()
    def process(*, obj: str) -> str:
        return f"default {obj}"

    assert process(obj="anything") == "first"


def test_dispatcher_dispatches_using_first_positional_argument() -> None:
    dispatcher = Dispatcher()

    @dispatcher.register(partial(if_in_list, lst=("hit",)))
    def handle(obj: str) -> str:
        return "matched positional"

    @dispatcher.dispatcher()
    def process(obj: str) -> str:
        return f"default {obj}"

    assert process("hit") == "matched positional"
    assert process("miss") == "default miss"


def test_dispatcher_accepts_truthy_non_boolean_predicates() -> None:
    dispatcher = Dispatcher()

    @dispatcher.register(const("truthy"))
    def handle(obj: str) -> str:
        return f"truthy {obj}"

    @dispatcher.dispatcher()
    def process(*, obj: str) -> str:
        return f"default {obj}"

    assert process(obj="value") == "truthy value"


def test_dispatcher_complement_predicate_selects_handler() -> None:
    dispatcher = Dispatcher()

    @dispatcher.register(complement(always_false))
    def handle(obj: str) -> str:
        return "complement"

    @dispatcher.register(always_true)
    def backup(obj: str) -> str:
        return "backup"

    @dispatcher.dispatcher()
    def process(*, obj: str) -> str:
        return f"default {obj}"

    assert process(obj="anything") == "complement"


def test_dispatcher_all_conditions_short_circuit() -> None:
    dispatcher = Dispatcher()
    called: list[str] = []

    def false_condition(obj: object) -> bool:
        called.append("false")
        return False

    def should_not_run(obj: object) -> bool:
        called.append("should_not_run")
        return True

    @dispatcher.register(false_condition, should_not_run)
    def handle(obj: object) -> str:
        return "never"

    @dispatcher.dispatcher()
    def process(*, obj: object) -> str:
        return f"default {obj}"

    assert process(obj="boom") == "default boom"
    assert called == ["false"]


def test_dispatcher_handles_many_conditions_mixed_from_funcstuffs() -> None:
    dispatcher = Dispatcher()

    def starts_with_a(obj: str) -> bool:
        return obj.startswith("a")

    @dispatcher.register(
        always_true,
        complement(always_false),
        partial(if_in_list, lst=("alpha", "omega")),
        starts_with_a,
    )
    def handle(obj: str) -> str:
        return f"matched {obj}"

    @dispatcher.dispatcher()
    def process(*, obj: str) -> str:
        return f"default {obj}"

    assert process(obj="alpha") == "matched alpha"


def test_dispatcher_propagates_condition_errors() -> None:
    dispatcher = Dispatcher()

    def broken_condition(obj: object) -> bool:
        raise RuntimeError("condition blew up")

    @dispatcher.register(broken_condition)
    def handle(obj: object) -> str:
        return "won't reach"

    @dispatcher.dispatcher()
    def process(*, obj: object) -> str:
        return f"default {obj}"

    with pytest.raises(RuntimeError, match="condition blew up"):
        process(obj="boom")


def test_dispatcher_bubbles_type_error_when_argument_missing() -> None:
    dispatcher = Dispatcher()

    @dispatcher.register(always_true)
    def handle(obj: str) -> str:
        return "handled"

    @dispatcher.dispatcher()
    def process(obj: str) -> str:
        return f"default {obj}"

    with pytest.raises(TypeError):
        process()  # type: ignore[call-arg] # This is intentional for the test
