import object_identifier_pb2 as _object_identifier_pb2
import storage_location_pb2 as _storage_location_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class VolumeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    VT_MANAGED: _ClassVar[VolumeType]
    VT_EXTERNAL: _ClassVar[VolumeType]
VT_MANAGED: VolumeType
VT_EXTERNAL: VolumeType

class Volume(_message.Message):
    __slots__ = ('volume_type', 'url', 'connection', 'meta_collection', 'recursive', 'filemeta_table', 'location_info')

    class MetaCollection(_message.Message):
        __slots__ = ('enable', 'auto_refresh')
        ENABLE_FIELD_NUMBER: _ClassVar[int]
        AUTO_REFRESH_FIELD_NUMBER: _ClassVar[int]
        enable: bool
        auto_refresh: bool

        def __init__(self, enable: bool=..., auto_refresh: bool=...) -> None:
            ...
    VOLUME_TYPE_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_FIELD_NUMBER: _ClassVar[int]
    META_COLLECTION_FIELD_NUMBER: _ClassVar[int]
    RECURSIVE_FIELD_NUMBER: _ClassVar[int]
    FILEMETA_TABLE_FIELD_NUMBER: _ClassVar[int]
    LOCATION_INFO_FIELD_NUMBER: _ClassVar[int]
    volume_type: VolumeType
    url: str
    connection: _object_identifier_pb2.ObjectIdentifier
    meta_collection: Volume.MetaCollection
    recursive: bool
    filemeta_table: _object_identifier_pb2.ObjectIdentifier
    location_info: _storage_location_pb2.LocationInfo

    def __init__(self, volume_type: _Optional[_Union[VolumeType, str]]=..., url: _Optional[str]=..., connection: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., meta_collection: _Optional[_Union[Volume.MetaCollection, _Mapping]]=..., recursive: bool=..., filemeta_table: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., location_info: _Optional[_Union[_storage_location_pb2.LocationInfo, _Mapping]]=...) -> None:
        ...

class VolumeFileTransferRequest(_message.Message):
    __slots__ = ('command', 'local_paths', 'volume', 'volume_identifier', 'subdirectory', 'file', 'options')

    class Option(_message.Message):
        __slots__ = ('name', 'value')
        NAME_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        name: str
        value: str

        def __init__(self, name: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    LOCAL_PATHS_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    VOLUME_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    SUBDIRECTORY_FIELD_NUMBER: _ClassVar[int]
    FILE_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    command: str
    local_paths: _containers.RepeatedScalarFieldContainer[str]
    volume: str
    volume_identifier: str
    subdirectory: str
    file: str
    options: _containers.RepeatedCompositeFieldContainer[VolumeFileTransferRequest.Option]

    def __init__(self, command: _Optional[str]=..., local_paths: _Optional[_Iterable[str]]=..., volume: _Optional[str]=..., volume_identifier: _Optional[str]=..., subdirectory: _Optional[str]=..., file: _Optional[str]=..., options: _Optional[_Iterable[_Union[VolumeFileTransferRequest.Option, _Mapping]]]=...) -> None:
        ...

class VolumeFileTransferTicket(_message.Message):
    __slots__ = ('presigned_urls',)
    PRESIGNED_URLS_FIELD_NUMBER: _ClassVar[int]
    presigned_urls: _containers.RepeatedScalarFieldContainer[str]

    def __init__(self, presigned_urls: _Optional[_Iterable[str]]=...) -> None:
        ...

class VolumeFileTransferOutcome(_message.Message):
    __slots__ = ('status', 'error', 'request', 'ticket', 'next_marker')

    class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        SUCCESS: _ClassVar[VolumeFileTransferOutcome.Status]
        FAILED: _ClassVar[VolumeFileTransferOutcome.Status]
        CONTINUE: _ClassVar[VolumeFileTransferOutcome.Status]
    SUCCESS: VolumeFileTransferOutcome.Status
    FAILED: VolumeFileTransferOutcome.Status
    CONTINUE: VolumeFileTransferOutcome.Status
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    REQUEST_FIELD_NUMBER: _ClassVar[int]
    TICKET_FIELD_NUMBER: _ClassVar[int]
    NEXT_MARKER_FIELD_NUMBER: _ClassVar[int]
    status: VolumeFileTransferOutcome.Status
    error: str
    request: VolumeFileTransferRequest
    ticket: VolumeFileTransferTicket
    next_marker: str

    def __init__(self, status: _Optional[_Union[VolumeFileTransferOutcome.Status, str]]=..., error: _Optional[str]=..., request: _Optional[_Union[VolumeFileTransferRequest, _Mapping]]=..., ticket: _Optional[_Union[VolumeFileTransferTicket, _Mapping]]=..., next_marker: _Optional[str]=...) -> None:
        ...