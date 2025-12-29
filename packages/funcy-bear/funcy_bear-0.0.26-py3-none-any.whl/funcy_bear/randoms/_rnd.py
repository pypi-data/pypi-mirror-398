from collections.abc import Callable, Sequence  # noqa: TC003
from typing import TYPE_CHECKING, Literal, overload

from funcy_bear.ops.dispatch import to_int
from funcy_bear.randoms.random_bits import rnd_bits
from funcy_bear.sentinels import NOTSET, NotSetType
from lazy_bear import LazyLoader

if TYPE_CHECKING:
    import random
    import string
else:
    random = LazyLoader("random")
    string = LazyLoader("string")


@overload
def init(
    seed: float | bytes | None = None,
    factory: Callable[..., int] | NotSetType = NOTSET,
    *,
    return_instance: Literal[True] = True,
) -> random.Random: ...
@overload
def init(
    seed: float | bytes | None = None,
    factory: Callable[..., int] | NotSetType = NOTSET,
    *,
    return_instance: Literal[False],
) -> int: ...


def init(
    seed: float | bytes | None = None,
    factory: Callable[..., int] | NotSetType = NOTSET,
    *,
    return_instance: bool = False,
) -> int | random.Random:
    """Seed the random number generator.

    Args:
        seed (int | None, optional): The seed value. If None, the RNG is seeded
            with the current system time or entropy source. Defaults to None.
        factory (Callable[..., int] | None, optional): A callable that returns
            an integer seed value. If provided, this function is called to
            generate the seed. Defaults to None.
        return_instance (bool, optional): If True, return the random.Random
            instance instead of the seed value. Defaults to False.
    """
    s: int = (
        factory()
        if not isinstance(factory, NotSetType) and callable(factory)
        else to_int(seed)
        if seed is not None
        else rnd_bits(32)
    )
    rnd = random.Random(s)
    if return_instance:
        return rnd
    return s


def rint(a: int, b: int) -> int:
    """Generate a random integer between low and high, inclusive.

    Args:
        a (int): The lower bound of the range.
        b (int): The upper bound of the range.

    Returns:
        int: A random integer between low and high.
    """
    return random.randint(a, b)


def rfloat(a: float, b: float, ndigits: int | None = None) -> float:
    """Generate a random float between low and high.

    Args:
        a (float): The lower bound of the range.
        b (float): The upper bound of the range.
        ndigits (int | None): If provided, limit the number of decimal places

    Returns:
        float: A random float between low and high.
    """
    return random.uniform(a, b) if ndigits is None else round(random.uniform(a, b), ndigits)


def rbool(chance: float = 0.5) -> bool:
    """Generate a random boolean value based on a given chance.

    Args:
        chance (float, optional): The probability of returning True. Defaults to 0.5.

    Returns:
        bool: A random boolean value, True with the specified probability.
    """
    return random.random() < chance


def rbytes(n: int) -> bytes:
    """Generate a random bytes object of length n.

    Args:
        n (int): The number of random bytes to generate.

    Returns:
        bytes: A bytes object containing n random bytes.
    """
    return random.randbytes(n)


def rsample[T](population: Sequence[T], k: int) -> list[T]:
    """Generate a random sample of k unique elements from a population.

    Args:
        population (Sequence[T]): The population to sample from.
        k (int): The number of unique elements to sample.

    Returns:
        list[T]: A list containing k unique randomly selected elements from the population.

    Raises:
        ValueError: If k is larger than the size of the population.
    """
    return random.sample(population, k)


def _rshuffnew[T](seq: list[T]) -> list[T]:
    shuffled: list[T] = seq.copy()
    random.shuffle(shuffled)
    return shuffled


def _rshuffinplace[T](seq: list[T]) -> list[T]:
    random.shuffle(seq)
    return seq


def rshuffle[T](seq: list[T], inplace: bool = False) -> list[T]:
    """Shuffle a list randomly.

    Args:
        seq (list[T]): The list to shuffle.
        inplace (bool, optional): If True, shuffle the list in place and return it.
            If False, return a new shuffled list. Defaults to False.

    Returns:
        list[T]: The shuffled list.
    """
    return _rshuffnew(seq) if not inplace else _rshuffinplace(seq)


def rgaussian(mu: float = 0.0, sigma: float = 1.0) -> float:
    """Generate a random float from a Gaussian distribution.

    Args:
        mu (float, optional): The mean of the distribution. Defaults to 0.0.
        sigma (float, optional): The standard deviation of the distribution. Defaults to 1.0.

    Returns:
        float: A random float from the Gaussian distribution.
    """
    return random.gauss(mu, sigma)


def rstring(
    length: int,
    chars: str | None = None,
    *,
    lowercase_ascii: bool = False,
    uppercase_ascii: bool = False,
    hex_digits: bool = False,
    digits: bool = False,
    punctuation: bool = False,
) -> str:
    """Generate a random string of specified length from given characters.

    Args:
        length (int): The length of the random string to generate.
        chars (str | LiteralString, optional): The characters to choose from.
            Defaults to string.ascii_letters.
        digits (bool, optional): If True, include digits in the character set. Defaults to False.
        hex_digits (bool, optional): If True, use hexadecimal characters (0-9, a-f). Defaults to False.
        lowercase_ascii (bool, optional): If True, include lowercase ASCII letters in the character set. Defaults to False.
        uppercase_ascii (bool, optional): If True, include uppercase ASCII letters in the character set. Defaults to False.
        punctuation (bool, optional): If True, include punctuation symbols in the character set. Defaults to False.

    Returns:
        str: A randomly generated string of the specified length.
    """
    output_chars: str = ""
    if chars is not None:
        output_chars += chars
    else:
        output_chars += string.ascii_letters
    if hex_digits:
        output_chars += string.hexdigits
    if lowercase_ascii:
        output_chars += string.ascii_lowercase
    if uppercase_ascii:
        output_chars += string.ascii_uppercase
    if digits:
        output_chars += string.digits
    if punctuation:
        output_chars += string.punctuation
    return "".join(rchoices(output_chars, k=length))


def rhex(length: int) -> str:
    """Generate a random hexadecimal string of specified length.

    Args:
        length (int): The length of the hexadecimal string to generate.

    Returns:
        str: A randomly generated hexadecimal string of the specified length.
    """
    return rstring(length, hex_digits=True)


def rchoice[T](seq: Sequence[T]) -> T:
    """Select a random element from a non-empty sequence.

    Args:
        seq (Sequence[T]): A non-empty sequence (like a list or tuple) to choose from.

    Returns:
        T: A randomly selected element from the sequence.

    Raises:
        IndexError: If the sequence is empty.
    """
    if not seq:
        raise IndexError("Cannot choose from an empty sequence")
    return random.choice(seq)


def rchoices[T](seq: Sequence[T], k: int) -> list[T]:
    """Select k random elements from a sequence, allowing for duplicates.

    Args:
        seq (Sequence[T]): A sequence (like a list or tuple) to choose from.
        k (int): The number of elements to select.

    Returns:
        list[T]: A list containing k randomly selected elements from the sequence.
    """
    return random.choices(seq, k=k)


def rweighted[T](seq: Sequence[T], weights: Sequence[float], k: int = 1) -> list[T]:
    """Select k random elements from a sequence based on specified weights.

    Args:
        seq (Sequence[T]): A sequence (like a list or tuple) to choose from.
        weights (Sequence[float]): A sequence of weights corresponding to the elements in seq.
        k (int, optional): The number of elements to select. Defaults to 1.

    Returns:
        list[T]: A list containing k randomly selected elements from the sequence based on the provided weights.
    """
    return random.choices(seq, weights=weights, k=k)


def rpercent(*, normalized: bool = False, ndigits: int | None = None) -> float:
    """Random percentage 0.0 to 100.0

    Args:
        normalized (bool): If True, return a float between 0.0 and 1.0
        ndigits (int | None): If provided, limit the number of decimal places
            in the returned float.

    Returns:
        float: A random percentage float, either normalized (0.0 to 1.0) or standard (0.0 to 100.0).
            If ndigits is specified, the float will be rounded to that many decimal places.
    """
    return rfloat(0.0, 1.0 if normalized else 100.0, ndigits=ndigits)


def rdollar(a: float, b: float) -> float:
    """Generate a random dollar amount between low and high.

    Args:
        a (float): The lower bound of the range.
        b (float): The upper bound of the range.

    Returns:
        float: A random dollar amount between low and high, rounded to 2 decimal places.
    """
    return rfloat(a, b, ndigits=2)


def coin_flip() -> bool:
    """Simulate a coin flip.

    bool: True for heads, False for tails.
    """
    return rbool()
