import expression_pb2 as _expression_pb2
import data_type_pb2 as _data_type_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class ConstantField(_message.Message):
    __slots__ = ('field_id', 'type', 'value', 'field_name')
    FIELD_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    FIELD_NAME_FIELD_NUMBER: _ClassVar[int]
    field_id: int
    type: _data_type_pb2.DataType
    value: _expression_pb2.Constant
    field_name: str

    def __init__(self, field_id: _Optional[int]=..., type: _Optional[_Union[_data_type_pb2.DataType, _Mapping]]=..., value: _Optional[_Union[_expression_pb2.Constant, _Mapping]]=..., field_name: _Optional[str]=...) -> None:
        ...

class VirtualColumnValues(_message.Message):
    __slots__ = ('values', 'block_ids')
    VALUES_FIELD_NUMBER: _ClassVar[int]
    BLOCK_IDS_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedCompositeFieldContainer[ConstantField]
    block_ids: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, values: _Optional[_Iterable[_Union[ConstantField, _Mapping]]]=..., block_ids: _Optional[_Iterable[int]]=...) -> None:
        ...

class VirtualValueInfo(_message.Message):
    __slots__ = ('virtual_values',)
    VIRTUAL_VALUES_FIELD_NUMBER: _ClassVar[int]
    virtual_values: VirtualColumnValues

    def __init__(self, virtual_values: _Optional[_Union[VirtualColumnValues, _Mapping]]=...) -> None:
        ...