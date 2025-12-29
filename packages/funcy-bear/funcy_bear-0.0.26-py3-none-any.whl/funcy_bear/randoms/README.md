# funcy_bear.randoms

Randomization utilities for tests, simulations, and playful CLI output. This
package wraps Python’s `random` module with lazy imports, plus D&D-style dice
tools.

## Quick Start
```python
from funcy_bear.randoms import init, rint, rchoice, rfloat, rstring

init(seed=42)
num = rint(1, 10)
letter = rchoice(list("bear"))
price = rfloat(5.0, 15.0, ndigits=2)
token = rstring(12, digits=True, uppercase_ascii=True)
```

- `init(seed, *, factory=None)` seeds the RNG. Pass a callable factory to defer
  seed creation (e.g., using `secrets.token_hex`).
- `rint`, `rfloat`, `rbool`, `rpercent`, `rdollar`, `rgaussian` provide
  frequently-needed variants.
- `rchoice`, `rchoices`, `rweighted`, `rsample`, `rshuffle` cover selection and
  shuffling (with cloning or in-place options).
- `rstring`, `rhex`, `rbytes` generate strings or byte blobs with custom char
  sets.

---

## Dice Utilities

The `dice.py` module speaks fluent dice notation.

```python
from funcy_bear.randoms.dice import roll, rollv, DiceModifier, parse_dice_notation

# Roll a single d20
result = roll(20)
print(result.total, result.rolls)

# Roll “3d6+2” three times
result = rollv("3d6+2", times=3)
print(result.total, result.advantage)
```

- `roll(sides, times=1)` rolls a standard die (4, 6, 10, 12, 20, 100).
- `rollv(sides|notation, times=1)` accepts integers, lists, or strings like
  `"2d8-1"`.
- `parse_dice_notation("3d6+2")` returns a `DiceNotation(num=3, sides=6, modifier=2)`.
- `get_custom_dice_class(sides, num, modifier)` builds a dataclass-backed die
  for exotic shapes or modifiers.
- `DiceResult` exposes `total`, `rolls`, and convenience properties (e.g.,
  `.advantage` for highest roll).

---

## Tips
- Because the module lazy-loads `random`, seeding happens at the first call to
  `init` or any random function—call `init` early in tests for reproducibility.
- Pair `rweighted` with query results to simulate weighted choices.
- For reproducible dice tests, seed once and pass `times` to `rollv` rather than
  looping manually; the result keeps all rolls for assertions.

Roll on, Bear! 🎲🐻✨
