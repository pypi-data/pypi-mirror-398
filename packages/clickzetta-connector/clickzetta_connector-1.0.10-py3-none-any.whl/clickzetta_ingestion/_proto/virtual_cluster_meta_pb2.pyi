import virtual_cluster_pb2 as _virtual_cluster_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class AnalyticsProperties(_message.Message):
    __slots__ = ('min_replicas', 'max_replicas', 'max_concurrency_per_replica', 'scale_policy', 'cur_replicas', 'preload_tables')
    MIN_REPLICAS_FIELD_NUMBER: _ClassVar[int]
    MAX_REPLICAS_FIELD_NUMBER: _ClassVar[int]
    MAX_CONCURRENCY_PER_REPLICA_FIELD_NUMBER: _ClassVar[int]
    SCALE_POLICY_FIELD_NUMBER: _ClassVar[int]
    CUR_REPLICAS_FIELD_NUMBER: _ClassVar[int]
    PRELOAD_TABLES_FIELD_NUMBER: _ClassVar[int]
    min_replicas: int
    max_replicas: int
    max_concurrency_per_replica: int
    scale_policy: _virtual_cluster_pb2.ScalePolicy
    cur_replicas: int
    preload_tables: str

    def __init__(self, min_replicas: _Optional[int]=..., max_replicas: _Optional[int]=..., max_concurrency_per_replica: _Optional[int]=..., scale_policy: _Optional[_Union[_virtual_cluster_pb2.ScalePolicy, str]]=..., cur_replicas: _Optional[int]=..., preload_tables: _Optional[str]=...) -> None:
        ...

class GeneralProperties(_message.Message):
    __slots__ = ('cluster_max_size',)
    CLUSTER_MAX_SIZE_FIELD_NUMBER: _ClassVar[int]
    cluster_max_size: _virtual_cluster_pb2.VClusterSize

    def __init__(self, cluster_max_size: _Optional[_Union[_virtual_cluster_pb2.VClusterSize, str]]=...) -> None:
        ...

class JobInfo(_message.Message):
    __slots__ = ('jobs_running', 'jobs_in_queue')
    JOBS_RUNNING_FIELD_NUMBER: _ClassVar[int]
    JOBS_IN_QUEUE_FIELD_NUMBER: _ClassVar[int]
    jobs_running: int
    jobs_in_queue: int

    def __init__(self, jobs_running: _Optional[int]=..., jobs_in_queue: _Optional[int]=...) -> None:
        ...

class VirtualClusterMeta(_message.Message):
    __slots__ = ('cluster_type', 'cluster_size', 'analytics_properties', 'general_properties', 'auto_stop_latency_sec', 'auto_start_enabled', 'tag', 'query_process_time_limit_sec', 'state', 'pre_state', 'error_msg', 'job_info', 'workspace_id', 'vc_id', 'state_info', 'version')

    class TagEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    CLUSTER_TYPE_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_SIZE_FIELD_NUMBER: _ClassVar[int]
    ANALYTICS_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    GENERAL_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    AUTO_STOP_LATENCY_SEC_FIELD_NUMBER: _ClassVar[int]
    AUTO_START_ENABLED_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    QUERY_PROCESS_TIME_LIMIT_SEC_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    PRE_STATE_FIELD_NUMBER: _ClassVar[int]
    ERROR_MSG_FIELD_NUMBER: _ClassVar[int]
    JOB_INFO_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    STATE_INFO_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    cluster_type: _virtual_cluster_pb2.VClusterType
    cluster_size: _virtual_cluster_pb2.VClusterSize
    analytics_properties: AnalyticsProperties
    general_properties: GeneralProperties
    auto_stop_latency_sec: int
    auto_start_enabled: bool
    tag: _containers.ScalarMap[str, str]
    query_process_time_limit_sec: int
    state: _virtual_cluster_pb2.VirtualClusterState
    pre_state: _virtual_cluster_pb2.VirtualClusterState
    error_msg: str
    job_info: JobInfo
    workspace_id: int
    vc_id: int
    state_info: str
    version: str

    def __init__(self, cluster_type: _Optional[_Union[_virtual_cluster_pb2.VClusterType, str]]=..., cluster_size: _Optional[_Union[_virtual_cluster_pb2.VClusterSize, str]]=..., analytics_properties: _Optional[_Union[AnalyticsProperties, _Mapping]]=..., general_properties: _Optional[_Union[GeneralProperties, _Mapping]]=..., auto_stop_latency_sec: _Optional[int]=..., auto_start_enabled: bool=..., tag: _Optional[_Mapping[str, str]]=..., query_process_time_limit_sec: _Optional[int]=..., state: _Optional[_Union[_virtual_cluster_pb2.VirtualClusterState, str]]=..., pre_state: _Optional[_Union[_virtual_cluster_pb2.VirtualClusterState, str]]=..., error_msg: _Optional[str]=..., job_info: _Optional[_Union[JobInfo, _Mapping]]=..., workspace_id: _Optional[int]=..., vc_id: _Optional[int]=..., state_info: _Optional[str]=..., version: _Optional[str]=...) -> None:
        ...