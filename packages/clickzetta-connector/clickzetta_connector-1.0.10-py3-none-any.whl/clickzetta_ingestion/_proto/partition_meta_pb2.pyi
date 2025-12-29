import virtual_value_info_pb2 as _virtual_value_info_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class Partition(_message.Message):
    __slots__ = ('virtual_value_info', 'partition_keys')
    VIRTUAL_VALUE_INFO_FIELD_NUMBER: _ClassVar[int]
    PARTITION_KEYS_FIELD_NUMBER: _ClassVar[int]
    virtual_value_info: _virtual_value_info_pb2.VirtualValueInfo
    partition_keys: _containers.RepeatedScalarFieldContainer[str]

    def __init__(self, virtual_value_info: _Optional[_Union[_virtual_value_info_pb2.VirtualValueInfo, _Mapping]]=..., partition_keys: _Optional[_Iterable[str]]=...) -> None:
        ...