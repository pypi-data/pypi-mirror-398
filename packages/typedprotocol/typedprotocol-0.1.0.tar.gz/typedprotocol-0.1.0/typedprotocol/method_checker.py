"""Method signature compatibility checking."""

import inspect
import sys
import typing

if sys.version_info >= (3, 13):
    from typing import TypeVar
else:
    from typing_extensions import TypeVar
from .substitution import SubstitutedMethod
from .type_checker import TypeChecker


class MethodChecker:
    """Handles method signature compatibility checking."""

    @staticmethod
    def are_compatible_with_unification(  # noqa: C901
        actual_method: typing.Callable[..., typing.Any],
        protocol_method: typing.Callable[..., typing.Any],
        type_var_mapping: dict[TypeVar, typing.Any],
    ) -> bool:
        """Check if method signatures are compatible with TypeVar unification."""
        try:
            actual_sig = inspect.signature(actual_method)

            # Handle SubstitutedMethod specially
            if isinstance(protocol_method, SubstitutedMethod):
                protocol_sig = inspect.signature(protocol_method.original_method)
                protocol_annotations = getattr(protocol_method, "__annotations__", {})
            else:
                protocol_sig = inspect.signature(protocol_method)
                protocol_annotations = getattr(protocol_method, "__annotations__", {})

            # Check async compatibility
            if inspect.iscoroutinefunction(actual_method) != inspect.iscoroutinefunction(
                protocol_method
            ):
                return False

            actual_annotations = getattr(actual_method, "__annotations__", {})

            # Check parameter compatibility
            actual_params = list(actual_sig.parameters.values())
            protocol_params = list(protocol_sig.parameters.values())

            if len(actual_params) != len(protocol_params):
                return False

            for actual_param, protocol_param in zip(actual_params, protocol_params, strict=False):
                if actual_param.name != protocol_param.name:
                    return False

                actual_param_type = actual_annotations.get(actual_param.name)
                protocol_param_type = protocol_annotations.get(protocol_param.name)

                if protocol_param_type is not None:
                    if actual_param_type is None:
                        return False
                    # Parameters are contravariant: actual should be supertype of expected
                    if not TypeChecker.is_compatible_with_unification(
                        actual_param_type,
                        protocol_param_type,
                        type_var_mapping,
                        contravariant=True,
                    ):
                        return False

            # Check return type
            actual_return = actual_annotations.get("return")
            protocol_return = protocol_annotations.get("return")

            if protocol_return is not None:
                if actual_return is None:
                    return False
                # Return types are covariant: actual should be subtype of expected
                if not TypeChecker.is_compatible_with_unification(
                    actual_return,
                    protocol_return,
                    type_var_mapping,
                    contravariant=False,
                ):
                    return False

            return True

        except (TypeError, ValueError, AttributeError):
            return False

    @staticmethod
    def are_compatible(
        actual_method: typing.Callable[..., typing.Any],
        protocol_method: typing.Callable[..., typing.Any],
    ) -> bool:
        """Check basic method compatibility without unification."""
        return MethodChecker.are_compatible_with_unification(actual_method, protocol_method, {})
