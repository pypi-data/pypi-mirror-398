from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class IGSTableType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NORMAL: _ClassVar[IGSTableType]
    CLUSTER: _ClassVar[IGSTableType]
    ACID: _ClassVar[IGSTableType]
    UNKNOWN: _ClassVar[IGSTableType]

class Code(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SUCCESS: _ClassVar[Code]
    FAILED: _ClassVar[Code]
    IGS_WORKER_REGISTED: _ClassVar[Code]
    THROTTLED: _ClassVar[Code]
    NOT_FOUND: _ClassVar[Code]
    ALREADY_PRESENT: _ClassVar[Code]
    TABLE_EXIST: _ClassVar[Code]
    TABLE_DROPPED: _ClassVar[Code]
    CORRUPTION: _ClassVar[Code]

class MethodEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    GATEWAY_RPC_CALL: _ClassVar[MethodEnum]
    GET_TABLE_META: _ClassVar[MethodEnum]
    CREATE_TABLET: _ClassVar[MethodEnum]
    GET_MUTATE_WORKER: _ClassVar[MethodEnum]
    COMMIT_TABLET: _ClassVar[MethodEnum]
    DROP_TABLET: _ClassVar[MethodEnum]
    CHECK_TABLE_EXISTS: _ClassVar[MethodEnum]
    CREATE_BULK_LOAD_STREAM: _ClassVar[MethodEnum]
    GET_BULK_LOAD_STREAM: _ClassVar[MethodEnum]
    COMMIT_BULK_LOAD_STREAM: _ClassVar[MethodEnum]
    OPEN_BULK_LOAD_STREAM_WRITER: _ClassVar[MethodEnum]
    FINISH_BULK_LOAD_STREAM_WRITER: _ClassVar[MethodEnum]
    CREATE_OR_GET_STREAM_V2: _ClassVar[MethodEnum]
    CLOSE_STREAM_V2: _ClassVar[MethodEnum]
    GET_ROUTE_WORKER_V2: _ClassVar[MethodEnum]
    CREATE_BULK_LOAD_STREAM_V2: _ClassVar[MethodEnum]
    GET_BULK_LOAD_STREAM_V2: _ClassVar[MethodEnum]
    COMMIT_BULK_LOAD_STREAM_V2: _ClassVar[MethodEnum]
    OPEN_BULK_LOAD_STREAM_WRITER_V2: _ClassVar[MethodEnum]
    FINISH_BULK_LOAD_STREAM_WRITER_V2: _ClassVar[MethodEnum]
    GET_BULK_LOAD_STREAM_STS_TOKEN_V2: _ClassVar[MethodEnum]
    COMMIT_V2: _ClassVar[MethodEnum]
    ASYNC_COMMIT_V2: _ClassVar[MethodEnum]
    CHECK_COMMIT_RESULT_V2: _ClassVar[MethodEnum]
    GET_ROUTER_CONTROLLER_ADDRESS: _ClassVar[MethodEnum]
    SCHEMA_CHANGE: _ClassVar[MethodEnum]
    MAINTAIN_TABLETS: _ClassVar[MethodEnum]
NORMAL: IGSTableType
CLUSTER: IGSTableType
ACID: IGSTableType
UNKNOWN: IGSTableType
SUCCESS: Code
FAILED: Code
IGS_WORKER_REGISTED: Code
THROTTLED: Code
NOT_FOUND: Code
ALREADY_PRESENT: Code
TABLE_EXIST: Code
TABLE_DROPPED: Code
CORRUPTION: Code
GATEWAY_RPC_CALL: MethodEnum
GET_TABLE_META: MethodEnum
CREATE_TABLET: MethodEnum
GET_MUTATE_WORKER: MethodEnum
COMMIT_TABLET: MethodEnum
DROP_TABLET: MethodEnum
CHECK_TABLE_EXISTS: MethodEnum
CREATE_BULK_LOAD_STREAM: MethodEnum
GET_BULK_LOAD_STREAM: MethodEnum
COMMIT_BULK_LOAD_STREAM: MethodEnum
OPEN_BULK_LOAD_STREAM_WRITER: MethodEnum
FINISH_BULK_LOAD_STREAM_WRITER: MethodEnum
CREATE_OR_GET_STREAM_V2: MethodEnum
CLOSE_STREAM_V2: MethodEnum
GET_ROUTE_WORKER_V2: MethodEnum
CREATE_BULK_LOAD_STREAM_V2: MethodEnum
GET_BULK_LOAD_STREAM_V2: MethodEnum
COMMIT_BULK_LOAD_STREAM_V2: MethodEnum
OPEN_BULK_LOAD_STREAM_WRITER_V2: MethodEnum
FINISH_BULK_LOAD_STREAM_WRITER_V2: MethodEnum
GET_BULK_LOAD_STREAM_STS_TOKEN_V2: MethodEnum
COMMIT_V2: MethodEnum
ASYNC_COMMIT_V2: MethodEnum
CHECK_COMMIT_RESULT_V2: MethodEnum
GET_ROUTER_CONTROLLER_ADDRESS: MethodEnum
SCHEMA_CHANGE: MethodEnum
MAINTAIN_TABLETS: MethodEnum

class ResponseStatus(_message.Message):
    __slots__ = ('code', 'message', 'request_id')
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    code: Code
    message: str
    request_id: str

    def __init__(self, code: _Optional[_Union[Code, str]]=..., message: _Optional[str]=..., request_id: _Optional[str]=...) -> None:
        ...

class VersionInfo(_message.Message):
    __slots__ = ('name', 'version')
    NAME_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    name: str
    version: int

    def __init__(self, name: _Optional[str]=..., version: _Optional[int]=...) -> None:
        ...

class GatewayRequest(_message.Message):
    __slots__ = ('methodEnumValue', 'message', 'instanceId', 'userId', 'versionInfo')
    METHODENUMVALUE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    INSTANCEID_FIELD_NUMBER: _ClassVar[int]
    USERID_FIELD_NUMBER: _ClassVar[int]
    VERSIONINFO_FIELD_NUMBER: _ClassVar[int]
    methodEnumValue: int
    message: str
    instanceId: int
    userId: int
    versionInfo: VersionInfo

    def __init__(self, methodEnumValue: _Optional[int]=..., message: _Optional[str]=..., instanceId: _Optional[int]=..., userId: _Optional[int]=..., versionInfo: _Optional[_Union[VersionInfo, _Mapping]]=...) -> None:
        ...

class GatewayResponse(_message.Message):
    __slots__ = ('status', 'message')
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus
    message: str

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=..., message: _Optional[str]=...) -> None:
        ...