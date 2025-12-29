"""A module providing randomish utilities."""

from __future__ import annotations

from collections.abc import Generator, Iterator  # noqa: TC003
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from random import Random, getstate, setstate
import re
from typing import Any, Final, Literal, NamedTuple, Protocol, Self, cast, overload

from funcy_bear.tools.dispatcher import Dispatcher
from funcy_bear.type_stuffs.validate import is_int, is_list, is_str


@overload
def random_seed(instance: Literal[False] = False, seed: Any = None) -> int: ...


@overload
def random_seed(instance: Literal[True], seed: Any = None) -> Random: ...


def random_seed(instance: bool = False, seed: Any | None = None) -> int | Random:
    """Generate a random seed value using current timestamp.

    Args:
        instance: If True, return a Random instance seeded with the generated seed.
                  If False, return the seed integer value.
        seed: Optional seed value to initialize the RNG. If None, uses system time or entropy source.

    Returns:
        int | Random: The generated seed integer or Random instance.
    """
    from funcy_bear.randoms._rnd import init  # noqa: PLC0415
    from funcy_bear.randoms.random_bits import rnd_bits  # noqa: PLC0415

    if instance:
        return init(seed=seed, return_instance=True)
    return rnd_bits(32)


class DiceModifier(StrEnum):
    """Standard dice notation formats."""

    STANDARD = "standard"
    ADVANTAGE = "advantage"
    DISADVANTAGE = "disadvantage"


RE_NOTATION: Final = r"(\d+)d(\d+)([+-]\d+)?"
"""Regex pattern for dice notation (e.g., '3d6+2')."""


class DiceProtocol(Protocol):
    """Protocol for dice roll classes."""

    @classmethod
    def roll(cls, *args, **kwargs) -> int:
        """Roll the die and return the result."""
        raise NotImplementedError


class DiceRollMeta(type):
    """Metaclass for dice roll classes."""

    @property
    def dice_sides(cls) -> int:
        """Get the number of sides for the die."""
        name: str = cls.__name__
        if name.startswith("D") and name[1:].isdigit():
            return int(name[1:])
        raise ValueError("sides must be provided or inferred from class name.")


@dataclass(slots=True)
class DiceRollBase(metaclass=DiceRollMeta):
    """Base class for dice rolls."""

    @property
    def sides(self) -> int:
        """Get the number of sides for the die."""
        return type(self).dice_sides

    @classmethod
    def roll(cls, rng: Random | None = None) -> int:
        """Roll the die and return the result.

        Args:
            rng: Optional Random instance for deterministic rolling.
                 If None, uses global random module.

        Returns:
            int: The result of the dice roll.
        """
        if rng is None:
            rng = random_seed(instance=True)
        return rng.randint(1, cls.dice_sides)

    def __str__(self) -> str:
        """Return the string representation of the dice roll."""
        return f"d{self.sides}"

    def __repr__(self) -> str:
        """Return the string representation of the dice roll."""
        return f"D{self.sides}(DiceRollBase)"


@dataclass(slots=True)
class D4(DiceRollBase):
    """Class for rolling a four-sided die (D4)."""


@dataclass(slots=True)
class D6(DiceRollBase):
    """Class for rolling a six-sided die (D6)."""


@dataclass(slots=True)
class D10(DiceRollBase):
    """Class for rolling a ten-sided die (D10)."""


@dataclass(slots=True)
class D12(DiceRollBase):
    """Class for rolling a twelve-sided die (D12)."""


@dataclass(slots=True)
class D20(DiceRollBase):
    """Class for rolling a twenty-sided die (D20)."""


@dataclass(slots=True)
class D100(DiceRollBase):
    """Class for rolling a one-hundred-sided die (D100)."""


DICE_CHOICE: dict[int, type[DiceRollBase]] = {
    4: D4,
    6: D6,
    10: D10,
    12: D12,
    20: D20,
    100: D100,
}


def get_custom_dice_class(
    sides: int,
    num: int | None = None,
    modifier: int = 0,
    *,
    dice_notation: str | None = None,
) -> type[DiceRollBase]:
    """Get a custom dice class for non-standard sides.

    Args:
        sides (int): The number of sides on the die.
        num (int | None): The number of dice to roll. Defaults to 1 if not provided.
        modifier (int): The modifier to add to the roll result. Defaults to 0.
        dice_notation (str | None): Optional dice notation string to parse for sides, num, and modifier.


    Returns:
        type[DiceRollBase]: A custom dice class.
    """
    if dice_notation is not None:
        notation: DiceNotation = parse_dice_notation(dice_notation)
        sides = notation.sides
        num = notation.num
        modifier = notation.modifier
    return dataclass(
        type(f"D{sides}", (DiceRollBase,), {"sides": sides, "num": num or 1, "modifier": modifier}), slots=True
    )


@lru_cache(maxsize=1)
def get_compiled_pattern() -> re.Pattern[str]:
    """Get the compiled regex pattern for dice notation.

    Returns:
        re.Pattern[str]: The compiled regex pattern.
    """
    return re.compile(RE_NOTATION, re.IGNORECASE)


def get_match(notation: str) -> re.Match[str] | None:
    """Get the regex match for the dice notation.

    Args:
        notation (str): The dice notation string.

    Returns:
        re.Match[str] | None: The regex match object or None if no match.
    """

    @lru_cache(maxsize=128)
    def _get_match(notation: str) -> re.Match[str] | None:
        pattern: re.Pattern[str] = get_compiled_pattern()
        return pattern.match(notation)

    return _get_match(notation.lower())


class DiceNotation(NamedTuple):
    """Named tuple to represent parsed dice notation."""

    num: int
    sides: int
    modifier: int


def parse_dice_notation(notation: str) -> DiceNotation:
    """Parse dice notation into count, sides, and modifier.

    Example:
        "3d6+2" -> (3, 6, 2)
        "1d20-1" -> (1, 20, -1)
        "2d10"   -> (2, 10, 0)

    Args:
        notation (str): The dice notation string.

    Returns:
        DiceNotationResult: A named tuple containing the number of dice, sides, and modifier.
    """
    match: re.Match[str] | None = get_match(notation)
    if match is None:
        raise ValueError(f"Invalid dice notation: {notation}")

    return DiceNotation(
        num=int(match.group(1)),
        sides=int(match.group(2)),
        modifier=int(match.group(3) or 0),
    )


_dice_type_dispatcher = Dispatcher(arg="sides")


@_dice_type_dispatcher.register(is_int)
def _get_dice_type_int(sides: int) -> type[DiceProtocol]:
    """Handle integer dice sides."""
    return (
        type(f"D{sides}", (DiceRollBase,), {"sides": sides})
        if sides not in DICE_CHOICE and sides > 0
        else DICE_CHOICE[sides]
    )


@_dice_type_dispatcher.register(is_str)
def _get_dice_type_str(sides: str) -> type[DiceProtocol]:
    """Handle dice notation strings (e.g., '3d6+2')."""
    dice_roll: DiceNotation = parse_dice_notation(sides)
    return cast("type[DiceProtocol]", get_dice_type(dice_roll.sides))


@_dice_type_dispatcher.register(is_list)
def _get_dice_type_list(sides: Any) -> list[type[DiceProtocol]]:
    """Handle list of dice sides (ints or notation strings)."""
    dice_types: list[Any] = []
    for side in sides:
        dice_types.append(get_dice_type(side))
    return dice_types


@_dice_type_dispatcher.dispatcher()
def get_dice_type(sides: int | list[int] | str | list[str]) -> type[DiceProtocol] | list[type[DiceProtocol]]:
    """Get the dice type(s) for the given sides.

    Uses bear-dereth's Dispatcher system for flexible type-based routing with
    predicate conditions and LRU caching for performance.

    Args:
        sides: The number of sides on the die(s) or dice notation string.
               Can be a single int, string notation, or list of either.

    Returns:
        type[DiceProtocol] | list[type[DiceProtocol]]: The dice type(s) corresponding to the sides.

    Raises:
        TypeError: If the sides type is not supported.

    Examples:
        >>> get_dice_type(6)  # Single die
        <class 'D6'>
        >>> get_dice_type("3d6+2")  # Notation string
        <class 'D6'>
        >>> get_dice_type([4, 6, 20])  # Multiple dice
        [<class 'D4'>, <class 'D6'>, <class 'D20'>]
    """
    raise TypeError(f"Unsupported type for sides: {type(sides)}")


@dataclass(slots=True, frozen=True)
class DiceResult:
    """Class to represent the result of a dice roll.

    The seed is captured BEFORE rolling to ensure reproducibility.
    Use the same seed with DiceRoller or context managers to replay rolls.
    """

    dice_thrown: list[type[DiceProtocol]]
    rolls: list[int]
    total: int
    seed: int

    @property
    def advantage(self) -> int:
        """Return the highest roll (for advantage)."""
        return max(self.rolls)

    @property
    def disadvantage(self) -> int:
        """Return the lowest roll (for disadvantage)."""
        return min(self.rolls)

    def verify(self) -> bool:
        """Verify that this result is legitimate by re-rolling with the same seed.

        This is useful for DMs or game masters who want to verify that a player's
        dice rolls haven't been tampered with. Re-rolls the same dice with the
        stored seed and checks if the results match.

        Returns:
            bool: True if the rolls match (legitimate), False otherwise.

        Examples:
            >>> result = rollv("3d6", seed=12345)
            >>> result.verify()  # Should return True
            True
            >>> # If someone tries to fake a result:
            >>> fake = DiceResult(dice_thrown=[D6], rolls=[6, 6, 6], total=18, seed=12345)
            >>> fake.verify()  # Will return False if those weren't the actual rolls
            False
        """
        # Handle edge case: empty dice_thrown is invalid
        if not self.dice_thrown:
            return len(self.rolls) == 0  # Only valid if rolls is also empty

        # Calculate how many times each die was rolled
        times: int = len(self.rolls) // len(self.dice_thrown)

        # Re-roll with the same seed and dice
        verification_result: DiceResult = DiceResult.dice_roll(self.dice_thrown, times=times, seed=self.seed)
        return self.rolls == verification_result.rolls

    @classmethod
    def dice_roll(
        cls, dice: type[DiceProtocol] | list[type[DiceProtocol]], times: int = 1, seed: int | None = None
    ) -> Self:
        """Roll a list of dice and return the total sum.

        Args:
            dice: Single dice type or list of dice types to roll.
            times: Number of times to roll each die.
            seed: Optional seed for deterministic rolling. If None, generates a random seed.

        Returns:
            DiceResult with rolls, total, and the seed used.
        """
        if not isinstance(dice, list):
            dice = [dice]
        if seed is None:
            seed = random_seed()
        rng: Random = random_seed(instance=True, seed=seed)
        rolls: list[int] = [d.roll(rng) for d in dice for r in range(times)]
        total: int = sum(rolls)
        return cls(dice_thrown=dice, rolls=rolls, total=total, seed=seed)


class DiceRoller:
    """Dice roller with isolated RNG state for deterministic rolling.

    This class provides a stateful dice roller that maintains its own Random
    instance, allowing for reproducible rolls and seed management without
    affecting the global random state.

    Examples:
        >>> roller = DiceRoller(seed=12345)
        >>> result1 = roller.roll(6, times=3)
        >>> result2 = roller.roll(20)
        >>>
        >>> # Use context manager for temporary seed scope
        >>> with roller.seeded(99999) as r:
        ...     result = r.rollv("3d6+2")
    """

    def __init__(self, seed: int | None = None):
        """Initialize a DiceRoller with an optional seed.

        Args:
            seed: Optional seed for deterministic rolling. If None, generates a random seed.
        """
        self.seed: int = seed if seed is not None else random_seed()
        self.rng: Random = random_seed(instance=True, seed=self.seed)

    def roll(self, sides: int, times: int = 1) -> DiceResult:
        """Roll a die with the specified number of sides.

        Args:
            sides: The number of sides on the die.
            times: The number of times to roll the die.

        Returns:
            DiceResult with rolls, total, and the seed used by this roller.
        """
        dice_type: type[DiceProtocol] = get_dice_type(sides)  # type: ignore[assignment]
        return self._roll_with_rng(dice_type, times)

    def rollv(self, sides: int | list[int] | str | list[str], times: int = 1) -> DiceResult:
        """Roll variable-sided dice using this roller's RNG.

        Args:
            sides: The number of sides on the die(s) or dice notation.
            times: The number of times to roll each die.

        Returns:
            DiceResult with rolls, total, and the seed used by this roller.
        """
        dice_type: type[DiceProtocol] | list[type[DiceProtocol]] = get_dice_type(sides)
        return self._roll_with_rng(dice_type, times)

    def _roll_with_rng(self, dice: type[DiceProtocol] | list[type[DiceProtocol]], times: int) -> DiceResult:
        """Internal method to roll dice using this roller's RNG."""
        if not isinstance(dice, list):
            dice = [dice]

        rolls: list[int] = [d.roll(self.rng) for d in dice for _ in range(times)]
        total: int = sum(rolls)

        return DiceResult(dice_thrown=dice, rolls=rolls, total=total, seed=self.seed)

    @contextmanager
    def seeded(self, seed: int) -> Generator[DiceRoller, Any]:
        """Context manager for temporary seed scope.

        Creates a new DiceRoller with the specified seed that exists only
        within the context. The original roller's state is unchanged.

        Args:
            seed: The seed to use for rolls within this context.

        Yields:
            DiceRoller: A new roller with the specified seed.

        Examples:
            >>> roller = DiceRoller(seed=12345)
            >>> with roller.seeded(99999) as temp_roller:
            ...     result = temp_roller.roll(20)  # Uses seed 99999
            >>> result2 = roller.roll(20)  # Still uses seed 12345
        """
        temp_roller = DiceRoller(seed=seed)
        yield temp_roller

    def verify(self, result: DiceResult) -> bool:
        """Verify that a DiceResult is legitimate using this roller.

        This is a convenience method that delegates to DiceResult.verify().
        Useful for DMs who want to verify player rolls.

        Args:
            result: The DiceResult to verify.

        Returns:
            bool: True if the result is legitimate, False otherwise.

        Examples:
            >>> roller = DiceRoller()
            >>> player_result = rollv("3d6", seed=12345)
            >>> roller.verify(player_result)  # DM verifies the roll
            True
        """
        return result.verify()

    def replay(self, result: DiceResult) -> DiceResult:
        """Replay a previous roll using the same dice and seed.

        Creates an exact replica of the original roll. Useful for debugging
        or demonstrating deterministic behavior.

        Args:
            result: The DiceResult to replay.

        Returns:
            DiceResult: A new result with the same rolls, total, and seed.

        Examples:
            >>> original = rollv("3d6", seed=12345)
            >>> roller = DiceRoller()
            >>> replayed = roller.replay(original)
            >>> original.rolls == replayed.rolls
            True
        """
        times = len(result.rolls) // len(result.dice_thrown) if result.dice_thrown else 1
        return DiceResult.dice_roll(result.dice_thrown, times=times, seed=result.seed)


@contextmanager
def seeded_rolls(seed: int | None = None) -> Iterator[int]:
    """Context manager for deterministic dice rolling without affecting global RNG.

    This saves the global random state, seeds a temporary RNG, and restores
    the original state upon exit. Useful for one-off deterministic rolls.

    Args:
        seed: The seed to use for rolls within this context. If None, generates a random seed.

    Yields:
        int: The seed being used for this context.

    Examples:
        >>> with seeded_rolls(12345) as seed:
        ...     result = rollv("3d6+2")
        ...     assert result.seed == seed == 12345
    """
    from funcy_bear.randoms._rnd import init  # noqa: PLC0415

    seed = seed if seed is not None else random_seed()
    old_state: tuple[Any, ...] = getstate()
    seed = init(seed=seed, return_instance=False)
    try:
        yield seed
    finally:
        setstate(old_state)


def rollv(sides: int | list[int] | str | list[str], times: int = 1, seed: int | None = None) -> DiceResult:
    """Roll a variable-sided die a specified number of times.

    Args:
        sides: The number of sides on the die(s) or dice notation.
        times: The number of times to roll the die. Defaults to 1.
        seed: Optional seed for deterministic rolling. If None, generates a random seed.

    Returns:
        DiceResult: The result of the dice rolls including the seed used.

    Examples:
        >>> result = rollv("3d6+2", seed=12345)  # Deterministic roll
        >>> same_result = rollv("3d6+2", seed=12345)  # Same result
        >>> result.seed == same_result.seed == 12345
        True
    """
    dice_type: type[DiceProtocol] | list[type[DiceProtocol]] = get_dice_type(sides)
    return DiceResult.dice_roll(dice_type, times=times, seed=seed)


def roll(sides: int, times: int = 1, seed: int | None = None) -> DiceResult:
    """Roll a die with the specified number of sides a given number of times.

    Args:
        sides: The number of sides on the die.
        times: The number of times to roll the die. Defaults to 1.
        seed: Optional seed for deterministic rolling. If None, generates a random seed.

    Returns:
        DiceResult: The result of the dice rolls including the seed used.
    """
    return rollv(sides, times=times, seed=seed)


def verify_result(result: DiceResult) -> bool:
    """Verify that a DiceResult is legitimate.

    Standalone convenience function for verifying dice results without
    needing to instantiate a DiceRoller. Particularly useful for DMs
    who need to quickly verify player rolls.

    Args:
        result: The DiceResult to verify.

    Returns:
        bool: True if the result is legitimate, False if tampered with.

    Examples:
        >>> player_roll = rollv("3d6+2", seed=12345)
        >>> verify_result(player_roll)
        True
        >>> # A DM can verify any player's result
        >>> verify_result(player_roll)  # Checks if rolls match the seed
        True
    """
    return result.verify()


__all__ = [
    "D4",
    "D6",
    "D10",
    "D12",
    "D20",
    "D100",
    "DiceModifier",
    "DiceNotation",
    "DiceResult",
    "DiceRollBase",
    "DiceRoller",
    "get_custom_dice_class",
    "parse_dice_notation",
    "roll",
    "rollv",
    "seeded_rolls",
    "verify_result",
]
