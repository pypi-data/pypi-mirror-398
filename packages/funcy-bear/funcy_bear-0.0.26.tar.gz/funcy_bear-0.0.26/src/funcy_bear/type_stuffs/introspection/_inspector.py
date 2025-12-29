from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from functools import cached_property
from inspect import (
    Signature,
    cleandoc,
    getdoc,
    getfile,
    isbuiltin,
    isclass,
    iscoroutinefunction,
    isfunction,
    ismethod,
    ismodule,
    signature,
)
from typing import TYPE_CHECKING, Any, Final, Literal, Self

from rich.control import escape_control_codes
from rich.highlighter import ReprHighlighter
from rich.text import Text

from funcy_bear.constants.characters import SINGLE_TRIPLE_QUOTE, TRIPLE_QUOTE, UNDERSCORE
from funcy_bear.ops.curried_ops import ends_with, starts_with
from funcy_bear.ops.func_stuffs import all_of
from funcy_bear.tools import Names
from funcy_bear.type_stuffs.introspection._helpers import ParamWrapper

TWO_UNDERSCORES: Final[str] = UNDERSCORE * 2

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterator
    from inspect import Signature

PrefixLiteral = Literal["class", "async def", "def"]

repr_highlighter = ReprHighlighter()


def single_line_docstring(line: str) -> bool:
    """Return True if the docstring is a single line.

    That is, if it starts with triple quotes and ends with triple quotes on the same line.
    """
    stripped: str = line.strip()
    triple_quote_count: int = stripped.count(TRIPLE_QUOTE)
    single_quote_count: int = stripped.count(SINGLE_TRIPLE_QUOTE)
    string: str = SINGLE_TRIPLE_QUOTE if single_quote_count > 0 and triple_quote_count == 0 else TRIPLE_QUOTE
    return stripped.count(string) >= 2 and stripped.startswith(string) and stripped.endswith(string)


@dataclass
class ObjectKey:
    """A tuple representing an object's attribute with its name and Value."""

    name: str
    error: Exception | None = None
    value: Any = None

    def as_tuple(self) -> tuple[str, tuple[Any, Any]]:
        """Return the ObjectKey as a tuple."""
        return (self.name, (self.error, self.value))

    @property
    def is_callable(self) -> bool:
        """Check if the value is callable."""
        return callable(self.value)

    @property
    def is_class(self) -> bool:
        """Check if the value is a class."""
        return isclass(self.value)

    @property
    def is_coroutine_function(self) -> bool:
        """Check if the value is a coroutine function."""
        return iscoroutinefunction(self.value)

    @property
    def is_function(self) -> bool:
        """Check if the value is a function."""
        return isfunction(self.value)

    @property
    def is_module(self) -> bool:
        """Check if the value is a module."""
        return ismodule(self.value)

    @property
    def is_dunder(self) -> bool:
        """Check if the name is a dunder (double underscore) attribute."""
        return self.name.startswith(TWO_UNDERSCORES) and self.name.endswith(TWO_UNDERSCORES)

    @property
    def is_property(self) -> bool:
        """Check if the value is a property."""
        return isinstance(self.value, property)

    @property
    def is_method(self) -> bool:
        """Check if the value is a method."""
        return ismethod(self.value)

    @property
    def is_attribute(self) -> bool:
        """Check if the value is a non-callable attribute."""
        return not any(
            (self.is_callable, self.is_property, self.is_class, self.is_module, self.is_function, self.is_method)
        )

    @property
    def is_builtin(self) -> bool:
        """Check if the value is a built-in function or method."""
        return (
            isbuiltin(self.value)
            or str(type(self.value)).startswith("<class 'builtin_function_or_method'>")
            or isinstance(self.value, type)
        )

    @cached_property
    def _signature(self) -> Signature | None:
        if (not self.is_callable and not self.is_property) or self.is_builtin:
            return None
        from funcy_bear.type_stuffs.introspection.general import get_function_signature  # noqa: PLC0415

        if not self.is_property:
            return get_function_signature(self.value)
        return get_function_signature(self.value.fget)

    @cached_property
    def parameters(self) -> dict[str, ParamWrapper] | None:
        """Get the parameters of the value if it's a function.

        Returns:
            dict[str, ParamWrapper] | None: A dictionary of parameter names to ParamWrapper instances,
            or None if the value is not a function.
        """
        if not self.is_function and not self.is_property:
            return None
        if self._signature is None:
            return None
        return {name: ParamWrapper(param) for name, param in self._signature.parameters.items()}

    @cached_property
    def return_annotation(self) -> Any | None:
        """Get the return annotation of the value if it's a function."""
        if not self.is_function and not self.is_property:
            return None
        if self._signature is None:
            return None
        return self._signature.return_annotation

    @cached_property
    def text_signature(self) -> Text | None:
        """Get the signature of the value if it's callable."""
        if not self.is_callable and not self.is_property:
            return None
        sig: Signature | None = self._signature
        if sig is None:
            return None
        _sig = str(sig).replace("'", "")
        return repr_highlighter(_sig)

    @cached_property
    def docs(self) -> Text | None:
        """Get the docstring of the value if available."""
        _doc: str | None = getdoc(self.value)
        if _doc is not None:
            doc: str = cleandoc(_doc).strip()
            doc_text = Text(doc, style="inspect.help")
            doc_text: Text = repr_highlighter(doc_text)
            return doc_text
        return None

    @cached_property
    def source(self) -> list[str] | None:
        """Get the source code of the value if available."""
        import inspect  # noqa: PLC0415

        pop_true: bool = False
        try:
            val: Any = self.value.fget if self.is_property else self.value
            lines: list[str] = inspect.getsourcelines(val)[0]
            values: list[str] = []
            for value in lines:
                stripped: str = value.strip()
                if stripped.startswith(("@", "def ", "class ", "async def ")):
                    continue
                if TRIPLE_QUOTE in stripped or SINGLE_TRIPLE_QUOTE in stripped:
                    if single_line_docstring(value):
                        continue
                    pop_true = not pop_true  # begin or end of docstring
                    continue
                if not pop_true:
                    values.append(value.replace("\n", ""))
            return values
        except Exception:
            return None

    def __str__(self) -> str:
        return f"{self.name}{self.text_signature or ''}"

    def to_dict(self) -> dict[str, Any]:
        """Convert the ObjectKey to a dictionary."""
        return {
            "name": self.name,
            "value": repr(self.value),
            "is_callable": self.is_callable,
            "is_class": self.is_class,
            "is_method": self.is_method,
            "is_coroutine": self.is_coroutine_function,
            "is_function": self.is_function,
            "is_module": self.is_module,
            "is_dunder": self.is_dunder,
            "is_property": self.is_property,
            "is_attribute": self.is_attribute,
            "signature": str(self.text_signature) if self.text_signature else "null",
            "parameters": {k: str(v.annotation) for k, v in (self.parameters or {}).items()},
            "return_annotation": self.return_annotation,
            "source": self.source or "",
            "docs": str(self.docs) if self.docs else "",
        }

    def to_json(self, indent: int = 4, sort: bool = False) -> str:
        """Convert the ObjectKey to a JSON string."""
        import json  # noqa: PLC0415

        return json.dumps(self.to_dict(), indent=indent, sort_keys=sort)


class ObjectKeys(Names[ObjectKey]):
    """A Namespace of ObjectKey representing an object's attributes."""

    def __iter__(self) -> Iterator[tuple[str, ObjectKey]]:
        yield from self.items()

    @classmethod
    def from_keys(cls, keys: Collection[str]) -> ObjectKeys:
        """Create an ObjectKeys instance from a collection of keys."""
        obj_keys: Self = cls()
        for key in keys:
            obj_keys.add(key, ObjectKey(key))
        return obj_keys

    def update_key(self, key: str, error: Exception | None, value: Any) -> None:
        """Update an existing ObjectKey in the ObjectKeys.

        Args:
            key (str): The name of the attribute to update.
            error (Exception | None): The error encountered when accessing the attribute, if any.
            value (Any): The value of the attribute.
        """
        obj_key: ObjectKey = self.get(key, strict=True)
        obj_key.error = error
        obj_key.value = value

    def filter_out_by_key(self, *predicates: Callable[..., bool]) -> None:
        """Filter the ObjectKeys by a predicate.

        Args:
            predicates (Callable[[str], bool]): One or more predicate functions to filter the keys.
        """
        for key in self.keys():
            if all(predicate(key) for predicate in predicates):
                self.remove(key)


class DoInspect:
    """An inspector for any Python Object.

    Args:
        obj (Any): An object to inspect.
        title (str, optional): Title to use, defaults to None.
        help (bool, optional): Capture full help text rather than just first paragraph. Defaults to False.
        methods (bool, optional): Enable inspection of callables. Defaults to False.
        docs (bool, optional): Also capture doc strings. Defaults to True.
        private (bool, optional): Capture private attributes (beginning with underscore). Defaults to False.
        dunder (bool, optional): Capture attributes starting with double underscore. Defaults to False.
        all (bool, optional): Capture all attributes. Defaults to False.
        value (bool, optional): Capture value of object. Defaults to True.
    """

    def __init__(
        self,
        obj: Any,
        *,
        title: str | None = None,
        help: bool = False,
        methods: bool = False,
        docs: bool = True,
        private: bool = False,
        dunder: bool = False,
        all: bool = False,
        value: bool = True,
    ) -> None:
        self.obj: Any = obj
        self.obj_key = ObjectKey(name=str(obj), value=obj)
        self.title: str = title or get_title(obj)
        if all:
            methods = private = dunder = True
        self.help: bool = help
        self.methods: bool = methods
        self.get_docs: bool = docs or help
        self.private: bool = private or dunder
        self.dunder: bool = dunder
        self.get_value: bool = value
        self._obj_keys: ObjectKeys | None = None

    @cached_property
    def keys(self) -> list[str]:
        return list(dir(self.obj))

    @cached_property
    def total_count(self) -> int:
        return len(self.keys)

    def obj_keys(self) -> ObjectKeys:
        """Get the object's attributes as a list of ObjectKeys.

        Returns:
            ObjectKeys: A list of ObjectKeys representing the object's attributes.
        """
        if self._obj_keys is None:

            def safe_getattr(key: str, obj: ObjectKey) -> None:
                """Safely get the attribute value and error for an ObjectKey."""
                try:
                    obj.value = getattr(self.obj, key)
                except Exception as e:
                    obj.error = e

            privates: Callable[..., bool] = starts_with(prefix=UNDERSCORE)
            dunder_start: Callable[..., bool] = starts_with(prefix=TWO_UNDERSCORES)
            dunder_end: Callable[..., bool] = ends_with(suffix=TWO_UNDERSCORES)
            items: ObjectKeys = ObjectKeys.from_keys(self.keys)
            if not self.private:
                items.filter_out_by_key(privates)
            if not self.dunder:
                items.filter_out_by_key(all_of(dunder_start, dunder_end))
            for key, obj in items:
                safe_getattr(key, obj)
            self._obj_keys = items
        return self._obj_keys

    @cached_property
    def obj_keys_count(self) -> int:
        return len(self.obj_keys())

    @cached_property
    def is_callable(self) -> bool:
        """Check if the inspected object is callable."""
        return callable(self.obj)

    @cached_property
    def signature(self) -> Text | None:
        """Get the signature of the inspected object, if it's callable."""
        if not self.is_callable:
            return None
        return get_signature(self.title, self.obj)

    @cached_property
    def docs(self) -> Text | None:
        """Get the docstring of the inspected object, if available."""
        _doc: str | None = get_formatted_doc(self.obj, self.help)
        if _doc is not None:
            doc_text = Text(_doc, style="inspect.help")
            doc_text: Text = repr_highlighter(doc_text)
            return doc_text
        return None

    @cached_property
    def value(self) -> Text:
        obj: Any = self.obj
        if self.get_value and not (isclass(obj) or callable(obj) or ismodule(obj)):
            return repr_highlighter(repr(obj))
        return Text("")


def get_formatted_doc(object_: Any, help: bool) -> str | None:
    """Extract the docstring of an object, process it and returns it.

    The processing consists in cleaning up the docstring's indentation,
    taking only its 1st paragraph if `self.help` is not True,
    and escape its control codes.

    Args:
        object_ (Any): the object to get the docstring from.

    Returns:
        str | None: the processed docstring, or None if no docstring was found.
    """
    docs: str | None = getdoc(object_)
    if docs is None:
        return None
    docs = cleandoc(docs).strip()
    if not help:
        docs = first_paragraph(docs)
    return escape_control_codes(docs)


def get_signature(name: str, obj: Any) -> Text:
    """Get a signature for a callable.

    Args:
        name (str): The name of the callable.
        obj (Any): The callable object.
        highlighter (ReprHighlighter): A highlighter to use for syntax highlighting.

    Returns:
        Text | None: The signature as a Text object, or None if it cannot be obtained
    """
    try:
        _signature: str = str(signature(obj)) + ":"
    except ValueError:
        _signature = "(...)"
    except TypeError:
        return Text("NONE")

    source_filename: str | None = None
    with suppress(Exception):
        source_filename = getfile(obj)

    callable_name = Text(name, style="inspect.callable")
    if source_filename:
        callable_name.stylize(f"link file://{source_filename}")

    signature_text: Text = repr_highlighter(_signature)
    qualname: str = name or getattr(obj, "__qualname__", name)
    # If obj is a module, there may be classes (which are callable) to display
    prefix: PrefixLiteral = "class" if isclass(obj) else "async def" if iscoroutinefunction(obj) else "def"
    return Text.assemble(
        (f"{prefix} ", f"inspect.{prefix.replace(' ', '_')}"),
        (qualname, "inspect.callable"),
        signature_text,
    )


def get_title(obj: Any) -> str:
    return repr_highlighter(str(obj) if (isclass(obj) or callable(obj) or ismodule(obj)) else str(type(obj))).plain


def class_name(obj: Any) -> str:
    """Get the class name of an object."""
    if isclass(obj) and hasattr(obj, "__class__"):
        return obj.__class__.__name__
    return type(obj).__name__


def first_paragraph(doc: str) -> str:
    """Get the first paragraph from a docstring."""
    paragraphs: tuple[str, str, str] = doc.partition("\n\n")
    return paragraphs[0].strip()


def get_object_types_mro(obj: object | type[Any]) -> tuple[type, ...]:
    """Returns the MRO of an object's class, or of the object itself if it's a class."""
    if not hasattr(obj, "__mro__"):
        # N.B. we cannot use `if type(obj) is type` here because it doesn't work with
        # some types of classes, such as the ones that use abc.ABCMeta.
        obj = type(obj)
    return getattr(obj, "__mro__", ())


def get_object_types_mro_as_strings(obj: object) -> Collection[str]:
    """Returns the MRO of an object's class as full qualified names, or of the object itself if it's a class.

    Examples:
        `object_types_mro_as_strings(JSONDecoder)` will return `['json.decoder.JSONDecoder', 'builtins.object']`
    """
    return [
        f"{getattr(type_, '__module__', '')}.{getattr(type_, '__qualname__', '')}"
        for type_ in get_object_types_mro(obj)
    ]


def is_object_one_of_types(obj: object, fully_qualified_types_names: Collection[str]) -> bool:
    """Returns `True` if the given object's class has one of the fully qualified names in its MRO."""
    return any(type_name in fully_qualified_types_names for type_name in get_object_types_mro_as_strings(obj))


# ruff: noqa: A002 PLR2004
