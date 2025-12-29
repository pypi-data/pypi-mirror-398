# funcy_bear.rich_enums

Data-rich Enum helpers that power the project’s color themes, CLI styles, and
typed configuration metadata. These classes extend Python’s standard `Enum`
types with extra text, defaults, and lookup ergonomics.

## Building Blocks

| Module             | What It Adds                                                                                          |
| ------------------ | ----------------------------------------------------------------------------------------------------- |
| `base_value.py`    | `BaseValue` dataclass + `BaseEnumMixin` with cached lookups (`keys`, `values`, `from_value`, etc.).   |
| `str_enum.py`      | `RichStrEnum` + `StrValue` for string-backed enums with metadata.                                     |
| `int_enum.py`      | `RichIntEnum` + `IntValue` for integer-backed enums with metadata.                                    |
| `variable_enum.py` | `VariableEnum`, `VariableValue`, and typed metadata (`VariableType`) for richer variable definitions. |

Importing `funcy_bear.rich_enums` re-exports the primary classes to keep
call-sites concise.

---

## Core Concepts

### Metadata-Carrying Values

Each enum member is created from a small dataclass (e.g. `StrValue`,
`IntValue`) that stores:
- `value`: The raw enum value (`str` or `int`).
- `text`: Human-friendly description.
- `default`: Optional default primitive.
- Additional metadata via `meta` when using `VariableEnum`.

Enums consume these dataclasses so every member exposes `.text`, `.default`,
and any extra attributes you attach.

### Cached Lookups

`BaseEnumMixin` builds cached mapping proxies for value, name, and text.
Utility methods rely on those caches to keep lookups cheap:

```python
style = FontStyle.get("dotted")          # case-insensitive by name
style = FontStyle.get("·")               # by text
FontStyle.keys()                         # -> tuple of names
FontStyle.from_value("solid")            # direct lookup
```

`RichIntEnum.get` supports both ints and strings, while `RichStrEnum.get`
accepts enum instances, raw strings, or text descriptors. Pass `default=` to
opt into graceful fallbacks instead of raising.

---

## RichStrEnum & RichIntEnum

Define members with the corresponding value dataclass:

```python
from funcy_bear.rich_enums import RichStrEnum, StrValue

class Mode(RichStrEnum):
    SILENT = StrValue("silent", "Lowest output")
    VERBOSE = StrValue("verbose", "Extra diagnostics")

assert Mode.SILENT.text == "Lowest output"
assert Mode.get("verbose") is Mode.VERBOSE
```

For `RichIntEnum`, swap in `IntValue`:

```python
from funcy_bear.rich_enums import RichIntEnum, IntValue

class ExitCode(RichIntEnum):
    SUCCESS = IntValue(0, "Success")
    FAILURE = IntValue(1, "Failure")

assert ExitCode.from_int(1) is ExitCode.FAILURE
assert ExitCode.int_to_text(3) == "Unknown value"
```

---

## VariableEnum

When a simple value/label isn’t enough, `VariableEnum` couples a string value
with a Pydantic model (`VariableType`) that describes how to parse and validate
the underlying data.

```python
from funcy_bear.rich_enums import VariableEnum, VariableType, VariableValue

class EnvVarMeta(VariableType[int]):
    parser = int
    description = "Max retries"
    required = True
    default = 3

class EnvVars(VariableEnum):
    RETRIES = VariableValue("MAX_RETRIES", "Retry limit", EnvVarMeta())

assert EnvVars.RETRIES.parser("42") == 42
assert EnvVars.RETRIES.required is True
```

Accessing `.parser`, `.description`, or any custom fields forwards directly to
the Pydantic model (`meta`), keeping usage ergonomic.

---

## Tips
- Favor `.get(value, default=...)` when reading untrusted input to avoid
  exceptions.
- `VariableEnum` members are still strings—safe for env var names and config
  keys—so they integrate seamlessly with Typer/Click options.
- Reuse these enums throughout the project (logging themes, CLI styles,
  config schema) to keep docs and generated UIs consistent.

Enums, but make them fancy, Bear! 🎨🧮🐻
