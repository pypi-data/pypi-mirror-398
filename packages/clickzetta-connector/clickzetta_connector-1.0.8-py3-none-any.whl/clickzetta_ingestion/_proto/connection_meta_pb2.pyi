import property_pb2 as _property_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class ConnectionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CLOUD_FUNCTION: _ClassVar[ConnectionType]
    FILE_SYSTEM: _ClassVar[ConnectionType]

class ConnectionCategory(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DATA_CONNECTION: _ClassVar[ConnectionCategory]
    API_CONNECTION: _ClassVar[ConnectionCategory]
CLOUD_FUNCTION: ConnectionType
FILE_SYSTEM: ConnectionType
DATA_CONNECTION: ConnectionCategory
API_CONNECTION: ConnectionCategory

class FileSystemConnectionInfo(_message.Message):
    __slots__ = ('file_system_type', 'config')
    FILE_SYSTEM_TYPE_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    file_system_type: str
    config: _property_pb2.Properties

    def __init__(self, file_system_type: _Optional[str]=..., config: _Optional[_Union[_property_pb2.Properties, _Mapping]]=...) -> None:
        ...

class ConnectionInfo(_message.Message):
    __slots__ = ('file_system_connection_info',)
    FILE_SYSTEM_CONNECTION_INFO_FIELD_NUMBER: _ClassVar[int]
    file_system_connection_info: FileSystemConnectionInfo

    def __init__(self, file_system_connection_info: _Optional[_Union[FileSystemConnectionInfo, _Mapping]]=...) -> None:
        ...

class Connection(_message.Message):
    __slots__ = ('connection_type', 'connection_category', 'enabled', 'connection_info')
    CONNECTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_CATEGORY_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_INFO_FIELD_NUMBER: _ClassVar[int]
    connection_type: ConnectionType
    connection_category: ConnectionCategory
    enabled: bool
    connection_info: ConnectionInfo

    def __init__(self, connection_type: _Optional[_Union[ConnectionType, str]]=..., connection_category: _Optional[_Union[ConnectionCategory, str]]=..., enabled: bool=..., connection_info: _Optional[_Union[ConnectionInfo, _Mapping]]=...) -> None:
        ...