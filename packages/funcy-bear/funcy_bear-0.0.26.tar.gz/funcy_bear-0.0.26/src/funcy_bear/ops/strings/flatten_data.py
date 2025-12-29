"""Functions for flattening nested data structures into key-value pairs."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from typing import Any, NamedTuple, overload

from funcy_bear.constants.type_constants import ArrayLike, LitFalse, LitTrue


class ToFlatten(NamedTuple):
    """A helper class to hold data and its prefix for flattening."""

    data: Mapping | ArrayLike | Any
    prefix: str = ""


class FlattenPower:
    """A class to flatten nested data structures into key-value pairs."""

    def __init__(self, data: Mapping | ArrayLike | Any, prefix: str = "", end: str = "\n") -> None:
        """A class to flatten nested data structures into key-value pairs."""
        if not isinstance(data, (Mapping | ArrayLike)):
            raise TypeError("Data must be a Mapping or ArrayLike")
        self.end: str = end
        self.data: Mapping | ArrayLike = data
        self.prefix: str = prefix
        self.stack: deque[ToFlatten] = deque([ToFlatten(data, prefix)])
        self.working_data: list[str] = []

    def _process_mapping(self, data: Mapping, prefix: str) -> None:
        """Process a mapping (dictionary) and flatten its contents."""
        for key, value in data.items():
            new_prefix: str = f"{prefix}.{key}" if prefix else f"{key}"
            if isinstance(value, (Mapping | ArrayLike)):
                self.stack.append(ToFlatten(value, new_prefix))
            else:
                self.working_data.append(f"{new_prefix}: {value}")

    def _process_array_like(self, data: ArrayLike, prefix: str) -> None:
        """Process an array-like structure (list, tuple, set) and flatten its contents."""
        for i, item in enumerate(data):
            new_prefix: str = f"{prefix}[{i}]" if prefix else f"[{i}]"
            if isinstance(item, (Mapping | ArrayLike)):
                self.stack.append(ToFlatten(item, new_prefix))
            else:
                self.working_data.append(f"{new_prefix}: {item}")

    def flatten(self) -> None:
        """Flatten the data structure."""
        while self.stack:
            current: ToFlatten = self.stack.popleft()

            if isinstance(current.data, Mapping):
                self._process_mapping(current.data, current.prefix)
            elif isinstance(current.data, ArrayLike):
                self._process_array_like(current.data, current.prefix)

    @property
    def output_str(self) -> str:
        """Get the flattened data as a single string."""
        return f"{self.end}".join(self.working_data)

    @overload
    def get(self, combine: LitTrue = True) -> str: ...
    @overload
    def get(self, combine: LitFalse) -> list[str]: ...

    def get(self, combine: bool = True) -> str | list[str]:
        """Get the flattened data as a list of strings or a single string.

        Args:
            combine (bool): If True, return a single string. If False, return a list
        """
        return self.output_str if combine else self.working_data


def flatten(data: Mapping | ArrayLike | Any, prefix: str = "") -> FlattenPower:
    """Flatten nested data structures into key-value pairs.

    Args:
        data (Mapping | ArrayLike | Any): The data to flatten.
        prefix (str): An optional prefix to prepend to each flattened value.

    Returns:
        FlattenPower: An instance of FlattenPower for further processing.
    """
    flattener = FlattenPower(data, prefix)
    flattener.flatten()
    return flattener


# if __name__ == "__main__":
#     sample_data = {
#         "name": "Alice",
#         "age": 30,
#         "address": {
#             "street": "123 Main St",
#             "city": "Wonderland",
#             "coordinates": [34.0522, -118.2437],
#         },
#         "hobbies": ["reading", "traveling", {"type": "sports", "name": "tennis"}],
#     }

#     flattener = flatten(sample_data, prefix="user")
#     var = flattener.get(combine=True)
#     var2 = flattener.get(combine=False)
#     print(var)
#     print(var2)
