"""TypeVar substitution utilities for generic protocol inheritance."""

import sys
import typing
from collections.abc import Mapping

if sys.version_info >= (3, 13):
    from typing import TypeVar
else:
    from typing_extensions import TypeVar


class TypeVarSubstitutor:
    """Handles TypeVar substitution in generic protocol inheritance."""

    @staticmethod
    def build_substitutions(protocol_cls: type) -> dict[TypeVar, TypeVar]:
        """Build TypeVar substitution mapping from generic inheritance."""
        substitutions: dict[TypeVar, TypeVar] = {}

        if hasattr(protocol_cls, "__orig_bases__"):
            orig_bases: tuple[typing.Any, ...] = getattr(protocol_cls, "__orig_bases__", ())
            for base in orig_bases:
                origin = typing.get_origin(base)
                args = typing.get_args(base)

                if origin and args and hasattr(origin, "__parameters__"):
                    params = origin.__parameters__
                    if len(params) == len(args):
                        for p, a in zip(params, args, strict=False):
                            if isinstance(p, TypeVar) and isinstance(a, TypeVar):
                                substitutions[p] = a

        return substitutions

    @staticmethod
    def substitute(
        type_annotation: typing.Any, substitutions: Mapping[TypeVar, typing.Any]
    ) -> typing.Any:
        """Substitute TypeVars in a type annotation using the substitution mapping."""
        if not substitutions:
            return type_annotation

        # Handle TypeVar directly
        if isinstance(type_annotation, TypeVar):
            return substitutions.get(type_annotation, type_annotation)

        # Handle generic types (e.g., List[T])
        if hasattr(typing, "get_origin") and hasattr(typing, "get_args"):
            origin = typing.get_origin(type_annotation)
            args = typing.get_args(type_annotation)

            if origin and args:
                new_args = tuple(TypeVarSubstitutor.substitute(arg, substitutions) for arg in args)
                if new_args != args:
                    return origin[new_args] if hasattr(origin, "__getitem__") else type_annotation

        return type_annotation


class SubstitutedMethod:
    """Wrapper for methods with substituted type annotations."""

    def __init__(
        self,
        original_method: typing.Callable[..., typing.Any],
        substituted_annotations: dict[str, typing.Any],
    ) -> None:
        self.__annotations__: dict[str, typing.Any] = substituted_annotations
        self.original_method: typing.Callable[..., typing.Any] = original_method

        # Copy important attributes
        if hasattr(original_method, "__name__"):
            self.__name__: str = original_method.__name__
        if hasattr(original_method, "__qualname__"):
            self.__qualname__: str = original_method.__qualname__

    def __call__(self, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        return self.original_method(*args, **kwargs) if callable(self.original_method) else None
