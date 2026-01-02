"""
Reduced bindings of github.com/google/cel-cpp,supporting static type checking and function extensions
"""
from __future__ import annotations
import typing
__all__ = ['BoolType', 'BytesType', 'CelExpression', 'CheckedExpr', 'Compiler', 'Descriptor', 'DescriptorPool', 'DescriptorProto', 'DoubleType', 'FieldDescriptorProto', 'FileDescriptor', 'FileDescriptorProto', 'FunctionRegistry', 'IntType', 'Interpreter', 'LABEL_OPTIONAL', 'LABEL_REPEATED', 'LABEL_REQUIRED', 'ListType', 'Message', 'NullType', 'OneofDescriptorProto', 'StringType', 'TYPE_BOOL', 'TYPE_BYTES', 'TYPE_DOUBLE', 'TYPE_ENUM', 'TYPE_FLOAT', 'TYPE_INT32', 'TYPE_INT64', 'TYPE_MESSAGE', 'TYPE_SFIXED32', 'TYPE_SFIXED64', 'TYPE_SINT32', 'TYPE_SINT64', 'TYPE_STRING', 'TYPE_UINT32', 'TYPE_UINT64', 'UintType']
class BoolType:
    def __init__(self) -> None:
        ...
class BytesType:
    def __init__(self) -> None:
        ...
class CelExpression:
    pass
class CheckedExpr:
    pass
class Compiler:
    """
    Parses and type-checks an expression.
    """
    def __init__(self, descriptor_pool: DescriptorPool, context: dict[str, BoolType | IntType | UintType | DoubleType | StringType | BytesType | NullType | Descriptor | ListType], function_registry: FunctionRegistry | None) -> None:
        ...
    def compile_to_checked_expr(self, expr: str) -> CheckedExpr:
        """
        Parses and type-checks an expression, returning a reusable CheckedExpr
        """
class Descriptor:
    pass
class DescriptorPool:
    """
    A pool of object descriptions used to type-check CEL expressions.
    """
    def BuildFile(self, arg0: FileDescriptorProto) -> FileDescriptor:
        ...
    def __init__(self) -> None:
        ...
    def add_json_schema(self, name: str, schema: str) -> Descriptor:
        """
        Adds a object description to the pool given a JSON schema.
        """
class DescriptorProto(Message):
    def add_field(self) -> FieldDescriptorProto:
        ...
    def add_oneof_decl(self) -> OneofDescriptorProto:
        ...
    def debug_string(self) -> str:
        ...
    def oneof_decl_size(self) -> int:
        ...
    def set_name(self, arg0: str) -> None:
        ...
class DoubleType:
    def __init__(self) -> None:
        ...
class FieldDescriptorProto:
    def set_label(self, arg0: int) -> None:
        ...
    def set_name(self, arg0: str) -> None:
        ...
    def set_number(self, arg0: int) -> None:
        ...
    def set_oneof_index(self, arg0: int) -> None:
        ...
    def set_type(self, arg0: int) -> None:
        ...
    def set_type_name(self, arg0: str) -> None:
        ...
class FileDescriptor:
    def FindMessageTypeByName(self, arg0: str) -> Descriptor:
        ...
class FileDescriptorProto:
    def __init__(self) -> None:
        ...
    def add_message_type(self) -> DescriptorProto:
        ...
    def set_name(self, arg0: str) -> None:
        ...
    def set_package(self, arg0: str) -> None:
        ...
    def set_syntax(self, arg0: str) -> None:
        ...
class FunctionRegistry:
    """
    Registry for python extension functions to be made available to expressions.
    """
    def __init__(self) -> None:
        ...
    def add_function(self, name: str, func: typing.Callable, return_type: BoolType | IntType | UintType | DoubleType | StringType | BytesType | NullType | Descriptor | ListType, arguments_type: list[BoolType | IntType | UintType | DoubleType | StringType | BytesType | NullType | Descriptor | ListType]) -> None:
        """
        Registers an extension function to be used in expressions.
        """
class IntType:
    def __init__(self) -> None:
        ...
class Interpreter:
    def __init__(self, descriptor_pool: DescriptorPool, context: dict[str, BoolType | IntType | UintType | DoubleType | StringType | BytesType | NullType | Descriptor | ListType], function_registry: FunctionRegistry | None) -> None:
        ...
    def build_expression_plan(self, checked_expr: CheckedExpr) -> CelExpression:
        """
        Builds an execution plan for a checked expression. Execution plan should be reused.
        """
    def evaluate(self, expr_plan: CelExpression, environment: dict[str, typing.Any]) -> bool | int | int | float | str | bytes | None | dict | list:
        """
        Executes a planned expression with the given environment values.
        """
class ListType:
    def __init__(self, arg0: BoolType | IntType | UintType | DoubleType | StringType | BytesType | NullType | Descriptor | ListType) -> None:
        ...
class Message:
    pass
class NullType:
    def __init__(self) -> None:
        ...
class OneofDescriptorProto(Message):
    def set_name(self, arg0: str) -> None:
        ...
class StringType:
    def __init__(self) -> None:
        ...
class UintType:
    def __init__(self) -> None:
        ...
LABEL_OPTIONAL: int = 1
LABEL_REPEATED: int = 3
LABEL_REQUIRED: int = 2
TYPE_BOOL: int = 8
TYPE_BYTES: int = 12
TYPE_DOUBLE: int = 1
TYPE_ENUM: int = 14
TYPE_FLOAT: int = 2
TYPE_INT32: int = 5
TYPE_INT64: int = 3
TYPE_MESSAGE: int = 11
TYPE_SFIXED32: int = 15
TYPE_SFIXED64: int = 16
TYPE_SINT32: int = 17
TYPE_SINT64: int = 18
TYPE_STRING: int = 9
TYPE_UINT32: int = 13
TYPE_UINT64: int = 4
