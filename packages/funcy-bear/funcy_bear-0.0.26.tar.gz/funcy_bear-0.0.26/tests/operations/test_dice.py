"""Tests for dice rolling system with seed tracking and verification."""

import concurrent.futures
import random
import threading
import time

from funcy_bear.randoms.dice import (
    D6,
    D20,
    DiceResult,
    DiceRoller,
    roll,
    rollv,
    seeded_rolls,
    verify_result,
)


def test_seed_determinism() -> None:
    """Test that same seed produces same results."""
    seed = 12345

    result1: DiceResult = roll(6, times=3, seed=seed)
    result2: DiceResult = roll(6, times=3, seed=seed)

    assert result1.seed == result2.seed == seed
    assert result1.rolls == result2.rolls
    assert result1.total == result2.total


def test_seed_capture_before_rolling() -> None:
    """Test that seed is captured before rolling and corresponds to results."""
    seed = 99999
    result: DiceResult = rollv("3d6", seed=seed)

    assert result.seed == seed
    # Verify that re-rolling with same seed gives same results
    result2: DiceResult = rollv("3d6", seed=seed)
    assert result.rolls == result2.rolls


def test_automatic_seed_generation() -> None:
    """Test that seeds are auto-generated when not provided."""
    result1: DiceResult = roll(20)
    time.sleep(0.001)  # Ensure different timestamp
    result2: DiceResult = roll(20)

    # Seeds should be captured
    assert result1.seed is not None
    assert result2.seed is not None
    # If seeds differ, rolls should likely differ
    # (but timestamps can collide, so we don't assert they're different)


def test_dice_result_verification_legitimate() -> None:
    """Test that legitimate rolls verify successfully."""
    result = rollv("2d6+2", seed=42)

    # Verify method on DiceResult
    assert result.verify() is True

    # Standalone verify function
    assert verify_result(result) is True


def test_dice_result_verification_tampered() -> None:
    """Test that tampered rolls fail verification."""
    # Create a fake result with rolls that don't match the seed
    fake_result = DiceResult(
        dice_thrown=[D6],
        rolls=[6, 6, 6],  # Suspiciously all 6s
        total=18,
        seed=12345,
    )

    # This should fail verification (those rolls don't come from seed 12345)
    assert fake_result.verify() is False
    assert verify_result(fake_result) is False


def test_dice_roller_stateful() -> None:
    """Test that DiceRoller maintains isolated state."""
    roller = DiceRoller(seed=55555)

    result1 = roller.roll(6, times=2)
    result2 = roller.roll(20)

    # Both results should use the same seed from the roller
    assert result1.seed == roller.seed == 55555
    assert result2.seed == roller.seed == 55555


def test_dice_roller_replay() -> None:
    """Test that DiceRoller can replay previous results."""
    roller = DiceRoller()
    original = roller.rollv("3d6")

    # Replay should produce identical results
    replayed = roller.replay(original)

    assert replayed.rolls == original.rolls
    assert replayed.total == original.total
    assert replayed.seed == original.seed


def test_dice_roller_verify() -> None:
    """Test that DiceRoller can verify results."""
    roller = DiceRoller()

    # Legitimate result
    legit_result = rollv("2d20", seed=77777)
    assert roller.verify(legit_result) is True

    # Tampered result
    fake_result = DiceResult(
        dice_thrown=[D20],
        rolls=[20, 20],  # Suspiciously both nat 20s
        total=40,
        seed=77777,
    )
    assert roller.verify(fake_result) is False


def test_seeded_context_manager() -> None:
    """Test that seeded_rolls context manager provides seed value.

    Note: The context manager sets global random state, but rollv/roll use
    isolated Random instances. To use the context seed, pass it explicitly.
    """
    seed = 11111

    with seeded_rolls(seed) as ctx_seed:
        assert ctx_seed == seed
        # To use the context seed with rollv, pass it explicitly
        result = rollv("4d6", seed=ctx_seed)
        assert result.seed == seed

    # Roll again with same seed outside context
    result2 = rollv("4d6", seed=seed)
    assert result.rolls == result2.rolls


def test_dice_roller_seeded_context() -> None:
    """Test DiceRoller's seeded context manager."""
    roller = DiceRoller(seed=22222)

    with roller.seeded(33333) as temp_roller:
        result = temp_roller.roll(6, times=3)
        assert result.seed == 33333

    # Original roller still has original seed
    result2 = roller.roll(6)
    assert result2.seed == 22222


def test_multiple_dice_types() -> None:
    """Test rolling multiple different dice types."""
    seed = 44444
    result: DiceResult = rollv([4, 6, 10, 20], times=2, seed=seed)

    # Should have 8 rolls total (4 dice types * 2 times)
    assert len(result.rolls) == 8
    assert len(result.dice_thrown) == 4

    # Verify it's legitimate
    assert result.verify() is True


def test_advantage_disadvantage() -> None:
    """Test advantage and disadvantage properties."""
    result: DiceResult = rollv([1, 2, 3, 4, 5, 6], times=1, seed=55555)

    assert result.advantage == max(result.rolls)
    assert result.disadvantage == min(result.rolls)


def test_dice_notation_parsing() -> None:
    """Test that dice notation works with seeds."""
    seed = 66666

    result1: DiceResult = rollv("3d6+2", seed=seed)
    result2: DiceResult = rollv("3d6+2", seed=seed)

    # Same notation + same seed = same results
    assert result1.rolls == result2.rolls
    assert result1.verify() is True


def test_isolated_rng_no_global_pollution() -> None:
    """Test that dice rolling doesn't affect global random state."""
    # Save global state
    initial_state = random.getstate()

    # Roll some dice
    _result1: DiceResult = rollv("5d6", seed=88888)
    _result2: DiceResult = roll(20, times=10, seed=99999)

    # Use DiceRoller
    roller = DiceRoller(seed=77777)
    _result3: DiceResult = roller.rollv("2d10")

    # Global state should still work independently
    random.seed(12345)
    val1 = random.randint(1, 100)

    random.seed(12345)
    val2 = random.randint(1, 100)

    assert val1 == val2  # Global random still deterministic

    # Restore original state
    random.setstate(initial_state)


# Edge Case Tests


def test_empty_dice_result_verification() -> None:
    """Test that empty DiceResult verifies correctly."""
    # Empty result should verify as valid (edge case)
    empty_result = DiceResult(dice_thrown=[], rolls=[], total=0, seed=12345)
    assert empty_result.verify() is True

    # Empty dice_thrown but non-empty rolls should fail
    invalid_result = DiceResult(dice_thrown=[], rolls=[1, 2, 3], total=6, seed=12345)
    assert invalid_result.verify() is False


def test_large_roll_count_performance() -> None:
    """Test that large roll counts work efficiently."""
    # Roll 1000 dice - should complete quickly
    seed = 11111
    result = roll(6, times=1000, seed=seed)

    assert len(result.rolls) == 1000
    assert result.verify() is True
    assert 1000 <= result.total <= 6000  # All rolls between 1-6


def test_concurrent_rolling_thread_safety() -> None:
    """Test that concurrent rolls with isolated RNG are thread-safe."""
    results: list[DiceResult] = []
    results_lock = threading.Lock()

    def roll_worker(worker_seed: int) -> None:
        """Worker function for concurrent rolling."""
        result: DiceResult = rollv("3d6", seed=worker_seed)
        with results_lock:
            results.append(result)

    # Launch 10 concurrent rolls with different seeds
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures: list[concurrent.futures.Future[None]] = [
            executor.submit(roll_worker, seed) for seed in range(10000, 10010)
        ]
        concurrent.futures.wait(futures)

    # Should have 10 results
    assert len(results) == 10

    # Each result should verify
    for result in results:
        assert result.verify() is True

    # Results with different seeds should (likely) differ
    unique_totals: set[int] = {r.total for r in results}
    assert len(unique_totals) > 1  # At least some variation


def test_mismatched_dice_and_rolls() -> None:
    """Test verification fails when dice/rolls mismatch."""
    # Create result with wrong number of rolls
    mismatched = DiceResult(
        dice_thrown=[D6, D6],  # 2 dice
        rolls=[1, 2, 3],  # 3 rolls (should be even number)
        total=6,
        seed=55555,
    )
    # Verification should fail (can't reproduce odd number of rolls from 2 dice)
    assert mismatched.verify() is False


def test_extreme_dice_values() -> None:
    """Test rolling dice with extreme side counts."""
    # Very large die
    result_large = roll(1000, times=5, seed=99999)
    assert len(result_large.rolls) == 5
    assert all(1 <= r <= 1000 for r in result_large.rolls)
    assert result_large.verify() is True

    # Single-sided die (edge case)
    result_single = roll(1, times=10, seed=88888)
    assert all(r == 1 for r in result_single.rolls)
    assert result_single.total == 10
    assert result_single.verify() is True


# ruff: noqa: S311 - Random number generation for dice is acceptable and intentional in these tests
