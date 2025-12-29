from __future__ import annotations

from funcy_bear.sentinels import EXIT_SIGNAL, NO_DEFAULT, ExitSignalType, Nullish


def test_nullish_singleton_is_falsy_and_repr() -> None:
    a = Nullish()
    b = Nullish()

    assert bool(a) is False
    assert a is b  # Singleton behaviour
    assert repr(a) == "<Nullish>"

    c = ExitSignalType()
    d = ExitSignalType()

    assert c is d
    assert repr(c) == "<ExitSignal>"

    assert a == c


def test_sentinel_constants_are_singletons() -> None:
    assert isinstance(NO_DEFAULT, Nullish)
    assert isinstance(EXIT_SIGNAL, Nullish)
    assert NO_DEFAULT == EXIT_SIGNAL


def test_nullish_value_returns_none() -> None:
    assert NO_DEFAULT.value() is None
