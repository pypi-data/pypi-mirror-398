from funcy_bear.tools.add_methods import ComparisonMethods, add_comparison_methods
from funcy_bear.type_stuffs.hint import TypeHint


@add_comparison_methods("value")
class SimpleClass(TypeHint(ComparisonMethods[int])):
    def __init__(self, value: int) -> None:
        """A simple class to test comparison methods."""
        self.value: int = value


def test_add_comparison_methods() -> None:
    obj1 = SimpleClass(10)
    obj2 = SimpleClass(20)
    obj3 = SimpleClass(10)

    # Test equality and inequality
    assert obj1 == obj3
    assert obj1 != obj2

    # Test less than and greater than
    assert obj1 < obj2
    assert obj2 > obj1

    # Test less than or equal and greater than or equal
    assert obj1 <= obj3
    assert obj2 >= obj1

    # Test comparison with primitive types
    assert obj1 == 10
    assert obj1 != 20
    assert obj1 < 20
    assert obj1 <= 10
    assert obj1 > 5
    assert obj1 >= 10


def test_introspection_of_other_class() -> None:
    """Test comparison with an instance of another class having the same attribute.

    It automatically checks for the presence of the attribute and uses it for comparison.
    """
    obj1 = SimpleClass(10)

    class OtherClass:
        def __init__(self, value: int) -> None:
            self.value: int = value

    other = OtherClass(10)
    assert (obj1 == other) is True
    assert (obj1 != other) is False
    assert (obj1 < other) is False
    assert (obj1 <= other) is True
    assert (obj1 > other) is False
    assert (obj1 >= other) is True
