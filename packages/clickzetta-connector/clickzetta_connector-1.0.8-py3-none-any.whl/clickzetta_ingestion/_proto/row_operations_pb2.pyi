import pb_util_pb2 as _pb_util_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional
DESCRIPTOR: _descriptor.FileDescriptor

class RowOperationsPB(_message.Message):
    __slots__ = ('rows', 'indirect_data')

    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[RowOperationsPB.Type]
        INSERT: _ClassVar[RowOperationsPB.Type]
        UPDATE: _ClassVar[RowOperationsPB.Type]
        DELETE: _ClassVar[RowOperationsPB.Type]
        UPSERT: _ClassVar[RowOperationsPB.Type]
        INSERT_IGNORE: _ClassVar[RowOperationsPB.Type]
        UPDATE_IGNORE: _ClassVar[RowOperationsPB.Type]
        DELETE_IGNORE: _ClassVar[RowOperationsPB.Type]
        SPLIT_ROW: _ClassVar[RowOperationsPB.Type]
        RANGE_LOWER_BOUND: _ClassVar[RowOperationsPB.Type]
        RANGE_UPPER_BOUND: _ClassVar[RowOperationsPB.Type]
        EXCLUSIVE_RANGE_LOWER_BOUND: _ClassVar[RowOperationsPB.Type]
        INCLUSIVE_RANGE_UPPER_BOUND: _ClassVar[RowOperationsPB.Type]
        REPLY_DETLA: _ClassVar[RowOperationsPB.Type]
    UNKNOWN: RowOperationsPB.Type
    INSERT: RowOperationsPB.Type
    UPDATE: RowOperationsPB.Type
    DELETE: RowOperationsPB.Type
    UPSERT: RowOperationsPB.Type
    INSERT_IGNORE: RowOperationsPB.Type
    UPDATE_IGNORE: RowOperationsPB.Type
    DELETE_IGNORE: RowOperationsPB.Type
    SPLIT_ROW: RowOperationsPB.Type
    RANGE_LOWER_BOUND: RowOperationsPB.Type
    RANGE_UPPER_BOUND: RowOperationsPB.Type
    EXCLUSIVE_RANGE_LOWER_BOUND: RowOperationsPB.Type
    INCLUSIVE_RANGE_UPPER_BOUND: RowOperationsPB.Type
    REPLY_DETLA: RowOperationsPB.Type
    ROWS_FIELD_NUMBER: _ClassVar[int]
    INDIRECT_DATA_FIELD_NUMBER: _ClassVar[int]
    rows: bytes
    indirect_data: bytes

    def __init__(self, rows: _Optional[bytes]=..., indirect_data: _Optional[bytes]=...) -> None:
        ...