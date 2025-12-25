import statistics_pb2 as _statistics_pb2
import operator_pb2 as _operator_pb2
import ddl_pb2 as _ddl_pb2
import time_range_pb2 as _time_range_pb2
import meter_pb2 as _meter_pb2
import runtime_run_span_stats_pb2 as _runtime_run_span_stats_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class Job(_message.Message):
    __slots__ = ('settings', 'statements', 'dml', 'user_id')

    class SettingsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...

    class UserId(_message.Message):
        __slots__ = ('instance_id', 'ns', 'id')
        INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
        NS_FIELD_NUMBER: _ClassVar[int]
        ID_FIELD_NUMBER: _ClassVar[int]
        instance_id: int
        ns: _containers.RepeatedScalarFieldContainer[str]
        id: int

        def __init__(self, instance_id: _Optional[int]=..., ns: _Optional[_Iterable[str]]=..., id: _Optional[int]=...) -> None:
            ...
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    STATEMENTS_FIELD_NUMBER: _ClassVar[int]
    DML_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    settings: _containers.ScalarMap[str, str]
    statements: _containers.RepeatedCompositeFieldContainer[_ddl_pb2.AccessStatement]
    dml: DML
    user_id: Job.UserId

    def __init__(self, settings: _Optional[_Mapping[str, str]]=..., statements: _Optional[_Iterable[_Union[_ddl_pb2.AccessStatement, _Mapping]]]=..., dml: _Optional[_Union[DML, _Mapping]]=..., user_id: _Optional[_Union[Job.UserId, _Mapping]]=...) -> None:
        ...

class DML(_message.Message):
    __slots__ = ('stages', 'boundaries', 'pipes', 'plan_index', 'traits')
    STAGES_FIELD_NUMBER: _ClassVar[int]
    BOUNDARIES_FIELD_NUMBER: _ClassVar[int]
    PIPES_FIELD_NUMBER: _ClassVar[int]
    PLAN_INDEX_FIELD_NUMBER: _ClassVar[int]
    TRAITS_FIELD_NUMBER: _ClassVar[int]
    stages: _containers.RepeatedCompositeFieldContainer[Stage]
    boundaries: _containers.RepeatedCompositeFieldContainer[_statistics_pb2.RangeBoundary]
    pipes: _containers.RepeatedCompositeFieldContainer[Pipe]
    plan_index: int
    traits: _containers.RepeatedCompositeFieldContainer[_operator_pb2.Traits]

    def __init__(self, stages: _Optional[_Iterable[_Union[Stage, _Mapping]]]=..., boundaries: _Optional[_Iterable[_Union[_statistics_pb2.RangeBoundary, _Mapping]]]=..., pipes: _Optional[_Iterable[_Union[Pipe, _Mapping]]]=..., plan_index: _Optional[int]=..., traits: _Optional[_Iterable[_Union[_operator_pb2.Traits, _Mapping]]]=...) -> None:
        ...

class Stage(_message.Message):
    __slots__ = ('id', 'batchSize', 'operators', 'dop', 'cpu_core', 'memory_mb', 'enforced_dop', 'index')
    ID_FIELD_NUMBER: _ClassVar[int]
    BATCHSIZE_FIELD_NUMBER: _ClassVar[int]
    OPERATORS_FIELD_NUMBER: _ClassVar[int]
    DOP_FIELD_NUMBER: _ClassVar[int]
    CPU_CORE_FIELD_NUMBER: _ClassVar[int]
    MEMORY_MB_FIELD_NUMBER: _ClassVar[int]
    ENFORCED_DOP_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    id: str
    batchSize: int
    operators: _containers.RepeatedCompositeFieldContainer[_operator_pb2.Operator]
    dop: int
    cpu_core: int
    memory_mb: int
    enforced_dop: bool
    index: int

    def __init__(self, id: _Optional[str]=..., batchSize: _Optional[int]=..., operators: _Optional[_Iterable[_Union[_operator_pb2.Operator, _Mapping]]]=..., dop: _Optional[int]=..., cpu_core: _Optional[int]=..., memory_mb: _Optional[int]=..., enforced_dop: bool=..., index: _Optional[int]=...) -> None:
        ...

class Pipe(_message.Message):
    __slots__ = ('from_op', 'to', 'to_op', 'shuffle_type', 'start_fraction', 'merge_sort', 'can_split', 'can_merge', 'can_copy', 're_optimize_threshold', 'virtual_edge')
    FROM_FIELD_NUMBER: _ClassVar[int]
    FROM_OP_FIELD_NUMBER: _ClassVar[int]
    TO_FIELD_NUMBER: _ClassVar[int]
    TO_OP_FIELD_NUMBER: _ClassVar[int]
    SHUFFLE_TYPE_FIELD_NUMBER: _ClassVar[int]
    START_FRACTION_FIELD_NUMBER: _ClassVar[int]
    MERGE_SORT_FIELD_NUMBER: _ClassVar[int]
    CAN_SPLIT_FIELD_NUMBER: _ClassVar[int]
    CAN_MERGE_FIELD_NUMBER: _ClassVar[int]
    CAN_COPY_FIELD_NUMBER: _ClassVar[int]
    RE_OPTIMIZE_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    VIRTUAL_EDGE_FIELD_NUMBER: _ClassVar[int]
    from_op: str
    to: str
    to_op: str
    shuffle_type: _operator_pb2.ShuffleType
    start_fraction: int
    merge_sort: bool
    can_split: bool
    can_merge: bool
    can_copy: bool
    re_optimize_threshold: int
    virtual_edge: bool

    def __init__(self, from_op: _Optional[str]=..., to: _Optional[str]=..., to_op: _Optional[str]=..., shuffle_type: _Optional[_Union[_operator_pb2.ShuffleType, _Mapping]]=..., start_fraction: _Optional[int]=..., merge_sort: bool=..., can_split: bool=..., can_merge: bool=..., can_copy: bool=..., re_optimize_threshold: _Optional[int]=..., virtual_edge: bool=..., **kwargs) -> None:
        ...

class RuntimeDriverStats(_message.Message):
    __slots__ = ('id', 'time_range_us', 'run_stats', 'pipeline_id', 'driver_sequence', 'block_timing_nanos', 'queue_timing_nanos', 'yield_count', 'block_count')
    ID_FIELD_NUMBER: _ClassVar[int]
    TIME_RANGE_US_FIELD_NUMBER: _ClassVar[int]
    RUN_STATS_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_ID_FIELD_NUMBER: _ClassVar[int]
    DRIVER_SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    BLOCK_TIMING_NANOS_FIELD_NUMBER: _ClassVar[int]
    QUEUE_TIMING_NANOS_FIELD_NUMBER: _ClassVar[int]
    YIELD_COUNT_FIELD_NUMBER: _ClassVar[int]
    BLOCK_COUNT_FIELD_NUMBER: _ClassVar[int]
    id: str
    time_range_us: _time_range_pb2.TimeRange
    run_stats: _containers.RepeatedCompositeFieldContainer[_runtime_run_span_stats_pb2.RuntimeRunSpanStats]
    pipeline_id: int
    driver_sequence: int
    block_timing_nanos: int
    queue_timing_nanos: int
    yield_count: int
    block_count: int

    def __init__(self, id: _Optional[str]=..., time_range_us: _Optional[_Union[_time_range_pb2.TimeRange, _Mapping]]=..., run_stats: _Optional[_Iterable[_Union[_runtime_run_span_stats_pb2.RuntimeRunSpanStats, _Mapping]]]=..., pipeline_id: _Optional[int]=..., driver_sequence: _Optional[int]=..., block_timing_nanos: _Optional[int]=..., queue_timing_nanos: _Optional[int]=..., yield_count: _Optional[int]=..., block_count: _Optional[int]=...) -> None:
        ...

class RuntimePipelineStats(_message.Message):
    __slots__ = ('id', 'dop')
    ID_FIELD_NUMBER: _ClassVar[int]
    DOP_FIELD_NUMBER: _ClassVar[int]
    id: int
    dop: int

    def __init__(self, id: _Optional[int]=..., dop: _Optional[int]=...) -> None:
        ...

class WorkerStats(_message.Message):
    __slots__ = ('timing', 'operator_stats', 'time_range_ms', 'peak_memory', 'driver_stats', 'runner_id', 'pipeline_stats')
    TIMING_FIELD_NUMBER: _ClassVar[int]
    OPERATOR_STATS_FIELD_NUMBER: _ClassVar[int]
    TIME_RANGE_MS_FIELD_NUMBER: _ClassVar[int]
    PEAK_MEMORY_FIELD_NUMBER: _ClassVar[int]
    DRIVER_STATS_FIELD_NUMBER: _ClassVar[int]
    RUNNER_ID_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_STATS_FIELD_NUMBER: _ClassVar[int]
    timing: _operator_pb2.Timing
    operator_stats: _containers.RepeatedCompositeFieldContainer[_operator_pb2.OperatorStats]
    time_range_ms: _time_range_pb2.TimeRange
    peak_memory: int
    driver_stats: _containers.RepeatedCompositeFieldContainer[RuntimeDriverStats]
    runner_id: int
    pipeline_stats: _containers.RepeatedCompositeFieldContainer[RuntimePipelineStats]

    def __init__(self, timing: _Optional[_Union[_operator_pb2.Timing, _Mapping]]=..., operator_stats: _Optional[_Iterable[_Union[_operator_pb2.OperatorStats, _Mapping]]]=..., time_range_ms: _Optional[_Union[_time_range_pb2.TimeRange, _Mapping]]=..., peak_memory: _Optional[int]=..., driver_stats: _Optional[_Iterable[_Union[RuntimeDriverStats, _Mapping]]]=..., runner_id: _Optional[int]=..., pipeline_stats: _Optional[_Iterable[_Union[RuntimePipelineStats, _Mapping]]]=...) -> None:
        ...

class LogicalPlan(_message.Message):
    __slots__ = ('operators', 'boundaries', 'traits')
    OPERATORS_FIELD_NUMBER: _ClassVar[int]
    BOUNDARIES_FIELD_NUMBER: _ClassVar[int]
    TRAITS_FIELD_NUMBER: _ClassVar[int]
    operators: _containers.RepeatedCompositeFieldContainer[_operator_pb2.Operator]
    boundaries: _containers.RepeatedCompositeFieldContainer[_statistics_pb2.RangeBoundary]
    traits: _containers.RepeatedCompositeFieldContainer[_operator_pb2.Traits]

    def __init__(self, operators: _Optional[_Iterable[_Union[_operator_pb2.Operator, _Mapping]]]=..., boundaries: _Optional[_Iterable[_Union[_statistics_pb2.RangeBoundary, _Mapping]]]=..., traits: _Optional[_Iterable[_Union[_operator_pb2.Traits, _Mapping]]]=...) -> None:
        ...

class WorkerId(_message.Message):
    __slots__ = ('job_id', 'sub_job_id', 'stage_id', 'id', 'backup_id', 'retry_id', 'ta_id', 'dag_id')
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    SUB_JOB_ID_FIELD_NUMBER: _ClassVar[int]
    STAGE_ID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    BACKUP_ID_FIELD_NUMBER: _ClassVar[int]
    RETRY_ID_FIELD_NUMBER: _ClassVar[int]
    TA_ID_FIELD_NUMBER: _ClassVar[int]
    DAG_ID_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    sub_job_id: int
    stage_id: str
    id: int
    backup_id: int
    retry_id: int
    ta_id: int
    dag_id: str

    def __init__(self, job_id: _Optional[str]=..., sub_job_id: _Optional[int]=..., stage_id: _Optional[str]=..., id: _Optional[int]=..., backup_id: _Optional[int]=..., retry_id: _Optional[int]=..., ta_id: _Optional[int]=..., dag_id: _Optional[str]=...) -> None:
        ...

class WorkerDetail(_message.Message):
    __slots__ = ('worker_stats', 'worker_id')
    WORKER_STATS_FIELD_NUMBER: _ClassVar[int]
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    worker_stats: WorkerStats
    worker_id: WorkerId

    def __init__(self, worker_stats: _Optional[_Union[WorkerStats, _Mapping]]=..., worker_id: _Optional[_Union[WorkerId, _Mapping]]=...) -> None:
        ...

class DetailState(_message.Message):
    __slots__ = ()

    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        NEW: _ClassVar[DetailState.State]
        RUNNING: _ClassVar[DetailState.State]
        SUCCEEDED: _ClassVar[DetailState.State]
        FAILED: _ClassVar[DetailState.State]
        KILLED: _ClassVar[DetailState.State]
        ERROR: _ClassVar[DetailState.State]
    NEW: DetailState.State
    RUNNING: DetailState.State
    SUCCEEDED: DetailState.State
    FAILED: DetailState.State
    KILLED: DetailState.State
    ERROR: DetailState.State

    def __init__(self) -> None:
        ...

class TaskAttemptProgress(_message.Message):
    __slots__ = ('time_on_executor', 'time_on_master', 'executor_address', 'stats', 'diagnostic', 'state', 'attempt_id', 'inited_time', 'time_on_wait_resource')

    class StatsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: bytes

        def __init__(self, key: _Optional[str]=..., value: _Optional[bytes]=...) -> None:
            ...
    TIME_ON_EXECUTOR_FIELD_NUMBER: _ClassVar[int]
    TIME_ON_MASTER_FIELD_NUMBER: _ClassVar[int]
    EXECUTOR_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    STATS_FIELD_NUMBER: _ClassVar[int]
    DIAGNOSTIC_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    ATTEMPT_ID_FIELD_NUMBER: _ClassVar[int]
    INITED_TIME_FIELD_NUMBER: _ClassVar[int]
    TIME_ON_WAIT_RESOURCE_FIELD_NUMBER: _ClassVar[int]
    time_on_executor: _time_range_pb2.TimeRange
    time_on_master: _time_range_pb2.TimeRange
    executor_address: str
    stats: _containers.ScalarMap[str, bytes]
    diagnostic: str
    state: DetailState.State
    attempt_id: str
    inited_time: int
    time_on_wait_resource: _time_range_pb2.TimeRange

    def __init__(self, time_on_executor: _Optional[_Union[_time_range_pb2.TimeRange, _Mapping]]=..., time_on_master: _Optional[_Union[_time_range_pb2.TimeRange, _Mapping]]=..., executor_address: _Optional[str]=..., stats: _Optional[_Mapping[str, bytes]]=..., diagnostic: _Optional[str]=..., state: _Optional[_Union[DetailState.State, str]]=..., attempt_id: _Optional[str]=..., inited_time: _Optional[int]=..., time_on_wait_resource: _Optional[_Union[_time_range_pb2.TimeRange, _Mapping]]=...) -> None:
        ...

class TaskProgress(_message.Message):
    __slots__ = ('task_id', 'start_time', 'schedule_time', 'diagnostic', 'attempts', 'state', 'finish_time', 'attempt_count')
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    SCHEDULE_TIME_FIELD_NUMBER: _ClassVar[int]
    DIAGNOSTIC_FIELD_NUMBER: _ClassVar[int]
    ATTEMPTS_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    FINISH_TIME_FIELD_NUMBER: _ClassVar[int]
    ATTEMPT_COUNT_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    start_time: int
    schedule_time: int
    diagnostic: str
    attempts: _containers.RepeatedCompositeFieldContainer[TaskAttemptProgress]
    state: DetailState.State
    finish_time: int
    attempt_count: int

    def __init__(self, task_id: _Optional[str]=..., start_time: _Optional[int]=..., schedule_time: _Optional[int]=..., diagnostic: _Optional[str]=..., attempts: _Optional[_Iterable[_Union[TaskAttemptProgress, _Mapping]]]=..., state: _Optional[_Union[DetailState.State, str]]=..., finish_time: _Optional[int]=..., attempt_count: _Optional[int]=...) -> None:
        ...

class StageProgress(_message.Message):
    __slots__ = ('failed', 'succeed', 'running', 'total', 'task_progress', 'init_time', 'start_time', 'finish_time', 'state', 'diagnostic', 'deprecated')

    class TaskProgressEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: TaskProgress

        def __init__(self, key: _Optional[str]=..., value: _Optional[_Union[TaskProgress, _Mapping]]=...) -> None:
            ...
    FAILED_FIELD_NUMBER: _ClassVar[int]
    SUCCEED_FIELD_NUMBER: _ClassVar[int]
    RUNNING_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    TASK_PROGRESS_FIELD_NUMBER: _ClassVar[int]
    INIT_TIME_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    FINISH_TIME_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    DIAGNOSTIC_FIELD_NUMBER: _ClassVar[int]
    DEPRECATED_FIELD_NUMBER: _ClassVar[int]
    failed: int
    succeed: int
    running: int
    total: int
    task_progress: _containers.MessageMap[str, TaskProgress]
    init_time: int
    start_time: int
    finish_time: int
    state: DetailState.State
    diagnostic: str
    deprecated: bool

    def __init__(self, failed: _Optional[int]=..., succeed: _Optional[int]=..., running: _Optional[int]=..., total: _Optional[int]=..., task_progress: _Optional[_Mapping[str, TaskProgress]]=..., init_time: _Optional[int]=..., start_time: _Optional[int]=..., finish_time: _Optional[int]=..., state: _Optional[_Union[DetailState.State, str]]=..., diagnostic: _Optional[str]=..., deprecated: bool=...) -> None:
        ...

class ContinuousBatchInfo(_message.Message):
    __slots__ = ('snapshot_id', 'batch_index', 'wall_nanos', 'lag')
    SNAPSHOT_ID_FIELD_NUMBER: _ClassVar[int]
    BATCH_INDEX_FIELD_NUMBER: _ClassVar[int]
    WALL_NANOS_FIELD_NUMBER: _ClassVar[int]
    LAG_FIELD_NUMBER: _ClassVar[int]
    snapshot_id: str
    batch_index: int
    wall_nanos: int
    lag: int

    def __init__(self, snapshot_id: _Optional[str]=..., batch_index: _Optional[int]=..., wall_nanos: _Optional[int]=..., lag: _Optional[int]=...) -> None:
        ...

class ContinuousBatchStat(_message.Message):
    __slots__ = ('start_time', 'finish_time', 'input_rows', 'output_rows', 'lag', 'wall_nanos', 'batch_index')
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    FINISH_TIME_FIELD_NUMBER: _ClassVar[int]
    INPUT_ROWS_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_ROWS_FIELD_NUMBER: _ClassVar[int]
    LAG_FIELD_NUMBER: _ClassVar[int]
    WALL_NANOS_FIELD_NUMBER: _ClassVar[int]
    BATCH_INDEX_FIELD_NUMBER: _ClassVar[int]
    start_time: int
    finish_time: int
    input_rows: int
    output_rows: int
    lag: int
    wall_nanos: int
    batch_index: int

    def __init__(self, start_time: _Optional[int]=..., finish_time: _Optional[int]=..., input_rows: _Optional[int]=..., output_rows: _Optional[int]=..., lag: _Optional[int]=..., wall_nanos: _Optional[int]=..., batch_index: _Optional[int]=...) -> None:
        ...

class ContinuousProgress(_message.Message):
    __slots__ = ('total_count', 'succeeded_count', 'running_count', 'conflict_count', 'ddl_error_count', 'retry_succeeded_count', 'batch_retried_count', 'dag_rerun_count', 'total_wall_nanos', 'latest_commit_batch', 'latest_running_batch', 'batch_stats')
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    SUCCEEDED_COUNT_FIELD_NUMBER: _ClassVar[int]
    RUNNING_COUNT_FIELD_NUMBER: _ClassVar[int]
    CONFLICT_COUNT_FIELD_NUMBER: _ClassVar[int]
    DDL_ERROR_COUNT_FIELD_NUMBER: _ClassVar[int]
    RETRY_SUCCEEDED_COUNT_FIELD_NUMBER: _ClassVar[int]
    BATCH_RETRIED_COUNT_FIELD_NUMBER: _ClassVar[int]
    DAG_RERUN_COUNT_FIELD_NUMBER: _ClassVar[int]
    TOTAL_WALL_NANOS_FIELD_NUMBER: _ClassVar[int]
    LATEST_COMMIT_BATCH_FIELD_NUMBER: _ClassVar[int]
    LATEST_RUNNING_BATCH_FIELD_NUMBER: _ClassVar[int]
    BATCH_STATS_FIELD_NUMBER: _ClassVar[int]
    total_count: int
    succeeded_count: int
    running_count: int
    conflict_count: int
    ddl_error_count: int
    retry_succeeded_count: int
    batch_retried_count: int
    dag_rerun_count: int
    total_wall_nanos: int
    latest_commit_batch: ContinuousBatchInfo
    latest_running_batch: ContinuousBatchInfo
    batch_stats: _containers.RepeatedCompositeFieldContainer[ContinuousBatchStat]

    def __init__(self, total_count: _Optional[int]=..., succeeded_count: _Optional[int]=..., running_count: _Optional[int]=..., conflict_count: _Optional[int]=..., ddl_error_count: _Optional[int]=..., retry_succeeded_count: _Optional[int]=..., batch_retried_count: _Optional[int]=..., dag_rerun_count: _Optional[int]=..., total_wall_nanos: _Optional[int]=..., latest_commit_batch: _Optional[_Union[ContinuousBatchInfo, _Mapping]]=..., latest_running_batch: _Optional[_Union[ContinuousBatchInfo, _Mapping]]=..., batch_stats: _Optional[_Iterable[_Union[ContinuousBatchStat, _Mapping]]]=...) -> None:
        ...

class JobProgress(_message.Message):
    __slots__ = ('stage_progress', 'continuous_progress')

    class StageProgressEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: StageProgress

        def __init__(self, key: _Optional[str]=..., value: _Optional[_Union[StageProgress, _Mapping]]=...) -> None:
            ...
    STAGE_PROGRESS_FIELD_NUMBER: _ClassVar[int]
    CONTINUOUS_PROGRESS_FIELD_NUMBER: _ClassVar[int]
    stage_progress: _containers.MessageMap[str, StageProgress]
    continuous_progress: ContinuousProgress

    def __init__(self, stage_progress: _Optional[_Mapping[str, StageProgress]]=..., continuous_progress: _Optional[_Union[ContinuousProgress, _Mapping]]=...) -> None:
        ...

class InputOutputStats(_message.Message):
    __slots__ = ('files_write_count', 'output_row_count', 'output_bytes', 'output_io_time_elapsed_us', 'files_read_count', 'input_row_count', 'input_bytes', 'input_cache_bytes', 'input_disk_bytes', 'input_io_time_elapsed_us', 'spilling_bytes')
    FILES_WRITE_COUNT_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_BYTES_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_IO_TIME_ELAPSED_US_FIELD_NUMBER: _ClassVar[int]
    FILES_READ_COUNT_FIELD_NUMBER: _ClassVar[int]
    INPUT_ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    INPUT_BYTES_FIELD_NUMBER: _ClassVar[int]
    INPUT_CACHE_BYTES_FIELD_NUMBER: _ClassVar[int]
    INPUT_DISK_BYTES_FIELD_NUMBER: _ClassVar[int]
    INPUT_IO_TIME_ELAPSED_US_FIELD_NUMBER: _ClassVar[int]
    SPILLING_BYTES_FIELD_NUMBER: _ClassVar[int]
    files_write_count: int
    output_row_count: int
    output_bytes: int
    output_io_time_elapsed_us: int
    files_read_count: int
    input_row_count: int
    input_bytes: int
    input_cache_bytes: int
    input_disk_bytes: int
    input_io_time_elapsed_us: int
    spilling_bytes: int

    def __init__(self, files_write_count: _Optional[int]=..., output_row_count: _Optional[int]=..., output_bytes: _Optional[int]=..., output_io_time_elapsed_us: _Optional[int]=..., files_read_count: _Optional[int]=..., input_row_count: _Optional[int]=..., input_bytes: _Optional[int]=..., input_cache_bytes: _Optional[int]=..., input_disk_bytes: _Optional[int]=..., input_io_time_elapsed_us: _Optional[int]=..., spilling_bytes: _Optional[int]=...) -> None:
        ...

class JobStats(_message.Message):
    __slots__ = ('input_output_stats',)
    INPUT_OUTPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    input_output_stats: InputOutputStats

    def __init__(self, input_output_stats: _Optional[_Union[InputOutputStats, _Mapping]]=...) -> None:
        ...

class TaskSummary(_message.Message):
    __slots__ = ('task_id', 'backup_id', 'retry_id', 'start_time', 'end_time', 'pending_time', 'running_time', 'executor', 'diagnostic', 'input_output_stats')
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    BACKUP_ID_FIELD_NUMBER: _ClassVar[int]
    RETRY_ID_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    PENDING_TIME_FIELD_NUMBER: _ClassVar[int]
    RUNNING_TIME_FIELD_NUMBER: _ClassVar[int]
    EXECUTOR_FIELD_NUMBER: _ClassVar[int]
    DIAGNOSTIC_FIELD_NUMBER: _ClassVar[int]
    INPUT_OUTPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    task_id: int
    backup_id: int
    retry_id: int
    start_time: int
    end_time: int
    pending_time: int
    running_time: int
    executor: str
    diagnostic: str
    input_output_stats: InputOutputStats

    def __init__(self, task_id: _Optional[int]=..., backup_id: _Optional[int]=..., retry_id: _Optional[int]=..., start_time: _Optional[int]=..., end_time: _Optional[int]=..., pending_time: _Optional[int]=..., running_time: _Optional[int]=..., executor: _Optional[str]=..., diagnostic: _Optional[str]=..., input_output_stats: _Optional[_Union[InputOutputStats, _Mapping]]=...) -> None:
        ...

class OperatorStatistics(_message.Message):
    __slots__ = ('records', 'max', 'min', 'sum', 'avg')
    RECORDS_FIELD_NUMBER: _ClassVar[int]
    MAX_FIELD_NUMBER: _ClassVar[int]
    MIN_FIELD_NUMBER: _ClassVar[int]
    SUM_FIELD_NUMBER: _ClassVar[int]
    AVG_FIELD_NUMBER: _ClassVar[int]
    records: _containers.RepeatedScalarFieldContainer[int]
    max: int
    min: int
    sum: int
    avg: int

    def __init__(self, records: _Optional[_Iterable[int]]=..., max: _Optional[int]=..., min: _Optional[int]=..., sum: _Optional[int]=..., avg: _Optional[int]=...) -> None:
        ...

class TableScanSummary(_message.Message):
    __slots__ = ('input_bytes', 'split_cnt', 'table_scan_source_stats', 'parquet_row_group_stats', 'parquet_row_count_stats', 'parquet_pruned_splits_stats')

    class ParquetRowGroupStats(_message.Message):
        __slots__ = ('bloom_pruned_row_group', 'stats_pruned_row_group', 'dict_pruned_row_group', 'request_row_group')
        BLOOM_PRUNED_ROW_GROUP_FIELD_NUMBER: _ClassVar[int]
        STATS_PRUNED_ROW_GROUP_FIELD_NUMBER: _ClassVar[int]
        DICT_PRUNED_ROW_GROUP_FIELD_NUMBER: _ClassVar[int]
        REQUEST_ROW_GROUP_FIELD_NUMBER: _ClassVar[int]
        bloom_pruned_row_group: int
        stats_pruned_row_group: int
        dict_pruned_row_group: int
        request_row_group: int

        def __init__(self, bloom_pruned_row_group: _Optional[int]=..., stats_pruned_row_group: _Optional[int]=..., dict_pruned_row_group: _Optional[int]=..., request_row_group: _Optional[int]=...) -> None:
            ...

    class ParquetRowCountStats(_message.Message):
        __slots__ = ('parquet_read_row_cnt', 'parquet_request_row_cnt')
        PARQUET_READ_ROW_CNT_FIELD_NUMBER: _ClassVar[int]
        PARQUET_REQUEST_ROW_CNT_FIELD_NUMBER: _ClassVar[int]
        parquet_read_row_cnt: int
        parquet_request_row_cnt: int

        def __init__(self, parquet_read_row_cnt: _Optional[int]=..., parquet_request_row_cnt: _Optional[int]=...) -> None:
            ...

    class ParquetPrunedSplitsStats(_message.Message):
        __slots__ = ('pruned_file_cnt', 'bitmap_pruned_splits', 'bloom_filter_pruned_splits')
        PRUNED_FILE_CNT_FIELD_NUMBER: _ClassVar[int]
        BITMAP_PRUNED_SPLITS_FIELD_NUMBER: _ClassVar[int]
        BLOOM_FILTER_PRUNED_SPLITS_FIELD_NUMBER: _ClassVar[int]
        pruned_file_cnt: int
        bitmap_pruned_splits: int
        bloom_filter_pruned_splits: int

        def __init__(self, pruned_file_cnt: _Optional[int]=..., bitmap_pruned_splits: _Optional[int]=..., bloom_filter_pruned_splits: _Optional[int]=...) -> None:
            ...

    class TableScanSourceStats(_message.Message):
        __slots__ = ('short_circuit_bytes', 'short_circuit_percentage', 'rpc_bytes', 'rpc_percentage', 'object_storage_bytes', 'object_storage_percentage')
        SHORT_CIRCUIT_BYTES_FIELD_NUMBER: _ClassVar[int]
        SHORT_CIRCUIT_PERCENTAGE_FIELD_NUMBER: _ClassVar[int]
        RPC_BYTES_FIELD_NUMBER: _ClassVar[int]
        RPC_PERCENTAGE_FIELD_NUMBER: _ClassVar[int]
        OBJECT_STORAGE_BYTES_FIELD_NUMBER: _ClassVar[int]
        OBJECT_STORAGE_PERCENTAGE_FIELD_NUMBER: _ClassVar[int]
        short_circuit_bytes: int
        short_circuit_percentage: float
        rpc_bytes: int
        rpc_percentage: float
        object_storage_bytes: int
        object_storage_percentage: float

        def __init__(self, short_circuit_bytes: _Optional[int]=..., short_circuit_percentage: _Optional[float]=..., rpc_bytes: _Optional[int]=..., rpc_percentage: _Optional[float]=..., object_storage_bytes: _Optional[int]=..., object_storage_percentage: _Optional[float]=...) -> None:
            ...
    INPUT_BYTES_FIELD_NUMBER: _ClassVar[int]
    SPLIT_CNT_FIELD_NUMBER: _ClassVar[int]
    TABLE_SCAN_SOURCE_STATS_FIELD_NUMBER: _ClassVar[int]
    PARQUET_ROW_GROUP_STATS_FIELD_NUMBER: _ClassVar[int]
    PARQUET_ROW_COUNT_STATS_FIELD_NUMBER: _ClassVar[int]
    PARQUET_PRUNED_SPLITS_STATS_FIELD_NUMBER: _ClassVar[int]
    input_bytes: OperatorStatistics
    split_cnt: OperatorStatistics
    table_scan_source_stats: TableScanSummary.TableScanSourceStats
    parquet_row_group_stats: TableScanSummary.ParquetRowGroupStats
    parquet_row_count_stats: TableScanSummary.ParquetRowCountStats
    parquet_pruned_splits_stats: TableScanSummary.ParquetPrunedSplitsStats

    def __init__(self, input_bytes: _Optional[_Union[OperatorStatistics, _Mapping]]=..., split_cnt: _Optional[_Union[OperatorStatistics, _Mapping]]=..., table_scan_source_stats: _Optional[_Union[TableScanSummary.TableScanSourceStats, _Mapping]]=..., parquet_row_group_stats: _Optional[_Union[TableScanSummary.ParquetRowGroupStats, _Mapping]]=..., parquet_row_count_stats: _Optional[_Union[TableScanSummary.ParquetRowCountStats, _Mapping]]=..., parquet_pruned_splits_stats: _Optional[_Union[TableScanSummary.ParquetPrunedSplitsStats, _Mapping]]=...) -> None:
        ...

class TableSinkSummary(_message.Message):
    __slots__ = ('compressed_output_bytes', 'total_file_count')
    COMPRESSED_OUTPUT_BYTES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FILE_COUNT_FIELD_NUMBER: _ClassVar[int]
    compressed_output_bytes: OperatorStatistics
    total_file_count: int

    def __init__(self, compressed_output_bytes: _Optional[_Union[OperatorStatistics, _Mapping]]=..., total_file_count: _Optional[int]=...) -> None:
        ...

class CalcSummary(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class HashJoinSummary(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class MergeJoinSummary(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class HashAggregateSummary(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class MergeAggregateSummary(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class LocalSortSummary(_message.Message):
    __slots__ = ('gen_run_wall_time_ns', 'gen_run_cpu_time_ns', 'merge_run_wall_time_ns', 'merge_run_cpu_time_ns')
    GEN_RUN_WALL_TIME_NS_FIELD_NUMBER: _ClassVar[int]
    GEN_RUN_CPU_TIME_NS_FIELD_NUMBER: _ClassVar[int]
    MERGE_RUN_WALL_TIME_NS_FIELD_NUMBER: _ClassVar[int]
    MERGE_RUN_CPU_TIME_NS_FIELD_NUMBER: _ClassVar[int]
    gen_run_wall_time_ns: OperatorStatistics
    gen_run_cpu_time_ns: OperatorStatistics
    merge_run_wall_time_ns: OperatorStatistics
    merge_run_cpu_time_ns: OperatorStatistics

    def __init__(self, gen_run_wall_time_ns: _Optional[_Union[OperatorStatistics, _Mapping]]=..., gen_run_cpu_time_ns: _Optional[_Union[OperatorStatistics, _Mapping]]=..., merge_run_wall_time_ns: _Optional[_Union[OperatorStatistics, _Mapping]]=..., merge_run_cpu_time_ns: _Optional[_Union[OperatorStatistics, _Mapping]]=...) -> None:
        ...

class MergeSortSummary(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class ValuesSummary(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class ExchangeSinkSummary(_message.Message):
    __slots__ = ('compressed_shuffle_bytes', 'uncompressed_shuffle_bytes', 'submit_wall_time_ns', 'close_wall_time_ns')
    COMPRESSED_SHUFFLE_BYTES_FIELD_NUMBER: _ClassVar[int]
    UNCOMPRESSED_SHUFFLE_BYTES_FIELD_NUMBER: _ClassVar[int]
    SUBMIT_WALL_TIME_NS_FIELD_NUMBER: _ClassVar[int]
    CLOSE_WALL_TIME_NS_FIELD_NUMBER: _ClassVar[int]
    compressed_shuffle_bytes: OperatorStatistics
    uncompressed_shuffle_bytes: OperatorStatistics
    submit_wall_time_ns: OperatorStatistics
    close_wall_time_ns: OperatorStatistics

    def __init__(self, compressed_shuffle_bytes: _Optional[_Union[OperatorStatistics, _Mapping]]=..., uncompressed_shuffle_bytes: _Optional[_Union[OperatorStatistics, _Mapping]]=..., submit_wall_time_ns: _Optional[_Union[OperatorStatistics, _Mapping]]=..., close_wall_time_ns: _Optional[_Union[OperatorStatistics, _Mapping]]=...) -> None:
        ...

class ExchangeSourceSummary(_message.Message):
    __slots__ = ('compressed_shuffle_bytes', 'uncompressed_shuffle_bytes', 'read_buffer_timing_wall_ns')
    COMPRESSED_SHUFFLE_BYTES_FIELD_NUMBER: _ClassVar[int]
    UNCOMPRESSED_SHUFFLE_BYTES_FIELD_NUMBER: _ClassVar[int]
    READ_BUFFER_TIMING_WALL_NS_FIELD_NUMBER: _ClassVar[int]
    compressed_shuffle_bytes: OperatorStatistics
    uncompressed_shuffle_bytes: OperatorStatistics
    read_buffer_timing_wall_ns: OperatorStatistics

    def __init__(self, compressed_shuffle_bytes: _Optional[_Union[OperatorStatistics, _Mapping]]=..., uncompressed_shuffle_bytes: _Optional[_Union[OperatorStatistics, _Mapping]]=..., read_buffer_timing_wall_ns: _Optional[_Union[OperatorStatistics, _Mapping]]=...) -> None:
        ...

class UnionAllSummary(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class BufferSummary(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class WindowSummary(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class ExpandSummary(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class LateralViewSummary(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class PartialWindowSummary(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class LocalExchangeSummary(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class OperatorSummary(_message.Message):
    __slots__ = ('op_id', 'input_output_stats', 'wall_time_ns', 'row_count', 'table_scan_summary', 'table_sink_summary', 'calc_summary', 'hash_join_summary', 'merge_join_summary', 'hash_aggregate_summary', 'merge_aggregate_summary', 'local_sort_summary', 'merge_sort_summary', 'values_summary', 'exchange_sink_summary', 'exchange_source_summary', 'union_all_summary', 'buffer_summary', 'window_summary', 'expand_summary', 'lateral_view_summary', 'partial_window_summary', 'local_exchange_summary')
    OP_ID_FIELD_NUMBER: _ClassVar[int]
    INPUT_OUTPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    WALL_TIME_NS_FIELD_NUMBER: _ClassVar[int]
    ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    TABLE_SCAN_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    TABLE_SINK_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    CALC_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    HASH_JOIN_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    MERGE_JOIN_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    HASH_AGGREGATE_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    MERGE_AGGREGATE_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    LOCAL_SORT_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    MERGE_SORT_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    VALUES_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    EXCHANGE_SINK_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    EXCHANGE_SOURCE_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    UNION_ALL_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    BUFFER_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    WINDOW_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    EXPAND_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    LATERAL_VIEW_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    PARTIAL_WINDOW_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    LOCAL_EXCHANGE_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    op_id: str
    input_output_stats: InputOutputStats
    wall_time_ns: OperatorStatistics
    row_count: OperatorStatistics
    table_scan_summary: TableScanSummary
    table_sink_summary: TableSinkSummary
    calc_summary: CalcSummary
    hash_join_summary: HashJoinSummary
    merge_join_summary: MergeJoinSummary
    hash_aggregate_summary: HashAggregateSummary
    merge_aggregate_summary: MergeAggregateSummary
    local_sort_summary: LocalSortSummary
    merge_sort_summary: MergeSortSummary
    values_summary: ValuesSummary
    exchange_sink_summary: ExchangeSinkSummary
    exchange_source_summary: ExchangeSourceSummary
    union_all_summary: UnionAllSummary
    buffer_summary: BufferSummary
    window_summary: WindowSummary
    expand_summary: ExpandSummary
    lateral_view_summary: LateralViewSummary
    partial_window_summary: PartialWindowSummary
    local_exchange_summary: LocalExchangeSummary

    def __init__(self, op_id: _Optional[str]=..., input_output_stats: _Optional[_Union[InputOutputStats, _Mapping]]=..., wall_time_ns: _Optional[_Union[OperatorStatistics, _Mapping]]=..., row_count: _Optional[_Union[OperatorStatistics, _Mapping]]=..., table_scan_summary: _Optional[_Union[TableScanSummary, _Mapping]]=..., table_sink_summary: _Optional[_Union[TableSinkSummary, _Mapping]]=..., calc_summary: _Optional[_Union[CalcSummary, _Mapping]]=..., hash_join_summary: _Optional[_Union[HashJoinSummary, _Mapping]]=..., merge_join_summary: _Optional[_Union[MergeJoinSummary, _Mapping]]=..., hash_aggregate_summary: _Optional[_Union[HashAggregateSummary, _Mapping]]=..., merge_aggregate_summary: _Optional[_Union[MergeAggregateSummary, _Mapping]]=..., local_sort_summary: _Optional[_Union[LocalSortSummary, _Mapping]]=..., merge_sort_summary: _Optional[_Union[MergeSortSummary, _Mapping]]=..., values_summary: _Optional[_Union[ValuesSummary, _Mapping]]=..., exchange_sink_summary: _Optional[_Union[ExchangeSinkSummary, _Mapping]]=..., exchange_source_summary: _Optional[_Union[ExchangeSourceSummary, _Mapping]]=..., union_all_summary: _Optional[_Union[UnionAllSummary, _Mapping]]=..., buffer_summary: _Optional[_Union[BufferSummary, _Mapping]]=..., window_summary: _Optional[_Union[WindowSummary, _Mapping]]=..., expand_summary: _Optional[_Union[ExpandSummary, _Mapping]]=..., lateral_view_summary: _Optional[_Union[LateralViewSummary, _Mapping]]=..., partial_window_summary: _Optional[_Union[PartialWindowSummary, _Mapping]]=..., local_exchange_summary: _Optional[_Union[LocalExchangeSummary, _Mapping]]=...) -> None:
        ...

class StageSummary(_message.Message):
    __slots__ = ('stage_id', 'start_time', 'end_time', 'pending_time', 'running_time', 'input_output_stats', 'task_summary', 'operator_summary')

    class TaskSummaryEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: TaskSummary

        def __init__(self, key: _Optional[int]=..., value: _Optional[_Union[TaskSummary, _Mapping]]=...) -> None:
            ...

    class OperatorSummaryEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: OperatorSummary

        def __init__(self, key: _Optional[str]=..., value: _Optional[_Union[OperatorSummary, _Mapping]]=...) -> None:
            ...
    STAGE_ID_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    PENDING_TIME_FIELD_NUMBER: _ClassVar[int]
    RUNNING_TIME_FIELD_NUMBER: _ClassVar[int]
    INPUT_OUTPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    TASK_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    OPERATOR_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    stage_id: str
    start_time: int
    end_time: int
    pending_time: int
    running_time: int
    input_output_stats: InputOutputStats
    task_summary: _containers.MessageMap[int, TaskSummary]
    operator_summary: _containers.MessageMap[str, OperatorSummary]

    def __init__(self, stage_id: _Optional[str]=..., start_time: _Optional[int]=..., end_time: _Optional[int]=..., pending_time: _Optional[int]=..., running_time: _Optional[int]=..., input_output_stats: _Optional[_Union[InputOutputStats, _Mapping]]=..., task_summary: _Optional[_Mapping[int, TaskSummary]]=..., operator_summary: _Optional[_Mapping[str, OperatorSummary]]=...) -> None:
        ...

class JobSummary(_message.Message):
    __slots__ = ('stats', 'stage_summary', 'meter')

    class StageSummaryEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: StageSummary

        def __init__(self, key: _Optional[str]=..., value: _Optional[_Union[StageSummary, _Mapping]]=...) -> None:
            ...
    STATS_FIELD_NUMBER: _ClassVar[int]
    STAGE_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    METER_FIELD_NUMBER: _ClassVar[int]
    stats: JobStats
    stage_summary: _containers.MessageMap[str, StageSummary]
    meter: _meter_pb2.Meter

    def __init__(self, stats: _Optional[_Union[JobStats, _Mapping]]=..., stage_summary: _Optional[_Mapping[str, StageSummary]]=..., meter: _Optional[_Union[_meter_pb2.Meter, _Mapping]]=...) -> None:
        ...

class SimplifyDagSubVertex(_message.Message):
    __slots__ = ('operator_id', 'parent_operator_id', 'operator_digest', 'operator_attribute')

    class OperatorAttributeEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    OPERATOR_ID_FIELD_NUMBER: _ClassVar[int]
    PARENT_OPERATOR_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATOR_DIGEST_FIELD_NUMBER: _ClassVar[int]
    OPERATOR_ATTRIBUTE_FIELD_NUMBER: _ClassVar[int]
    operator_id: str
    parent_operator_id: _containers.RepeatedScalarFieldContainer[str]
    operator_digest: str
    operator_attribute: _containers.ScalarMap[str, str]

    def __init__(self, operator_id: _Optional[str]=..., parent_operator_id: _Optional[_Iterable[str]]=..., operator_digest: _Optional[str]=..., operator_attribute: _Optional[_Mapping[str, str]]=...) -> None:
        ...

class SimplifyDagVertex(_message.Message):
    __slots__ = ('stage_id', 'parent_stage', 'operators', 'dop')
    STAGE_ID_FIELD_NUMBER: _ClassVar[int]
    PARENT_STAGE_FIELD_NUMBER: _ClassVar[int]
    OPERATORS_FIELD_NUMBER: _ClassVar[int]
    DOP_FIELD_NUMBER: _ClassVar[int]
    stage_id: str
    parent_stage: _containers.RepeatedScalarFieldContainer[str]
    operators: _containers.RepeatedCompositeFieldContainer[SimplifyDagSubVertex]
    dop: int

    def __init__(self, stage_id: _Optional[str]=..., parent_stage: _Optional[_Iterable[str]]=..., operators: _Optional[_Iterable[_Union[SimplifyDagSubVertex, _Mapping]]]=..., dop: _Optional[int]=...) -> None:
        ...

class SimplifyDag(_message.Message):
    __slots__ = ('stages', 'input_tables', 'output_tables')
    STAGES_FIELD_NUMBER: _ClassVar[int]
    INPUT_TABLES_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_TABLES_FIELD_NUMBER: _ClassVar[int]
    stages: _containers.RepeatedCompositeFieldContainer[SimplifyDagVertex]
    input_tables: _containers.RepeatedScalarFieldContainer[str]
    output_tables: _containers.RepeatedScalarFieldContainer[str]

    def __init__(self, stages: _Optional[_Iterable[_Union[SimplifyDagVertex, _Mapping]]]=..., input_tables: _Optional[_Iterable[str]]=..., output_tables: _Optional[_Iterable[str]]=...) -> None:
        ...

class DAGProgress(_message.Message):
    __slots__ = ('state', 'job_id', 'submit_time', 'init_time', 'start_time', 'finish_time', 'diagnostic', 'stage_progress', 'running_mode')

    class StageProgressEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: StageProgress

        def __init__(self, key: _Optional[str]=..., value: _Optional[_Union[StageProgress, _Mapping]]=...) -> None:
            ...
    STATE_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    SUBMIT_TIME_FIELD_NUMBER: _ClassVar[int]
    INIT_TIME_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    FINISH_TIME_FIELD_NUMBER: _ClassVar[int]
    DIAGNOSTIC_FIELD_NUMBER: _ClassVar[int]
    STAGE_PROGRESS_FIELD_NUMBER: _ClassVar[int]
    RUNNING_MODE_FIELD_NUMBER: _ClassVar[int]
    state: DetailState.State
    job_id: str
    submit_time: int
    init_time: int
    start_time: int
    finish_time: int
    diagnostic: str
    stage_progress: _containers.MessageMap[str, StageProgress]
    running_mode: str

    def __init__(self, state: _Optional[_Union[DetailState.State, str]]=..., job_id: _Optional[str]=..., submit_time: _Optional[int]=..., init_time: _Optional[int]=..., start_time: _Optional[int]=..., finish_time: _Optional[int]=..., diagnostic: _Optional[str]=..., stage_progress: _Optional[_Mapping[str, StageProgress]]=..., running_mode: _Optional[str]=...) -> None:
        ...