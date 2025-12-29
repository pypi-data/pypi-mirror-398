import service_common_pb2 as _service_common_pb2
import object_identifier_pb2 as _object_identifier_pb2
import coordinator_service_pb2 as _coordinator_service_pb2
import file_system_pb2 as _file_system_pb2
import file_format_type_pb2 as _file_format_type_pb2
import table_common_pb2 as _table_common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class StreamSchema(_message.Message):
    __slots__ = ('fields',)
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[_table_common_pb2.FieldSchema]

    def __init__(self, fields: _Optional[_Iterable[_Union[_table_common_pb2.FieldSchema, _Mapping]]]=...) -> None:
        ...

class ChannelMeta(_message.Message):
    __slots__ = ('channel_id', 'recycle_offset', 'compaction_offset', 'current_offset', 'create_time', 'last_modify_time', 'location', 'file_format')
    CHANNEL_ID_FIELD_NUMBER: _ClassVar[int]
    RECYCLE_OFFSET_FIELD_NUMBER: _ClassVar[int]
    COMPACTION_OFFSET_FIELD_NUMBER: _ClassVar[int]
    CURRENT_OFFSET_FIELD_NUMBER: _ClassVar[int]
    CREATE_TIME_FIELD_NUMBER: _ClassVar[int]
    LAST_MODIFY_TIME_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    FILE_FORMAT_FIELD_NUMBER: _ClassVar[int]
    channel_id: int
    recycle_offset: int
    compaction_offset: int
    current_offset: int
    create_time: int
    last_modify_time: int
    location: str
    file_format: _file_format_type_pb2.FileFormatType

    def __init__(self, channel_id: _Optional[int]=..., recycle_offset: _Optional[int]=..., compaction_offset: _Optional[int]=..., current_offset: _Optional[int]=..., create_time: _Optional[int]=..., last_modify_time: _Optional[int]=..., location: _Optional[str]=..., file_format: _Optional[_Union[_file_format_type_pb2.FileFormatType, str]]=...) -> None:
        ...

class ChannelFileMeta(_message.Message):
    __slots__ = ('path', 'start_row_id', 'end_row_id', 'channel_id', 'offset', 'commit_time', 'size', 'row_count')
    PATH_FIELD_NUMBER: _ClassVar[int]
    START_ROW_ID_FIELD_NUMBER: _ClassVar[int]
    END_ROW_ID_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_ID_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    COMMIT_TIME_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    path: str
    start_row_id: str
    end_row_id: str
    channel_id: int
    offset: int
    commit_time: int
    size: int
    row_count: int

    def __init__(self, path: _Optional[str]=..., start_row_id: _Optional[str]=..., end_row_id: _Optional[str]=..., channel_id: _Optional[int]=..., offset: _Optional[int]=..., commit_time: _Optional[int]=..., size: _Optional[int]=..., row_count: _Optional[int]=...) -> None:
        ...

class ChannelTempDirToken(_message.Message):
    __slots__ = ('location', 'file_system', 'sts_ak_id', 'sts_ak_secret', 'sts_token', 'endpoint', 'internal_endpoint', 'region')
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    FILE_SYSTEM_FIELD_NUMBER: _ClassVar[int]
    STS_AK_ID_FIELD_NUMBER: _ClassVar[int]
    STS_AK_SECRET_FIELD_NUMBER: _ClassVar[int]
    STS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    INTERNAL_ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    REGION_FIELD_NUMBER: _ClassVar[int]
    location: str
    file_system: _file_system_pb2.FileSystemType
    sts_ak_id: str
    sts_ak_secret: str
    sts_token: str
    endpoint: str
    internal_endpoint: str
    region: str

    def __init__(self, location: _Optional[str]=..., file_system: _Optional[_Union[_file_system_pb2.FileSystemType, str]]=..., sts_ak_id: _Optional[str]=..., sts_ak_secret: _Optional[str]=..., sts_token: _Optional[str]=..., endpoint: _Optional[str]=..., internal_endpoint: _Optional[str]=..., region: _Optional[str]=...) -> None:
        ...

class CreateChannelRequest(_message.Message):
    __slots__ = ('table_id', 'file_format')
    TABLE_ID_FIELD_NUMBER: _ClassVar[int]
    FILE_FORMAT_FIELD_NUMBER: _ClassVar[int]
    table_id: _object_identifier_pb2.ObjectIdentifier
    file_format: _file_format_type_pb2.FileFormatType

    def __init__(self, table_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., file_format: _Optional[_Union[_file_format_type_pb2.FileFormatType, str]]=...) -> None:
        ...

class CreateChannelResponse(_message.Message):
    __slots__ = ('resp_status', 'channel_meta', 'temp_dir_token', 'schema')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_META_FIELD_NUMBER: _ClassVar[int]
    TEMP_DIR_TOKEN_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    channel_meta: ChannelMeta
    temp_dir_token: ChannelTempDirToken
    schema: StreamSchema

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., channel_meta: _Optional[_Union[ChannelMeta, _Mapping]]=..., temp_dir_token: _Optional[_Union[ChannelTempDirToken, _Mapping]]=..., schema: _Optional[_Union[StreamSchema, _Mapping]]=...) -> None:
        ...

class ListChannelRequest(_message.Message):
    __slots__ = ('table_id',)
    TABLE_ID_FIELD_NUMBER: _ClassVar[int]
    table_id: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, table_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class ListChannelResponse(_message.Message):
    __slots__ = ('resp_status', 'channel_meta')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_META_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    channel_meta: _containers.RepeatedCompositeFieldContainer[ChannelMeta]

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., channel_meta: _Optional[_Iterable[_Union[ChannelMeta, _Mapping]]]=...) -> None:
        ...

class GetChannelRequest(_message.Message):
    __slots__ = ('table_id', 'channel_id')
    TABLE_ID_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_ID_FIELD_NUMBER: _ClassVar[int]
    table_id: _object_identifier_pb2.ObjectIdentifier
    channel_id: int

    def __init__(self, table_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., channel_id: _Optional[int]=...) -> None:
        ...

class GetChannelResponse(_message.Message):
    __slots__ = ('resp_status', 'channel_meta', 'temp_dir_token', 'schema')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_META_FIELD_NUMBER: _ClassVar[int]
    TEMP_DIR_TOKEN_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    channel_meta: ChannelMeta
    temp_dir_token: ChannelTempDirToken
    schema: StreamSchema

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., channel_meta: _Optional[_Union[ChannelMeta, _Mapping]]=..., temp_dir_token: _Optional[_Union[ChannelTempDirToken, _Mapping]]=..., schema: _Optional[_Union[StreamSchema, _Mapping]]=...) -> None:
        ...

class DeleteChannelRequest(_message.Message):
    __slots__ = ('table_id', 'channel_id', 'delete_all')
    TABLE_ID_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_ID_FIELD_NUMBER: _ClassVar[int]
    DELETE_ALL_FIELD_NUMBER: _ClassVar[int]
    table_id: _object_identifier_pb2.ObjectIdentifier
    channel_id: int
    delete_all: bool

    def __init__(self, table_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., channel_id: _Optional[int]=..., delete_all: bool=...) -> None:
        ...

class DeleteChannelResponse(_message.Message):
    __slots__ = ('resp_status',)
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=...) -> None:
        ...

class CommitFileRequest(_message.Message):
    __slots__ = ('table_id', 'channel_id', 'file_meta_list')
    TABLE_ID_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_ID_FIELD_NUMBER: _ClassVar[int]
    FILE_META_LIST_FIELD_NUMBER: _ClassVar[int]
    table_id: _object_identifier_pb2.ObjectIdentifier
    channel_id: int
    file_meta_list: _containers.RepeatedCompositeFieldContainer[ChannelFileMeta]

    def __init__(self, table_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., channel_id: _Optional[int]=..., file_meta_list: _Optional[_Iterable[_Union[ChannelFileMeta, _Mapping]]]=...) -> None:
        ...

class CommitFileResponse(_message.Message):
    __slots__ = ('resp_status',)
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=...) -> None:
        ...

class StreamingPipeRequest(_message.Message):
    __slots__ = ('account', 'request_id', 'instance_id', 'create_channel_request', 'list_channel_request', 'get_channel_request', 'delete_channel_request', 'commit_file_request')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    CREATE_CHANNEL_REQUEST_FIELD_NUMBER: _ClassVar[int]
    LIST_CHANNEL_REQUEST_FIELD_NUMBER: _ClassVar[int]
    GET_CHANNEL_REQUEST_FIELD_NUMBER: _ClassVar[int]
    DELETE_CHANNEL_REQUEST_FIELD_NUMBER: _ClassVar[int]
    COMMIT_FILE_REQUEST_FIELD_NUMBER: _ClassVar[int]
    account: _coordinator_service_pb2.Account
    request_id: str
    instance_id: int
    create_channel_request: CreateChannelRequest
    list_channel_request: ListChannelRequest
    get_channel_request: GetChannelRequest
    delete_channel_request: DeleteChannelRequest
    commit_file_request: CommitFileRequest

    def __init__(self, account: _Optional[_Union[_coordinator_service_pb2.Account, _Mapping]]=..., request_id: _Optional[str]=..., instance_id: _Optional[int]=..., create_channel_request: _Optional[_Union[CreateChannelRequest, _Mapping]]=..., list_channel_request: _Optional[_Union[ListChannelRequest, _Mapping]]=..., get_channel_request: _Optional[_Union[GetChannelRequest, _Mapping]]=..., delete_channel_request: _Optional[_Union[DeleteChannelRequest, _Mapping]]=..., commit_file_request: _Optional[_Union[CommitFileRequest, _Mapping]]=...) -> None:
        ...

class StreamingPipeResponse(_message.Message):
    __slots__ = ('create_channel_response', 'list_channel_response', 'get_channel_response', 'delete_channel_response', 'commit_file_response')
    CREATE_CHANNEL_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    LIST_CHANNEL_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    GET_CHANNEL_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    DELETE_CHANNEL_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    COMMIT_FILE_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    create_channel_response: CreateChannelResponse
    list_channel_response: ListChannelResponse
    get_channel_response: GetChannelResponse
    delete_channel_response: DeleteChannelResponse
    commit_file_response: CommitFileResponse

    def __init__(self, create_channel_response: _Optional[_Union[CreateChannelResponse, _Mapping]]=..., list_channel_response: _Optional[_Union[ListChannelResponse, _Mapping]]=..., get_channel_response: _Optional[_Union[GetChannelResponse, _Mapping]]=..., delete_channel_response: _Optional[_Union[DeleteChannelResponse, _Mapping]]=..., commit_file_response: _Optional[_Union[CommitFileResponse, _Mapping]]=...) -> None:
        ...