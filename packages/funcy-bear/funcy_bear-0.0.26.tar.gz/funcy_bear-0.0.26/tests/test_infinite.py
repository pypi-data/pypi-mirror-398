from funcy_bear.ops.math.infinity import INFINITE, MAX_SIZE, Infinity


def test_infinite_comparisons() -> None:
    assert INFINITE > 1
    assert INFINITE > MAX_SIZE
    assert INFINITE > -MAX_SIZE
    assert INFINITE >= 1
    assert INFINITE >= MAX_SIZE
    assert INFINITE >= -MAX_SIZE
    assert not (INFINITE < 1)
    assert not (INFINITE < MAX_SIZE)
    assert not (INFINITE < -MAX_SIZE)
    assert not (INFINITE <= 1)
    assert not (INFINITE <= MAX_SIZE)
    assert not (INFINITE <= -MAX_SIZE)
    assert Infinity() == INFINITE
    assert INFINITE != 1
    assert INFINITE != MAX_SIZE
    assert INFINITE != -MAX_SIZE
    assert int(INFINITE) == MAX_SIZE
    assert float(INFINITE) == float("inf")
    assert hash(INFINITE) == hash(float("inf"))
    assert repr(INFINITE) == "Infinity"
    assert str(INFINITE) == "Infinity"
