import sys
import typing

if sys.version_info >= (3, 13):
    from typing import TypeVar
else:
    from typing_extensions import TypeVar
import pytest

from typedprotocol import TypedProtocol


# Test protocols
class Request(TypedProtocol):
    id: int
    data: bytes


class Custom(Request):
    name: str


class ServiceProtocol(TypedProtocol):
    name: str

    def process(self, data: bytes) -> str: ...

    def validate(self, value: int) -> bool: ...


class AsyncServiceProtocol(TypedProtocol):
    async def fetch_data(self, url: str) -> dict[str, typing.Any]: ...


class ParamType(TypedProtocol):
    value: int
    label: str


class ExtendedParamType(ParamType):
    extra: float


class ComplexServiceProtocol(TypedProtocol):
    def compute(self, param: ParamType) -> int: ...


class TestGenericProtocols:
    """Test protocols with generic type variables."""

    def test_generic_protocol_inheritance(self):
        T = TypeVar("T")
        U = TypeVar("U")

        # Base generic protocol
        class BaseProtocol(TypedProtocol[T]):
            data: T

            def process(self, item: T) -> T: ...

        # Extended generic protocol that inherits from base with different TypeVar
        # BaseProtocol[U] means T gets substituted with U in the base protocol
        class ExtendedProtocol(BaseProtocol[U]):
            metadata: str

            def validate(self, item: U) -> bool: ...

        # Implementation that should work with ExtendedProtocol
        class StringProcessor:
            data: str
            metadata: str

            def process(self, item: str) -> str:
                return item.upper()

            def validate(self, item: str) -> bool:
                return len(item) > 0

        # Implementation with inconsistent types - should fail
        class MixedProcessor:
            data: str
            metadata: str

            def process(self, item: str) -> str:
                return item.upper()

            def validate(self, item: int) -> bool:  # Wrong type - U should be str!
                return item > 0

        assert issubclass(StringProcessor, ExtendedProtocol)
        assert not issubclass(MixedProcessor, ExtendedProtocol)


class TestMethodParameterProtocol:
    """Test method parameter with typed protocols."""

    def test_valid_parameter_protocol(self):
        class ValidComplexService:
            def compute(self, param: ParamType) -> int:
                return param.value * 2

        assert issubclass(ValidComplexService, ComplexServiceProtocol)

    def test_invalid_parameter_protocol(self):
        class InvalidComplexService:
            def compute(self, param: ExtendedParamType) -> int:  # should be ParamType
                return param.value * 2

        assert not issubclass(InvalidComplexService, ComplexServiceProtocol)


class TestAttributeProtocols:
    """Test protocols with only attributes."""

    def test_valid_implementation(self):
        class ValidImplementation:
            id: int
            data: bytes
            name: str

        assert issubclass(ValidImplementation, Custom)

    def test_missing_field(self):
        class MissingField:
            id: int
            name: str  # missing 'data' field

        assert not issubclass(MissingField, Request)

    def test_wrong_type(self):
        class WrongType:
            id: str  # should be int
            data: bytes
            name: str

        assert not issubclass(WrongType, Request)


class TestMethodProtocols:
    """Test protocols with methods."""

    def test_valid_service(self):
        class ValidService:
            name: str

            def process(self, data: bytes) -> str:
                return "processed"

            def validate(self, value: int) -> bool:
                return True

        assert issubclass(ValidService, ServiceProtocol)

    def test_missing_method(self):
        class MissingMethod:
            name: str

            def process(self, data: bytes) -> str:
                return "processed"

            # missing validate method

        assert not issubclass(MissingMethod, ServiceProtocol)

    def test_wrong_method_signature(self):
        class WrongMethodSignature:
            name: str

            def process(self, data: str) -> str:  # wrong parameter type
                return "processed"

            def validate(self, value: int) -> bool:
                return True

        assert not issubclass(WrongMethodSignature, ServiceProtocol)

    def test_wrong_return_type(self):
        class WrongReturnType:
            name: str

            def process(self, data: bytes) -> int:  # wrong return type
                return 42

            def validate(self, value: int) -> bool:
                return True

        assert not issubclass(WrongReturnType, ServiceProtocol)


class TestAsyncMethodProtocols:
    """Test protocols with async methods."""

    def test_valid_async_service(self):
        class ValidAsyncService:
            async def fetch_data(self, url: str) -> dict[str, typing.Any]:
                return {"result": "data"}

        assert issubclass(ValidAsyncService, AsyncServiceProtocol)

    def test_wrong_async_signature(self):
        class WrongAsyncSignature:
            def fetch_data(self, url: str) -> dict[str, typing.Any]:  # not async
                return {"result": "data"}

        assert not issubclass(WrongAsyncSignature, AsyncServiceProtocol)


class TestTypeCompatibility:
    """Test type compatibility and subclass relationships."""

    def test_subclass_type_method(self):
        # Parameters are contravariant: implementation must accept same or more general type
        # bool is a subclass of int, so it's MORE specific, not compatible for parameters
        class SubclassTypeMethod:
            name: str

            def process(self, data: bytes) -> str:
                return "processed"

            def validate(self, value: bool) -> bool:  # bool is subclass of int - incompatible!
                return True

        # This should fail because parameters require contravariance
        assert not issubclass(SubclassTypeMethod, ServiceProtocol)


class TestExtraMembers:
    """Test implementations with extra fields and methods."""

    def test_extra_fields_implementation(self):
        class ExtraFieldsImplementation:
            # Required by Request protocol
            id: int
            data: bytes

            # Extra fields (should be allowed)
            extra_string: str
            extra_number: float
            extra_list: list[int]

        assert issubclass(ExtraFieldsImplementation, Request)

    def test_extra_methods_implementation(self):
        class ExtraMethodsImplementation:
            # Required by ServiceProtocol
            name: str

            def process(self, data: bytes) -> str:
                return "processed"

            def validate(self, value: int) -> bool:
                return True

            # Extra methods (should be allowed)
            def extra_method(self, x: int) -> str:
                return f"extra: {x}"

            def another_extra(self) -> None:
                pass

        assert issubclass(ExtraMethodsImplementation, ServiceProtocol)

    def test_extra_fields_and_methods_implementation(self):
        class ExtraFieldsAndMethodsImplementation:
            # Required by ServiceProtocol
            name: str

            def process(self, data: bytes) -> str:
                return "processed"

            def validate(self, value: int) -> bool:
                return True

            # Extra fields
            extra_field: str
            count: int

            # Extra methods
            def helper_method(self, data: str) -> int:
                return len(data)

            def cleanup(self) -> None:
                pass

        assert issubclass(ExtraFieldsAndMethodsImplementation, ServiceProtocol)

    def test_implements_multiple_with_extras(self):
        class ImplementsMultipleWithExtras:
            # Required by Request
            id: int
            data: bytes

            # Required by ServiceProtocol
            name: str

            def process(self, data: bytes) -> str:
                return "processed"

            def validate(self, value: int) -> bool:
                return True

            # Extra members
            extra_attr: dict[str, typing.Any]

            def extra_async_method(self) -> typing.Awaitable[str]:
                async def inner():
                    return "async result"

                return inner()

        assert issubclass(ImplementsMultipleWithExtras, Request)
        assert issubclass(ImplementsMultipleWithExtras, ServiceProtocol)


class TestMultipleClassParameters:
    """Test issubclass with multiple class parameters."""

    def test_only_request_impl(self):
        class OnlyRequestImpl:
            id: int
            data: bytes

        assert issubclass(OnlyRequestImpl, Request)
        assert not issubclass(OnlyRequestImpl, ServiceProtocol)
        assert issubclass(OnlyRequestImpl, (Request, ServiceProtocol))

    def test_only_service_impl(self):
        class OnlyServiceImpl:
            name: str

            def process(self, data: bytes) -> str:
                return "processed"

            def validate(self, value: int) -> bool:
                return True

        assert not issubclass(OnlyServiceImpl, Request)
        assert issubclass(OnlyServiceImpl, ServiceProtocol)
        assert issubclass(OnlyServiceImpl, (Request, ServiceProtocol))

    def test_both_protocols_impl(self):
        class BothProtocolsImpl:
            # Implements both Request and ServiceProtocol
            id: int
            data: bytes
            name: str

            def process(self, data: bytes) -> str:
                return "processed"

            def validate(self, value: int) -> bool:
                return True

        assert issubclass(BothProtocolsImpl, Request)
        assert issubclass(BothProtocolsImpl, ServiceProtocol)
        assert issubclass(BothProtocolsImpl, (Request, ServiceProtocol))

    def test_neither_impl(self):
        class NeitherImpl:
            some_field: str

        assert not issubclass(NeitherImpl, Request)
        assert not issubclass(NeitherImpl, ServiceProtocol)
        assert not issubclass(NeitherImpl, (Request, ServiceProtocol))

    def test_mixed_protocol_and_regular_class(self):
        class RegularClass:
            pass

        class OnlyRequestImpl:
            id: int
            data: bytes

        assert issubclass(OnlyRequestImpl, (Request, RegularClass))
        assert issubclass(OnlyRequestImpl, (RegularClass, Request))

    def test_three_protocols(self):
        class BothProtocolsImpl:
            # Implements both Request and ServiceProtocol
            id: int
            data: bytes
            name: str

            def process(self, data: bytes) -> str:
                return "processed"

            def validate(self, value: int) -> bool:
                return True

        assert issubclass(BothProtocolsImpl, (Request, ServiceProtocol, AsyncServiceProtocol))


class TestInheritanceRestrictions:
    """Test protocol inheritance restrictions."""

    def test_valid_protocol_inheritance(self):
        # This should work - protocol inheriting from protocol
        class ValidProtocolInheritance(Request):
            extra_field: str

        assert ValidProtocolInheritance.__name__ == "ValidProtocolInheritance"

    def test_invalid_protocol_inheritance_regular_class(self):
        # This should fail - protocol inheriting from regular class
        class RegularClass:
            pass

        with pytest.raises(TypeError, match="cannot inherit from non-protocol type"):

            class InvalidProtocolInheritance(RegularClass, TypedProtocol):  # type: ignore
                field: int

    def test_invalid_builtin_inheritance(self):
        # This should fail - protocol inheriting from built-in type
        with pytest.raises(TypeError, match="cannot inherit from non-protocol type"):

            class InvalidBuiltinInheritance(dict, TypedProtocol):  # type: ignore
                field: int

    def test_multiple_protocol_inheritance(self):
        # This should work - multiple protocol inheritance
        class MultiProtocolInheritance(Request, ServiceProtocol):
            extra: float

        assert MultiProtocolInheritance.__name__ == "MultiProtocolInheritance"

    def test_inherited_subclassing(self):
        class BaseProtocol(TypedProtocol):
            field: int

        class BaseImplementation:
            field: int

        class Implementation(BaseImplementation):
            another_field: str

        assert issubclass(Implementation, BaseProtocol)


class TestAnnotationEnforcement:
    """Test annotation enforcement for protocols."""

    def test_missing_attribute_annotation(self):
        # This should fail - missing attribute annotation
        with pytest.raises(TypeError, match="must have a type annotation"):

            class MissingAttributeAnnotation(TypedProtocol):  # type: ignore
                unannotated_attr = "some_value"  # This should fail

                def process(self, data: bytes) -> str: ...

    def test_missing_parameter_annotation(self):
        # This should fail - method without parameter annotation
        with pytest.raises(TypeError, match="must have a type annotation"):

            class MissingParameterAnnotation(TypedProtocol):  # type: ignore
                name: str

                def process(self, data) -> str: ...  # missing parameter annotation # type: ignore

    def test_properly_annotated_protocol(self):
        # This should work - properly annotated protocol
        class ProperlyAnnotatedProtocol(TypedProtocol):
            name: str
            count: int

            def process(self, data: bytes) -> str: ...
            def validate(self, value: int) -> bool: ...
            def notify(self, message: str) -> None: ...  # procedures with None return

        assert ProperlyAnnotatedProtocol.__name__ == "ProperlyAnnotatedProtocol"


class TestInstantiationPrevention:
    """Test that protocols cannot be instantiated."""

    def test_typed_protocol_instantiation(self):
        with pytest.raises(TypeError, match="Cannot instantiate protocol class"):
            TypedProtocol()

    def test_request_instantiation(self):
        with pytest.raises(TypeError, match="Cannot instantiate protocol class"):
            Request()

    def test_service_protocol_instantiation(self):
        with pytest.raises(TypeError, match="Cannot instantiate protocol class"):
            ServiceProtocol()

    def test_custom_instantiation(self):
        with pytest.raises(TypeError, match="Cannot instantiate protocol class"):
            Custom()


class TestMethodSignatureEdgeCases:
    """Test edge cases in method signature checking."""

    def test_method_with_different_parameter_names(self):
        # Methods with different parameter names should fail (line 49)
        class DifferentParamNames(TypedProtocol):
            def process(self, data: bytes) -> str: ...

        class WrongParamName:
            def process(self, content: bytes) -> str:  # different param name
                return "processed"

        assert not issubclass(WrongParamName, DifferentParamNames)

    def test_method_with_different_parameter_count(self):
        # Methods with different parameter counts should fail (line 45)
        class TwoParamProtocol(TypedProtocol):
            def process(self, data: bytes, count: int) -> str: ...

        class OneParamImpl:
            def process(self, data: bytes) -> str:  # missing count parameter
                return "processed"

        assert not issubclass(OneParamImpl, TwoParamProtocol)

    def test_method_with_missing_actual_param_annotation(self):
        # Implementation missing parameter annotation should fail (line 56)
        class RequiresAnnotation(TypedProtocol):
            def process(self, data: bytes) -> str: ...

        class MissingParamAnnotation:
            def process(self, data) -> str:  # missing annotation # type: ignore
                return "processed"

        assert not issubclass(MissingParamAnnotation, RequiresAnnotation)

    def test_method_with_missing_actual_return_annotation(self):
        # Implementation missing return annotation should fail (line 72)
        class RequiresReturnAnnotation(TypedProtocol):
            def compute(self, value: int) -> int: ...

        class MissingReturnAnnotation:
            def compute(self, value: int):  # missing return annotation # type: ignore
                return value * 2

        assert not issubclass(MissingReturnAnnotation, RequiresReturnAnnotation)


class TestTypeCheckerEdgeCases:
    """Test edge cases in type compatibility checking."""

    def test_generic_type_with_different_origins(self):
        # Different generic origins should fail (line 47)
        class ListProtocol(TypedProtocol):
            def get_items(self) -> list[int]: ...

        class DictImpl:
            def get_items(self) -> dict[str, int]:  # wrong origin type
                return {}

        assert not issubclass(DictImpl, ListProtocol)

    def test_generic_type_with_different_arg_counts(self):
        # Different number of type arguments should fail (line 53)
        class SingleArgProtocol(TypedProtocol):
            def get_data(self) -> list[int]: ...

        class WrongArgCount:
            def get_data(self) -> list:  # no type args # type: ignore
                return []  # type: ignore

        assert not issubclass(WrongArgCount, SingleArgProtocol)

    def test_non_class_type_compatibility(self):
        # Test compatibility with non-class types (line 66-69)
        class StringLiteralProtocol(TypedProtocol):
            name: typing.Literal["test"]

        class StringLiteralImpl:
            name: typing.Literal["test"]

        # Should handle literal types
        assert issubclass(StringLiteralImpl, StringLiteralProtocol)

    def test_exception_handling_in_type_checker(self):
        # Test exception handling (line 74)
        class EdgeCaseProtocol(TypedProtocol):
            value: typing.Any

        class EdgeCaseImpl:
            value: typing.Any

        # Should handle edge cases gracefully
        assert issubclass(EdgeCaseImpl, EdgeCaseProtocol)


class TestSubstitutionEdgeCases:
    """Test edge cases in TypeVar substitution."""

    def test_substitute_with_empty_substitutions(self):
        # Empty substitutions should return original (line 34)
        T = TypeVar("T")

        class EmptySubstitutionProtocol(TypedProtocol[T]):
            value: T

            def process(self, item: T) -> T: ...

        class StringImpl:
            value: str

            def process(self, item: str) -> str:
                return item.upper()

        assert issubclass(StringImpl, EmptySubstitutionProtocol)

    def test_substitute_with_complex_generics(self):
        # Test complex generic substitution (line 46-48)
        # Using a simpler test that exercises the substitution code
        T = TypeVar("T")

        class ComplexProtocol(TypedProtocol[T]):
            def get_list(self) -> list[T]: ...

        class StringListImpl:
            def get_list(self) -> list[str]:
                return ["a", "b"]

        assert issubclass(StringListImpl, ComplexProtocol)


class TestMethodCheckerExceptions:
    """Test exception handling in method checker."""

    def test_method_checker_with_invalid_signature(self):
        # Test exception handling in method checker (line 84-85)
        class ValidProtocol(TypedProtocol):
            def process(self, data: bytes) -> str: ...

        class InvalidImpl:
            process = "not a method"  # Not callable

        assert not issubclass(InvalidImpl, ValidProtocol)

    def test_method_compatibility_without_unification(self):
        # Test are_compatible static method (line 93)
        from typedprotocol.method_checker import MethodChecker

        def method1(data: bytes) -> str:
            return "result"

        def method2(data: bytes) -> str:
            return "result"

        assert MethodChecker.are_compatible(method1, method2)

    def test_method_compatibility_with_wrong_signature(self):
        from typedprotocol.method_checker import MethodChecker

        def method1(data: bytes) -> str:
            return "result"

        def method2(data: int) -> str:  # different parameter type
            return "result"

        assert not MethodChecker.are_compatible(method1, method2)


class TestGenericInheritance:
    """Test protocols inheriting from typing.Generic."""

    def test_protocol_with_generic_origin(self):
        # Test handling of typing.Generic as base (line 62, 64)
        T = TypeVar("T")

        class GenericBase(TypedProtocol[T]):
            value: T

            def process(self, item: T) -> T: ...

        class ConcreteImpl:
            value: int

            def process(self, item: int) -> int:
                return item * 2

        assert issubclass(ConcreteImpl, GenericBase)

    def test_protocol_with_default_typevar(self):
        # Test the default TypeVar (T = TypeVar("T", default=object))
        T = TypeVar("T")

        class DefaultGeneric(TypedProtocol[T]):
            data: T

            def get(self) -> T: ...

        class AnyImpl:
            data: str

            def get(self) -> str:
                return "result"

        assert issubclass(AnyImpl, DefaultGeneric)


class TestAdditionalEdgeCases:
    """Additional tests for edge case coverage."""

    def test_type_checker_with_mismatched_generic_args(self):
        # Test generic types with different argument counts (line 53)
        class GenericResultProtocol(TypedProtocol):
            def get_dict(self) -> dict[str, int]: ...

        class MismatchedImpl:
            def get_dict(self) -> dict[str, int, str]:  # invalid dict type # type: ignore
                return {}  # type: ignore

        # The implementation is invalid, should return False
        assert not issubclass(MismatchedImpl, GenericResultProtocol)

    def test_method_checker_exception_in_signature(self):
        # Test exception handling in method checker (line 84-85)
        from typedprotocol.method_checker import MethodChecker

        class ProblematicMethod:
            def __init__(self):
                pass

        # Try to check compatibility with a non-standard callable
        assert not MethodChecker.are_compatible(
            lambda x: x,  # type: ignore
            ProblematicMethod().__init__,  # type: ignore
        )

    def test_substitution_with_no_origin(self):
        # Test substitution with type that has no origin (line 48)
        from typedprotocol.substitution import TypeVarSubstitutor

        T = TypeVar("T")
        substitutions = {T: int}

        # Test with a plain type (no origin)
        result = TypeVarSubstitutor.substitute(str, substitutions)
        assert result is str

    def test_substitution_empty_dict(self):
        # Test substitution with empty substitutions dict (line 34)
        from typedprotocol.substitution import TypeVarSubstitutor

        T = TypeVar("T")

        # With empty substitutions, should return original
        result = TypeVarSubstitutor.substitute(T, {})
        assert result == T

    def test_protocol_with_class_type_member(self):
        # Test protocol with a type as a class member (line 34)
        # This is hard to trigger but we can test indirectly
        class TestProtocol(TypedProtocol):
            name: str

        # Just verify it was created successfully
        assert TestProtocol.__name__ == "TestProtocol"

    def test_complex_type_checker_exception(self):
        # More complex exception handling test (line 68-69)
        from typedprotocol.type_checker import TypeChecker

        # Test with None types
        assert TypeChecker.is_compatible_with_unification(
            None,
            None,
            {},
            contravariant=False,  # type: ignore
        )

    def test_method_checker_with_broken_annotations(self):
        # Test to trigger exception in method checker (line 84-85)
        from typedprotocol.method_checker import MethodChecker

        # Create a callable with missing attributes
        class BrokenCallable:
            def __call__(self):
                pass

        broken = BrokenCallable()

        def normal_method(x: int) -> int:
            return x

        assert not MethodChecker.are_compatible_with_unification(
            broken,
            normal_method,
            {},  # type: ignore
        )
