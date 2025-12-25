from google.protobuf import descriptor_pb2 as _descriptor_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor
REDACT_FIELD_NUMBER: _ClassVar[int]
REDACT: _descriptor.FieldDescriptor

class ContainerSupHeaderPB(_message.Message):
    __slots__ = ('protos', 'pb_type')
    PROTOS_FIELD_NUMBER: _ClassVar[int]
    PB_TYPE_FIELD_NUMBER: _ClassVar[int]
    protos: _descriptor_pb2.FileDescriptorSet
    pb_type: str

    def __init__(self, protos: _Optional[_Union[_descriptor_pb2.FileDescriptorSet, _Mapping]]=..., pb_type: _Optional[str]=...) -> None:
        ...