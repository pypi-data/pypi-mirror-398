from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class VClusterSize(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    XSMALL: _ClassVar[VClusterSize]
    SMALL: _ClassVar[VClusterSize]
    MEDIUM: _ClassVar[VClusterSize]
    LARGE: _ClassVar[VClusterSize]
    XLARGE: _ClassVar[VClusterSize]
    X2LARGE: _ClassVar[VClusterSize]
    X3LARGE: _ClassVar[VClusterSize]
    X4LARGE: _ClassVar[VClusterSize]
    X5LARGE: _ClassVar[VClusterSize]
    X6LARGE: _ClassVar[VClusterSize]
    CUSTOMIZED3: _ClassVar[VClusterSize]
    CUSTOMIZED52: _ClassVar[VClusterSize]
    CUSTOMIZED48: _ClassVar[VClusterSize]
    CUSTOMIZED12: _ClassVar[VClusterSize]

class VClusterType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    GENERAL: _ClassVar[VClusterType]
    ANALYTICS: _ClassVar[VClusterType]

class ScalePolicy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STANDARD: _ClassVar[ScalePolicy]

class VirtualClusterState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SUSPENDED: _ClassVar[VirtualClusterState]
    RUNNING: _ClassVar[VirtualClusterState]
    STARTING: _ClassVar[VirtualClusterState]
    SCALING_UP: _ClassVar[VirtualClusterState]
    SCALING_DOWN: _ClassVar[VirtualClusterState]
    SUSPENDING: _ClassVar[VirtualClusterState]
    DROPPING: _ClassVar[VirtualClusterState]
    ERROR: _ClassVar[VirtualClusterState]
    DELETED: _ClassVar[VirtualClusterState]
    RESUMING: _ClassVar[VirtualClusterState]
    CANCELLING: _ClassVar[VirtualClusterState]
    UPGRADING: _ClassVar[VirtualClusterState]

class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SUCCEEDED: _ClassVar[Status]
    FAILED: _ClassVar[Status]
XSMALL: VClusterSize
SMALL: VClusterSize
MEDIUM: VClusterSize
LARGE: VClusterSize
XLARGE: VClusterSize
X2LARGE: VClusterSize
X3LARGE: VClusterSize
X4LARGE: VClusterSize
X5LARGE: VClusterSize
X6LARGE: VClusterSize
CUSTOMIZED3: VClusterSize
CUSTOMIZED52: VClusterSize
CUSTOMIZED48: VClusterSize
CUSTOMIZED12: VClusterSize
GENERAL: VClusterType
ANALYTICS: VClusterType
STANDARD: ScalePolicy
SUSPENDED: VirtualClusterState
RUNNING: VirtualClusterState
STARTING: VirtualClusterState
SCALING_UP: VirtualClusterState
SCALING_DOWN: VirtualClusterState
SUSPENDING: VirtualClusterState
DROPPING: VirtualClusterState
ERROR: VirtualClusterState
DELETED: VirtualClusterState
RESUMING: VirtualClusterState
CANCELLING: VirtualClusterState
UPGRADING: VirtualClusterState
SUCCEEDED: Status
FAILED: Status

class AnalyticsProperties(_message.Message):
    __slots__ = ('min_replicas', 'max_replicas', 'max_concurrency_per_replica', 'scale_policy', 'preload_tables')
    MIN_REPLICAS_FIELD_NUMBER: _ClassVar[int]
    MAX_REPLICAS_FIELD_NUMBER: _ClassVar[int]
    MAX_CONCURRENCY_PER_REPLICA_FIELD_NUMBER: _ClassVar[int]
    SCALE_POLICY_FIELD_NUMBER: _ClassVar[int]
    PRELOAD_TABLES_FIELD_NUMBER: _ClassVar[int]
    min_replicas: int
    max_replicas: int
    max_concurrency_per_replica: int
    scale_policy: ScalePolicy
    preload_tables: str

    def __init__(self, min_replicas: _Optional[int]=..., max_replicas: _Optional[int]=..., max_concurrency_per_replica: _Optional[int]=..., scale_policy: _Optional[_Union[ScalePolicy, str]]=..., preload_tables: _Optional[str]=...) -> None:
        ...

class GeneralProperties(_message.Message):
    __slots__ = ('cluster_max_size',)
    CLUSTER_MAX_SIZE_FIELD_NUMBER: _ClassVar[int]
    cluster_max_size: VClusterSize

    def __init__(self, cluster_max_size: _Optional[_Union[VClusterSize, str]]=...) -> None:
        ...

class VCResource(_message.Message):
    __slots__ = ('memory', 'virtual_cores')
    MEMORY_FIELD_NUMBER: _ClassVar[int]
    VIRTUAL_CORES_FIELD_NUMBER: _ClassVar[int]
    memory: int
    virtual_cores: int

    def __init__(self, memory: _Optional[int]=..., virtual_cores: _Optional[int]=...) -> None:
        ...

class VirtualClusterProperties(_message.Message):
    __slots__ = ('name', 'instance_id', 'workspace_id', 'cluster_type', 'cluster_size', 'analytics_properties', 'general_properties', 'auto_stop_latency_sec', 'auto_start_enabled', 'tag', 'comment', 'query_process_time_limit_sec', 'create_time_ms', 'last_modify_time_ms', 'creator_user_id', 'version')

    class TagEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_TYPE_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_SIZE_FIELD_NUMBER: _ClassVar[int]
    ANALYTICS_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    GENERAL_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    AUTO_STOP_LATENCY_SEC_FIELD_NUMBER: _ClassVar[int]
    AUTO_START_ENABLED_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    QUERY_PROCESS_TIME_LIMIT_SEC_FIELD_NUMBER: _ClassVar[int]
    CREATE_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    LAST_MODIFY_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    CREATOR_USER_ID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    name: str
    instance_id: int
    workspace_id: int
    cluster_type: VClusterType
    cluster_size: VClusterSize
    analytics_properties: AnalyticsProperties
    general_properties: GeneralProperties
    auto_stop_latency_sec: int
    auto_start_enabled: bool
    tag: _containers.ScalarMap[str, str]
    comment: str
    query_process_time_limit_sec: int
    create_time_ms: int
    last_modify_time_ms: int
    creator_user_id: int
    version: str

    def __init__(self, name: _Optional[str]=..., instance_id: _Optional[int]=..., workspace_id: _Optional[int]=..., cluster_type: _Optional[_Union[VClusterType, str]]=..., cluster_size: _Optional[_Union[VClusterSize, str]]=..., analytics_properties: _Optional[_Union[AnalyticsProperties, _Mapping]]=..., general_properties: _Optional[_Union[GeneralProperties, _Mapping]]=..., auto_stop_latency_sec: _Optional[int]=..., auto_start_enabled: bool=..., tag: _Optional[_Mapping[str, str]]=..., comment: _Optional[str]=..., query_process_time_limit_sec: _Optional[int]=..., create_time_ms: _Optional[int]=..., last_modify_time_ms: _Optional[int]=..., creator_user_id: _Optional[int]=..., version: _Optional[str]=...) -> None:
        ...

class RequestInfo(_message.Message):
    __slots__ = ('request_id', 'operator_token')
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATOR_TOKEN_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    operator_token: bytes

    def __init__(self, request_id: _Optional[str]=..., operator_token: _Optional[bytes]=...) -> None:
        ...

class ResponseInfo(_message.Message):
    __slots__ = ('request_id', 'status', 'error_code', 'error_msg')
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    ERROR_MSG_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    status: Status
    error_code: str
    error_msg: str

    def __init__(self, request_id: _Optional[str]=..., status: _Optional[_Union[Status, str]]=..., error_code: _Optional[str]=..., error_msg: _Optional[str]=...) -> None:
        ...

class VClusterIdentifier(_message.Message):
    __slots__ = ('instance_id', 'workspace_id', 'name')
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    instance_id: int
    workspace_id: int
    name: str

    def __init__(self, instance_id: _Optional[int]=..., workspace_id: _Optional[int]=..., name: _Optional[str]=...) -> None:
        ...