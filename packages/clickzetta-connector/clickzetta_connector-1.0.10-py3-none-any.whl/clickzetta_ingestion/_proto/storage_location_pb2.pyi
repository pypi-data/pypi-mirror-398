import object_identifier_pb2 as _object_identifier_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class FileSystemLocation(_message.Message):
    __slots__ = ('file_format',)
    FILE_FORMAT_FIELD_NUMBER: _ClassVar[int]
    file_format: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, file_format: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class DatabaseLocation(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class LocationInfo(_message.Message):
    __slots__ = ('file_system', 'database')
    FILE_SYSTEM_FIELD_NUMBER: _ClassVar[int]
    DATABASE_FIELD_NUMBER: _ClassVar[int]
    file_system: FileSystemLocation
    database: DatabaseLocation

    def __init__(self, file_system: _Optional[_Union[FileSystemLocation, _Mapping]]=..., database: _Optional[_Union[DatabaseLocation, _Mapping]]=...) -> None:
        ...

class StorageLocation(_message.Message):
    __slots__ = ('external', 'url', 'connection', 'meta_collection', 'recursive', 'filemeta_table', 'location_info')

    class MetaCollection(_message.Message):
        __slots__ = ('enable', 'auto_refresh')
        ENABLE_FIELD_NUMBER: _ClassVar[int]
        AUTO_REFRESH_FIELD_NUMBER: _ClassVar[int]
        enable: bool
        auto_refresh: bool

        def __init__(self, enable: bool=..., auto_refresh: bool=...) -> None:
            ...
    EXTERNAL_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_FIELD_NUMBER: _ClassVar[int]
    META_COLLECTION_FIELD_NUMBER: _ClassVar[int]
    RECURSIVE_FIELD_NUMBER: _ClassVar[int]
    FILEMETA_TABLE_FIELD_NUMBER: _ClassVar[int]
    LOCATION_INFO_FIELD_NUMBER: _ClassVar[int]
    external: bool
    url: str
    connection: _object_identifier_pb2.ObjectIdentifier
    meta_collection: StorageLocation.MetaCollection
    recursive: bool
    filemeta_table: _object_identifier_pb2.ObjectIdentifier
    location_info: LocationInfo

    def __init__(self, external: bool=..., url: _Optional[str]=..., connection: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., meta_collection: _Optional[_Union[StorageLocation.MetaCollection, _Mapping]]=..., recursive: bool=..., filemeta_table: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., location_info: _Optional[_Union[LocationInfo, _Mapping]]=...) -> None:
        ...