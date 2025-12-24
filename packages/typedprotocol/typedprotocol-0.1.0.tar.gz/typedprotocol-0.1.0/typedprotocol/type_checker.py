"""Type compatibility checking utilities for TypedProtocol."""

import inspect
import sys
import typing

if sys.version_info >= (3, 13):
    from typing import TypeVar
else:
    from typing_extensions import TypeVar


class TypeChecker:
    """Handles type compatibility checking and TypeVar unification."""

    @staticmethod
    def is_compatible_with_unification(
        actual: typing.Any,
        expected: typing.Any,
        type_var_mapping: dict[TypeVar, typing.Any],
        contravariant: bool = False,
    ) -> bool:
        """Check if actual type is compatible with expected type, maintaining TypeVar consistency.

        Args:
            actual: The actual type from the implementation
            expected: The expected type from the protocol
            type_var_mapping: Mapping of TypeVars to their bound types
            contravariant: If True, check contravariant compatibility (for parameters).
                         If False, check covariant compatibility (for return types).
        """
        try:
            # Handle TypeVar with unification
            if isinstance(expected, TypeVar):
                if expected in type_var_mapping:
                    return type_var_mapping[expected] == actual
                else:
                    type_var_mapping[expected] = actual
                    return True

            # For contravariant checking (parameters), swap the direction
            # actual should be a supertype of expected
            if contravariant:
                actual, expected = expected, actual

            # Handle generic types
            if hasattr(typing, "get_origin"):
                actual_origin = typing.get_origin(actual)
                expected_origin = typing.get_origin(expected)

                if actual_origin is not None or expected_origin is not None:
                    if actual_origin != expected_origin:
                        return False

                    actual_args = typing.get_args(actual) if actual_origin else ()
                    expected_args = typing.get_args(expected) if expected_origin else ()

                    if len(actual_args) != len(expected_args):
                        return False

                    return all(
                        TypeChecker.is_compatible_with_unification(
                            a, e, type_var_mapping, contravariant
                        )
                        for a, e in zip(actual_args, expected_args, strict=False)
                    )

            # For regular classes, check inheritance
            if inspect.isclass(actual) and inspect.isclass(expected):
                return issubclass(actual, expected)

            return actual == expected

        except (TypeError, AttributeError):
            return actual == expected

    @staticmethod
    def is_compatible(actual: typing.Any, expected: typing.Any) -> bool:
        """Check basic type compatibility without unification."""
        return TypeChecker.is_compatible_with_unification(actual, expected, {})
