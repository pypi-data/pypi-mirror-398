from __future__ import annotations

from dataclasses import dataclass
from inspect import Parameter
from typing import TYPE_CHECKING, Any, Literal, get_args, get_origin

from funcy_bear.type_stuffs import validate as val

if TYPE_CHECKING:
    from inspect import _ParameterKind  # type: ignore[import]

ParamKind = Literal["POSITIONAL_ONLY", "POSITIONAL_OR_KEYWORD", "VAR_POSITIONAL", "KEYWORD_ONLY", "VAR_KEYWORD"]


@dataclass(slots=True)
class ParamWrapper:
    """A wrapper around a Parameter to provide type introspection utilities."""

    param: Parameter

    @classmethod
    def new(cls, name: str, annotation: Any, kind: ParamKind = "POSITIONAL_OR_KEYWORD") -> ParamWrapper:
        """Create a new ParamWrapper instance.

        Args:
            name (str): The name of the parameter.
            annotation (Any): The type annotation of the parameter.
            kind (ParamKind, optional): The kind of the parameter. Defaults to "POSITIONAL_OR_KEYWORD".

        Returns:
            ParamWrapper: A new instance of ParamWrapper.
        """
        kind_value: _ParameterKind = getattr(Parameter, kind)
        param = Parameter(name=name, kind=kind_value, annotation=annotation)
        return cls(param)

    @property
    def annotation(self) -> Any:
        """Get the annotation of the parameter.

        Examples:
            >>> from inspect import Parameter
            >>> from funcy_bear.type_stuffs.validators.helpers import ParamWrapper
            >>> param = Parameter(
            ...     name="x", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=int
            ... )
            >>> wrapper = ParamWrapper(param)
            >>> wrapper.annotation
            <class 'int'>

        Returns:
            Any: The annotation of the parameter
        """
        return self.param.annotation

    @property
    def name(self) -> str:
        """Get the name of the parameter."""
        return self.param.name

    @property
    def kind(self) -> _ParameterKind:
        """Access the kind of the parameter.

        Examples:
            >>> from inspect import Parameter
            >>> from funcy_bear.type_stuffs.validators.helpers import ParamWrapper
            >>> param = Parameter(
            ...     name="x", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=int
            ... )
            >>> wrapper = ParamWrapper(param)
            >>> wrapper.kind
            <_ParameterKind.POSITIONAL_OR_KEYWORD: 1>

        Returns:
            _ParameterKind: The kind of the parameter.
        """
        return self.param.kind

    @property
    def is_typed(self) -> bool:
        """Check if the parameter has a type annotation.

        Examples:
            >>> from inspect import Parameter
            >>> from funcy_bear.type_stuffs.validators.helpers import ParamWrapper
            >>> param = Parameter(
            ...     name="x", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=int
            ... )
            >>> wrapper = ParamWrapper(param)
            >>> wrapper.is_typed
            True

        Returns:
            bool: True if the parameter has a type annotation, False otherwise.
        """
        return val.is_typed(self.annotation)

    @property
    def is_str(self) -> bool:
        """Check if the parameter's annotation is a string type."""
        return val.is_str(self.annotation)

    @property
    def is_union(self) -> bool:
        """Check if the parameter's annotation is a Union type."""
        return val.is_union(self.annotation)

    @property
    def is_annotated(self) -> bool:
        """Check if the parameter's annotation is an Annotated type."""
        return val.is_annotated(self.annotation)

    @property
    def is_generic(self) -> bool:
        """Check if the parameter's annotation is a GenericAlias type."""
        return val.is_generic_alias(self.annotation)

    @property
    def is_generic_callable(self) -> bool:
        """Check if the parameter's annotation is a generic Callable type."""
        return val.is_generic_callable(self.annotation)

    @property
    def is_concrete(self) -> bool:
        """Check if the parameter's annotation is a concrete (non-generic) type."""
        return not self.is_generic

    @property
    def origin(self) -> Any | None:
        """Get the origin of the parameter's annotation."""
        return get_origin(self.annotation)

    @property
    def args(self) -> tuple[Any, ...]:
        """Get the type arguments of the parameter's annotation."""
        return get_args(self.annotation)

    def from_annotation(self, annotation: Any) -> None:
        """Create a new ParamWrapper from the given annotation.

        Args:
            annotation (Any): The new annotation to use.
        """
        self.param = Parameter(name=self.param.name, kind=self.param.kind, annotation=annotation)

    def first_arg(self) -> Any | None:
        """Get the first type argument of the parameter's annotation.

        Returns:
            Any | None: The first type argument, or None if there are no arguments.
        """
        if args := self.args:
            return args[0]
        return None

    def unwrap_first(self) -> ParamWrapper:
        """Unwrap the first type argument of the parameter's annotation.

        Returns:
            ParamWrapper: A new ParamWrapper with the first type argument as its annotation.
        """
        first: Any | None = self.first_arg()
        if first is not None:
            return ParamWrapper(Parameter(name=self.param.name, kind=self.param.kind, annotation=first))
        raise ValueError("No type arguments to unwrap.")
