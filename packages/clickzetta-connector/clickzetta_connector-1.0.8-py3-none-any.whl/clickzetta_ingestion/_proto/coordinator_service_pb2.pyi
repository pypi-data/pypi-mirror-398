import service_common_pb2 as _service_common_pb2
import table_common_pb2 as _table_common_pb2
import metadata_entity_pb2 as _metadata_entity_pb2
import object_identifier_pb2 as _object_identifier_pb2
import file_system_pb2 as _file_system_pb2
import job_meta_pb2 as _job_meta_pb2
import job_pb2 as _job_pb2
import encryption_pb2 as _encryption_pb2
import property_pb2 as _property_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class JobRequestMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN: _ClassVar[JobRequestMode]
    HYBRID: _ClassVar[JobRequestMode]
    ASYNC: _ClassVar[JobRequestMode]
    SYNC: _ClassVar[JobRequestMode]

class EventCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEFAULT_EVENT_CODE: _ClassVar[EventCode]
    CZ_JOB_PROFILING_COORDINATOR_CLIENT_SUBMIT: _ClassVar[EventCode]
    CZ_JOB_PROFILING_RECEIVE_SUBMIT: _ClassVar[EventCode]
    CZ_JOB_PROFILING_PRECHECK_START: _ClassVar[EventCode]
    CZ_JOB_PROFILING_PRECHECK_END: _ClassVar[EventCode]
    CZ_JOB_PROFILING_JOB_META_CREATED: _ClassVar[EventCode]
    CZ_JOB_PROFILING_COORDINATOR_QUEUE: _ClassVar[EventCode]
    CZ_JOB_PROFILING_COORDINATOR_PRE_RUN: _ClassVar[EventCode]
    CZ_JOB_PROFILING_COORDINATOR_RUN: _ClassVar[EventCode]
    CZ_JOB_PROFILING_PLAN_CREATED: _ClassVar[EventCode]
    CZ_JOB_PROFILING_SUBMIT_TO_RM: _ClassVar[EventCode]
    CZ_JOB_PROFILING_VC_RUNNING: _ClassVar[EventCode]
    CZ_JOB_PROFILING_RM_APP_CREATED: _ClassVar[EventCode]
    CZ_JOB_PROFILING_GOT_FIRST_RESOURCE_START_RUN: _ClassVar[EventCode]
    CZ_JOB_PROFILING_DAG_COMPLETE: _ClassVar[EventCode]
    CZ_JOB_PROFILING_QUICK_ADHOC_FINISH: _ClassVar[EventCode]
    CZ_JOB_PROFILING_QUERY_SUCCEED: _ClassVar[EventCode]
    CZ_JOB_PROFILING_RUN_FINISH: _ClassVar[EventCode]
    CZ_JOB_PROFILING_KEY_PATH_END: _ClassVar[EventCode]
    CZ_JOB_PROFILING_START_PERSIST: _ClassVar[EventCode]
    CZ_JOB_PROFILING_SUMMARY_UPLOADED: _ClassVar[EventCode]
    CZ_JOB_PROFILING_RECYCLE: _ClassVar[EventCode]
    CZ_JOB_PROFILING_FINISHED: _ClassVar[EventCode]

class ResultFormat(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TEXT: _ClassVar[ResultFormat]
    CSV: _ClassVar[ResultFormat]
    JSON: _ClassVar[ResultFormat]
    PARQUET: _ClassVar[ResultFormat]
    HIVE_RESULT: _ClassVar[ResultFormat]
    ARROW: _ClassVar[ResultFormat]
    MYSQL_PROTOCOL: _ClassVar[ResultFormat]
    NONE: _ClassVar[ResultFormat]

class ResultType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BUFFERED_STREAM: _ClassVar[ResultType]
    FILE_SYSTEM: _ClassVar[ResultType]

class RescheduleJobType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONTINUOUS_JOB: _ClassVar[RescheduleJobType]
    GP_QUEUEING_JOB: _ClassVar[RescheduleJobType]

class CoordinatorState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STARTING: _ClassVar[CoordinatorState]
    NORMAL: _ClassVar[CoordinatorState]
    DRAINING: _ClassVar[CoordinatorState]
    TERMINATING: _ClassVar[CoordinatorState]
    DISCONNECTED: _ClassVar[CoordinatorState]
    JUDGED_TO_DISCONNECT: _ClassVar[CoordinatorState]

class JobScheduleStrategy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    JOB_AFFINITY: _ClassVar[JobScheduleStrategy]
    JOB_AFFINITY_BASED_LOAD_BALANCE: _ClassVar[JobScheduleStrategy]
    JOB_AFFINITY_BASED_MEMORY: _ClassVar[JobScheduleStrategy]
    RANDOM: _ClassVar[JobScheduleStrategy]

class UpgradeActionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    START_UPGRADE: _ClassVar[UpgradeActionType]
    FINISH_UPGRADE: _ClassVar[UpgradeActionType]
    ABORT_UPGRADE: _ClassVar[UpgradeActionType]
UNKNOWN: JobRequestMode
HYBRID: JobRequestMode
ASYNC: JobRequestMode
SYNC: JobRequestMode
DEFAULT_EVENT_CODE: EventCode
CZ_JOB_PROFILING_COORDINATOR_CLIENT_SUBMIT: EventCode
CZ_JOB_PROFILING_RECEIVE_SUBMIT: EventCode
CZ_JOB_PROFILING_PRECHECK_START: EventCode
CZ_JOB_PROFILING_PRECHECK_END: EventCode
CZ_JOB_PROFILING_JOB_META_CREATED: EventCode
CZ_JOB_PROFILING_COORDINATOR_QUEUE: EventCode
CZ_JOB_PROFILING_COORDINATOR_PRE_RUN: EventCode
CZ_JOB_PROFILING_COORDINATOR_RUN: EventCode
CZ_JOB_PROFILING_PLAN_CREATED: EventCode
CZ_JOB_PROFILING_SUBMIT_TO_RM: EventCode
CZ_JOB_PROFILING_VC_RUNNING: EventCode
CZ_JOB_PROFILING_RM_APP_CREATED: EventCode
CZ_JOB_PROFILING_GOT_FIRST_RESOURCE_START_RUN: EventCode
CZ_JOB_PROFILING_DAG_COMPLETE: EventCode
CZ_JOB_PROFILING_QUICK_ADHOC_FINISH: EventCode
CZ_JOB_PROFILING_QUERY_SUCCEED: EventCode
CZ_JOB_PROFILING_RUN_FINISH: EventCode
CZ_JOB_PROFILING_KEY_PATH_END: EventCode
CZ_JOB_PROFILING_START_PERSIST: EventCode
CZ_JOB_PROFILING_SUMMARY_UPLOADED: EventCode
CZ_JOB_PROFILING_RECYCLE: EventCode
CZ_JOB_PROFILING_FINISHED: EventCode
TEXT: ResultFormat
CSV: ResultFormat
JSON: ResultFormat
PARQUET: ResultFormat
HIVE_RESULT: ResultFormat
ARROW: ResultFormat
MYSQL_PROTOCOL: ResultFormat
NONE: ResultFormat
BUFFERED_STREAM: ResultType
FILE_SYSTEM: ResultType
CONTINUOUS_JOB: RescheduleJobType
GP_QUEUEING_JOB: RescheduleJobType
STARTING: CoordinatorState
NORMAL: CoordinatorState
DRAINING: CoordinatorState
TERMINATING: CoordinatorState
DISCONNECTED: CoordinatorState
JUDGED_TO_DISCONNECT: CoordinatorState
JOB_AFFINITY: JobScheduleStrategy
JOB_AFFINITY_BASED_LOAD_BALANCE: JobScheduleStrategy
JOB_AFFINITY_BASED_MEMORY: JobScheduleStrategy
RANDOM: JobScheduleStrategy
START_UPGRADE: UpgradeActionType
FINISH_UPGRADE: UpgradeActionType
ABORT_UPGRADE: UpgradeActionType

class JobID(_message.Message):
    __slots__ = ('id', 'workspace', 'instance_id')
    ID_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    workspace: str
    instance_id: int

    def __init__(self, id: _Optional[str]=..., workspace: _Optional[str]=..., instance_id: _Optional[int]=...) -> None:
        ...

class Account(_message.Message):
    __slots__ = ('user_id', 'access_token')
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    user_id: int
    access_token: str

    def __init__(self, user_id: _Optional[int]=..., access_token: _Optional[str]=...) -> None:
        ...

class ClientContextInfo(_message.Message):
    __slots__ = ('config_statements', 'context_json')
    CONFIG_STATEMENTS_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_JSON_FIELD_NUMBER: _ClassVar[int]
    config_statements: _containers.RepeatedScalarFieldContainer[str]
    context_json: str

    def __init__(self, config_statements: _Optional[_Iterable[str]]=..., context_json: _Optional[str]=...) -> None:
        ...

class JobDesc(_message.Message):
    __slots__ = ('virtual_cluster', 'type', 'job_id', 'job_name', 'account', 'request_mode', 'hybrid_polling_timeout', 'job_config', 'sql_job', 'job_timeout_ms', 'user_agent', 'priority', 'priority_string', 'client_context', 'query_tag', 'jdbc_domain', 'client_profiling', 'sub_type')

    class JobConfigEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    VIRTUAL_CLUSTER_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    JOB_NAME_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    REQUEST_MODE_FIELD_NUMBER: _ClassVar[int]
    HYBRID_POLLING_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    JOB_CONFIG_FIELD_NUMBER: _ClassVar[int]
    SQL_JOB_FIELD_NUMBER: _ClassVar[int]
    JOB_TIMEOUT_MS_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_STRING_FIELD_NUMBER: _ClassVar[int]
    CLIENT_CONTEXT_FIELD_NUMBER: _ClassVar[int]
    QUERY_TAG_FIELD_NUMBER: _ClassVar[int]
    JDBC_DOMAIN_FIELD_NUMBER: _ClassVar[int]
    CLIENT_PROFILING_FIELD_NUMBER: _ClassVar[int]
    SUB_TYPE_FIELD_NUMBER: _ClassVar[int]
    virtual_cluster: str
    type: _job_meta_pb2.JobType
    job_id: JobID
    job_name: str
    account: Account
    request_mode: JobRequestMode
    hybrid_polling_timeout: int
    job_config: _containers.ScalarMap[str, str]
    sql_job: _job_meta_pb2.SQLJob
    job_timeout_ms: int
    user_agent: str
    priority: int
    priority_string: str
    client_context: ClientContextInfo
    query_tag: str
    jdbc_domain: str
    client_profiling: _job_meta_pb2.JobProfiling
    sub_type: _job_meta_pb2.JobSubType

    def __init__(self, virtual_cluster: _Optional[str]=..., type: _Optional[_Union[_job_meta_pb2.JobType, str]]=..., job_id: _Optional[_Union[JobID, _Mapping]]=..., job_name: _Optional[str]=..., account: _Optional[_Union[Account, _Mapping]]=..., request_mode: _Optional[_Union[JobRequestMode, str]]=..., hybrid_polling_timeout: _Optional[int]=..., job_config: _Optional[_Mapping[str, str]]=..., sql_job: _Optional[_Union[_job_meta_pb2.SQLJob, _Mapping]]=..., job_timeout_ms: _Optional[int]=..., user_agent: _Optional[str]=..., priority: _Optional[int]=..., priority_string: _Optional[str]=..., client_context: _Optional[_Union[ClientContextInfo, _Mapping]]=..., query_tag: _Optional[str]=..., jdbc_domain: _Optional[str]=..., client_profiling: _Optional[_Union[_job_meta_pb2.JobProfiling, _Mapping]]=..., sub_type: _Optional[_Union[_job_meta_pb2.JobSubType, str]]=...) -> None:
        ...

class JobStatus(_message.Message):
    __slots__ = ('job_id', 'state', 'message', 'submit_time', 'start_time', 'end_time', 'pending_time', 'running_time', 'status', 'execution_log', 'error_code', 'job_profiling')
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SUBMIT_TIME_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    PENDING_TIME_FIELD_NUMBER: _ClassVar[int]
    RUNNING_TIME_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_LOG_FIELD_NUMBER: _ClassVar[int]
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    JOB_PROFILING_FIELD_NUMBER: _ClassVar[int]
    job_id: JobID
    state: str
    message: str
    submit_time: int
    start_time: int
    end_time: int
    pending_time: int
    running_time: int
    status: _job_meta_pb2.JobStatus
    execution_log: _containers.RepeatedScalarFieldContainer[str]
    error_code: str
    job_profiling: _job_meta_pb2.JobProfiling

    def __init__(self, job_id: _Optional[_Union[JobID, _Mapping]]=..., state: _Optional[str]=..., message: _Optional[str]=..., submit_time: _Optional[int]=..., start_time: _Optional[int]=..., end_time: _Optional[int]=..., pending_time: _Optional[int]=..., running_time: _Optional[int]=..., status: _Optional[_Union[_job_meta_pb2.JobStatus, str]]=..., execution_log: _Optional[_Iterable[str]]=..., error_code: _Optional[str]=..., job_profiling: _Optional[_Union[_job_meta_pb2.JobProfiling, _Mapping]]=...) -> None:
        ...

class JobResultData(_message.Message):
    __slots__ = ('data',)
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: _containers.RepeatedScalarFieldContainer[bytes]

    def __init__(self, data: _Optional[_Iterable[bytes]]=...) -> None:
        ...

class LocationFileInfo(_message.Message):
    __slots__ = ('file_path', 'file_size')
    FILE_PATH_FIELD_NUMBER: _ClassVar[int]
    FILE_SIZE_FIELD_NUMBER: _ClassVar[int]
    file_path: str
    file_size: int

    def __init__(self, file_path: _Optional[str]=..., file_size: _Optional[int]=...) -> None:
        ...

class JobResultLocation(_message.Message):
    __slots__ = ('location', 'file_system', 'sts_ak_id', 'sts_ak_secret', 'sts_token', 'oss_endpoint', 'oss_internal_endpoint', 'location_files', 'object_storage_region', 'presigned_urls')
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    FILE_SYSTEM_FIELD_NUMBER: _ClassVar[int]
    STS_AK_ID_FIELD_NUMBER: _ClassVar[int]
    STS_AK_SECRET_FIELD_NUMBER: _ClassVar[int]
    STS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    OSS_ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    OSS_INTERNAL_ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FILES_FIELD_NUMBER: _ClassVar[int]
    OBJECT_STORAGE_REGION_FIELD_NUMBER: _ClassVar[int]
    PRESIGNED_URLS_FIELD_NUMBER: _ClassVar[int]
    location: _containers.RepeatedScalarFieldContainer[str]
    file_system: _file_system_pb2.FileSystemType
    sts_ak_id: str
    sts_ak_secret: str
    sts_token: str
    oss_endpoint: str
    oss_internal_endpoint: str
    location_files: _containers.RepeatedCompositeFieldContainer[LocationFileInfo]
    object_storage_region: str
    presigned_urls: _containers.RepeatedScalarFieldContainer[str]

    def __init__(self, location: _Optional[_Iterable[str]]=..., file_system: _Optional[_Union[_file_system_pb2.FileSystemType, str]]=..., sts_ak_id: _Optional[str]=..., sts_ak_secret: _Optional[str]=..., sts_token: _Optional[str]=..., oss_endpoint: _Optional[str]=..., oss_internal_endpoint: _Optional[str]=..., location_files: _Optional[_Iterable[_Union[LocationFileInfo, _Mapping]]]=..., object_storage_region: _Optional[str]=..., presigned_urls: _Optional[_Iterable[str]]=...) -> None:
        ...

class ResultStatistics(_message.Message):
    __slots__ = ('deleted_rows', 'inserted_rows', 'copied_delta_rows', 'added_file_count', 'deleted_file_count', 'added_delta_file_count', 'copied_delta_file_count', 'table')
    DELETED_ROWS_FIELD_NUMBER: _ClassVar[int]
    INSERTED_ROWS_FIELD_NUMBER: _ClassVar[int]
    COPIED_DELTA_ROWS_FIELD_NUMBER: _ClassVar[int]
    ADDED_FILE_COUNT_FIELD_NUMBER: _ClassVar[int]
    DELETED_FILE_COUNT_FIELD_NUMBER: _ClassVar[int]
    ADDED_DELTA_FILE_COUNT_FIELD_NUMBER: _ClassVar[int]
    COPIED_DELTA_FILE_COUNT_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    deleted_rows: int
    inserted_rows: int
    copied_delta_rows: int
    added_file_count: int
    deleted_file_count: int
    added_delta_file_count: int
    copied_delta_file_count: int
    table: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, deleted_rows: _Optional[int]=..., inserted_rows: _Optional[int]=..., copied_delta_rows: _Optional[int]=..., added_file_count: _Optional[int]=..., deleted_file_count: _Optional[int]=..., added_delta_file_count: _Optional[int]=..., copied_delta_file_count: _Optional[int]=..., table: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class JobResultSetMetadata(_message.Message):
    __slots__ = ('num_rows', 'format', 'type', 'fields', 'time_zone')
    NUM_ROWS_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    TIME_ZONE_FIELD_NUMBER: _ClassVar[int]
    num_rows: int
    format: ResultFormat
    type: ResultType
    fields: _containers.RepeatedCompositeFieldContainer[_table_common_pb2.FieldSchema]
    time_zone: str

    def __init__(self, num_rows: _Optional[int]=..., format: _Optional[_Union[ResultFormat, str]]=..., type: _Optional[_Union[ResultType, str]]=..., fields: _Optional[_Iterable[_Union[_table_common_pb2.FieldSchema, _Mapping]]]=..., time_zone: _Optional[str]=...) -> None:
        ...

class JobResultSet(_message.Message):
    __slots__ = ('metadata', 'data', 'location', 'stats')
    METADATA_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    STATS_FIELD_NUMBER: _ClassVar[int]
    metadata: JobResultSetMetadata
    data: JobResultData
    location: JobResultLocation
    stats: _containers.RepeatedCompositeFieldContainer[ResultStatistics]

    def __init__(self, metadata: _Optional[_Union[JobResultSetMetadata, _Mapping]]=..., data: _Optional[_Union[JobResultData, _Mapping]]=..., location: _Optional[_Union[JobResultLocation, _Mapping]]=..., stats: _Optional[_Iterable[_Union[ResultStatistics, _Mapping]]]=...) -> None:
        ...

class SubmitJobRequest(_message.Message):
    __slots__ = ('job_desc',)
    JOB_DESC_FIELD_NUMBER: _ClassVar[int]
    job_desc: JobDesc

    def __init__(self, job_desc: _Optional[_Union[JobDesc, _Mapping]]=...) -> None:
        ...

class SubmitJobResponse(_message.Message):
    __slots__ = ('resp_status', 'status', 'result_set')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    status: JobStatus
    result_set: JobResultSet

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., status: _Optional[_Union[JobStatus, _Mapping]]=..., result_set: _Optional[_Union[JobResultSet, _Mapping]]=...) -> None:
        ...

class ListJobsRequest(_message.Message):
    __slots__ = ('account', 'workspace', 'instance_id', 'virtual_cluster', 'job_status', 'min_start_time', 'max_start_time', 'max_size', 'list_in_meta', 'offset', 'order_by', 'ascending', 'priority_string', 'job_id', 'owner_id', 'min_running_time_ms', 'max_running_time_ms', 'query_tag', 'schema', 'priority', 'job_source', 'exclude_job_source', 'job_sub_type', 'exclude_job_sub_type', 'detail', 'force', 'user_agent')

    class ListOrderby(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ORDER_BY_START_TIME: _ClassVar[ListJobsRequest.ListOrderby]
        ORDER_BY_RUNNING_TIME: _ClassVar[ListJobsRequest.ListOrderby]
        ORDER_BY_JOB_PRIORITY: _ClassVar[ListJobsRequest.ListOrderby]
        ORDER_BY_JOB_STATUS: _ClassVar[ListJobsRequest.ListOrderby]
    ORDER_BY_START_TIME: ListJobsRequest.ListOrderby
    ORDER_BY_RUNNING_TIME: ListJobsRequest.ListOrderby
    ORDER_BY_JOB_PRIORITY: ListJobsRequest.ListOrderby
    ORDER_BY_JOB_STATUS: ListJobsRequest.ListOrderby
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    VIRTUAL_CLUSTER_FIELD_NUMBER: _ClassVar[int]
    JOB_STATUS_FIELD_NUMBER: _ClassVar[int]
    MIN_START_TIME_FIELD_NUMBER: _ClassVar[int]
    MAX_START_TIME_FIELD_NUMBER: _ClassVar[int]
    MAX_SIZE_FIELD_NUMBER: _ClassVar[int]
    LIST_IN_META_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    ORDER_BY_FIELD_NUMBER: _ClassVar[int]
    ASCENDING_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_STRING_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    OWNER_ID_FIELD_NUMBER: _ClassVar[int]
    MIN_RUNNING_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    MAX_RUNNING_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    QUERY_TAG_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    JOB_SOURCE_FIELD_NUMBER: _ClassVar[int]
    EXCLUDE_JOB_SOURCE_FIELD_NUMBER: _ClassVar[int]
    JOB_SUB_TYPE_FIELD_NUMBER: _ClassVar[int]
    EXCLUDE_JOB_SUB_TYPE_FIELD_NUMBER: _ClassVar[int]
    DETAIL_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    account: Account
    workspace: str
    instance_id: int
    virtual_cluster: str
    job_status: str
    min_start_time: int
    max_start_time: int
    max_size: int
    list_in_meta: bool
    offset: int
    order_by: ListJobsRequest.ListOrderby
    ascending: bool
    priority_string: str
    job_id: str
    owner_id: int
    min_running_time_ms: int
    max_running_time_ms: int
    query_tag: str
    schema: str
    priority: int
    job_source: int
    exclude_job_source: _containers.RepeatedScalarFieldContainer[int]
    job_sub_type: int
    exclude_job_sub_type: _containers.RepeatedScalarFieldContainer[int]
    detail: bool
    force: bool
    user_agent: str

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., workspace: _Optional[str]=..., instance_id: _Optional[int]=..., virtual_cluster: _Optional[str]=..., job_status: _Optional[str]=..., min_start_time: _Optional[int]=..., max_start_time: _Optional[int]=..., max_size: _Optional[int]=..., list_in_meta: bool=..., offset: _Optional[int]=..., order_by: _Optional[_Union[ListJobsRequest.ListOrderby, str]]=..., ascending: bool=..., priority_string: _Optional[str]=..., job_id: _Optional[str]=..., owner_id: _Optional[int]=..., min_running_time_ms: _Optional[int]=..., max_running_time_ms: _Optional[int]=..., query_tag: _Optional[str]=..., schema: _Optional[str]=..., priority: _Optional[int]=..., job_source: _Optional[int]=..., exclude_job_source: _Optional[_Iterable[int]]=..., job_sub_type: _Optional[int]=..., exclude_job_sub_type: _Optional[_Iterable[int]]=..., detail: bool=..., force: bool=..., user_agent: _Optional[str]=...) -> None:
        ...

class ListJobsResponse(_message.Message):
    __slots__ = ('resp_status', 'job_details', 'total_job_count', 'current_ms')

    class JobDetail(_message.Message):
        __slots__ = ('status', 'job_name', 'owner_id', 'priority', 'job_type', 'statement', 'input_bytes', 'rows_produced', 'virtual_cluster', 'priority_string', 'job_history', 'virtual_cluster_type', 'virtual_cluster_size', 'query_tag', 'query_lite', 'schema', 'job_source', 'job_sub_type', 'query_md5', 'memory_usage_bytes')
        STATUS_FIELD_NUMBER: _ClassVar[int]
        JOB_NAME_FIELD_NUMBER: _ClassVar[int]
        OWNER_ID_FIELD_NUMBER: _ClassVar[int]
        PRIORITY_FIELD_NUMBER: _ClassVar[int]
        JOB_TYPE_FIELD_NUMBER: _ClassVar[int]
        STATEMENT_FIELD_NUMBER: _ClassVar[int]
        INPUT_BYTES_FIELD_NUMBER: _ClassVar[int]
        ROWS_PRODUCED_FIELD_NUMBER: _ClassVar[int]
        VIRTUAL_CLUSTER_FIELD_NUMBER: _ClassVar[int]
        PRIORITY_STRING_FIELD_NUMBER: _ClassVar[int]
        JOB_HISTORY_FIELD_NUMBER: _ClassVar[int]
        VIRTUAL_CLUSTER_TYPE_FIELD_NUMBER: _ClassVar[int]
        VIRTUAL_CLUSTER_SIZE_FIELD_NUMBER: _ClassVar[int]
        QUERY_TAG_FIELD_NUMBER: _ClassVar[int]
        QUERY_LITE_FIELD_NUMBER: _ClassVar[int]
        SCHEMA_FIELD_NUMBER: _ClassVar[int]
        JOB_SOURCE_FIELD_NUMBER: _ClassVar[int]
        JOB_SUB_TYPE_FIELD_NUMBER: _ClassVar[int]
        QUERY_MD5_FIELD_NUMBER: _ClassVar[int]
        MEMORY_USAGE_BYTES_FIELD_NUMBER: _ClassVar[int]
        status: JobStatus
        job_name: str
        owner_id: int
        priority: int
        job_type: str
        statement: _containers.RepeatedScalarFieldContainer[str]
        input_bytes: int
        rows_produced: int
        virtual_cluster: str
        priority_string: str
        job_history: _containers.RepeatedCompositeFieldContainer[_job_meta_pb2.JobHistory]
        virtual_cluster_type: str
        virtual_cluster_size: str
        query_tag: str
        query_lite: _job_meta_pb2.JobMetaLite.QueryLite
        schema: str
        job_source: _job_meta_pb2.JobSource
        job_sub_type: _job_meta_pb2.JobSubType
        query_md5: str
        memory_usage_bytes: int

        def __init__(self, status: _Optional[_Union[JobStatus, _Mapping]]=..., job_name: _Optional[str]=..., owner_id: _Optional[int]=..., priority: _Optional[int]=..., job_type: _Optional[str]=..., statement: _Optional[_Iterable[str]]=..., input_bytes: _Optional[int]=..., rows_produced: _Optional[int]=..., virtual_cluster: _Optional[str]=..., priority_string: _Optional[str]=..., job_history: _Optional[_Iterable[_Union[_job_meta_pb2.JobHistory, _Mapping]]]=..., virtual_cluster_type: _Optional[str]=..., virtual_cluster_size: _Optional[str]=..., query_tag: _Optional[str]=..., query_lite: _Optional[_Union[_job_meta_pb2.JobMetaLite.QueryLite, _Mapping]]=..., schema: _Optional[str]=..., job_source: _Optional[_Union[_job_meta_pb2.JobSource, str]]=..., job_sub_type: _Optional[_Union[_job_meta_pb2.JobSubType, str]]=..., query_md5: _Optional[str]=..., memory_usage_bytes: _Optional[int]=...) -> None:
            ...
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    JOB_DETAILS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_JOB_COUNT_FIELD_NUMBER: _ClassVar[int]
    CURRENT_MS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    job_details: _containers.RepeatedCompositeFieldContainer[ListJobsResponse.JobDetail]
    total_job_count: int
    current_ms: int

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., job_details: _Optional[_Iterable[_Union[ListJobsResponse.JobDetail, _Mapping]]]=..., total_job_count: _Optional[int]=..., current_ms: _Optional[int]=...) -> None:
        ...

class CancelJobRequest(_message.Message):
    __slots__ = ('account', 'job_id', 'force', 'user_agent')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    account: Account
    job_id: JobID
    force: bool
    user_agent: str

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., job_id: _Optional[_Union[JobID, _Mapping]]=..., force: bool=..., user_agent: _Optional[str]=...) -> None:
        ...

class CancelJobResponse(_message.Message):
    __slots__ = ('resp_status',)
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=...) -> None:
        ...

class GetJobRequest(_message.Message):
    __slots__ = ('account', 'job_id', 'user_agent')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    account: Account
    job_id: JobID
    user_agent: str

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., job_id: _Optional[_Union[JobID, _Mapping]]=..., user_agent: _Optional[str]=...) -> None:
        ...

class GetJobResponse(_message.Message):
    __slots__ = ('resp_status', 'job_desc')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    JOB_DESC_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    job_desc: JobDesc

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., job_desc: _Optional[_Union[JobDesc, _Mapping]]=...) -> None:
        ...

class GetJobStatusRequest(_message.Message):
    __slots__ = ('account', 'job_id', 'user_agent')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    account: Account
    job_id: JobID
    user_agent: str

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., job_id: _Optional[_Union[JobID, _Mapping]]=..., user_agent: _Optional[str]=...) -> None:
        ...

class GetJobStatusResponse(_message.Message):
    __slots__ = ('resp_status', 'status')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    status: JobStatus

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., status: _Optional[_Union[JobStatus, _Mapping]]=...) -> None:
        ...

class GetJobResultRequest(_message.Message):
    __slots__ = ('account', 'job_id', 'offset', 'user_agent', 'jdbc_domain')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    JDBC_DOMAIN_FIELD_NUMBER: _ClassVar[int]
    account: Account
    job_id: JobID
    offset: int
    user_agent: str
    jdbc_domain: str

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., job_id: _Optional[_Union[JobID, _Mapping]]=..., offset: _Optional[int]=..., user_agent: _Optional[str]=..., jdbc_domain: _Optional[str]=...) -> None:
        ...

class GetJobResultResponse(_message.Message):
    __slots__ = ('resp_status', 'status', 'result_set')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    status: JobStatus
    result_set: JobResultSet

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., status: _Optional[_Union[JobStatus, _Mapping]]=..., result_set: _Optional[_Union[JobResultSet, _Mapping]]=...) -> None:
        ...

class GetJobProfileRequest(_message.Message):
    __slots__ = ('account', 'job_id', 'user_agent', 'filter_task_summary')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    FILTER_TASK_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    account: Account
    job_id: JobID
    user_agent: str
    filter_task_summary: bool

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., job_id: _Optional[_Union[JobID, _Mapping]]=..., user_agent: _Optional[str]=..., filter_task_summary: bool=...) -> None:
        ...

class GetJobProfileResponse(_message.Message):
    __slots__ = ('resp_status', 'job_desc', 'job_status', 'job_summary', 'job_client', 'job_profiling', 'stats_download_url', 'plan_download_url', 'job_histories', 'current_ms', 'job_meta_lite', 'schema', 'external_scheduled_info', 'job_source', 'job_sub_type', 'presigned_url', 'memory_usage_bytes')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    JOB_DESC_FIELD_NUMBER: _ClassVar[int]
    JOB_STATUS_FIELD_NUMBER: _ClassVar[int]
    JOB_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    JOB_CLIENT_FIELD_NUMBER: _ClassVar[int]
    JOB_PROFILING_FIELD_NUMBER: _ClassVar[int]
    STATS_DOWNLOAD_URL_FIELD_NUMBER: _ClassVar[int]
    PLAN_DOWNLOAD_URL_FIELD_NUMBER: _ClassVar[int]
    JOB_HISTORIES_FIELD_NUMBER: _ClassVar[int]
    CURRENT_MS_FIELD_NUMBER: _ClassVar[int]
    JOB_META_LITE_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_SCHEDULED_INFO_FIELD_NUMBER: _ClassVar[int]
    JOB_SOURCE_FIELD_NUMBER: _ClassVar[int]
    JOB_SUB_TYPE_FIELD_NUMBER: _ClassVar[int]
    PRESIGNED_URL_FIELD_NUMBER: _ClassVar[int]
    MEMORY_USAGE_BYTES_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    job_desc: JobDesc
    job_status: JobStatus
    job_summary: _job_pb2.JobSummary
    job_client: str
    job_profiling: _job_meta_pb2.JobProfiling
    stats_download_url: str
    plan_download_url: str
    job_histories: _containers.RepeatedCompositeFieldContainer[_job_meta_pb2.JobHistory]
    current_ms: int
    job_meta_lite: _job_meta_pb2.JobMetaLite
    schema: str
    external_scheduled_info: str
    job_source: _job_meta_pb2.JobSource
    job_sub_type: _job_meta_pb2.JobSubType
    presigned_url: str
    memory_usage_bytes: int

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., job_desc: _Optional[_Union[JobDesc, _Mapping]]=..., job_status: _Optional[_Union[JobStatus, _Mapping]]=..., job_summary: _Optional[_Union[_job_pb2.JobSummary, _Mapping]]=..., job_client: _Optional[str]=..., job_profiling: _Optional[_Union[_job_meta_pb2.JobProfiling, _Mapping]]=..., stats_download_url: _Optional[str]=..., plan_download_url: _Optional[str]=..., job_histories: _Optional[_Iterable[_Union[_job_meta_pb2.JobHistory, _Mapping]]]=..., current_ms: _Optional[int]=..., job_meta_lite: _Optional[_Union[_job_meta_pb2.JobMetaLite, _Mapping]]=..., schema: _Optional[str]=..., external_scheduled_info: _Optional[str]=..., job_source: _Optional[_Union[_job_meta_pb2.JobSource, str]]=..., job_sub_type: _Optional[_Union[_job_meta_pb2.JobSubType, str]]=..., presigned_url: _Optional[str]=..., memory_usage_bytes: _Optional[int]=...) -> None:
        ...

class GetJobSummaryRequest(_message.Message):
    __slots__ = ('account', 'job_id', 'user_agent')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    account: Account
    job_id: JobID
    user_agent: str

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., job_id: _Optional[_Union[JobID, _Mapping]]=..., user_agent: _Optional[str]=...) -> None:
        ...

class GetJobSummaryResponse(_message.Message):
    __slots__ = ('resp_status', 'job_summary', 'presigned_url')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    JOB_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    PRESIGNED_URL_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    job_summary: _job_pb2.JobSummary
    presigned_url: str

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., job_summary: _Optional[_Union[_job_pb2.JobSummary, _Mapping]]=..., presigned_url: _Optional[str]=...) -> None:
        ...

class GetJobProgressRequest(_message.Message):
    __slots__ = ('account', 'job_id', 'verbose', 'user_agent')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    VERBOSE_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    account: Account
    job_id: JobID
    verbose: bool
    user_agent: str

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., job_id: _Optional[_Union[JobID, _Mapping]]=..., verbose: bool=..., user_agent: _Optional[str]=...) -> None:
        ...

class GetJobProgressResponse(_message.Message):
    __slots__ = ('resp_status', 'progress')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    progress: _job_pb2.JobProgress

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., progress: _Optional[_Union[_job_pb2.JobProgress, _Mapping]]=...) -> None:
        ...

class GetJobPlanRequest(_message.Message):
    __slots__ = ('account', 'job_id', 'user_agent')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    account: Account
    job_id: JobID
    user_agent: str

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., job_id: _Optional[_Union[JobID, _Mapping]]=..., user_agent: _Optional[str]=...) -> None:
        ...

class GetJobPlanResponse(_message.Message):
    __slots__ = ('resp_status', 'job_plan')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    JOB_PLAN_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    job_plan: _job_pb2.SimplifyDag

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., job_plan: _Optional[_Union[_job_pb2.SimplifyDag, _Mapping]]=...) -> None:
        ...

class JobRequest(_message.Message):
    __slots__ = ('get_result_request', 'get_summary_request', 'get_plan_request', 'get_profile_request', 'get_progress_request', 'user_agent')
    GET_RESULT_REQUEST_FIELD_NUMBER: _ClassVar[int]
    GET_SUMMARY_REQUEST_FIELD_NUMBER: _ClassVar[int]
    GET_PLAN_REQUEST_FIELD_NUMBER: _ClassVar[int]
    GET_PROFILE_REQUEST_FIELD_NUMBER: _ClassVar[int]
    GET_PROGRESS_REQUEST_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    get_result_request: GetJobResultRequest
    get_summary_request: GetJobSummaryRequest
    get_plan_request: GetJobPlanRequest
    get_profile_request: GetJobProfileRequest
    get_progress_request: GetJobProgressRequest
    user_agent: str

    def __init__(self, get_result_request: _Optional[_Union[GetJobResultRequest, _Mapping]]=..., get_summary_request: _Optional[_Union[GetJobSummaryRequest, _Mapping]]=..., get_plan_request: _Optional[_Union[GetJobPlanRequest, _Mapping]]=..., get_profile_request: _Optional[_Union[GetJobProfileRequest, _Mapping]]=..., get_progress_request: _Optional[_Union[GetJobProgressRequest, _Mapping]]=..., user_agent: _Optional[str]=...) -> None:
        ...

class InitializeInstanceRequest(_message.Message):
    __slots__ = ('create_workspace', 'instance_creator')
    CREATE_WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_CREATOR_FIELD_NUMBER: _ClassVar[int]
    create_workspace: _containers.RepeatedCompositeFieldContainer[CreateWorkspaceRequest]
    instance_creator: int

    def __init__(self, create_workspace: _Optional[_Iterable[_Union[CreateWorkspaceRequest, _Mapping]]]=..., instance_creator: _Optional[int]=...) -> None:
        ...

class InitializeInstanceResponse(_message.Message):
    __slots__ = ('resp_status', 'create_workspace')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    CREATE_WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    create_workspace: _containers.RepeatedCompositeFieldContainer[CreateWorkspaceResponse]

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., create_workspace: _Optional[_Iterable[_Union[CreateWorkspaceResponse, _Mapping]]]=...) -> None:
        ...

class SuspendInstanceRequest(_message.Message):
    __slots__ = ('instance_id',)
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    instance_id: int

    def __init__(self, instance_id: _Optional[int]=...) -> None:
        ...

class SuspendInstanceResponse(_message.Message):
    __slots__ = ('resp_status',)
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=...) -> None:
        ...

class ResumeInstanceRequest(_message.Message):
    __slots__ = ('instance_id',)
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    instance_id: int

    def __init__(self, instance_id: _Optional[int]=...) -> None:
        ...

class ResumeInstanceResponse(_message.Message):
    __slots__ = ('resp_status',)
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=...) -> None:
        ...

class CreateWorkspaceRequest(_message.Message):
    __slots__ = ('workspace', 'user_agent')
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    workspace: _metadata_entity_pb2.Entity
    user_agent: str

    def __init__(self, workspace: _Optional[_Union[_metadata_entity_pb2.Entity, _Mapping]]=..., user_agent: _Optional[str]=...) -> None:
        ...

class CreateWorkspaceResponse(_message.Message):
    __slots__ = ('resp_status', 'workspace_id')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    workspace_id: int

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., workspace_id: _Optional[int]=...) -> None:
        ...

class UpdateWorkspaceRequest(_message.Message):
    __slots__ = ('identifier', 'account', 'new_name', 'new_comment', 'encryption_config', 'properties', 'user_agent')
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    NEW_NAME_FIELD_NUMBER: _ClassVar[int]
    NEW_COMMENT_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTION_CONFIG_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier
    account: Account
    new_name: str
    new_comment: str
    encryption_config: _encryption_pb2.EncryptionConfig
    properties: _containers.RepeatedCompositeFieldContainer[_property_pb2.Property]
    user_agent: str

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., account: _Optional[_Union[Account, _Mapping]]=..., new_name: _Optional[str]=..., new_comment: _Optional[str]=..., encryption_config: _Optional[_Union[_encryption_pb2.EncryptionConfig, _Mapping]]=..., properties: _Optional[_Iterable[_Union[_property_pb2.Property, _Mapping]]]=..., user_agent: _Optional[str]=...) -> None:
        ...

class UpdateWorkspaceResponse(_message.Message):
    __slots__ = ('resp_status',)
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=...) -> None:
        ...

class DeleteWorkspaceRequest(_message.Message):
    __slots__ = ('identifier', 'account', 'user_agent')
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier
    account: Account
    user_agent: str

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., account: _Optional[_Union[Account, _Mapping]]=..., user_agent: _Optional[str]=...) -> None:
        ...

class DeleteWorkspaceResponse(_message.Message):
    __slots__ = ('resp_status',)
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=...) -> None:
        ...

class ListWorkspacesRequest(_message.Message):
    __slots__ = ('instance_id', 'account', 'user_agent')
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    instance_id: int
    account: Account
    user_agent: str

    def __init__(self, instance_id: _Optional[int]=..., account: _Optional[_Union[Account, _Mapping]]=..., user_agent: _Optional[str]=...) -> None:
        ...

class ListWorkspacesResponse(_message.Message):
    __slots__ = ('resp_status', 'workspaces')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    WORKSPACES_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    workspaces: _containers.RepeatedCompositeFieldContainer[_metadata_entity_pb2.Entity]

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., workspaces: _Optional[_Iterable[_Union[_metadata_entity_pb2.Entity, _Mapping]]]=...) -> None:
        ...

class GetWorkspaceRequest(_message.Message):
    __slots__ = ('identifier', 'account', 'user_agent')
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier
    account: Account
    user_agent: str

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., account: _Optional[_Union[Account, _Mapping]]=..., user_agent: _Optional[str]=...) -> None:
        ...

class GetWorkspaceResponse(_message.Message):
    __slots__ = ('resp_status', 'workspace')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    workspace: _metadata_entity_pb2.Entity

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., workspace: _Optional[_Union[_metadata_entity_pb2.Entity, _Mapping]]=...) -> None:
        ...

class WorkspaceRequest(_message.Message):
    __slots__ = ('create_request', 'delete_request', 'update_request', 'list_request', 'get_request', 'user_agent')
    CREATE_REQUEST_FIELD_NUMBER: _ClassVar[int]
    DELETE_REQUEST_FIELD_NUMBER: _ClassVar[int]
    UPDATE_REQUEST_FIELD_NUMBER: _ClassVar[int]
    LIST_REQUEST_FIELD_NUMBER: _ClassVar[int]
    GET_REQUEST_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    create_request: CreateWorkspaceRequest
    delete_request: DeleteWorkspaceRequest
    update_request: UpdateWorkspaceRequest
    list_request: ListWorkspacesRequest
    get_request: GetWorkspaceRequest
    user_agent: str

    def __init__(self, create_request: _Optional[_Union[CreateWorkspaceRequest, _Mapping]]=..., delete_request: _Optional[_Union[DeleteWorkspaceRequest, _Mapping]]=..., update_request: _Optional[_Union[UpdateWorkspaceRequest, _Mapping]]=..., list_request: _Optional[_Union[ListWorkspacesRequest, _Mapping]]=..., get_request: _Optional[_Union[GetWorkspaceRequest, _Mapping]]=..., user_agent: _Optional[str]=...) -> None:
        ...

class GetUserRequest(_message.Message):
    __slots__ = ('account', 'instance_id', 'workspace', 'user_agent')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    account: Account
    instance_id: int
    workspace: str
    user_agent: str

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., instance_id: _Optional[int]=..., workspace: _Optional[str]=..., user_agent: _Optional[str]=...) -> None:
        ...

class GetUserResponse(_message.Message):
    __slots__ = ('resp_status', 'user')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    user: _metadata_entity_pb2.Entity

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., user: _Optional[_Union[_metadata_entity_pb2.Entity, _Mapping]]=...) -> None:
        ...

class RefreshMetaCacheRequest(_message.Message):
    __slots__ = ('events',)
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    events: _object_identifier_pb2.ObjectModificationEventList

    def __init__(self, events: _Optional[_Union[_object_identifier_pb2.ObjectModificationEventList, _Mapping]]=...) -> None:
        ...

class RefreshMetaCacheResponse(_message.Message):
    __slots__ = ('resp_status',)
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=...) -> None:
        ...

class RouteItem(_message.Message):
    __slots__ = ('instance_name', 'instance_id', 'workspace', 'vc', 'target_release_version', 'flow_bucket', 'workspace_id', 'upgrading_version', 'schedule_strategy', 'coordinator_label', 'disable_label_fallback', 'account_type')

    class FlowBucketEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int

        def __init__(self, key: _Optional[str]=..., value: _Optional[int]=...) -> None:
            ...
    INSTANCE_NAME_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    VC_FIELD_NUMBER: _ClassVar[int]
    TARGET_RELEASE_VERSION_FIELD_NUMBER: _ClassVar[int]
    FLOW_BUCKET_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    UPGRADING_VERSION_FIELD_NUMBER: _ClassVar[int]
    SCHEDULE_STRATEGY_FIELD_NUMBER: _ClassVar[int]
    COORDINATOR_LABEL_FIELD_NUMBER: _ClassVar[int]
    DISABLE_LABEL_FALLBACK_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_TYPE_FIELD_NUMBER: _ClassVar[int]
    instance_name: str
    instance_id: int
    workspace: str
    vc: str
    target_release_version: str
    flow_bucket: _containers.ScalarMap[str, int]
    workspace_id: int
    upgrading_version: str
    schedule_strategy: JobScheduleStrategy
    coordinator_label: str
    disable_label_fallback: bool
    account_type: str

    def __init__(self, instance_name: _Optional[str]=..., instance_id: _Optional[int]=..., workspace: _Optional[str]=..., vc: _Optional[str]=..., target_release_version: _Optional[str]=..., flow_bucket: _Optional[_Mapping[str, int]]=..., workspace_id: _Optional[int]=..., upgrading_version: _Optional[str]=..., schedule_strategy: _Optional[_Union[JobScheduleStrategy, str]]=..., coordinator_label: _Optional[str]=..., disable_label_fallback: bool=..., account_type: _Optional[str]=...) -> None:
        ...

class LabelItem(_message.Message):
    __slots__ = ('label_name', 'applied_version', 'coordinator_count')
    LABEL_NAME_FIELD_NUMBER: _ClassVar[int]
    APPLIED_VERSION_FIELD_NUMBER: _ClassVar[int]
    COORDINATOR_COUNT_FIELD_NUMBER: _ClassVar[int]
    label_name: str
    applied_version: _containers.RepeatedScalarFieldContainer[str]
    coordinator_count: int

    def __init__(self, label_name: _Optional[str]=..., applied_version: _Optional[_Iterable[str]]=..., coordinator_count: _Optional[int]=...) -> None:
        ...

class ServiceRoute(_message.Message):
    __slots__ = ('route_items', 'version', 'label_items')
    ROUTE_ITEMS_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    LABEL_ITEMS_FIELD_NUMBER: _ClassVar[int]
    route_items: _containers.RepeatedCompositeFieldContainer[RouteItem]
    version: int
    label_items: _containers.RepeatedCompositeFieldContainer[LabelItem]

    def __init__(self, route_items: _Optional[_Iterable[_Union[RouteItem, _Mapping]]]=..., version: _Optional[int]=..., label_items: _Optional[_Iterable[_Union[LabelItem, _Mapping]]]=...) -> None:
        ...

class ListFlightingRouteTableResponse(_message.Message):
    __slots__ = ('resp_status', 'route_items')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    ROUTE_ITEMS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    route_items: _containers.RepeatedCompositeFieldContainer[RouteItem]

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., route_items: _Optional[_Iterable[_Union[RouteItem, _Mapping]]]=...) -> None:
        ...

class OpenTableRequest(_message.Message):
    __slots__ = ('account', 'table', 'iceberg')

    class IcebergFormat(_message.Message):
        __slots__ = ()

        def __init__(self) -> None:
            ...
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    ICEBERG_FIELD_NUMBER: _ClassVar[int]
    account: Account
    table: _object_identifier_pb2.ObjectIdentifier
    iceberg: OpenTableRequest.IcebergFormat

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., table: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., iceberg: _Optional[_Union[OpenTableRequest.IcebergFormat, _Mapping]]=...) -> None:
        ...

class OpenTableResponse(_message.Message):
    __slots__ = ('resp_status', 'iceberg')

    class IcebergFormat(_message.Message):
        __slots__ = ('metadata_location', 'properties')

        class PropertiesEntry(_message.Message):
            __slots__ = ('key', 'value')
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str

            def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
                ...
        METADATA_LOCATION_FIELD_NUMBER: _ClassVar[int]
        PROPERTIES_FIELD_NUMBER: _ClassVar[int]
        metadata_location: str
        properties: _containers.ScalarMap[str, str]

        def __init__(self, metadata_location: _Optional[str]=..., properties: _Optional[_Mapping[str, str]]=...) -> None:
            ...
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    ICEBERG_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    iceberg: OpenTableResponse.IcebergFormat

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., iceberg: _Optional[_Union[OpenTableResponse.IcebergFormat, _Mapping]]=...) -> None:
        ...

class NetworkPolicyRequest(_message.Message):
    __slots__ = ('instance_id', 'workspace', 'username', 'ip')
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    IP_FIELD_NUMBER: _ClassVar[int]
    instance_id: int
    workspace: str
    username: str
    ip: str

    def __init__(self, instance_id: _Optional[int]=..., workspace: _Optional[str]=..., username: _Optional[str]=..., ip: _Optional[str]=...) -> None:
        ...

class NetworkPolicyResponse(_message.Message):
    __slots__ = ('resp_status', 'access')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    ACCESS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    access: bool

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., access: bool=...) -> None:
        ...

class JobMetaDump(_message.Message):
    __slots__ = ('result', 'profiling', 'inputTables', 'outputTables', 'content', 'job_cost')
    RESULT_FIELD_NUMBER: _ClassVar[int]
    PROFILING_FIELD_NUMBER: _ClassVar[int]
    INPUTTABLES_FIELD_NUMBER: _ClassVar[int]
    OUTPUTTABLES_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    JOB_COST_FIELD_NUMBER: _ClassVar[int]
    result: JobResultSet
    profiling: _job_meta_pb2.JobProfiling
    inputTables: _job_meta_pb2.JobMeta.TableList
    outputTables: _job_meta_pb2.JobMeta.TableList
    content: _job_meta_pb2.JobMeta.Content
    job_cost: _job_meta_pb2.JobCost

    def __init__(self, result: _Optional[_Union[JobResultSet, _Mapping]]=..., profiling: _Optional[_Union[_job_meta_pb2.JobProfiling, _Mapping]]=..., inputTables: _Optional[_Union[_job_meta_pb2.JobMeta.TableList, _Mapping]]=..., outputTables: _Optional[_Union[_job_meta_pb2.JobMeta.TableList, _Mapping]]=..., content: _Optional[_Union[_job_meta_pb2.JobMeta.Content, _Mapping]]=..., job_cost: _Optional[_Union[_job_meta_pb2.JobCost, _Mapping]]=...) -> None:
        ...

class JobInfoDumpOnOom(_message.Message):
    __slots__ = ('job_info',)

    class JobInfo(_message.Message):
        __slots__ = ('job_id', 'status', 'job_profiling', 'priority', 'statement', 'virtual_cluster_name', 'virtual_cluster_id', 'virtual_cluster_type', 'job_history', 'query_md5', 'memory_usage_bytes')
        JOB_ID_FIELD_NUMBER: _ClassVar[int]
        STATUS_FIELD_NUMBER: _ClassVar[int]
        JOB_PROFILING_FIELD_NUMBER: _ClassVar[int]
        PRIORITY_FIELD_NUMBER: _ClassVar[int]
        STATEMENT_FIELD_NUMBER: _ClassVar[int]
        VIRTUAL_CLUSTER_NAME_FIELD_NUMBER: _ClassVar[int]
        VIRTUAL_CLUSTER_ID_FIELD_NUMBER: _ClassVar[int]
        VIRTUAL_CLUSTER_TYPE_FIELD_NUMBER: _ClassVar[int]
        JOB_HISTORY_FIELD_NUMBER: _ClassVar[int]
        QUERY_MD5_FIELD_NUMBER: _ClassVar[int]
        MEMORY_USAGE_BYTES_FIELD_NUMBER: _ClassVar[int]
        job_id: JobID
        status: _job_meta_pb2.JobStatus
        job_profiling: _job_meta_pb2.JobProfiling
        priority: int
        statement: str
        virtual_cluster_name: str
        virtual_cluster_id: int
        virtual_cluster_type: str
        job_history: _job_meta_pb2.JobMeta.HistoryList
        query_md5: str
        memory_usage_bytes: int

        def __init__(self, job_id: _Optional[_Union[JobID, _Mapping]]=..., status: _Optional[_Union[_job_meta_pb2.JobStatus, str]]=..., job_profiling: _Optional[_Union[_job_meta_pb2.JobProfiling, _Mapping]]=..., priority: _Optional[int]=..., statement: _Optional[str]=..., virtual_cluster_name: _Optional[str]=..., virtual_cluster_id: _Optional[int]=..., virtual_cluster_type: _Optional[str]=..., job_history: _Optional[_Union[_job_meta_pb2.JobMeta.HistoryList, _Mapping]]=..., query_md5: _Optional[str]=..., memory_usage_bytes: _Optional[int]=...) -> None:
            ...
    JOB_INFO_FIELD_NUMBER: _ClassVar[int]
    job_info: _containers.RepeatedCompositeFieldContainer[JobInfoDumpOnOom.JobInfo]

    def __init__(self, job_info: _Optional[_Iterable[_Union[JobInfoDumpOnOom.JobInfo, _Mapping]]]=...) -> None:
        ...

class RescheduleJobItem(_message.Message):
    __slots__ = ('job_id', 'reschedule_job_type')
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    RESCHEDULE_JOB_TYPE_FIELD_NUMBER: _ClassVar[int]
    job_id: JobID
    reschedule_job_type: RescheduleJobType

    def __init__(self, job_id: _Optional[_Union[JobID, _Mapping]]=..., reschedule_job_type: _Optional[_Union[RescheduleJobType, str]]=...) -> None:
        ...

class RescheduleJobsRequest(_message.Message):
    __slots__ = ('job_id', 'source_version', 'target_version')
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_VERSION_FIELD_NUMBER: _ClassVar[int]
    TARGET_VERSION_FIELD_NUMBER: _ClassVar[int]
    job_id: _containers.RepeatedCompositeFieldContainer[RescheduleJobItem]
    source_version: str
    target_version: str

    def __init__(self, job_id: _Optional[_Iterable[_Union[RescheduleJobItem, _Mapping]]]=..., source_version: _Optional[str]=..., target_version: _Optional[str]=...) -> None:
        ...

class RescheduleJobsResponse(_message.Message):
    __slots__ = ('resp_status', 'details')

    class DetailsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    details: _containers.ScalarMap[str, str]

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., details: _Optional[_Mapping[str, str]]=...) -> None:
        ...

class SetAccountConfigRequest(_message.Message):
    __slots__ = ('instance_id', 'feature_tier_name', 'config_key', 'config_value')
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    FEATURE_TIER_NAME_FIELD_NUMBER: _ClassVar[int]
    CONFIG_KEY_FIELD_NUMBER: _ClassVar[int]
    CONFIG_VALUE_FIELD_NUMBER: _ClassVar[int]
    instance_id: int
    feature_tier_name: str
    config_key: str
    config_value: str

    def __init__(self, instance_id: _Optional[int]=..., feature_tier_name: _Optional[str]=..., config_key: _Optional[str]=..., config_value: _Optional[str]=...) -> None:
        ...

class SetAccountConfigResponse(_message.Message):
    __slots__ = ('resp_status',)
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=...) -> None:
        ...

class GetInstanceConfigRequest(_message.Message):
    __slots__ = ('instance_id', 'merge_feature_tier_config')
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    MERGE_FEATURE_TIER_CONFIG_FIELD_NUMBER: _ClassVar[int]
    instance_id: int
    merge_feature_tier_config: bool

    def __init__(self, instance_id: _Optional[int]=..., merge_feature_tier_config: bool=...) -> None:
        ...

class GetAccountConfigRequest(_message.Message):
    __slots__ = ('get_instance_config_request', 'feature_tier_name')
    GET_INSTANCE_CONFIG_REQUEST_FIELD_NUMBER: _ClassVar[int]
    FEATURE_TIER_NAME_FIELD_NUMBER: _ClassVar[int]
    get_instance_config_request: GetInstanceConfigRequest
    feature_tier_name: str

    def __init__(self, get_instance_config_request: _Optional[_Union[GetInstanceConfigRequest, _Mapping]]=..., feature_tier_name: _Optional[str]=...) -> None:
        ...

class GetAccountConfigResponse(_message.Message):
    __slots__ = ('resp_status', 'configs')

    class ConfigsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    CONFIGS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    configs: _containers.ScalarMap[str, str]

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., configs: _Optional[_Mapping[str, str]]=...) -> None:
        ...

class GetJobAddressRequest(_message.Message):
    __slots__ = ('job_id',)
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    job_id: JobID

    def __init__(self, job_id: _Optional[_Union[JobID, _Mapping]]=...) -> None:
        ...

class GetJobAddressResponse(_message.Message):
    __slots__ = ('resp_status', 'address', 'worker_version')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    WORKER_VERSION_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    address: str
    worker_version: int

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., address: _Optional[str]=..., worker_version: _Optional[int]=...) -> None:
        ...

class ProcessInfo(_message.Message):
    __slots__ = ('memory_mb', 'execute_thread', 'job_waiting', 'job_running')
    MEMORY_MB_FIELD_NUMBER: _ClassVar[int]
    EXECUTE_THREAD_FIELD_NUMBER: _ClassVar[int]
    JOB_WAITING_FIELD_NUMBER: _ClassVar[int]
    JOB_RUNNING_FIELD_NUMBER: _ClassVar[int]
    memory_mb: int
    execute_thread: int
    job_waiting: int
    job_running: int

    def __init__(self, memory_mb: _Optional[int]=..., execute_thread: _Optional[int]=..., job_waiting: _Optional[int]=..., job_running: _Optional[int]=...) -> None:
        ...

class HystrixInfo(_message.Message):
    __slots__ = ('instance_id', 'workspace', 'prohibit', 'version')
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    PROHIBIT_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    instance_id: int
    workspace: str
    prohibit: bool
    version: str

    def __init__(self, instance_id: _Optional[int]=..., workspace: _Optional[str]=..., prohibit: bool=..., version: _Optional[str]=...) -> None:
        ...

class RunningJobInfo(_message.Message):
    __slots__ = ('job_id', 'virtual_cluster', 'job_status', 'start_time', 'priority_string', 'owner_id', 'query_tag', 'schema', 'job_type', 'priority', 'memory_usage_bytes', 'query_lite')
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    VIRTUAL_CLUSTER_FIELD_NUMBER: _ClassVar[int]
    JOB_STATUS_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_STRING_FIELD_NUMBER: _ClassVar[int]
    OWNER_ID_FIELD_NUMBER: _ClassVar[int]
    QUERY_TAG_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    JOB_TYPE_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    MEMORY_USAGE_BYTES_FIELD_NUMBER: _ClassVar[int]
    QUERY_LITE_FIELD_NUMBER: _ClassVar[int]
    job_id: JobID
    virtual_cluster: str
    job_status: str
    start_time: int
    priority_string: str
    owner_id: int
    query_tag: str
    schema: str
    job_type: str
    priority: int
    memory_usage_bytes: int
    query_lite: _job_meta_pb2.JobMetaLite.QueryLite

    def __init__(self, job_id: _Optional[_Union[JobID, _Mapping]]=..., virtual_cluster: _Optional[str]=..., job_status: _Optional[str]=..., start_time: _Optional[int]=..., priority_string: _Optional[str]=..., owner_id: _Optional[int]=..., query_tag: _Optional[str]=..., schema: _Optional[str]=..., job_type: _Optional[str]=..., priority: _Optional[int]=..., memory_usage_bytes: _Optional[int]=..., query_lite: _Optional[_Union[_job_meta_pb2.JobMetaLite.QueryLite, _Mapping]]=...) -> None:
        ...

class HeartBeat(_message.Message):
    __slots__ = ('worker_version', 'worker_address', 'hb_time', 'sequence_num', 'job_ids', 'terminated_job_ids', 'release_version', 'process_info', 'service_route_version', 'job_profilings', 'running_jobs', 'state', 'job_blackroom_version', 'node_ip', 'coordinator_label', 'pod_name', 'is_elastic', 'common_api_address')

    class JobProfilingsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _job_meta_pb2.JobProfiling

        def __init__(self, key: _Optional[str]=..., value: _Optional[_Union[_job_meta_pb2.JobProfiling, _Mapping]]=...) -> None:
            ...
    WORKER_VERSION_FIELD_NUMBER: _ClassVar[int]
    WORKER_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    HB_TIME_FIELD_NUMBER: _ClassVar[int]
    SEQUENCE_NUM_FIELD_NUMBER: _ClassVar[int]
    JOB_IDS_FIELD_NUMBER: _ClassVar[int]
    TERMINATED_JOB_IDS_FIELD_NUMBER: _ClassVar[int]
    RELEASE_VERSION_FIELD_NUMBER: _ClassVar[int]
    PROCESS_INFO_FIELD_NUMBER: _ClassVar[int]
    SERVICE_ROUTE_VERSION_FIELD_NUMBER: _ClassVar[int]
    JOB_PROFILINGS_FIELD_NUMBER: _ClassVar[int]
    RUNNING_JOBS_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    JOB_BLACKROOM_VERSION_FIELD_NUMBER: _ClassVar[int]
    NODE_IP_FIELD_NUMBER: _ClassVar[int]
    COORDINATOR_LABEL_FIELD_NUMBER: _ClassVar[int]
    POD_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ELASTIC_FIELD_NUMBER: _ClassVar[int]
    COMMON_API_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    worker_version: int
    worker_address: str
    hb_time: int
    sequence_num: int
    job_ids: _containers.RepeatedCompositeFieldContainer[JobID]
    terminated_job_ids: _containers.RepeatedCompositeFieldContainer[JobID]
    release_version: str
    process_info: ProcessInfo
    service_route_version: int
    job_profilings: _containers.MessageMap[str, _job_meta_pb2.JobProfiling]
    running_jobs: _containers.RepeatedCompositeFieldContainer[RunningJobInfo]
    state: CoordinatorState
    job_blackroom_version: int
    node_ip: str
    coordinator_label: str
    pod_name: str
    is_elastic: bool
    common_api_address: str

    def __init__(self, worker_version: _Optional[int]=..., worker_address: _Optional[str]=..., hb_time: _Optional[int]=..., sequence_num: _Optional[int]=..., job_ids: _Optional[_Iterable[_Union[JobID, _Mapping]]]=..., terminated_job_ids: _Optional[_Iterable[_Union[JobID, _Mapping]]]=..., release_version: _Optional[str]=..., process_info: _Optional[_Union[ProcessInfo, _Mapping]]=..., service_route_version: _Optional[int]=..., job_profilings: _Optional[_Mapping[str, _job_meta_pb2.JobProfiling]]=..., running_jobs: _Optional[_Iterable[_Union[RunningJobInfo, _Mapping]]]=..., state: _Optional[_Union[CoordinatorState, str]]=..., job_blackroom_version: _Optional[int]=..., node_ip: _Optional[str]=..., coordinator_label: _Optional[str]=..., pod_name: _Optional[str]=..., is_elastic: bool=..., common_api_address: _Optional[str]=...) -> None:
        ...

class HeartBeatResponse(_message.Message):
    __slots__ = ('resp_status', 'refresh_cache', 'suicide', 'master_version', 'hystrix', 'route_items', 'service_route_version', 'running_jobs', 'job_blackroom_version', 'criminal_job_md5', 'label')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    REFRESH_CACHE_FIELD_NUMBER: _ClassVar[int]
    SUICIDE_FIELD_NUMBER: _ClassVar[int]
    MASTER_VERSION_FIELD_NUMBER: _ClassVar[int]
    HYSTRIX_FIELD_NUMBER: _ClassVar[int]
    ROUTE_ITEMS_FIELD_NUMBER: _ClassVar[int]
    SERVICE_ROUTE_VERSION_FIELD_NUMBER: _ClassVar[int]
    RUNNING_JOBS_FIELD_NUMBER: _ClassVar[int]
    JOB_BLACKROOM_VERSION_FIELD_NUMBER: _ClassVar[int]
    CRIMINAL_JOB_MD5_FIELD_NUMBER: _ClassVar[int]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    refresh_cache: bool
    suicide: bool
    master_version: int
    hystrix: _containers.RepeatedCompositeFieldContainer[HystrixInfo]
    route_items: _containers.RepeatedCompositeFieldContainer[RouteItem]
    service_route_version: int
    running_jobs: _containers.RepeatedCompositeFieldContainer[RunningJobInfo]
    job_blackroom_version: int
    criminal_job_md5: _containers.RepeatedScalarFieldContainer[str]
    label: str

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., refresh_cache: bool=..., suicide: bool=..., master_version: _Optional[int]=..., hystrix: _Optional[_Iterable[_Union[HystrixInfo, _Mapping]]]=..., route_items: _Optional[_Iterable[_Union[RouteItem, _Mapping]]]=..., service_route_version: _Optional[int]=..., running_jobs: _Optional[_Iterable[_Union[RunningJobInfo, _Mapping]]]=..., job_blackroom_version: _Optional[int]=..., criminal_job_md5: _Optional[_Iterable[str]]=..., label: _Optional[str]=...) -> None:
        ...

class ListWorkerRequest(_message.Message):
    __slots__ = ('verbose', 'get_flighting_route_table', 'service_route_version')
    VERBOSE_FIELD_NUMBER: _ClassVar[int]
    GET_FLIGHTING_ROUTE_TABLE_FIELD_NUMBER: _ClassVar[int]
    SERVICE_ROUTE_VERSION_FIELD_NUMBER: _ClassVar[int]
    verbose: bool
    get_flighting_route_table: bool
    service_route_version: int

    def __init__(self, verbose: bool=..., get_flighting_route_table: bool=..., service_route_version: _Optional[int]=...) -> None:
        ...

class WorkDetail(_message.Message):
    __slots__ = ('worker_address', 'worker_version', 'worker_state', 'load_balance_score', 'status', 'release_version', 'process_info', 'label', 'common_api_address')
    WORKER_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    WORKER_VERSION_FIELD_NUMBER: _ClassVar[int]
    WORKER_STATE_FIELD_NUMBER: _ClassVar[int]
    LOAD_BALANCE_SCORE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RELEASE_VERSION_FIELD_NUMBER: _ClassVar[int]
    PROCESS_INFO_FIELD_NUMBER: _ClassVar[int]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    COMMON_API_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    worker_address: str
    worker_version: int
    worker_state: str
    load_balance_score: int
    status: HeartBeat
    release_version: str
    process_info: ProcessInfo
    label: str
    common_api_address: str

    def __init__(self, worker_address: _Optional[str]=..., worker_version: _Optional[int]=..., worker_state: _Optional[str]=..., load_balance_score: _Optional[int]=..., status: _Optional[_Union[HeartBeat, _Mapping]]=..., release_version: _Optional[str]=..., process_info: _Optional[_Union[ProcessInfo, _Mapping]]=..., label: _Optional[str]=..., common_api_address: _Optional[str]=...) -> None:
        ...

class ListWorkerResponse(_message.Message):
    __slots__ = ('resp_status', 'worker', 'load_score_hard_limit', 'route_items', 'job_schedule_strategy', 'job_schedule_load_balance_scope', 'service_route_version', 'submit_busy_punish_ms', 'disable_label_scheduling', 'enable_account_type_aware_label_scheduling')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    WORKER_FIELD_NUMBER: _ClassVar[int]
    LOAD_SCORE_HARD_LIMIT_FIELD_NUMBER: _ClassVar[int]
    ROUTE_ITEMS_FIELD_NUMBER: _ClassVar[int]
    JOB_SCHEDULE_STRATEGY_FIELD_NUMBER: _ClassVar[int]
    JOB_SCHEDULE_LOAD_BALANCE_SCOPE_FIELD_NUMBER: _ClassVar[int]
    SERVICE_ROUTE_VERSION_FIELD_NUMBER: _ClassVar[int]
    SUBMIT_BUSY_PUNISH_MS_FIELD_NUMBER: _ClassVar[int]
    DISABLE_LABEL_SCHEDULING_FIELD_NUMBER: _ClassVar[int]
    ENABLE_ACCOUNT_TYPE_AWARE_LABEL_SCHEDULING_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    worker: _containers.RepeatedCompositeFieldContainer[WorkDetail]
    load_score_hard_limit: int
    route_items: _containers.RepeatedCompositeFieldContainer[RouteItem]
    job_schedule_strategy: JobScheduleStrategy
    job_schedule_load_balance_scope: int
    service_route_version: int
    submit_busy_punish_ms: int
    disable_label_scheduling: bool
    enable_account_type_aware_label_scheduling: bool

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., worker: _Optional[_Iterable[_Union[WorkDetail, _Mapping]]]=..., load_score_hard_limit: _Optional[int]=..., route_items: _Optional[_Iterable[_Union[RouteItem, _Mapping]]]=..., job_schedule_strategy: _Optional[_Union[JobScheduleStrategy, str]]=..., job_schedule_load_balance_scope: _Optional[int]=..., service_route_version: _Optional[int]=..., submit_busy_punish_ms: _Optional[int]=..., disable_label_scheduling: bool=..., enable_account_type_aware_label_scheduling: bool=...) -> None:
        ...

class SetServiceRouteRequest(_message.Message):
    __slots__ = ('account', 'route_items', 'force', 'dedup', 'label_items')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    ROUTE_ITEMS_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    DEDUP_FIELD_NUMBER: _ClassVar[int]
    LABEL_ITEMS_FIELD_NUMBER: _ClassVar[int]
    account: Account
    route_items: _containers.RepeatedCompositeFieldContainer[RouteItem]
    force: bool
    dedup: bool
    label_items: _containers.RepeatedCompositeFieldContainer[LabelItem]

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., route_items: _Optional[_Iterable[_Union[RouteItem, _Mapping]]]=..., force: bool=..., dedup: bool=..., label_items: _Optional[_Iterable[_Union[LabelItem, _Mapping]]]=...) -> None:
        ...

class SetServiceRouteResponse(_message.Message):
    __slots__ = ('resp_status', 'details')

    class DetailsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    details: _containers.ScalarMap[str, str]

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., details: _Optional[_Mapping[str, str]]=...) -> None:
        ...

class SetLabelConfigRequest(_message.Message):
    __slots__ = ('label_name', 'coordinator_count', 'applied_version')
    LABEL_NAME_FIELD_NUMBER: _ClassVar[int]
    COORDINATOR_COUNT_FIELD_NUMBER: _ClassVar[int]
    APPLIED_VERSION_FIELD_NUMBER: _ClassVar[int]
    label_name: str
    coordinator_count: int
    applied_version: str

    def __init__(self, label_name: _Optional[str]=..., coordinator_count: _Optional[int]=..., applied_version: _Optional[str]=...) -> None:
        ...

class SetLabelConfigResponse(_message.Message):
    __slots__ = ('resp_status',)
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=...) -> None:
        ...

class ApplyAllLabelRequest(_message.Message):
    __slots__ = ('version', 'remove_label')
    VERSION_FIELD_NUMBER: _ClassVar[int]
    REMOVE_LABEL_FIELD_NUMBER: _ClassVar[int]
    version: str
    remove_label: bool

    def __init__(self, version: _Optional[str]=..., remove_label: bool=...) -> None:
        ...

class ApplyAllLabelResponse(_message.Message):
    __slots__ = ('resp_status',)
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=...) -> None:
        ...

class GetServiceRouteRequest(_message.Message):
    __slots__ = ('account',)
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    account: Account

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=...) -> None:
        ...

class GetServiceRouteResponse(_message.Message):
    __slots__ = ('resp_status', 'route_items', 'route_version', 'label_items')
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    ROUTE_ITEMS_FIELD_NUMBER: _ClassVar[int]
    ROUTE_VERSION_FIELD_NUMBER: _ClassVar[int]
    LABEL_ITEMS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    route_items: _containers.RepeatedCompositeFieldContainer[RouteItem]
    route_version: int
    label_items: _containers.RepeatedCompositeFieldContainer[LabelItem]

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., route_items: _Optional[_Iterable[_Union[RouteItem, _Mapping]]]=..., route_version: _Optional[int]=..., label_items: _Optional[_Iterable[_Union[LabelItem, _Mapping]]]=...) -> None:
        ...

class UpgradeUnit(_message.Message):
    __slots__ = ('instance_id', 'workspace', 'vc', 'workspace_id')
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    VC_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    instance_id: int
    workspace: str
    vc: str
    workspace_id: int

    def __init__(self, instance_id: _Optional[int]=..., workspace: _Optional[str]=..., vc: _Optional[str]=..., workspace_id: _Optional[int]=...) -> None:
        ...

class HotUpgradeRequest(_message.Message):
    __slots__ = ('units', 'source_version', 'target_version', 'type')
    UNITS_FIELD_NUMBER: _ClassVar[int]
    SOURCE_VERSION_FIELD_NUMBER: _ClassVar[int]
    TARGET_VERSION_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    units: _containers.RepeatedCompositeFieldContainer[UpgradeUnit]
    source_version: str
    target_version: str
    type: UpgradeActionType

    def __init__(self, units: _Optional[_Iterable[_Union[UpgradeUnit, _Mapping]]]=..., source_version: _Optional[str]=..., target_version: _Optional[str]=..., type: _Optional[_Union[UpgradeActionType, str]]=...) -> None:
        ...

class HotUpgradeResponse(_message.Message):
    __slots__ = ('resp_status', 'details')

    class DetailsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    details: _containers.ScalarMap[str, str]

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., details: _Optional[_Mapping[str, str]]=...) -> None:
        ...

class GetHotUpgradeStateRequest(_message.Message):
    __slots__ = ('units',)
    UNITS_FIELD_NUMBER: _ClassVar[int]
    units: _containers.RepeatedCompositeFieldContainer[UpgradeUnit]

    def __init__(self, units: _Optional[_Iterable[_Union[UpgradeUnit, _Mapping]]]=...) -> None:
        ...

class HotUpgradeState(_message.Message):
    __slots__ = ('upgrade_state', 'target_version', 'current_version', 'target_vc_id', 'current_vc_id')
    UPGRADE_STATE_FIELD_NUMBER: _ClassVar[int]
    TARGET_VERSION_FIELD_NUMBER: _ClassVar[int]
    CURRENT_VERSION_FIELD_NUMBER: _ClassVar[int]
    TARGET_VC_ID_FIELD_NUMBER: _ClassVar[int]
    CURRENT_VC_ID_FIELD_NUMBER: _ClassVar[int]
    upgrade_state: str
    target_version: str
    current_version: str
    target_vc_id: int
    current_vc_id: int

    def __init__(self, upgrade_state: _Optional[str]=..., target_version: _Optional[str]=..., current_version: _Optional[str]=..., target_vc_id: _Optional[int]=..., current_vc_id: _Optional[int]=...) -> None:
        ...

class HotUpgradeStateItem(_message.Message):
    __slots__ = ('unit', 'state')
    UNIT_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    unit: UpgradeUnit
    state: HotUpgradeState

    def __init__(self, unit: _Optional[_Union[UpgradeUnit, _Mapping]]=..., state: _Optional[_Union[HotUpgradeState, _Mapping]]=...) -> None:
        ...

class GetHotUpgradeStateResponse(_message.Message):
    __slots__ = ('resp_status', 'details')

    class DetailsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    details: _containers.ScalarMap[str, str]

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., details: _Optional[_Mapping[str, str]]=...) -> None:
        ...

class ListMasterJobsRequest(_message.Message):
    __slots__ = ('account', 'instance_id', 'workspace', 'vc', 'release_version')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    VC_FIELD_NUMBER: _ClassVar[int]
    RELEASE_VERSION_FIELD_NUMBER: _ClassVar[int]
    account: Account
    instance_id: int
    workspace: str
    vc: str
    release_version: str

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., instance_id: _Optional[int]=..., workspace: _Optional[str]=..., vc: _Optional[str]=..., release_version: _Optional[str]=...) -> None:
        ...

class RescheduleUnit(_message.Message):
    __slots__ = ('current_vc_id',)
    CURRENT_VC_ID_FIELD_NUMBER: _ClassVar[int]
    current_vc_id: int

    def __init__(self, current_vc_id: _Optional[int]=...) -> None:
        ...

class RescheduleVcJobsRequest(_message.Message):
    __slots__ = ('units', 'source_version', 'target_version', 'job_type')
    UNITS_FIELD_NUMBER: _ClassVar[int]
    SOURCE_VERSION_FIELD_NUMBER: _ClassVar[int]
    TARGET_VERSION_FIELD_NUMBER: _ClassVar[int]
    JOB_TYPE_FIELD_NUMBER: _ClassVar[int]
    units: _containers.RepeatedCompositeFieldContainer[RescheduleUnit]
    source_version: str
    target_version: str
    job_type: RescheduleJobType

    def __init__(self, units: _Optional[_Iterable[_Union[RescheduleUnit, _Mapping]]]=..., source_version: _Optional[str]=..., target_version: _Optional[str]=..., job_type: _Optional[_Union[RescheduleJobType, str]]=...) -> None:
        ...

class RescheduleVcJobsResponse(_message.Message):
    __slots__ = ('resp_status', 'details')

    class DetailsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    details: _containers.ScalarMap[str, str]

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., details: _Optional[_Mapping[str, str]]=...) -> None:
        ...

class GetLabelStatusRequest(_message.Message):
    __slots__ = ('version',)
    VERSION_FIELD_NUMBER: _ClassVar[int]
    version: str

    def __init__(self, version: _Optional[str]=...) -> None:
        ...

class GetLabelStatusResponse(_message.Message):
    __slots__ = ('resp_status', 'label_status')

    class LabelStatus(_message.Message):
        __slots__ = ('version', 'label', 'expected_count', 'actual_count')
        VERSION_FIELD_NUMBER: _ClassVar[int]
        LABEL_FIELD_NUMBER: _ClassVar[int]
        EXPECTED_COUNT_FIELD_NUMBER: _ClassVar[int]
        ACTUAL_COUNT_FIELD_NUMBER: _ClassVar[int]
        version: str
        label: str
        expected_count: int
        actual_count: int

        def __init__(self, version: _Optional[str]=..., label: _Optional[str]=..., expected_count: _Optional[int]=..., actual_count: _Optional[int]=...) -> None:
            ...
    RESP_STATUS_FIELD_NUMBER: _ClassVar[int]
    LABEL_STATUS_FIELD_NUMBER: _ClassVar[int]
    resp_status: _service_common_pb2.ResponseStatus
    label_status: _containers.RepeatedCompositeFieldContainer[GetLabelStatusResponse.LabelStatus]

    def __init__(self, resp_status: _Optional[_Union[_service_common_pb2.ResponseStatus, _Mapping]]=..., label_status: _Optional[_Iterable[_Union[GetLabelStatusResponse.LabelStatus, _Mapping]]]=...) -> None:
        ...