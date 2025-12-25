import object_identifier_pb2 as _object_identifier_pb2
import encryption_pb2 as _encryption_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class Workspace(_message.Message):
    __slots__ = ('location', 'optional_locations', 'encryption_config', 'share')
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    OPTIONAL_LOCATIONS_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTION_CONFIG_FIELD_NUMBER: _ClassVar[int]
    SHARE_FIELD_NUMBER: _ClassVar[int]
    location: str
    optional_locations: _containers.RepeatedScalarFieldContainer[str]
    encryption_config: _encryption_pb2.EncryptionConfig
    share: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, location: _Optional[str]=..., optional_locations: _Optional[_Iterable[str]]=..., encryption_config: _Optional[_Union[_encryption_pb2.EncryptionConfig, _Mapping]]=..., share: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...