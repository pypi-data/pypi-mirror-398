# funcy_bear.ops.math

Numerical helpers used across Bear Dereth for common interpolation, normalization, and sentinel-style infinity handling.

## Modules
- `general.py`: Scalar math utilities (clamp, lerp, smoothstep, etc.).
- `infinity.py`: `Infinity` sentinel that behaves like positive infinity while remaining hashable and comparable inside BearBase records or dict keys.

---

## General Utilities

These helpers smooth over repetitive math patterns in rendering, configuration, and timing code. All functions are pure and operate on basic numeric types.

| Function                                         | Purpose                                                |
| ------------------------------------------------ | ------------------------------------------------------ |
| `clamp(value, min_value, max_value)`             | Constrain a number to a closed interval.               |
| `normalize(value, min_value, max_value)`         | Map to `[0, 1]` given explicit bounds.                 |
| `relative_norm(value, denominator)`              | Quick one-liner for `value / denominator`.             |
| `lerp(start, end, t)`                            | Linear interpolation with `t` locked to `[0, 1]`.      |
| `inv_lerp(start, end, value)`                    | Solve for `t` given a value between `start` and `end`. |
| `remap(value, in_min, in_max, out_min, out_max)` | Range-to-range conversion (`inv_lerp` + `lerp`).       |
| `map_range(value, in_range, out_range)`          | Tuple-based wrapper around `remap`.                    |
| `smoothstep(edge0, edge1, x)`                    | Cubic ease-in/ease-out interpolation.                  |
| `neg(value)`                                     | Return the negative absolute value (always `<= 0`).    |
| `sign(value)`                                    | Return `-1`, `0`, or `1` based on input sign.          |

Typical usage:

```python
from funcy_bear.ops.math import clamp, lerp, map_range, smoothstep

alpha = clamp(mouse_x / window_width, 0.0, 1.0)
position = lerp(start=0.0, end=100.0, t=alpha)
warmup = map_range(cpu_percent, (0.0, 80.0), (0.0, 1.0))
fade = smoothstep(0.2, 0.8, alpha)
```

All normalization helpers raise `ValueError` if the provided range collapses (e.g., identical min/max).

---

## Infinity Sentinel

`INFINITE` is a singleton instance of the `Infinity` class. It inherits from `int` so it can slot into existing APIs that expect integer-like sentinels but internally uses `float("inf")` for comparisons and hashing.

Key behaviors:
- Hash equals `float("inf")`, making it safe for dict/set usage.
- Compares greater than any finite `int` or `float`.
- Arithmetic with positive numbers yields IEEE-style infinity (`float("inf")`).
- Division of finite numbers by `INFINITE` returns `0.0`.
- Multiplying or dividing by negative numbers raises `ValueError` to avoid undefined results.

Example:

```python
from funcy_bear.ops.math import INFINITE, clamp

timeout = INFINITE
assert timeout > 10_000
assert clamp(500, 0, timeout) == 500
assert hash(timeout) == hash(float("inf"))
```

Use `INFINITE` when you need an upper bound that dwarfs normal values without risking integer overflow or losing hash stability across runs.

---

## Tips
- Favor `map_range` over ad-hoc `remap` math to keep interpolation logic consistent.
- When chaining interpolation functions, work with floats to benefit from the built-in clamping.
- Re-exported symbols live in `funcy_bear.ops.math.__all__`, so `from funcy_bear import math` exposes the helpers directly.

Happy calculating, Bear! 🧮✨
