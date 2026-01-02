import typing
import types

from typing import Type, Optional, Dict

import pydantic

import cel
import cel.proto as cel_proto

def remove_optional(annotation: Type):
    origin = typing.get_origin(annotation)
    if origin is not types.UnionType and origin is not typing.Union:
        return annotation

    args = [arg for arg in typing.get_args(annotation) if arg is not type(None)]
    if len(args) != 1:
        raise ValueError(f"Unsupported union type: {annotation}")

    return args[0]

def non_trivial_union_args(annotation: Type):
    origin = typing.get_origin(annotation)
    if origin is not types.UnionType and origin is not typing.Union:
        return []
    
    return [arg for arg in typing.get_args(annotation) if arg is not type(None)]

def test_remove_optional():
    assert remove_optional(int) == int
    assert remove_optional(str) == str
    assert remove_optional(bytes) == bytes
    assert remove_optional(float) == float
    assert remove_optional(list[int]) == list[int]
    assert remove_optional(list[str]) == list[str]
    assert remove_optional(int | None) == int
    assert remove_optional(Optional[int]) == int

def get_base_type(origin: Type):
    if origin is int:
        return cel_proto.TYPE_SINT64
    elif origin is str:
        return cel_proto.TYPE_STRING
    elif origin is bytes:
        return cel_proto.TYPE_BYTES
    elif origin is float:
        return cel_proto.TYPE_DOUBLE
    else:
        return None

class PydanticMessagesBuilder:
    file_proto: cel_proto.FileDescriptorProto
    file_desc: Optional[cel_proto.FileDescriptor]

    _models_type_name: Dict[Type[pydantic.BaseModel], str]
    _message_types: set[str]

    def __init__(self, package_name: str, file_name: Optional[str] = None):
        self.file_proto = cel_proto.FileDescriptorProto()
        self.file_proto.set_name(file_name or package_name + ".proto")
        self.file_proto.set_package(package_name)
        self.file_proto.set_syntax("proto3")

        self._models_type_name = {}
        self._message_types = set()
    
    def _add_oneof_message_type(self, name: str, types: list[Type]):
        if name in self._message_types:
            raise ValueError(f"Oneof message type {name} already added")
        self._message_types.add(name)

        msg_proto = self.file_proto.add_message_type()
        # TODO: handle name collisions
        msg_proto.set_name(name)

        oneof_decl_index = msg_proto.oneof_decl_size()
        oneof_decl = msg_proto.add_oneof_decl()
        oneof_decl.set_name(f"{name}_decl")

        index = 1
        for type in types:
            # TODO: convert to snake_case
            field_proto = self._add_field(msg_proto, type.__name__, index, type)
            if field_proto is None:
                raise RuntimeError(f"Failed to add field {type.__name__}")
            field_proto.set_oneof_index(oneof_decl_index)
            index += 1

    def _add_field(self, msg_proto: cel_proto.DescriptorProto, name: str, index: int, annotation: Type):
        field_proto = msg_proto.add_field()

        def handle_non_list_type(annotation: Type):
            field_proto.set_name(name)
            field_proto.set_number(index)

            union_args = non_trivial_union_args(annotation)
            if len(union_args) > 1:
                # TODO: unique name
                oneof_type_name = f"{name}_oneof"
                self._add_oneof_message_type(oneof_type_name, union_args)
                field_proto.set_type_name(oneof_type_name)
                field_proto.set_label(cel_proto.LABEL_OPTIONAL)
                return field_proto

            annotation = remove_optional(annotation)
            origin = typing.get_origin(annotation) or annotation

            base_type = get_base_type(origin)
            if base_type is not None:
                field_proto.set_type(base_type)
                field_proto.set_label(cel_proto.LABEL_OPTIONAL)
                return field_proto


            if issubclass(origin, pydantic.BaseModel):
                field_proto.set_type_name(self._get_or_add_model(origin))
                return field_proto

            raise ValueError(f"Unsupported type: {annotation}")

        union_args = non_trivial_union_args(annotation) or [annotation]
        if len(union_args) != 1:
            return handle_non_list_type(annotation)

        annotation = union_args[0]

        origin = typing.get_origin(annotation) or annotation
        if origin is not list:
            return handle_non_list_type(annotation)

        # field is a list
        args = typing.get_args(annotation)
        if len(args) != 1:
            raise ValueError(f"Unsupported list type: {annotation}")

        # does not support list of optionals
        element_annotation = args[0]
        handle_non_list_type(element_annotation)
        field_proto.set_label(cel_proto.LABEL_REPEATED)
        return field_proto

    def _get_or_add_model(self, model: Type[pydantic.BaseModel]):
        type_name = self._models_type_name.get(model)
        if type_name is None:
            type_name = self.add_model(model)
        return type_name

    def add_model(self, model: Type[pydantic.BaseModel]):
        if model in self._models_type_name:
            return

        type_name = model.__name__
        if type_name in self._message_types:
            other_model = next(model for model in self._models_type_name if self._models_type_name[model] == type_name)
            raise ValueError(f"Model name {type_name} already used for another model: {other_model}")

        self._message_types.add(type_name)
        self._models_type_name[model] = type_name

        msg_proto = self.file_proto.add_message_type()
        # TODO: handle name collisions
        msg_proto.set_name(type_name)

        index = 1
        for name, field_info in model.model_fields.items():
            annotation = field_info.annotation
            if annotation is None:
                raise ValueError(f"Field {name} has no annotation")

            self._add_field(msg_proto, name, index, annotation)
            index += 1

        return type_name

    def build(self, pool: cel.DescriptorPool):
        self.file_desc = pool.BuildFile(self.file_proto)
    
    def get_message_type(self, model: Type[pydantic.BaseModel]):
        type_name = self._models_type_name[model]
        return self.file_desc.FindMessageTypeByName(type_name)