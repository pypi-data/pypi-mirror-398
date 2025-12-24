"""TypedProtocol: Strict runtime type checking for Python protocols."""

import abc
import inspect
import sys
import typing

if sys.version_info >= (3, 13):
    from typing import TypeVar
else:
    from typing_extensions import TypeVar

from .method_checker import MethodChecker
from .substitution import SubstitutedMethod, TypeVarSubstitutor
from .type_checker import TypeChecker


class TypedProtocolMeta(abc.ABCMeta):
    """Metaclass for TypedProtocol with strict type checking."""

    def validate_annotations(cls) -> None:
        """Validate that all protocol members have proper type annotations."""
        annotations = getattr(cls, "__annotations__", {})
        for attr_name in dir(cls):
            if attr_name.startswith("_"):
                continue

            attr_value = getattr(cls, attr_name)
            if callable(attr_value):
                method_sig = inspect.signature(attr_value)
                for param_name, param in method_sig.parameters.items():
                    if param_name != "self" and param.annotation is param.empty:
                        raise TypeError(
                            f"Parameter '{param_name}' in method '{attr_value.__name__}' of TypedProtocol '{cls.__name__}' must have a type annotation."
                        )

            elif attr_name not in annotations:
                # Allow types
                if isinstance(attr_value, type):
                    return

                # Check for generic aliases (like List[str], Dict[str, int])
                if hasattr(attr_value, "__origin__"):
                    return

                raise TypeError(
                    f"Attribute '{attr_name}' in TypedProtocol '{cls.__name__}' must have a type annotation."
                )

    def __new__(
        cls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, typing.Any],
        **kwargs: typing.Any,
    ) -> type:
        namespace["__slots__"] = ()
        new_class = super().__new__(cls, name, bases, namespace, **kwargs)

        if name == "TypedProtocol" and bases == (typing.Generic,):
            return new_class

        for base in bases:
            if hasattr(typing, "get_origin") and typing.get_origin(base) is typing.Generic:
                continue
            if base is typing.Generic:
                continue
            if base is not TypedProtocol and not isinstance(base, TypedProtocolMeta):
                raise TypeError(
                    f"TypedProtocol '{name}' cannot inherit from non-protocol type '{base.__name__}'. "
                    f"TypedProtocols can only inherit from other TypedProtocols."
                )
        new_class.validate_annotations()
        return new_class

    def __call__(cls, *args: typing.Any, **kwargs: typing.Any) -> typing.NoReturn:  # noqa: ARG002
        """Prevent instantiation of all TypedProtocol classes."""
        raise TypeError(
            f"Cannot instantiate protocol class {cls.__name__}. "
            f"Protocols define interfaces and cannot be instantiated directly."
        )

    def __subclasscheck__(cls, subclass: type) -> bool:  # noqa: C901
        """Check if subclass properly implements all protocol requirements with correct types."""
        if cls is TypedProtocol:
            return super().__subclasscheck__(subclass)

        type_var_mapping: dict[TypeVar, typing.Any] = {}
        protocol_annotations: dict[str, typing.Any] = {}
        subclass_annotations: dict[str, typing.Any] = {}
        protocol_methods: dict[str, typing.Callable[..., typing.Any]] = {}

        substitutions = TypeVarSubstitutor.build_substitutions(cls)

        for base in reversed(cls.__mro__):
            if base is not TypedProtocol:
                if hasattr(base, "__annotations__"):
                    for attr_name, attr_type in base.__annotations__.items():
                        if substitutions:
                            protocol_annotations[attr_name] = TypeVarSubstitutor.substitute(
                                attr_type, substitutions
                            )
                        else:
                            protocol_annotations[attr_name] = attr_type

                for attr_name in dir(base):
                    if not attr_name.startswith("_"):
                        attr_value = getattr(base, attr_name)
                        if callable(attr_value) and hasattr(attr_value, "__annotations__"):
                            if substitutions:
                                original_annotations = getattr(attr_value, "__annotations__", {})
                                substituted_annotations = {
                                    param: TypeVarSubstitutor.substitute(param_type, substitutions)
                                    for param, param_type in original_annotations.items()
                                }
                                protocol_methods[attr_name] = SubstitutedMethod(
                                    attr_value, substituted_annotations
                                )
                            else:
                                protocol_methods[attr_name] = attr_value
        # Collect subclass annotations from MRO
        for base in reversed(subclass.__mro__):
            subclass_annotations.update(getattr(base, "__annotations__", {}))
        # Check annotations
        for attr_name, expected_type in protocol_annotations.items():
            if attr_name in protocol_methods:
                continue

            if attr_name not in subclass_annotations:
                return False

            actual_type = subclass_annotations[attr_name]
            if not TypeChecker.is_compatible_with_unification(
                actual_type, expected_type, type_var_mapping
            ):
                return False

        # Check methods
        for method_name, protocol_method in protocol_methods.items():
            if not hasattr(subclass, method_name) or not callable(getattr(subclass, method_name)):
                return False

            subclass_method = getattr(subclass, method_name)
            if not MethodChecker.are_compatible_with_unification(
                subclass_method, protocol_method, type_var_mapping
            ):
                return False

        return True


T = TypeVar("T", default=object)


class TypedProtocol(typing.Generic[T], metaclass=TypedProtocolMeta):  # noqa: UP046
    """Base class for all typed protocols."""

    ...
