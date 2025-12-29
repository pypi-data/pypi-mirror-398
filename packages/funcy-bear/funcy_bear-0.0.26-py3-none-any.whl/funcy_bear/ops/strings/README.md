# funcy_bear.ops.strings

String utilities for flattening nested data, templating with dotted keys, and
massaging identifiers into friendly cases. These helpers power a lot of the
CLI text formatting scattered across the project.

## Modules
- `flatten_data.py`: Breadth-first flattening of mappings/sequences into
  `prefix: value` strings via the `FlattenPower` class and `flatten()` helper.
- `manipulation.py`: Case conversion, slugging, truncation, and casing
  detection utilities (`CaseConverter`, `slugify`, `to_snake`, etc.).
- `dot_template.py`: `DotTemplate` subclass of `string.Template` that dives
  through nested dictionaries. Includes helpers like `cache_unique()` to reuse
  key sets.
- `sorting_name.py`: Helpers for friendly sorting key generation (detailed
  below).

---

## Flattening Data

```python
from funcy_bear.ops.strings import flatten

payload = {"user": {"name": "Bear", "roles": ["admin", "friend"]}}
flattener = flatten(payload, prefix="session")

as_string = flattener.get()          # "session.user.name: Bear\nsession.user.roles[0]: admin..."
as_list = flattener.get(combine=False)
```

`FlattenPower` stores intermediate rows in `working_data`, so you can craft
custom joins or reuse the results multiple times without re-traversing.

---

## Case Conversion & Slugging

```python
from funcy_bear.ops.strings import slugify, to_camel, detect_case, truncate

slug = slugify("Bear hugs & beyond!")           # "bear-hugs-beyond"
camel = to_camel("bear_hugs")                   # "bearHugs"
case = detect_case("SCREAMING_SNAKE")           # "screaming_snake"
preview = truncate("Hibernate longer, bear!", 12)   # "Hibernate..."
```

`CaseConverter` auto-detects input casing before converting, so `to_snake` and
friends accept camel, Pascal, kebab, or screaming snake out of the box.

---

## Dot-Aware Templates

`DotTemplate.safe_substitute` flattens nested dicts (optionally with a
pre-cached set of keys) before performing substitution—perfect for log
formatting pipelines.

```python
from string import Template
from funcy_bear.ops.strings.dot_template import DotTemplate, cache_unique

context = {"payload": {"id": "42", "status": "warm"}}
template = DotTemplate("ID=$id - payload status=$status")
unique = cache_unique(template)

print(template.safe_substitute(context, unique_keys=unique))
```

---

## Sorting Names

`sorting_name.py` normalizes titles so UI lists behave nicely:

```python
from funcy_bear.ops.strings.sorting_name import sorting_name, SortingNameTool

assert sorting_name("The Legend of Zelda") == "Legend of Zelda"
assert sorting_name("Final Fantasy VII", roman=True) == "Final Fantasy 07"

tool = SortingNameTool("Resident Evil IV", roman=True, alphanum=True)
assert tool.sorting_name() == "Resident Evil 04"
```

Options include:
- `article_filter`: drop leading articles (`The`, `A`, `An`) by default.
- `roman`: convert trailing Roman numerals to zero-padded digits.
- `alphanum`: strip punctuation while preserving spaces.
- `sortable_nums`: pad digits (`3` → `03`) so lexical sorting matches numeric ordering.

---

## Misc Tools
- `to_lines(raw)` strips blank lines from a blob of text.
- `join_dicts([...])` outputs newline-separated JSON strings—handy for JSONL
  emissions.
- `sorting_name` (function + class) produce normalized keys for sorting names.

Keep those strings silky smooth, Bear! 🧵🐻✨
