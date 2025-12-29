import virtual_cluster_pb2 as _virtual_cluster_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class JobStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SETUP: _ClassVar[JobStatus]
    QUEUEING: _ClassVar[JobStatus]
    RUNNING: _ClassVar[JobStatus]
    SUCCEED: _ClassVar[JobStatus]
    CANCELLING: _ClassVar[JobStatus]
    CANCELLED: _ClassVar[JobStatus]
    FAILED: _ClassVar[JobStatus]
    RESUMING_CLUSTER: _ClassVar[JobStatus]

class QueryType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    QT_NONE: _ClassVar[QueryType]
    QT_SELECT: _ClassVar[QueryType]
    QT_INSERT: _ClassVar[QueryType]
    QT_MERGE: _ClassVar[QueryType]
    QT_UPDATE: _ClassVar[QueryType]
    QT_DELETE: _ClassVar[QueryType]
    QT_OTHER_DML: _ClassVar[QueryType]
    QT_DDL: _ClassVar[QueryType]
    QT_CREATE_TABLE_AS: _ClassVar[QueryType]
    QT_CREATE_MV: _ClassVar[QueryType]
    QT_SHOW_OR_LIST: _ClassVar[QueryType]

class JobType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SQL_JOB: _ClassVar[JobType]
    COMPACTION_JOB: _ClassVar[JobType]
    SQL_TRANSLATE_JOB: _ClassVar[JobType]

class JobMetaOperationStrategy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CREATE_WITH_STAGED: _ClassVar[JobMetaOperationStrategy]
    CREATE_WITHOUT_STAGED: _ClassVar[JobMetaOperationStrategy]
    CREATE_ON_FINISH: _ClassVar[JobMetaOperationStrategy]

class JobSource(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEFAULT_JOB_SOURCE: _ClassVar[JobSource]
    MAINTAIN_SERVICE: _ClassVar[JobSource]

class JobSubType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEFAULT_JOB_SUB_TYPE: _ClassVar[JobSubType]
    DYNAMIC_TABLE_REFRESH_JOB: _ClassVar[JobSubType]
    MATERIALIZED_VIEW_REFRESH_JOB: _ClassVar[JobSubType]
SETUP: JobStatus
QUEUEING: JobStatus
RUNNING: JobStatus
SUCCEED: JobStatus
CANCELLING: JobStatus
CANCELLED: JobStatus
FAILED: JobStatus
RESUMING_CLUSTER: JobStatus
QT_NONE: QueryType
QT_SELECT: QueryType
QT_INSERT: QueryType
QT_MERGE: QueryType
QT_UPDATE: QueryType
QT_DELETE: QueryType
QT_OTHER_DML: QueryType
QT_DDL: QueryType
QT_CREATE_TABLE_AS: QueryType
QT_CREATE_MV: QueryType
QT_SHOW_OR_LIST: QueryType
SQL_JOB: JobType
COMPACTION_JOB: JobType
SQL_TRANSLATE_JOB: JobType
CREATE_WITH_STAGED: JobMetaOperationStrategy
CREATE_WITHOUT_STAGED: JobMetaOperationStrategy
CREATE_ON_FINISH: JobMetaOperationStrategy
DEFAULT_JOB_SOURCE: JobSource
MAINTAIN_SERVICE: JobSource
DEFAULT_JOB_SUB_TYPE: JobSubType
DYNAMIC_TABLE_REFRESH_JOB: JobSubType
MATERIALIZED_VIEW_REFRESH_JOB: JobSubType

class JobCost(_message.Message):
    __slots__ = ('cpu', 'memory', 'runtime_wall_time_ns')
    CPU_FIELD_NUMBER: _ClassVar[int]
    MEMORY_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_WALL_TIME_NS_FIELD_NUMBER: _ClassVar[int]
    cpu: int
    memory: int
    runtime_wall_time_ns: int

    def __init__(self, cpu: _Optional[int]=..., memory: _Optional[int]=..., runtime_wall_time_ns: _Optional[int]=...) -> None:
        ...

class JobHistory(_message.Message):
    __slots__ = ('coordinator_host', 'coordinator_version', 'start_time_ms', 'release_version')
    COORDINATOR_HOST_FIELD_NUMBER: _ClassVar[int]
    COORDINATOR_VERSION_FIELD_NUMBER: _ClassVar[int]
    START_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    RELEASE_VERSION_FIELD_NUMBER: _ClassVar[int]
    coordinator_host: str
    coordinator_version: int
    start_time_ms: int
    release_version: str

    def __init__(self, coordinator_host: _Optional[str]=..., coordinator_version: _Optional[int]=..., start_time_ms: _Optional[int]=..., release_version: _Optional[str]=...) -> None:
        ...

class SQLJobConfig(_message.Message):
    __slots__ = ('timeout', 'adhoc_size_limit', 'adhoc_row_limit', 'hint')

    class HintEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    ADHOC_SIZE_LIMIT_FIELD_NUMBER: _ClassVar[int]
    ADHOC_ROW_LIMIT_FIELD_NUMBER: _ClassVar[int]
    HINT_FIELD_NUMBER: _ClassVar[int]
    timeout: int
    adhoc_size_limit: int
    adhoc_row_limit: int
    hint: _containers.ScalarMap[str, str]

    def __init__(self, timeout: _Optional[int]=..., adhoc_size_limit: _Optional[int]=..., adhoc_row_limit: _Optional[int]=..., hint: _Optional[_Mapping[str, str]]=...) -> None:
        ...

class SQLJob(_message.Message):
    __slots__ = ('query', 'default_namespace', 'sql_config', 'default_instance_id', 'query_type')
    QUERY_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    SQL_CONFIG_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    QUERY_TYPE_FIELD_NUMBER: _ClassVar[int]
    query: _containers.RepeatedScalarFieldContainer[str]
    default_namespace: _containers.RepeatedScalarFieldContainer[str]
    sql_config: SQLJobConfig
    default_instance_id: int
    query_type: QueryType

    def __init__(self, query: _Optional[_Iterable[str]]=..., default_namespace: _Optional[_Iterable[str]]=..., sql_config: _Optional[_Union[SQLJobConfig, _Mapping]]=..., default_instance_id: _Optional[int]=..., query_type: _Optional[_Union[QueryType, str]]=...) -> None:
        ...

class JobSummaryLocation(_message.Message):
    __slots__ = ('summary_location', 'plan_location', 'stats_location', 'progress_location', 'result_location', 'base_location', 'job_properties_location', 'table_stats_location', 'preprocess_plan_location', 'job_status_location', 'debug_plan_location', 'job_desc_location', 'job_meta_dump')
    SUMMARY_LOCATION_FIELD_NUMBER: _ClassVar[int]
    PLAN_LOCATION_FIELD_NUMBER: _ClassVar[int]
    STATS_LOCATION_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_LOCATION_FIELD_NUMBER: _ClassVar[int]
    RESULT_LOCATION_FIELD_NUMBER: _ClassVar[int]
    BASE_LOCATION_FIELD_NUMBER: _ClassVar[int]
    JOB_PROPERTIES_LOCATION_FIELD_NUMBER: _ClassVar[int]
    TABLE_STATS_LOCATION_FIELD_NUMBER: _ClassVar[int]
    PREPROCESS_PLAN_LOCATION_FIELD_NUMBER: _ClassVar[int]
    JOB_STATUS_LOCATION_FIELD_NUMBER: _ClassVar[int]
    DEBUG_PLAN_LOCATION_FIELD_NUMBER: _ClassVar[int]
    JOB_DESC_LOCATION_FIELD_NUMBER: _ClassVar[int]
    JOB_META_DUMP_FIELD_NUMBER: _ClassVar[int]
    summary_location: str
    plan_location: str
    stats_location: str
    progress_location: str
    result_location: str
    base_location: str
    job_properties_location: str
    table_stats_location: str
    preprocess_plan_location: str
    job_status_location: str
    debug_plan_location: str
    job_desc_location: str
    job_meta_dump: str

    def __init__(self, summary_location: _Optional[str]=..., plan_location: _Optional[str]=..., stats_location: _Optional[str]=..., progress_location: _Optional[str]=..., result_location: _Optional[str]=..., base_location: _Optional[str]=..., job_properties_location: _Optional[str]=..., table_stats_location: _Optional[str]=..., preprocess_plan_location: _Optional[str]=..., job_status_location: _Optional[str]=..., debug_plan_location: _Optional[str]=..., job_desc_location: _Optional[str]=..., job_meta_dump: _Optional[str]=...) -> None:
        ...

class JobProfiling(_message.Message):
    __slots__ = ('profiling',)

    class JobProfilingItem(_message.Message):
        __slots__ = ('e', 't')
        E_FIELD_NUMBER: _ClassVar[int]
        T_FIELD_NUMBER: _ClassVar[int]
        e: int
        t: int

        def __init__(self, e: _Optional[int]=..., t: _Optional[int]=...) -> None:
            ...
    PROFILING_FIELD_NUMBER: _ClassVar[int]
    profiling: _containers.RepeatedCompositeFieldContainer[JobProfiling.JobProfilingItem]

    def __init__(self, profiling: _Optional[_Iterable[_Union[JobProfiling.JobProfilingItem, _Mapping]]]=...) -> None:
        ...

class JobMeta(_message.Message):
    __slots__ = ('job_name', 'virtual_cluster', 'status', 'type', 'start_time', 'end_time', 'priority', 'signature', 'cost', 'histories', 'result', 'job_summary', 'input_tables', 'output_tables', 'content', 'error_code', 'error_message', 'profiling', 'query_tag', 'lite', 'job_uuid', 'job_source', 'job_sub_type')

    class HistoryList(_message.Message):
        __slots__ = ('history',)
        HISTORY_FIELD_NUMBER: _ClassVar[int]
        history: _containers.RepeatedCompositeFieldContainer[JobHistory]

        def __init__(self, history: _Optional[_Iterable[_Union[JobHistory, _Mapping]]]=...) -> None:
            ...

    class Partition(_message.Message):
        __slots__ = ('field_id', 'value')
        FIELD_ID_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        field_id: _containers.RepeatedScalarFieldContainer[int]
        value: _containers.RepeatedScalarFieldContainer[str]

        def __init__(self, field_id: _Optional[_Iterable[int]]=..., value: _Optional[_Iterable[str]]=...) -> None:
            ...

    class Table(_message.Message):
        __slots__ = ('namespace', 'tableName', 'size', 'record', 'cache_size', 'partitions', 'instance_id', 'delta_size', 'file_count', 'delta_file_count', 'type', 'id', 'version')
        NAMESPACE_FIELD_NUMBER: _ClassVar[int]
        TABLENAME_FIELD_NUMBER: _ClassVar[int]
        SIZE_FIELD_NUMBER: _ClassVar[int]
        RECORD_FIELD_NUMBER: _ClassVar[int]
        CACHE_SIZE_FIELD_NUMBER: _ClassVar[int]
        PARTITIONS_FIELD_NUMBER: _ClassVar[int]
        INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
        DELTA_SIZE_FIELD_NUMBER: _ClassVar[int]
        FILE_COUNT_FIELD_NUMBER: _ClassVar[int]
        DELTA_FILE_COUNT_FIELD_NUMBER: _ClassVar[int]
        TYPE_FIELD_NUMBER: _ClassVar[int]
        ID_FIELD_NUMBER: _ClassVar[int]
        VERSION_FIELD_NUMBER: _ClassVar[int]
        namespace: _containers.RepeatedScalarFieldContainer[str]
        tableName: str
        size: int
        record: int
        cache_size: int
        partitions: _containers.RepeatedCompositeFieldContainer[JobMeta.Partition]
        instance_id: int
        delta_size: int
        file_count: int
        delta_file_count: int
        type: str
        id: int
        version: int

        def __init__(self, namespace: _Optional[_Iterable[str]]=..., tableName: _Optional[str]=..., size: _Optional[int]=..., record: _Optional[int]=..., cache_size: _Optional[int]=..., partitions: _Optional[_Iterable[_Union[JobMeta.Partition, _Mapping]]]=..., instance_id: _Optional[int]=..., delta_size: _Optional[int]=..., file_count: _Optional[int]=..., delta_file_count: _Optional[int]=..., type: _Optional[str]=..., id: _Optional[int]=..., version: _Optional[int]=...) -> None:
            ...

    class TableList(_message.Message):
        __slots__ = ('table',)
        TABLE_FIELD_NUMBER: _ClassVar[int]
        table: _containers.RepeatedCompositeFieldContainer[JobMeta.Table]

        def __init__(self, table: _Optional[_Iterable[_Union[JobMeta.Table, _Mapping]]]=...) -> None:
            ...

    class Content(_message.Message):
        __slots__ = ('job_config', 'sql_job', 'release_version', 'virtual_cluster_name', 'job_client', 'schema', 'schema_id', 'external_scheduled_info', 'virtual_cluster_type', 'disable_failover', 'is_continuous_job', 'query_md5', 'coordinator_label', 'job_desc_location')

        class JobConfigEntry(_message.Message):
            __slots__ = ('key', 'value')
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str

            def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
                ...
        JOB_CONFIG_FIELD_NUMBER: _ClassVar[int]
        SQL_JOB_FIELD_NUMBER: _ClassVar[int]
        RELEASE_VERSION_FIELD_NUMBER: _ClassVar[int]
        VIRTUAL_CLUSTER_NAME_FIELD_NUMBER: _ClassVar[int]
        JOB_CLIENT_FIELD_NUMBER: _ClassVar[int]
        SCHEMA_FIELD_NUMBER: _ClassVar[int]
        SCHEMA_ID_FIELD_NUMBER: _ClassVar[int]
        EXTERNAL_SCHEDULED_INFO_FIELD_NUMBER: _ClassVar[int]
        VIRTUAL_CLUSTER_TYPE_FIELD_NUMBER: _ClassVar[int]
        DISABLE_FAILOVER_FIELD_NUMBER: _ClassVar[int]
        IS_CONTINUOUS_JOB_FIELD_NUMBER: _ClassVar[int]
        QUERY_MD5_FIELD_NUMBER: _ClassVar[int]
        COORDINATOR_LABEL_FIELD_NUMBER: _ClassVar[int]
        JOB_DESC_LOCATION_FIELD_NUMBER: _ClassVar[int]
        job_config: _containers.ScalarMap[str, str]
        sql_job: SQLJob
        release_version: str
        virtual_cluster_name: str
        job_client: str
        schema: str
        schema_id: int
        external_scheduled_info: str
        virtual_cluster_type: _virtual_cluster_pb2.VClusterType
        disable_failover: bool
        is_continuous_job: bool
        query_md5: str
        coordinator_label: str
        job_desc_location: str

        def __init__(self, job_config: _Optional[_Mapping[str, str]]=..., sql_job: _Optional[_Union[SQLJob, _Mapping]]=..., release_version: _Optional[str]=..., virtual_cluster_name: _Optional[str]=..., job_client: _Optional[str]=..., schema: _Optional[str]=..., schema_id: _Optional[int]=..., external_scheduled_info: _Optional[str]=..., virtual_cluster_type: _Optional[_Union[_virtual_cluster_pb2.VClusterType, str]]=..., disable_failover: bool=..., is_continuous_job: bool=..., query_md5: _Optional[str]=..., coordinator_label: _Optional[str]=..., job_desc_location: _Optional[str]=...) -> None:
            ...
    JOB_NAME_FIELD_NUMBER: _ClassVar[int]
    VIRTUAL_CLUSTER_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    COST_FIELD_NUMBER: _ClassVar[int]
    HISTORIES_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    JOB_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    INPUT_TABLES_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_TABLES_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    PROFILING_FIELD_NUMBER: _ClassVar[int]
    QUERY_TAG_FIELD_NUMBER: _ClassVar[int]
    LITE_FIELD_NUMBER: _ClassVar[int]
    JOB_UUID_FIELD_NUMBER: _ClassVar[int]
    JOB_SOURCE_FIELD_NUMBER: _ClassVar[int]
    JOB_SUB_TYPE_FIELD_NUMBER: _ClassVar[int]
    job_name: str
    virtual_cluster: int
    status: JobStatus
    type: JobType
    start_time: int
    end_time: int
    priority: int
    signature: str
    cost: JobCost
    histories: JobMeta.HistoryList
    result: str
    job_summary: JobSummaryLocation
    input_tables: JobMeta.TableList
    output_tables: JobMeta.TableList
    content: JobMeta.Content
    error_code: str
    error_message: str
    profiling: JobProfiling
    query_tag: str
    lite: JobMetaLite
    job_uuid: int
    job_source: JobSource
    job_sub_type: JobSubType

    def __init__(self, job_name: _Optional[str]=..., virtual_cluster: _Optional[int]=..., status: _Optional[_Union[JobStatus, str]]=..., type: _Optional[_Union[JobType, str]]=..., start_time: _Optional[int]=..., end_time: _Optional[int]=..., priority: _Optional[int]=..., signature: _Optional[str]=..., cost: _Optional[_Union[JobCost, _Mapping]]=..., histories: _Optional[_Union[JobMeta.HistoryList, _Mapping]]=..., result: _Optional[str]=..., job_summary: _Optional[_Union[JobSummaryLocation, _Mapping]]=..., input_tables: _Optional[_Union[JobMeta.TableList, _Mapping]]=..., output_tables: _Optional[_Union[JobMeta.TableList, _Mapping]]=..., content: _Optional[_Union[JobMeta.Content, _Mapping]]=..., error_code: _Optional[str]=..., error_message: _Optional[str]=..., profiling: _Optional[_Union[JobProfiling, _Mapping]]=..., query_tag: _Optional[str]=..., lite: _Optional[_Union[JobMetaLite, _Mapping]]=..., job_uuid: _Optional[int]=..., job_source: _Optional[_Union[JobSource, str]]=..., job_sub_type: _Optional[_Union[JobSubType, str]]=...) -> None:
        ...

class JobMetaLite(_message.Message):
    __slots__ = ('input_bytes', 'rows_produced', 'query_lite', 'job_meta_strategy', 'is_mv_used', 'is_automv_used', 'disable_dump_stats_in_persist', 'incremental_property', 'is_hit_result_cache', 'result_cache_job_id', 'result_cache_not_support_reason', 'result_cache_not_hit_reason', 'read_metadata_only')

    class QueryLite(_message.Message):
        __slots__ = ('statement', 'statement_cut')
        STATEMENT_FIELD_NUMBER: _ClassVar[int]
        STATEMENT_CUT_FIELD_NUMBER: _ClassVar[int]
        statement: _containers.RepeatedScalarFieldContainer[str]
        statement_cut: bool

        def __init__(self, statement: _Optional[_Iterable[str]]=..., statement_cut: bool=...) -> None:
            ...

    class IncrementalProperty(_message.Message):
        __slots__ = ('is_incremental_plan', 'submitter', 'is_dt_or_mv', 'mv_instance_id', 'mv_table_id', 'mv_name')
        IS_INCREMENTAL_PLAN_FIELD_NUMBER: _ClassVar[int]
        SUBMITTER_FIELD_NUMBER: _ClassVar[int]
        IS_DT_OR_MV_FIELD_NUMBER: _ClassVar[int]
        MV_INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
        MV_TABLE_ID_FIELD_NUMBER: _ClassVar[int]
        MV_NAME_FIELD_NUMBER: _ClassVar[int]
        is_incremental_plan: str
        submitter: str
        is_dt_or_mv: str
        mv_instance_id: str
        mv_table_id: str
        mv_name: str

        def __init__(self, is_incremental_plan: _Optional[str]=..., submitter: _Optional[str]=..., is_dt_or_mv: _Optional[str]=..., mv_instance_id: _Optional[str]=..., mv_table_id: _Optional[str]=..., mv_name: _Optional[str]=...) -> None:
            ...
    INPUT_BYTES_FIELD_NUMBER: _ClassVar[int]
    ROWS_PRODUCED_FIELD_NUMBER: _ClassVar[int]
    QUERY_LITE_FIELD_NUMBER: _ClassVar[int]
    JOB_META_STRATEGY_FIELD_NUMBER: _ClassVar[int]
    IS_MV_USED_FIELD_NUMBER: _ClassVar[int]
    IS_AUTOMV_USED_FIELD_NUMBER: _ClassVar[int]
    DISABLE_DUMP_STATS_IN_PERSIST_FIELD_NUMBER: _ClassVar[int]
    INCREMENTAL_PROPERTY_FIELD_NUMBER: _ClassVar[int]
    IS_HIT_RESULT_CACHE_FIELD_NUMBER: _ClassVar[int]
    RESULT_CACHE_JOB_ID_FIELD_NUMBER: _ClassVar[int]
    RESULT_CACHE_NOT_SUPPORT_REASON_FIELD_NUMBER: _ClassVar[int]
    RESULT_CACHE_NOT_HIT_REASON_FIELD_NUMBER: _ClassVar[int]
    READ_METADATA_ONLY_FIELD_NUMBER: _ClassVar[int]
    input_bytes: int
    rows_produced: int
    query_lite: JobMetaLite.QueryLite
    job_meta_strategy: JobMetaOperationStrategy
    is_mv_used: bool
    is_automv_used: bool
    disable_dump_stats_in_persist: bool
    incremental_property: JobMetaLite.IncrementalProperty
    is_hit_result_cache: bool
    result_cache_job_id: str
    result_cache_not_support_reason: str
    result_cache_not_hit_reason: str
    read_metadata_only: bool

    def __init__(self, input_bytes: _Optional[int]=..., rows_produced: _Optional[int]=..., query_lite: _Optional[_Union[JobMetaLite.QueryLite, _Mapping]]=..., job_meta_strategy: _Optional[_Union[JobMetaOperationStrategy, str]]=..., is_mv_used: bool=..., is_automv_used: bool=..., disable_dump_stats_in_persist: bool=..., incremental_property: _Optional[_Union[JobMetaLite.IncrementalProperty, _Mapping]]=..., is_hit_result_cache: bool=..., result_cache_job_id: _Optional[str]=..., result_cache_not_support_reason: _Optional[str]=..., result_cache_not_hit_reason: _Optional[str]=..., read_metadata_only: bool=...) -> None:
        ...