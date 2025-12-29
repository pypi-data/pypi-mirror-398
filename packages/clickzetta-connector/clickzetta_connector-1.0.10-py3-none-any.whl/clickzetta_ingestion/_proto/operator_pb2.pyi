import table_meta_pb2 as _table_meta_pb2
import table_common_pb2 as _table_common_pb2
import data_type_pb2 as _data_type_pb2
import expression_pb2 as _expression_pb2
import file_format_type_pb2 as _file_format_type_pb2
import file_meta_data_pb2 as _file_meta_data_pb2
import input_split_pb2 as _input_split_pb2
import file_system_pb2 as _file_system_pb2
import virtual_value_info_pb2 as _virtual_value_info_pb2
import property_pb2 as _property_pb2
import runtime_run_span_stats_pb2 as _runtime_run_span_stats_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class AggStage(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DUPLICATE: _ClassVar[AggStage]
    PARTIAL1: _ClassVar[AggStage]
    PARTIAL2: _ClassVar[AggStage]
    FINAL: _ClassVar[AggStage]
    COMPLETE: _ClassVar[AggStage]

class JoinType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    INNER: _ClassVar[JoinType]
    LEFT: _ClassVar[JoinType]
    RIGHT: _ClassVar[JoinType]
    FULL: _ClassVar[JoinType]
    LEFT_SEMI: _ClassVar[JoinType]
    LEFT_ANTI: _ClassVar[JoinType]

class DynamicFilterType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DF_NONE: _ClassVar[DynamicFilterType]
    DF_GLOBAL: _ClassVar[DynamicFilterType]
    DF_BROADCAST: _ClassVar[DynamicFilterType]
    DF_SHUFFLED: _ClassVar[DynamicFilterType]

class LazyEval(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NOT_LAZY: _ClassVar[LazyEval]
    LAZY_IN_CONDITION: _ClassVar[LazyEval]
    ALWAYS_LAZY: _ClassVar[LazyEval]

class SetOpType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNION: _ClassVar[SetOpType]
    INTERSECT: _ClassVar[SetOpType]
    EXCEPT: _ClassVar[SetOpType]
DUPLICATE: AggStage
PARTIAL1: AggStage
PARTIAL2: AggStage
FINAL: AggStage
COMPLETE: AggStage
INNER: JoinType
LEFT: JoinType
RIGHT: JoinType
FULL: JoinType
LEFT_SEMI: JoinType
LEFT_ANTI: JoinType
DF_NONE: DynamicFilterType
DF_GLOBAL: DynamicFilterType
DF_BROADCAST: DynamicFilterType
DF_SHUFFLED: DynamicFilterType
NOT_LAZY: LazyEval
LAZY_IN_CONDITION: LazyEval
ALWAYS_LAZY: LazyEval
UNION: SetOpType
INTERSECT: SetOpType
EXCEPT: SetOpType

class ColumnMapping(_message.Message):
    __slots__ = ('outputId', 'inputId')
    OUTPUTID_FIELD_NUMBER: _ClassVar[int]
    INPUTID_FIELD_NUMBER: _ClassVar[int]
    outputId: int
    inputId: int

    def __init__(self, outputId: _Optional[int]=..., inputId: _Optional[int]=...) -> None:
        ...

class Distribution(_message.Message):
    __slots__ = ('type', 'keys', 'has_dop', 'dop', 'has_hash_version', 'hash_version', 'has_bucket_type', 'bucket_type', 'range_dist_id')

    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ANY: _ClassVar[Distribution.Type]
        HASH: _ClassVar[Distribution.Type]
        RANGE: _ClassVar[Distribution.Type]
        SINGLETON: _ClassVar[Distribution.Type]
        BROADCAST: _ClassVar[Distribution.Type]
        ROUND_ROBIN: _ClassVar[Distribution.Type]
    ANY: Distribution.Type
    HASH: Distribution.Type
    RANGE: Distribution.Type
    SINGLETON: Distribution.Type
    BROADCAST: Distribution.Type
    ROUND_ROBIN: Distribution.Type
    TYPE_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    HAS_DOP_FIELD_NUMBER: _ClassVar[int]
    DOP_FIELD_NUMBER: _ClassVar[int]
    HAS_HASH_VERSION_FIELD_NUMBER: _ClassVar[int]
    HASH_VERSION_FIELD_NUMBER: _ClassVar[int]
    HAS_BUCKET_TYPE_FIELD_NUMBER: _ClassVar[int]
    BUCKET_TYPE_FIELD_NUMBER: _ClassVar[int]
    RANGE_DIST_ID_FIELD_NUMBER: _ClassVar[int]
    type: Distribution.Type
    keys: _containers.RepeatedScalarFieldContainer[int]
    has_dop: bool
    dop: int
    has_hash_version: bool
    hash_version: int
    has_bucket_type: bool
    bucket_type: _table_common_pb2.HashBucketType
    range_dist_id: int

    def __init__(self, type: _Optional[_Union[Distribution.Type, str]]=..., keys: _Optional[_Iterable[int]]=..., has_dop: bool=..., dop: _Optional[int]=..., has_hash_version: bool=..., hash_version: _Optional[int]=..., has_bucket_type: bool=..., bucket_type: _Optional[_Union[_table_common_pb2.HashBucketType, str]]=..., range_dist_id: _Optional[int]=...) -> None:
        ...

class Collation(_message.Message):
    __slots__ = ('orders',)

    class Key(_message.Message):
        __slots__ = ('field', 'order', 'null_order')
        FIELD_FIELD_NUMBER: _ClassVar[int]
        ORDER_FIELD_NUMBER: _ClassVar[int]
        NULL_ORDER_FIELD_NUMBER: _ClassVar[int]
        field: int
        order: _table_common_pb2.Order
        null_order: _table_common_pb2.NullOrder

        def __init__(self, field: _Optional[int]=..., order: _Optional[_Union[_table_common_pb2.Order, str]]=..., null_order: _Optional[_Union[_table_common_pb2.NullOrder, str]]=...) -> None:
            ...
    ORDERS_FIELD_NUMBER: _ClassVar[int]
    orders: _containers.RepeatedCompositeFieldContainer[Collation.Key]

    def __init__(self, orders: _Optional[_Iterable[_Union[Collation.Key, _Mapping]]]=...) -> None:
        ...

class Traits(_message.Message):
    __slots__ = ('engine', 'distribution', 'local_distribution', 'collation')

    class EngineType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        NONE: _ClassVar[Traits.EngineType]
        CZ: _ClassVar[Traits.EngineType]
    NONE: Traits.EngineType
    CZ: Traits.EngineType
    ENGINE_FIELD_NUMBER: _ClassVar[int]
    DISTRIBUTION_FIELD_NUMBER: _ClassVar[int]
    LOCAL_DISTRIBUTION_FIELD_NUMBER: _ClassVar[int]
    COLLATION_FIELD_NUMBER: _ClassVar[int]
    engine: Traits.EngineType
    distribution: Distribution
    local_distribution: Distribution
    collation: Collation

    def __init__(self, engine: _Optional[_Union[Traits.EngineType, str]]=..., distribution: _Optional[_Union[Distribution, _Mapping]]=..., local_distribution: _Optional[_Union[Distribution, _Mapping]]=..., collation: _Optional[_Union[Collation, _Mapping]]=...) -> None:
        ...

class Operator(_message.Message):
    __slots__ = ('id', 'inputIds', 'schema', 'columnMappings', 'signature', 'traits', 'table_scan', 'table_sink', 'calc', 'merge_sort', 'shuffle_write', 'shuffle_read', 'values', 'hash_agg', 'sorted_agg', 'merge_join', 'hash_join', 'local_sort', 'union_all', 'buffer', 'window', 'expand', 'lateral_view', 'grouping', 'join', 'aggregate', 'logical_calc', 'logical_sort', 'set_operator', 'agg_phase', 'spool', 'partial_window_filter', 'tree_join', 'tree_join_leaf', 'local_exchange', 'pt')
    ID_FIELD_NUMBER: _ClassVar[int]
    INPUTIDS_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    COLUMNMAPPINGS_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    TRAITS_FIELD_NUMBER: _ClassVar[int]
    TABLE_SCAN_FIELD_NUMBER: _ClassVar[int]
    TABLE_SINK_FIELD_NUMBER: _ClassVar[int]
    CALC_FIELD_NUMBER: _ClassVar[int]
    MERGE_SORT_FIELD_NUMBER: _ClassVar[int]
    SHUFFLE_WRITE_FIELD_NUMBER: _ClassVar[int]
    SHUFFLE_READ_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    HASH_AGG_FIELD_NUMBER: _ClassVar[int]
    SORTED_AGG_FIELD_NUMBER: _ClassVar[int]
    MERGE_JOIN_FIELD_NUMBER: _ClassVar[int]
    HASH_JOIN_FIELD_NUMBER: _ClassVar[int]
    LOCAL_SORT_FIELD_NUMBER: _ClassVar[int]
    UNION_ALL_FIELD_NUMBER: _ClassVar[int]
    BUFFER_FIELD_NUMBER: _ClassVar[int]
    WINDOW_FIELD_NUMBER: _ClassVar[int]
    EXPAND_FIELD_NUMBER: _ClassVar[int]
    LATERAL_VIEW_FIELD_NUMBER: _ClassVar[int]
    GROUPING_FIELD_NUMBER: _ClassVar[int]
    JOIN_FIELD_NUMBER: _ClassVar[int]
    AGGREGATE_FIELD_NUMBER: _ClassVar[int]
    LOGICAL_CALC_FIELD_NUMBER: _ClassVar[int]
    LOGICAL_SORT_FIELD_NUMBER: _ClassVar[int]
    SET_OPERATOR_FIELD_NUMBER: _ClassVar[int]
    AGG_PHASE_FIELD_NUMBER: _ClassVar[int]
    SPOOL_FIELD_NUMBER: _ClassVar[int]
    PARTIAL_WINDOW_FILTER_FIELD_NUMBER: _ClassVar[int]
    TREE_JOIN_FIELD_NUMBER: _ClassVar[int]
    TREE_JOIN_LEAF_FIELD_NUMBER: _ClassVar[int]
    LOCAL_EXCHANGE_FIELD_NUMBER: _ClassVar[int]
    PT_FIELD_NUMBER: _ClassVar[int]
    id: str
    inputIds: _containers.RepeatedScalarFieldContainer[str]
    schema: _data_type_pb2.DataType
    columnMappings: _containers.RepeatedCompositeFieldContainer[ColumnMapping]
    signature: int
    traits: int
    table_scan: TableScan
    table_sink: TableSink
    calc: Calc
    merge_sort: MergeSort
    shuffle_write: ShuffleWrite
    shuffle_read: ShuffleRead
    values: Values
    hash_agg: HashAggregate
    sorted_agg: SortedAggregate
    merge_join: SortMergeJoin
    hash_join: HashJoin
    local_sort: LocalSort
    union_all: UnionAll
    buffer: Buffer
    window: Window
    expand: Expand
    lateral_view: LateralView
    grouping: Grouping
    join: LogicalJoin
    aggregate: LogicalAggregate
    logical_calc: LogicalCalc
    logical_sort: LogicalSort
    set_operator: SetOperator
    agg_phase: AggregatePhase
    spool: Spool
    partial_window_filter: PartialWindowFilter
    tree_join: TreeJoin
    tree_join_leaf: TreeJoinLeaf
    local_exchange: LocalExchange
    pt: _expression_pb2.ParseTreeInfo

    def __init__(self, id: _Optional[str]=..., inputIds: _Optional[_Iterable[str]]=..., schema: _Optional[_Union[_data_type_pb2.DataType, _Mapping]]=..., columnMappings: _Optional[_Iterable[_Union[ColumnMapping, _Mapping]]]=..., signature: _Optional[int]=..., traits: _Optional[int]=..., table_scan: _Optional[_Union[TableScan, _Mapping]]=..., table_sink: _Optional[_Union[TableSink, _Mapping]]=..., calc: _Optional[_Union[Calc, _Mapping]]=..., merge_sort: _Optional[_Union[MergeSort, _Mapping]]=..., shuffle_write: _Optional[_Union[ShuffleWrite, _Mapping]]=..., shuffle_read: _Optional[_Union[ShuffleRead, _Mapping]]=..., values: _Optional[_Union[Values, _Mapping]]=..., hash_agg: _Optional[_Union[HashAggregate, _Mapping]]=..., sorted_agg: _Optional[_Union[SortedAggregate, _Mapping]]=..., merge_join: _Optional[_Union[SortMergeJoin, _Mapping]]=..., hash_join: _Optional[_Union[HashJoin, _Mapping]]=..., local_sort: _Optional[_Union[LocalSort, _Mapping]]=..., union_all: _Optional[_Union[UnionAll, _Mapping]]=..., buffer: _Optional[_Union[Buffer, _Mapping]]=..., window: _Optional[_Union[Window, _Mapping]]=..., expand: _Optional[_Union[Expand, _Mapping]]=..., lateral_view: _Optional[_Union[LateralView, _Mapping]]=..., grouping: _Optional[_Union[Grouping, _Mapping]]=..., join: _Optional[_Union[LogicalJoin, _Mapping]]=..., aggregate: _Optional[_Union[LogicalAggregate, _Mapping]]=..., logical_calc: _Optional[_Union[LogicalCalc, _Mapping]]=..., logical_sort: _Optional[_Union[LogicalSort, _Mapping]]=..., set_operator: _Optional[_Union[SetOperator, _Mapping]]=..., agg_phase: _Optional[_Union[AggregatePhase, _Mapping]]=..., spool: _Optional[_Union[Spool, _Mapping]]=..., partial_window_filter: _Optional[_Union[PartialWindowFilter, _Mapping]]=..., tree_join: _Optional[_Union[TreeJoin, _Mapping]]=..., tree_join_leaf: _Optional[_Union[TreeJoinLeaf, _Mapping]]=..., local_exchange: _Optional[_Union[LocalExchange, _Mapping]]=..., pt: _Optional[_Union[_expression_pb2.ParseTreeInfo, _Mapping]]=...) -> None:
        ...

class AggregateCall(_message.Message):
    __slots__ = ('function', 'distinct', 'stage', 'orders', 'filter', 'output_fields', 'initial_Type', 'partial_Type', 'output_Type')
    FUNCTION_FIELD_NUMBER: _ClassVar[int]
    DISTINCT_FIELD_NUMBER: _ClassVar[int]
    STAGE_FIELD_NUMBER: _ClassVar[int]
    ORDERS_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELDS_FIELD_NUMBER: _ClassVar[int]
    INITIAL_TYPE_FIELD_NUMBER: _ClassVar[int]
    PARTIAL_TYPE_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_TYPE_FIELD_NUMBER: _ClassVar[int]
    function: _expression_pb2.ScalarExpression
    distinct: bool
    stage: AggStage
    orders: _containers.RepeatedCompositeFieldContainer[OrderByDesc]
    filter: _expression_pb2.Reference
    output_fields: _containers.RepeatedScalarFieldContainer[int]
    initial_Type: _data_type_pb2.DataType
    partial_Type: _data_type_pb2.DataType
    output_Type: _data_type_pb2.DataType

    def __init__(self, function: _Optional[_Union[_expression_pb2.ScalarExpression, _Mapping]]=..., distinct: bool=..., stage: _Optional[_Union[AggStage, str]]=..., orders: _Optional[_Iterable[_Union[OrderByDesc, _Mapping]]]=..., filter: _Optional[_Union[_expression_pb2.Reference, _Mapping]]=..., output_fields: _Optional[_Iterable[int]]=..., initial_Type: _Optional[_Union[_data_type_pb2.DataType, _Mapping]]=..., partial_Type: _Optional[_Union[_data_type_pb2.DataType, _Mapping]]=..., output_Type: _Optional[_Union[_data_type_pb2.DataType, _Mapping]]=...) -> None:
        ...

class LogicalAggregate(_message.Message):
    __slots__ = ('keys', 'aggregate_calls', 'adaptive')
    KEYS_FIELD_NUMBER: _ClassVar[int]
    AGGREGATE_CALLS_FIELD_NUMBER: _ClassVar[int]
    ADAPTIVE_FIELD_NUMBER: _ClassVar[int]
    keys: _containers.RepeatedCompositeFieldContainer[_expression_pb2.Reference]
    aggregate_calls: _containers.RepeatedCompositeFieldContainer[AggregateCall]
    adaptive: bool

    def __init__(self, keys: _Optional[_Iterable[_Union[_expression_pb2.Reference, _Mapping]]]=..., aggregate_calls: _Optional[_Iterable[_Union[AggregateCall, _Mapping]]]=..., adaptive: bool=...) -> None:
        ...

class HashAggregate(_message.Message):
    __slots__ = ('aggregate', 'stage')
    AGGREGATE_FIELD_NUMBER: _ClassVar[int]
    STAGE_FIELD_NUMBER: _ClassVar[int]
    aggregate: LogicalAggregate
    stage: AggStage

    def __init__(self, aggregate: _Optional[_Union[LogicalAggregate, _Mapping]]=..., stage: _Optional[_Union[AggStage, str]]=...) -> None:
        ...

class SortedAggregate(_message.Message):
    __slots__ = ('aggregate', 'stage', 'orders')
    AGGREGATE_FIELD_NUMBER: _ClassVar[int]
    STAGE_FIELD_NUMBER: _ClassVar[int]
    ORDERS_FIELD_NUMBER: _ClassVar[int]
    aggregate: LogicalAggregate
    stage: AggStage
    orders: _containers.RepeatedCompositeFieldContainer[OrderByDesc]

    def __init__(self, aggregate: _Optional[_Union[LogicalAggregate, _Mapping]]=..., stage: _Optional[_Union[AggStage, str]]=..., orders: _Optional[_Iterable[_Union[OrderByDesc, _Mapping]]]=...) -> None:
        ...

class AggregatePhase(_message.Message):
    __slots__ = ('aggregate', 'stage')
    AGGREGATE_FIELD_NUMBER: _ClassVar[int]
    STAGE_FIELD_NUMBER: _ClassVar[int]
    aggregate: LogicalAggregate
    stage: AggStage

    def __init__(self, aggregate: _Optional[_Union[LogicalAggregate, _Mapping]]=..., stage: _Optional[_Union[AggStage, str]]=...) -> None:
        ...

class DynamicFilterInfo(_message.Message):
    __slots__ = ('type', 'consumer', 'selectivity', 'probe', 'partition_filter', 'table_scan_parents', 'sort_filter', 'bitset_filter')
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CONSUMER_FIELD_NUMBER: _ClassVar[int]
    SELECTIVITY_FIELD_NUMBER: _ClassVar[int]
    PROBE_FIELD_NUMBER: _ClassVar[int]
    PARTITION_FILTER_FIELD_NUMBER: _ClassVar[int]
    TABLE_SCAN_PARENTS_FIELD_NUMBER: _ClassVar[int]
    SORT_FILTER_FIELD_NUMBER: _ClassVar[int]
    BITSET_FILTER_FIELD_NUMBER: _ClassVar[int]
    type: DynamicFilterType
    consumer: bool
    selectivity: float
    probe: int
    partition_filter: bool
    table_scan_parents: int
    sort_filter: bool
    bitset_filter: bool

    def __init__(self, type: _Optional[_Union[DynamicFilterType, str]]=..., consumer: bool=..., selectivity: _Optional[float]=..., probe: _Optional[int]=..., partition_filter: bool=..., table_scan_parents: _Optional[int]=..., sort_filter: bool=..., bitset_filter: bool=...) -> None:
        ...

class JoinHintInfo(_message.Message):
    __slots__ = ('build_side', 'shuffle_type')
    BUILD_SIDE_FIELD_NUMBER: _ClassVar[int]
    SHUFFLE_TYPE_FIELD_NUMBER: _ClassVar[int]
    build_side: int
    shuffle_type: int

    def __init__(self, build_side: _Optional[int]=..., shuffle_type: _Optional[int]=...) -> None:
        ...

class TreeJoin(_message.Message):
    __slots__ = ('root_operators',)
    ROOT_OPERATORS_FIELD_NUMBER: _ClassVar[int]
    root_operators: _containers.RepeatedCompositeFieldContainer[Operator]

    def __init__(self, root_operators: _Optional[_Iterable[_Union[Operator, _Mapping]]]=...) -> None:
        ...

class TreeJoinLeaf(_message.Message):
    __slots__ = ('input_index', 'hint_build')
    INPUT_INDEX_FIELD_NUMBER: _ClassVar[int]
    HINT_BUILD_FIELD_NUMBER: _ClassVar[int]
    input_index: int
    hint_build: int

    def __init__(self, input_index: _Optional[int]=..., hint_build: _Optional[int]=...) -> None:
        ...

class LogicalJoin(_message.Message):
    __slots__ = ('type', 'condition', 'input_references', 'dynamic_filter', 'hintInfo')
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CONDITION_FIELD_NUMBER: _ClassVar[int]
    INPUT_REFERENCES_FIELD_NUMBER: _ClassVar[int]
    DYNAMIC_FILTER_FIELD_NUMBER: _ClassVar[int]
    HINTINFO_FIELD_NUMBER: _ClassVar[int]
    type: JoinType
    condition: _expression_pb2.ScalarExpression
    input_references: _containers.RepeatedScalarFieldContainer[int]
    dynamic_filter: DynamicFilterInfo
    hintInfo: JoinHintInfo

    def __init__(self, type: _Optional[_Union[JoinType, str]]=..., condition: _Optional[_Union[_expression_pb2.ScalarExpression, _Mapping]]=..., input_references: _Optional[_Iterable[int]]=..., dynamic_filter: _Optional[_Union[DynamicFilterInfo, _Mapping]]=..., hintInfo: _Optional[_Union[JoinHintInfo, _Mapping]]=...) -> None:
        ...

class SortMergeJoin(_message.Message):
    __slots__ = ('join', 'lhs_orders', 'rhs_orders')
    JOIN_FIELD_NUMBER: _ClassVar[int]
    LHS_ORDERS_FIELD_NUMBER: _ClassVar[int]
    RHS_ORDERS_FIELD_NUMBER: _ClassVar[int]
    join: LogicalJoin
    lhs_orders: _containers.RepeatedCompositeFieldContainer[OrderByDesc]
    rhs_orders: _containers.RepeatedCompositeFieldContainer[OrderByDesc]

    def __init__(self, join: _Optional[_Union[LogicalJoin, _Mapping]]=..., lhs_orders: _Optional[_Iterable[_Union[OrderByDesc, _Mapping]]]=..., rhs_orders: _Optional[_Iterable[_Union[OrderByDesc, _Mapping]]]=...) -> None:
        ...

class HashJoin(_message.Message):
    __slots__ = ('join', 'probe_operator_id', 'broadcast')
    JOIN_FIELD_NUMBER: _ClassVar[int]
    PROBE_OPERATOR_ID_FIELD_NUMBER: _ClassVar[int]
    BROADCAST_FIELD_NUMBER: _ClassVar[int]
    join: LogicalJoin
    probe_operator_id: str
    broadcast: bool

    def __init__(self, join: _Optional[_Union[LogicalJoin, _Mapping]]=..., probe_operator_id: _Optional[str]=..., broadcast: bool=...) -> None:
        ...

class Timing(_message.Message):
    __slots__ = ('cpu_nanos', 'wall_nanos')
    CPU_NANOS_FIELD_NUMBER: _ClassVar[int]
    WALL_NANOS_FIELD_NUMBER: _ClassVar[int]
    cpu_nanos: int
    wall_nanos: int

    def __init__(self, cpu_nanos: _Optional[int]=..., wall_nanos: _Optional[int]=...) -> None:
        ...

class OperatorStats(_message.Message):
    __slots__ = ('operator_id', 'row_count', 'timing', 'table_scan_stats', 'table_sink_stats', 'calc_stats', 'hash_join_stats', 'merge_join_stats', 'hash_aggregate_stats', 'merge_aggregate_stats', 'local_sort_stats', 'merge_sort_stats', 'values_stats', 'exchange_sink_stats', 'exchange_source_stats', 'union_all_stats', 'buffer_stats', 'window_stats', 'expand_stats', 'lateral_view_stats', 'partial_window_stats', 'local_exchange_stats', 'init_timing', 'batch_count', 'peak_memory', 'start_time_nanos', 'end_time_nanos', 'batch_signature', 'exec_node_id', 'pipeline_id', 'driver_sequence', 'block_timing_nanos', 'construct_timing', 'finish_timing', 'data_size_bytes', 'run_stats', 'extra_stats_binary', 'extra_stats')
    OPERATOR_ID_FIELD_NUMBER: _ClassVar[int]
    ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    TIMING_FIELD_NUMBER: _ClassVar[int]
    TABLE_SCAN_STATS_FIELD_NUMBER: _ClassVar[int]
    TABLE_SINK_STATS_FIELD_NUMBER: _ClassVar[int]
    CALC_STATS_FIELD_NUMBER: _ClassVar[int]
    HASH_JOIN_STATS_FIELD_NUMBER: _ClassVar[int]
    MERGE_JOIN_STATS_FIELD_NUMBER: _ClassVar[int]
    HASH_AGGREGATE_STATS_FIELD_NUMBER: _ClassVar[int]
    MERGE_AGGREGATE_STATS_FIELD_NUMBER: _ClassVar[int]
    LOCAL_SORT_STATS_FIELD_NUMBER: _ClassVar[int]
    MERGE_SORT_STATS_FIELD_NUMBER: _ClassVar[int]
    VALUES_STATS_FIELD_NUMBER: _ClassVar[int]
    EXCHANGE_SINK_STATS_FIELD_NUMBER: _ClassVar[int]
    EXCHANGE_SOURCE_STATS_FIELD_NUMBER: _ClassVar[int]
    UNION_ALL_STATS_FIELD_NUMBER: _ClassVar[int]
    BUFFER_STATS_FIELD_NUMBER: _ClassVar[int]
    WINDOW_STATS_FIELD_NUMBER: _ClassVar[int]
    EXPAND_STATS_FIELD_NUMBER: _ClassVar[int]
    LATERAL_VIEW_STATS_FIELD_NUMBER: _ClassVar[int]
    PARTIAL_WINDOW_STATS_FIELD_NUMBER: _ClassVar[int]
    LOCAL_EXCHANGE_STATS_FIELD_NUMBER: _ClassVar[int]
    INIT_TIMING_FIELD_NUMBER: _ClassVar[int]
    BATCH_COUNT_FIELD_NUMBER: _ClassVar[int]
    PEAK_MEMORY_FIELD_NUMBER: _ClassVar[int]
    START_TIME_NANOS_FIELD_NUMBER: _ClassVar[int]
    END_TIME_NANOS_FIELD_NUMBER: _ClassVar[int]
    BATCH_SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    EXEC_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_ID_FIELD_NUMBER: _ClassVar[int]
    DRIVER_SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    BLOCK_TIMING_NANOS_FIELD_NUMBER: _ClassVar[int]
    CONSTRUCT_TIMING_FIELD_NUMBER: _ClassVar[int]
    FINISH_TIMING_FIELD_NUMBER: _ClassVar[int]
    DATA_SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    RUN_STATS_FIELD_NUMBER: _ClassVar[int]
    EXTRA_STATS_BINARY_FIELD_NUMBER: _ClassVar[int]
    EXTRA_STATS_FIELD_NUMBER: _ClassVar[int]
    operator_id: str
    row_count: int
    timing: Timing
    table_scan_stats: TableScanStats
    table_sink_stats: TableSinkStats
    calc_stats: CalcStats
    hash_join_stats: HashJoinStats
    merge_join_stats: MergeJoinStats
    hash_aggregate_stats: HashAggregateStats
    merge_aggregate_stats: MergeAggregateStats
    local_sort_stats: LocalSortStats
    merge_sort_stats: MergeSortStats
    values_stats: ValuesStats
    exchange_sink_stats: ExchangeSinkStats
    exchange_source_stats: ExchangeSourceStats
    union_all_stats: UnionAllStats
    buffer_stats: BufferStats
    window_stats: WindowStats
    expand_stats: ExpandStats
    lateral_view_stats: LateralViewStats
    partial_window_stats: PartialWindowStats
    local_exchange_stats: LocalExchangeStats
    init_timing: Timing
    batch_count: int
    peak_memory: int
    start_time_nanos: int
    end_time_nanos: int
    batch_signature: int
    exec_node_id: str
    pipeline_id: int
    driver_sequence: int
    block_timing_nanos: int
    construct_timing: Timing
    finish_timing: Timing
    data_size_bytes: int
    run_stats: _containers.RepeatedCompositeFieldContainer[_runtime_run_span_stats_pb2.RuntimeRunSpanStats]
    extra_stats_binary: bytes
    extra_stats: str

    def __init__(self, operator_id: _Optional[str]=..., row_count: _Optional[int]=..., timing: _Optional[_Union[Timing, _Mapping]]=..., table_scan_stats: _Optional[_Union[TableScanStats, _Mapping]]=..., table_sink_stats: _Optional[_Union[TableSinkStats, _Mapping]]=..., calc_stats: _Optional[_Union[CalcStats, _Mapping]]=..., hash_join_stats: _Optional[_Union[HashJoinStats, _Mapping]]=..., merge_join_stats: _Optional[_Union[MergeJoinStats, _Mapping]]=..., hash_aggregate_stats: _Optional[_Union[HashAggregateStats, _Mapping]]=..., merge_aggregate_stats: _Optional[_Union[MergeAggregateStats, _Mapping]]=..., local_sort_stats: _Optional[_Union[LocalSortStats, _Mapping]]=..., merge_sort_stats: _Optional[_Union[MergeSortStats, _Mapping]]=..., values_stats: _Optional[_Union[ValuesStats, _Mapping]]=..., exchange_sink_stats: _Optional[_Union[ExchangeSinkStats, _Mapping]]=..., exchange_source_stats: _Optional[_Union[ExchangeSourceStats, _Mapping]]=..., union_all_stats: _Optional[_Union[UnionAllStats, _Mapping]]=..., buffer_stats: _Optional[_Union[BufferStats, _Mapping]]=..., window_stats: _Optional[_Union[WindowStats, _Mapping]]=..., expand_stats: _Optional[_Union[ExpandStats, _Mapping]]=..., lateral_view_stats: _Optional[_Union[LateralViewStats, _Mapping]]=..., partial_window_stats: _Optional[_Union[PartialWindowStats, _Mapping]]=..., local_exchange_stats: _Optional[_Union[LocalExchangeStats, _Mapping]]=..., init_timing: _Optional[_Union[Timing, _Mapping]]=..., batch_count: _Optional[int]=..., peak_memory: _Optional[int]=..., start_time_nanos: _Optional[int]=..., end_time_nanos: _Optional[int]=..., batch_signature: _Optional[int]=..., exec_node_id: _Optional[str]=..., pipeline_id: _Optional[int]=..., driver_sequence: _Optional[int]=..., block_timing_nanos: _Optional[int]=..., construct_timing: _Optional[_Union[Timing, _Mapping]]=..., finish_timing: _Optional[_Union[Timing, _Mapping]]=..., data_size_bytes: _Optional[int]=..., run_stats: _Optional[_Iterable[_Union[_runtime_run_span_stats_pb2.RuntimeRunSpanStats, _Mapping]]]=..., extra_stats_binary: _Optional[bytes]=..., extra_stats: _Optional[str]=...) -> None:
        ...

class OrderByDesc(_message.Message):
    __slots__ = ('reference', 'order', 'null_order')
    REFERENCE_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    NULL_ORDER_FIELD_NUMBER: _ClassVar[int]
    reference: _expression_pb2.Reference
    order: _table_common_pb2.Order
    null_order: _table_common_pb2.NullOrder

    def __init__(self, reference: _Optional[_Union[_expression_pb2.Reference, _Mapping]]=..., order: _Optional[_Union[_table_common_pb2.Order, str]]=..., null_order: _Optional[_Union[_table_common_pb2.NullOrder, str]]=...) -> None:
        ...

class MergeSort(_message.Message):
    __slots__ = ('orders', 'input_references', 'isIncrMergeUnion')
    ORDERS_FIELD_NUMBER: _ClassVar[int]
    INPUT_REFERENCES_FIELD_NUMBER: _ClassVar[int]
    ISINCRMERGEUNION_FIELD_NUMBER: _ClassVar[int]
    orders: _containers.RepeatedCompositeFieldContainer[OrderByDesc]
    input_references: _containers.RepeatedScalarFieldContainer[int]
    isIncrMergeUnion: bool

    def __init__(self, orders: _Optional[_Iterable[_Union[OrderByDesc, _Mapping]]]=..., input_references: _Optional[_Iterable[int]]=..., isIncrMergeUnion: bool=...) -> None:
        ...

class UnionAll(_message.Message):
    __slots__ = ('input_references', 'isIncrMergeUnion')
    INPUT_REFERENCES_FIELD_NUMBER: _ClassVar[int]
    ISINCRMERGEUNION_FIELD_NUMBER: _ClassVar[int]
    input_references: _containers.RepeatedScalarFieldContainer[int]
    isIncrMergeUnion: bool

    def __init__(self, input_references: _Optional[_Iterable[int]]=..., isIncrMergeUnion: bool=...) -> None:
        ...

class Buffer(_message.Message):
    __slots__ = ('shared',)
    SHARED_FIELD_NUMBER: _ClassVar[int]
    shared: bool

    def __init__(self, shared: bool=...) -> None:
        ...

class PartialWindowFilter(_message.Message):
    __slots__ = ('function', 'spec', 'limit')
    FUNCTION_FIELD_NUMBER: _ClassVar[int]
    SPEC_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    function: _expression_pb2.ScalarExpression
    spec: WindowSpec
    limit: int

    def __init__(self, function: _Optional[_Union[_expression_pb2.ScalarExpression, _Mapping]]=..., spec: _Optional[_Union[WindowSpec, _Mapping]]=..., limit: _Optional[int]=...) -> None:
        ...

class Window(_message.Message):
    __slots__ = ('groups', 'input_references')
    GROUPS_FIELD_NUMBER: _ClassVar[int]
    INPUT_REFERENCES_FIELD_NUMBER: _ClassVar[int]
    groups: _containers.RepeatedCompositeFieldContainer[WindowGroup]
    input_references: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, groups: _Optional[_Iterable[_Union[WindowGroup, _Mapping]]]=..., input_references: _Optional[_Iterable[int]]=...) -> None:
        ...

class WindowGroup(_message.Message):
    __slots__ = ('functions', 'spec')
    FUNCTIONS_FIELD_NUMBER: _ClassVar[int]
    SPEC_FIELD_NUMBER: _ClassVar[int]
    functions: _containers.RepeatedCompositeFieldContainer[WindowCall]
    spec: WindowSpec

    def __init__(self, functions: _Optional[_Iterable[_Union[WindowCall, _Mapping]]]=..., spec: _Optional[_Union[WindowSpec, _Mapping]]=...) -> None:
        ...

class WindowCall(_message.Message):
    __slots__ = ('function', 'distinct', 'partial_type')
    FUNCTION_FIELD_NUMBER: _ClassVar[int]
    DISTINCT_FIELD_NUMBER: _ClassVar[int]
    PARTIAL_TYPE_FIELD_NUMBER: _ClassVar[int]
    function: _expression_pb2.ScalarExpression
    distinct: bool
    partial_type: _data_type_pb2.DataType

    def __init__(self, function: _Optional[_Union[_expression_pb2.ScalarExpression, _Mapping]]=..., distinct: bool=..., partial_type: _Optional[_Union[_data_type_pb2.DataType, _Mapping]]=...) -> None:
        ...

class WindowSpec(_message.Message):
    __slots__ = ('keys', 'orders', 'boundary_type', 'lower_bound', 'upper_bound')

    class BoundaryType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ROWS: _ClassVar[WindowSpec.BoundaryType]
        RANGE: _ClassVar[WindowSpec.BoundaryType]
        GROUP: _ClassVar[WindowSpec.BoundaryType]
    ROWS: WindowSpec.BoundaryType
    RANGE: WindowSpec.BoundaryType
    GROUP: WindowSpec.BoundaryType
    KEYS_FIELD_NUMBER: _ClassVar[int]
    ORDERS_FIELD_NUMBER: _ClassVar[int]
    BOUNDARY_TYPE_FIELD_NUMBER: _ClassVar[int]
    LOWER_BOUND_FIELD_NUMBER: _ClassVar[int]
    UPPER_BOUND_FIELD_NUMBER: _ClassVar[int]
    keys: _containers.RepeatedCompositeFieldContainer[_expression_pb2.Reference]
    orders: _containers.RepeatedCompositeFieldContainer[OrderByDesc]
    boundary_type: WindowSpec.BoundaryType
    lower_bound: WindowBoundary
    upper_bound: WindowBoundary

    def __init__(self, keys: _Optional[_Iterable[_Union[_expression_pb2.Reference, _Mapping]]]=..., orders: _Optional[_Iterable[_Union[OrderByDesc, _Mapping]]]=..., boundary_type: _Optional[_Union[WindowSpec.BoundaryType, str]]=..., lower_bound: _Optional[_Union[WindowBoundary, _Mapping]]=..., upper_bound: _Optional[_Union[WindowBoundary, _Mapping]]=...) -> None:
        ...

class WindowBoundary(_message.Message):
    __slots__ = ('preceding', 'offset')
    PRECEDING_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    preceding: bool
    offset: _expression_pb2.Constant

    def __init__(self, preceding: bool=..., offset: _Optional[_Union[_expression_pb2.Constant, _Mapping]]=...) -> None:
        ...

class LateralView(_message.Message):
    __slots__ = ('functions', 'input_references')
    FUNCTIONS_FIELD_NUMBER: _ClassVar[int]
    INPUT_REFERENCES_FIELD_NUMBER: _ClassVar[int]
    functions: _containers.RepeatedCompositeFieldContainer[TableFunctionCall]
    input_references: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, functions: _Optional[_Iterable[_Union[TableFunctionCall, _Mapping]]]=..., input_references: _Optional[_Iterable[int]]=...) -> None:
        ...

class TableFunctionCall(_message.Message):
    __slots__ = ('function', 'outer', 'used_fields')
    FUNCTION_FIELD_NUMBER: _ClassVar[int]
    OUTER_FIELD_NUMBER: _ClassVar[int]
    USED_FIELDS_FIELD_NUMBER: _ClassVar[int]
    function: _expression_pb2.ScalarExpression
    outer: bool
    used_fields: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, function: _Optional[_Union[_expression_pb2.ScalarExpression, _Mapping]]=..., outer: bool=..., used_fields: _Optional[_Iterable[int]]=...) -> None:
        ...

class Spool(_message.Message):
    __slots__ = ('spool_id',)
    SPOOL_ID_FIELD_NUMBER: _ClassVar[int]
    spool_id: int

    def __init__(self, spool_id: _Optional[int]=...) -> None:
        ...

class Calc(_message.Message):
    __slots__ = ('expressions', 'no_filter', 'filter', 'projects', 'lazy', 'partial_window_filter_selectivity')
    EXPRESSIONS_FIELD_NUMBER: _ClassVar[int]
    NO_FILTER_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    PROJECTS_FIELD_NUMBER: _ClassVar[int]
    LAZY_FIELD_NUMBER: _ClassVar[int]
    PARTIAL_WINDOW_FILTER_SELECTIVITY_FIELD_NUMBER: _ClassVar[int]
    expressions: _containers.RepeatedCompositeFieldContainer[_expression_pb2.ScalarExpression]
    no_filter: bool
    filter: int
    projects: _containers.RepeatedScalarFieldContainer[int]
    lazy: _containers.RepeatedScalarFieldContainer[LazyEval]
    partial_window_filter_selectivity: float

    def __init__(self, expressions: _Optional[_Iterable[_Union[_expression_pb2.ScalarExpression, _Mapping]]]=..., no_filter: bool=..., filter: _Optional[int]=..., projects: _Optional[_Iterable[int]]=..., lazy: _Optional[_Iterable[_Union[LazyEval, str]]]=..., partial_window_filter_selectivity: _Optional[float]=...) -> None:
        ...

class LogicalCalc(_message.Message):
    __slots__ = ('condition', 'projects', 'partial_window_filter_selectivity')
    CONDITION_FIELD_NUMBER: _ClassVar[int]
    PROJECTS_FIELD_NUMBER: _ClassVar[int]
    PARTIAL_WINDOW_FILTER_SELECTIVITY_FIELD_NUMBER: _ClassVar[int]
    condition: _expression_pb2.ScalarExpression
    projects: _containers.RepeatedCompositeFieldContainer[_expression_pb2.ScalarExpression]
    partial_window_filter_selectivity: float

    def __init__(self, condition: _Optional[_Union[_expression_pb2.ScalarExpression, _Mapping]]=..., projects: _Optional[_Iterable[_Union[_expression_pb2.ScalarExpression, _Mapping]]]=..., partial_window_filter_selectivity: _Optional[float]=...) -> None:
        ...

class ExpandShuffleKeys(_message.Message):
    __slots__ = ('shuffle_keys',)
    SHUFFLE_KEYS_FIELD_NUMBER: _ClassVar[int]
    shuffle_keys: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, shuffle_keys: _Optional[_Iterable[int]]=...) -> None:
        ...

class Expand(_message.Message):
    __slots__ = ('expressions', 'shuffle_keys')
    EXPRESSIONS_FIELD_NUMBER: _ClassVar[int]
    SHUFFLE_KEYS_FIELD_NUMBER: _ClassVar[int]
    expressions: _containers.RepeatedCompositeFieldContainer[_expression_pb2.ScalarExpression]
    shuffle_keys: ExpandShuffleKeys

    def __init__(self, expressions: _Optional[_Iterable[_Union[_expression_pb2.ScalarExpression, _Mapping]]]=..., shuffle_keys: _Optional[_Union[ExpandShuffleKeys, _Mapping]]=...) -> None:
        ...

class GroupingKeySet(_message.Message):
    __slots__ = ('keys',)
    KEYS_FIELD_NUMBER: _ClassVar[int]
    keys: _containers.RepeatedCompositeFieldContainer[_expression_pb2.Reference]

    def __init__(self, keys: _Optional[_Iterable[_Union[_expression_pb2.Reference, _Mapping]]]=...) -> None:
        ...

class Grouping(_message.Message):
    __slots__ = ('keys', 'keySets', 'aggregate_calls', 'grouping_id_start_from', 'grouping_id_col_offset')
    KEYS_FIELD_NUMBER: _ClassVar[int]
    KEYSETS_FIELD_NUMBER: _ClassVar[int]
    AGGREGATE_CALLS_FIELD_NUMBER: _ClassVar[int]
    GROUPING_ID_START_FROM_FIELD_NUMBER: _ClassVar[int]
    GROUPING_ID_COL_OFFSET_FIELD_NUMBER: _ClassVar[int]
    keys: _containers.RepeatedCompositeFieldContainer[_expression_pb2.Reference]
    keySets: _containers.RepeatedCompositeFieldContainer[GroupingKeySet]
    aggregate_calls: _containers.RepeatedCompositeFieldContainer[AggregateCall]
    grouping_id_start_from: int
    grouping_id_col_offset: int

    def __init__(self, keys: _Optional[_Iterable[_Union[_expression_pb2.Reference, _Mapping]]]=..., keySets: _Optional[_Iterable[_Union[GroupingKeySet, _Mapping]]]=..., aggregate_calls: _Optional[_Iterable[_Union[AggregateCall, _Mapping]]]=..., grouping_id_start_from: _Optional[int]=..., grouping_id_col_offset: _Optional[int]=...) -> None:
        ...

class CalcStats(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class HashTableStats(_message.Message):
    __slots__ = ('num_buckets', 'num_keys', 'num_resize', 'num_accesses', 'num_collisions', 'used_memory')
    NUM_BUCKETS_FIELD_NUMBER: _ClassVar[int]
    NUM_KEYS_FIELD_NUMBER: _ClassVar[int]
    NUM_RESIZE_FIELD_NUMBER: _ClassVar[int]
    NUM_ACCESSES_FIELD_NUMBER: _ClassVar[int]
    NUM_COLLISIONS_FIELD_NUMBER: _ClassVar[int]
    USED_MEMORY_FIELD_NUMBER: _ClassVar[int]
    num_buckets: int
    num_keys: int
    num_resize: int
    num_accesses: int
    num_collisions: int
    used_memory: int

    def __init__(self, num_buckets: _Optional[int]=..., num_keys: _Optional[int]=..., num_resize: _Optional[int]=..., num_accesses: _Optional[int]=..., num_collisions: _Optional[int]=..., used_memory: _Optional[int]=...) -> None:
        ...

class HashJoinStats(_message.Message):
    __slots__ = ('build_timing', 'finish_build_timing', 'probe_timing', 'post_probe_timing', 'ht_stats', 'num_build_rows', 'num_distinct_build_rows', 'max_equal_build_rows', 'build_spill_stats', 'probe_spill_stats', 'probe_find_ht_timing', 'probe_output_timing', 'probe_eval_conjunct_timing', 'probe_output_conjunct_timing', 'num_null_rows')
    BUILD_TIMING_FIELD_NUMBER: _ClassVar[int]
    FINISH_BUILD_TIMING_FIELD_NUMBER: _ClassVar[int]
    PROBE_TIMING_FIELD_NUMBER: _ClassVar[int]
    POST_PROBE_TIMING_FIELD_NUMBER: _ClassVar[int]
    HT_STATS_FIELD_NUMBER: _ClassVar[int]
    NUM_BUILD_ROWS_FIELD_NUMBER: _ClassVar[int]
    NUM_DISTINCT_BUILD_ROWS_FIELD_NUMBER: _ClassVar[int]
    MAX_EQUAL_BUILD_ROWS_FIELD_NUMBER: _ClassVar[int]
    BUILD_SPILL_STATS_FIELD_NUMBER: _ClassVar[int]
    PROBE_SPILL_STATS_FIELD_NUMBER: _ClassVar[int]
    PROBE_FIND_HT_TIMING_FIELD_NUMBER: _ClassVar[int]
    PROBE_OUTPUT_TIMING_FIELD_NUMBER: _ClassVar[int]
    PROBE_EVAL_CONJUNCT_TIMING_FIELD_NUMBER: _ClassVar[int]
    PROBE_OUTPUT_CONJUNCT_TIMING_FIELD_NUMBER: _ClassVar[int]
    NUM_NULL_ROWS_FIELD_NUMBER: _ClassVar[int]
    build_timing: Timing
    finish_build_timing: Timing
    probe_timing: Timing
    post_probe_timing: Timing
    ht_stats: HashTableStats
    num_build_rows: int
    num_distinct_build_rows: int
    max_equal_build_rows: int
    build_spill_stats: SpillStats
    probe_spill_stats: SpillStats
    probe_find_ht_timing: Timing
    probe_output_timing: Timing
    probe_eval_conjunct_timing: Timing
    probe_output_conjunct_timing: Timing
    num_null_rows: int

    def __init__(self, build_timing: _Optional[_Union[Timing, _Mapping]]=..., finish_build_timing: _Optional[_Union[Timing, _Mapping]]=..., probe_timing: _Optional[_Union[Timing, _Mapping]]=..., post_probe_timing: _Optional[_Union[Timing, _Mapping]]=..., ht_stats: _Optional[_Union[HashTableStats, _Mapping]]=..., num_build_rows: _Optional[int]=..., num_distinct_build_rows: _Optional[int]=..., max_equal_build_rows: _Optional[int]=..., build_spill_stats: _Optional[_Union[SpillStats, _Mapping]]=..., probe_spill_stats: _Optional[_Union[SpillStats, _Mapping]]=..., probe_find_ht_timing: _Optional[_Union[Timing, _Mapping]]=..., probe_output_timing: _Optional[_Union[Timing, _Mapping]]=..., probe_eval_conjunct_timing: _Optional[_Union[Timing, _Mapping]]=..., probe_output_conjunct_timing: _Optional[_Union[Timing, _Mapping]]=..., num_null_rows: _Optional[int]=...) -> None:
        ...

class MergeJoinStats(_message.Message):
    __slots__ = ('drive_close_group_count', 'drive_open_group_count', 'matched_group_count', 'non_matched_group_count', 'num_compare_ovc', 'num_compare_data', 'num_ovc_conflict', 'match_group_timing', 'output_timing', 'eval_conjunct_timing', 'output_conjunct_timing', 'left_add_input_timing', 'left_advance_timing', 'left_materialize_rows', 'right_add_input_timing', 'right_advance_timing', 'right_materialize_rows')
    DRIVE_CLOSE_GROUP_COUNT_FIELD_NUMBER: _ClassVar[int]
    DRIVE_OPEN_GROUP_COUNT_FIELD_NUMBER: _ClassVar[int]
    MATCHED_GROUP_COUNT_FIELD_NUMBER: _ClassVar[int]
    NON_MATCHED_GROUP_COUNT_FIELD_NUMBER: _ClassVar[int]
    NUM_COMPARE_OVC_FIELD_NUMBER: _ClassVar[int]
    NUM_COMPARE_DATA_FIELD_NUMBER: _ClassVar[int]
    NUM_OVC_CONFLICT_FIELD_NUMBER: _ClassVar[int]
    MATCH_GROUP_TIMING_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_TIMING_FIELD_NUMBER: _ClassVar[int]
    EVAL_CONJUNCT_TIMING_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_CONJUNCT_TIMING_FIELD_NUMBER: _ClassVar[int]
    LEFT_ADD_INPUT_TIMING_FIELD_NUMBER: _ClassVar[int]
    LEFT_ADVANCE_TIMING_FIELD_NUMBER: _ClassVar[int]
    LEFT_MATERIALIZE_ROWS_FIELD_NUMBER: _ClassVar[int]
    RIGHT_ADD_INPUT_TIMING_FIELD_NUMBER: _ClassVar[int]
    RIGHT_ADVANCE_TIMING_FIELD_NUMBER: _ClassVar[int]
    RIGHT_MATERIALIZE_ROWS_FIELD_NUMBER: _ClassVar[int]
    drive_close_group_count: int
    drive_open_group_count: int
    matched_group_count: int
    non_matched_group_count: int
    num_compare_ovc: int
    num_compare_data: int
    num_ovc_conflict: int
    match_group_timing: Timing
    output_timing: Timing
    eval_conjunct_timing: Timing
    output_conjunct_timing: Timing
    left_add_input_timing: Timing
    left_advance_timing: Timing
    left_materialize_rows: int
    right_add_input_timing: Timing
    right_advance_timing: Timing
    right_materialize_rows: int

    def __init__(self, drive_close_group_count: _Optional[int]=..., drive_open_group_count: _Optional[int]=..., matched_group_count: _Optional[int]=..., non_matched_group_count: _Optional[int]=..., num_compare_ovc: _Optional[int]=..., num_compare_data: _Optional[int]=..., num_ovc_conflict: _Optional[int]=..., match_group_timing: _Optional[_Union[Timing, _Mapping]]=..., output_timing: _Optional[_Union[Timing, _Mapping]]=..., eval_conjunct_timing: _Optional[_Union[Timing, _Mapping]]=..., output_conjunct_timing: _Optional[_Union[Timing, _Mapping]]=..., left_add_input_timing: _Optional[_Union[Timing, _Mapping]]=..., left_advance_timing: _Optional[_Union[Timing, _Mapping]]=..., left_materialize_rows: _Optional[int]=..., right_add_input_timing: _Optional[_Union[Timing, _Mapping]]=..., right_advance_timing: _Optional[_Union[Timing, _Mapping]]=..., right_materialize_rows: _Optional[int]=...) -> None:
        ...

class HashAggregateStats(_message.Message):
    __slots__ = ('assign_states_timing', 'update_states_timing', 'output_timing', 'ht_stats', 'states_used_memory', 'pass_through_rows', 'input_spill_stats', 'aggregated_spill_stats')
    ASSIGN_STATES_TIMING_FIELD_NUMBER: _ClassVar[int]
    UPDATE_STATES_TIMING_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_TIMING_FIELD_NUMBER: _ClassVar[int]
    HT_STATS_FIELD_NUMBER: _ClassVar[int]
    STATES_USED_MEMORY_FIELD_NUMBER: _ClassVar[int]
    PASS_THROUGH_ROWS_FIELD_NUMBER: _ClassVar[int]
    INPUT_SPILL_STATS_FIELD_NUMBER: _ClassVar[int]
    AGGREGATED_SPILL_STATS_FIELD_NUMBER: _ClassVar[int]
    assign_states_timing: Timing
    update_states_timing: Timing
    output_timing: Timing
    ht_stats: HashTableStats
    states_used_memory: int
    pass_through_rows: int
    input_spill_stats: SpillStats
    aggregated_spill_stats: SpillStats

    def __init__(self, assign_states_timing: _Optional[_Union[Timing, _Mapping]]=..., update_states_timing: _Optional[_Union[Timing, _Mapping]]=..., output_timing: _Optional[_Union[Timing, _Mapping]]=..., ht_stats: _Optional[_Union[HashTableStats, _Mapping]]=..., states_used_memory: _Optional[int]=..., pass_through_rows: _Optional[int]=..., input_spill_stats: _Optional[_Union[SpillStats, _Mapping]]=..., aggregated_spill_stats: _Optional[_Union[SpillStats, _Mapping]]=...) -> None:
        ...

class MergeAggregateStats(_message.Message):
    __slots__ = ('assign_states_timing', 'update_states_timing', 'output_timing')
    ASSIGN_STATES_TIMING_FIELD_NUMBER: _ClassVar[int]
    UPDATE_STATES_TIMING_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_TIMING_FIELD_NUMBER: _ClassVar[int]
    assign_states_timing: Timing
    update_states_timing: Timing
    output_timing: Timing

    def __init__(self, assign_states_timing: _Optional[_Union[Timing, _Mapping]]=..., update_states_timing: _Optional[_Union[Timing, _Mapping]]=..., output_timing: _Optional[_Union[Timing, _Mapping]]=...) -> None:
        ...

class LocalSortStats(_message.Message):
    __slots__ = ('spill_stats', 'generate_run_timing', 'merge_run_timing', 'init_merge_timing', 'accumulate_block_timing', 'sort_key_timing', 'permute_payload_timing', 'spill_run_timing')
    SPILL_STATS_FIELD_NUMBER: _ClassVar[int]
    GENERATE_RUN_TIMING_FIELD_NUMBER: _ClassVar[int]
    MERGE_RUN_TIMING_FIELD_NUMBER: _ClassVar[int]
    INIT_MERGE_TIMING_FIELD_NUMBER: _ClassVar[int]
    ACCUMULATE_BLOCK_TIMING_FIELD_NUMBER: _ClassVar[int]
    SORT_KEY_TIMING_FIELD_NUMBER: _ClassVar[int]
    PERMUTE_PAYLOAD_TIMING_FIELD_NUMBER: _ClassVar[int]
    SPILL_RUN_TIMING_FIELD_NUMBER: _ClassVar[int]
    spill_stats: SpillStats
    generate_run_timing: Timing
    merge_run_timing: Timing
    init_merge_timing: Timing
    accumulate_block_timing: Timing
    sort_key_timing: Timing
    permute_payload_timing: Timing
    spill_run_timing: Timing

    def __init__(self, spill_stats: _Optional[_Union[SpillStats, _Mapping]]=..., generate_run_timing: _Optional[_Union[Timing, _Mapping]]=..., merge_run_timing: _Optional[_Union[Timing, _Mapping]]=..., init_merge_timing: _Optional[_Union[Timing, _Mapping]]=..., accumulate_block_timing: _Optional[_Union[Timing, _Mapping]]=..., sort_key_timing: _Optional[_Union[Timing, _Mapping]]=..., permute_payload_timing: _Optional[_Union[Timing, _Mapping]]=..., spill_run_timing: _Optional[_Union[Timing, _Mapping]]=...) -> None:
        ...

class MergeSortStats(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class UnionAllStats(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class ValuesStats(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class BufferStats(_message.Message):
    __slots__ = ('spill_stats',)
    SPILL_STATS_FIELD_NUMBER: _ClassVar[int]
    spill_stats: SpillStats

    def __init__(self, spill_stats: _Optional[_Union[SpillStats, _Mapping]]=...) -> None:
        ...

class WindowStats(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class PartialWindowStats(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class ExpandStats(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class LateralViewStats(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class LocalExchangeStats(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class ExchangeSinkStats(_message.Message):
    __slots__ = ('sent_byte_count', 'compress_input_byte_count', 'serialize_write_timing', 'serialize_flush_timing', 'compress_timing', 'acquire_buffer_timing', 'submit_buffer_timing', 'close_timing', 'submit_buffer_async_timing', 'flush_auto_count', 'flush_manual_count')
    SENT_BYTE_COUNT_FIELD_NUMBER: _ClassVar[int]
    COMPRESS_INPUT_BYTE_COUNT_FIELD_NUMBER: _ClassVar[int]
    SERIALIZE_WRITE_TIMING_FIELD_NUMBER: _ClassVar[int]
    SERIALIZE_FLUSH_TIMING_FIELD_NUMBER: _ClassVar[int]
    COMPRESS_TIMING_FIELD_NUMBER: _ClassVar[int]
    ACQUIRE_BUFFER_TIMING_FIELD_NUMBER: _ClassVar[int]
    SUBMIT_BUFFER_TIMING_FIELD_NUMBER: _ClassVar[int]
    CLOSE_TIMING_FIELD_NUMBER: _ClassVar[int]
    SUBMIT_BUFFER_ASYNC_TIMING_FIELD_NUMBER: _ClassVar[int]
    FLUSH_AUTO_COUNT_FIELD_NUMBER: _ClassVar[int]
    FLUSH_MANUAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    sent_byte_count: int
    compress_input_byte_count: int
    serialize_write_timing: Timing
    serialize_flush_timing: Timing
    compress_timing: Timing
    acquire_buffer_timing: Timing
    submit_buffer_timing: Timing
    close_timing: Timing
    submit_buffer_async_timing: Timing
    flush_auto_count: int
    flush_manual_count: int

    def __init__(self, sent_byte_count: _Optional[int]=..., compress_input_byte_count: _Optional[int]=..., serialize_write_timing: _Optional[_Union[Timing, _Mapping]]=..., serialize_flush_timing: _Optional[_Union[Timing, _Mapping]]=..., compress_timing: _Optional[_Union[Timing, _Mapping]]=..., acquire_buffer_timing: _Optional[_Union[Timing, _Mapping]]=..., submit_buffer_timing: _Optional[_Union[Timing, _Mapping]]=..., close_timing: _Optional[_Union[Timing, _Mapping]]=..., submit_buffer_async_timing: _Optional[_Union[Timing, _Mapping]]=..., flush_auto_count: _Optional[int]=..., flush_manual_count: _Optional[int]=...) -> None:
        ...

class ExchangeSourceStats(_message.Message):
    __slots__ = ('received_byte_count', 'decompress_output_byte_count', 'deserialize_timing', 'decompress_timing', 'read_buffer_timing', 'sort_timing', 'sorter_spill_stats')
    RECEIVED_BYTE_COUNT_FIELD_NUMBER: _ClassVar[int]
    DECOMPRESS_OUTPUT_BYTE_COUNT_FIELD_NUMBER: _ClassVar[int]
    DESERIALIZE_TIMING_FIELD_NUMBER: _ClassVar[int]
    DECOMPRESS_TIMING_FIELD_NUMBER: _ClassVar[int]
    READ_BUFFER_TIMING_FIELD_NUMBER: _ClassVar[int]
    SORT_TIMING_FIELD_NUMBER: _ClassVar[int]
    SORTER_SPILL_STATS_FIELD_NUMBER: _ClassVar[int]
    received_byte_count: int
    decompress_output_byte_count: int
    deserialize_timing: Timing
    decompress_timing: Timing
    read_buffer_timing: Timing
    sort_timing: Timing
    sorter_spill_stats: SpillStats

    def __init__(self, received_byte_count: _Optional[int]=..., decompress_output_byte_count: _Optional[int]=..., deserialize_timing: _Optional[_Union[Timing, _Mapping]]=..., decompress_timing: _Optional[_Union[Timing, _Mapping]]=..., read_buffer_timing: _Optional[_Union[Timing, _Mapping]]=..., sort_timing: _Optional[_Union[Timing, _Mapping]]=..., sorter_spill_stats: _Optional[_Union[SpillStats, _Mapping]]=...) -> None:
        ...

class Table(_message.Message):
    __slots__ = ('path', 'table_meta', 'instance_id', 'table_id', 'properties')
    PATH_FIELD_NUMBER: _ClassVar[int]
    TABLE_META_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    TABLE_ID_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    path: _containers.RepeatedScalarFieldContainer[str]
    table_meta: _table_meta_pb2.TableMeta
    instance_id: int
    table_id: int
    properties: _containers.RepeatedCompositeFieldContainer[_property_pb2.Property]

    def __init__(self, path: _Optional[_Iterable[str]]=..., table_meta: _Optional[_Union[_table_meta_pb2.TableMeta, _Mapping]]=..., instance_id: _Optional[int]=..., table_id: _Optional[int]=..., properties: _Optional[_Iterable[_Union[_property_pb2.Property, _Mapping]]]=...) -> None:
        ...

class Values(_message.Message):
    __slots__ = ('row_count', 'col_count', 'data', 'broadcast')
    ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    COL_COUNT_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    BROADCAST_FIELD_NUMBER: _ClassVar[int]
    row_count: int
    col_count: int
    data: _containers.RepeatedCompositeFieldContainer[_expression_pb2.ScalarExpression]
    broadcast: bool

    def __init__(self, row_count: _Optional[int]=..., col_count: _Optional[int]=..., data: _Optional[_Iterable[_Union[_expression_pb2.ScalarExpression, _Mapping]]]=..., broadcast: bool=...) -> None:
        ...

class SortKeyDesc(_message.Message):
    __slots__ = ('id', 'order', 'null_order')
    ID_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    NULL_ORDER_FIELD_NUMBER: _ClassVar[int]
    id: int
    order: _table_common_pb2.Order
    null_order: _table_common_pb2.NullOrder

    def __init__(self, id: _Optional[int]=..., order: _Optional[_Union[_table_common_pb2.Order, str]]=..., null_order: _Optional[_Union[_table_common_pb2.NullOrder, str]]=...) -> None:
        ...

class TableScan(_message.Message):
    __slots__ = ('table', 'data_source_info_id', 'cols', 'filter', 'ensuredFilter', 'props', 'align', 'alignDop', 'orders', 'range_keys', 'range_distribution_id', 'incremental_table_property', 'filter4Meta', 'subfields')

    class PropsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    TABLE_FIELD_NUMBER: _ClassVar[int]
    DATA_SOURCE_INFO_ID_FIELD_NUMBER: _ClassVar[int]
    COLS_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    ENSUREDFILTER_FIELD_NUMBER: _ClassVar[int]
    PROPS_FIELD_NUMBER: _ClassVar[int]
    ALIGN_FIELD_NUMBER: _ClassVar[int]
    ALIGNDOP_FIELD_NUMBER: _ClassVar[int]
    ORDERS_FIELD_NUMBER: _ClassVar[int]
    RANGE_KEYS_FIELD_NUMBER: _ClassVar[int]
    RANGE_DISTRIBUTION_ID_FIELD_NUMBER: _ClassVar[int]
    INCREMENTAL_TABLE_PROPERTY_FIELD_NUMBER: _ClassVar[int]
    FILTER4META_FIELD_NUMBER: _ClassVar[int]
    SUBFIELDS_FIELD_NUMBER: _ClassVar[int]
    table: Table
    data_source_info_id: int
    cols: _containers.RepeatedScalarFieldContainer[int]
    filter: _expression_pb2.ScalarExpression
    ensuredFilter: _expression_pb2.ScalarExpression
    props: _containers.ScalarMap[str, str]
    align: bool
    alignDop: int
    orders: _containers.RepeatedCompositeFieldContainer[SortKeyDesc]
    range_keys: _containers.RepeatedScalarFieldContainer[int]
    range_distribution_id: int
    incremental_table_property: IncrementalTableProperty
    filter4Meta: _expression_pb2.ScalarExpression
    subfields: _expression_pb2.SubFieldsPruning

    def __init__(self, table: _Optional[_Union[Table, _Mapping]]=..., data_source_info_id: _Optional[int]=..., cols: _Optional[_Iterable[int]]=..., filter: _Optional[_Union[_expression_pb2.ScalarExpression, _Mapping]]=..., ensuredFilter: _Optional[_Union[_expression_pb2.ScalarExpression, _Mapping]]=..., props: _Optional[_Mapping[str, str]]=..., align: bool=..., alignDop: _Optional[int]=..., orders: _Optional[_Iterable[_Union[SortKeyDesc, _Mapping]]]=..., range_keys: _Optional[_Iterable[int]]=..., range_distribution_id: _Optional[int]=..., incremental_table_property: _Optional[_Union[IncrementalTableProperty, _Mapping]]=..., filter4Meta: _Optional[_Union[_expression_pb2.ScalarExpression, _Mapping]]=..., subfields: _Optional[_Union[_expression_pb2.SubFieldsPruning, _Mapping]]=...) -> None:
        ...

class FilePruningStats(_message.Message):
    __slots__ = ('fileCount', 'prunedFileCount')
    FILECOUNT_FIELD_NUMBER: _ClassVar[int]
    PRUNEDFILECOUNT_FIELD_NUMBER: _ClassVar[int]
    fileCount: int
    prunedFileCount: int

    def __init__(self, fileCount: _Optional[int]=..., prunedFileCount: _Optional[int]=...) -> None:
        ...

class TableScanStats(_message.Message):
    __slots__ = ('input_stats', 'pruning_stats')
    INPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    PRUNING_STATS_FIELD_NUMBER: _ClassVar[int]
    input_stats: DataInputStats
    pruning_stats: FilePruningStats

    def __init__(self, input_stats: _Optional[_Union[DataInputStats, _Mapping]]=..., pruning_stats: _Optional[_Union[FilePruningStats, _Mapping]]=...) -> None:
        ...

class IncrementalTableProperty(_message.Message):
    __slots__ = ('to', 'consolidate', 'fromMetaVersion', 'toMetaVersion', 'rowCount', 'baseRowCount')
    FROM_FIELD_NUMBER: _ClassVar[int]
    TO_FIELD_NUMBER: _ClassVar[int]
    CONSOLIDATE_FIELD_NUMBER: _ClassVar[int]
    FROMMETAVERSION_FIELD_NUMBER: _ClassVar[int]
    TOMETAVERSION_FIELD_NUMBER: _ClassVar[int]
    ROWCOUNT_FIELD_NUMBER: _ClassVar[int]
    BASEROWCOUNT_FIELD_NUMBER: _ClassVar[int]
    to: int
    consolidate: bool
    fromMetaVersion: int
    toMetaVersion: int
    rowCount: int
    baseRowCount: int

    def __init__(self, to: _Optional[int]=..., consolidate: bool=..., fromMetaVersion: _Optional[int]=..., toMetaVersion: _Optional[int]=..., rowCount: _Optional[int]=..., baseRowCount: _Optional[int]=..., **kwargs) -> None:
        ...

class ShuffleType(_message.Message):
    __slots__ = ('type',)

    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        HASH: _ClassVar[ShuffleType.Type]
        RANGE: _ClassVar[ShuffleType.Type]
        BROADCAST: _ClassVar[ShuffleType.Type]
        SINGLE: _ClassVar[ShuffleType.Type]
        RANDOM: _ClassVar[ShuffleType.Type]
        PAIR_WIZE: _ClassVar[ShuffleType.Type]
        ADAPTIVE_HASH: _ClassVar[ShuffleType.Type]
        ADAPTIVE_RANGE: _ClassVar[ShuffleType.Type]
        ROUND_ROBIN: _ClassVar[ShuffleType.Type]
    HASH: ShuffleType.Type
    RANGE: ShuffleType.Type
    BROADCAST: ShuffleType.Type
    SINGLE: ShuffleType.Type
    RANDOM: ShuffleType.Type
    PAIR_WIZE: ShuffleType.Type
    ADAPTIVE_HASH: ShuffleType.Type
    ADAPTIVE_RANGE: ShuffleType.Type
    ROUND_ROBIN: ShuffleType.Type
    TYPE_FIELD_NUMBER: _ClassVar[int]
    type: ShuffleType.Type

    def __init__(self, type: _Optional[_Union[ShuffleType.Type, str]]=...) -> None:
        ...

class TableSink(_message.Message):
    __slots__ = ('table', 'overwrite', 'data_source_info_id', 'keys', 'flags', 'part_sort_keys', 'input_fields', 'file_slice_keys', 'static_partition', 'part_values', 'nop')
    TABLE_FIELD_NUMBER: _ClassVar[int]
    OVERWRITE_FIELD_NUMBER: _ClassVar[int]
    DATA_SOURCE_INFO_ID_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    FLAGS_FIELD_NUMBER: _ClassVar[int]
    PART_SORT_KEYS_FIELD_NUMBER: _ClassVar[int]
    INPUT_FIELDS_FIELD_NUMBER: _ClassVar[int]
    FILE_SLICE_KEYS_FIELD_NUMBER: _ClassVar[int]
    STATIC_PARTITION_FIELD_NUMBER: _ClassVar[int]
    PART_VALUES_FIELD_NUMBER: _ClassVar[int]
    NOP_FIELD_NUMBER: _ClassVar[int]
    table: Table
    overwrite: bool
    data_source_info_id: int
    keys: _containers.RepeatedCompositeFieldContainer[_expression_pb2.Reference]
    flags: int
    part_sort_keys: _containers.RepeatedCompositeFieldContainer[_expression_pb2.Reference]
    input_fields: _containers.RepeatedScalarFieldContainer[int]
    file_slice_keys: _containers.RepeatedCompositeFieldContainer[_expression_pb2.Reference]
    static_partition: bool
    part_values: _virtual_value_info_pb2.VirtualValueInfo
    nop: bool

    def __init__(self, table: _Optional[_Union[Table, _Mapping]]=..., overwrite: bool=..., data_source_info_id: _Optional[int]=..., keys: _Optional[_Iterable[_Union[_expression_pb2.Reference, _Mapping]]]=..., flags: _Optional[int]=..., part_sort_keys: _Optional[_Iterable[_Union[_expression_pb2.Reference, _Mapping]]]=..., input_fields: _Optional[_Iterable[int]]=..., file_slice_keys: _Optional[_Iterable[_Union[_expression_pb2.Reference, _Mapping]]]=..., static_partition: bool=..., part_values: _Optional[_Union[_virtual_value_info_pb2.VirtualValueInfo, _Mapping]]=..., nop: bool=...) -> None:
        ...

class ShuffleWrite(_message.Message):
    __slots__ = ('shuffleType', 'keys', 'orders', 'limit', 'function_version', 'bucket_type', 'range_distribution_id')
    SHUFFLETYPE_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    ORDERS_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_VERSION_FIELD_NUMBER: _ClassVar[int]
    BUCKET_TYPE_FIELD_NUMBER: _ClassVar[int]
    RANGE_DISTRIBUTION_ID_FIELD_NUMBER: _ClassVar[int]
    shuffleType: ShuffleType
    keys: _containers.RepeatedCompositeFieldContainer[_expression_pb2.Reference]
    orders: _containers.RepeatedCompositeFieldContainer[OrderByDesc]
    limit: int
    function_version: int
    bucket_type: _table_common_pb2.HashBucketType
    range_distribution_id: int

    def __init__(self, shuffleType: _Optional[_Union[ShuffleType, _Mapping]]=..., keys: _Optional[_Iterable[_Union[_expression_pb2.Reference, _Mapping]]]=..., orders: _Optional[_Iterable[_Union[OrderByDesc, _Mapping]]]=..., limit: _Optional[int]=..., function_version: _Optional[int]=..., bucket_type: _Optional[_Union[_table_common_pb2.HashBucketType, str]]=..., range_distribution_id: _Optional[int]=...) -> None:
        ...

class ShuffleRead(_message.Message):
    __slots__ = ('orders', 'limit', 'offset', 'shuffleType', 'multi_accessed', 'merge_sort')
    ORDERS_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    SHUFFLETYPE_FIELD_NUMBER: _ClassVar[int]
    MULTI_ACCESSED_FIELD_NUMBER: _ClassVar[int]
    MERGE_SORT_FIELD_NUMBER: _ClassVar[int]
    orders: _containers.RepeatedCompositeFieldContainer[OrderByDesc]
    limit: int
    offset: int
    shuffleType: ShuffleType
    multi_accessed: bool
    merge_sort: bool

    def __init__(self, orders: _Optional[_Iterable[_Union[OrderByDesc, _Mapping]]]=..., limit: _Optional[int]=..., offset: _Optional[int]=..., shuffleType: _Optional[_Union[ShuffleType, _Mapping]]=..., multi_accessed: bool=..., merge_sort: bool=...) -> None:
        ...

class LocalExchange(_message.Message):
    __slots__ = ('shuffleType', 'keys', 'orders', 'limit', 'offset', 'function_version')
    SHUFFLETYPE_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    ORDERS_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_VERSION_FIELD_NUMBER: _ClassVar[int]
    shuffleType: ShuffleType
    keys: _containers.RepeatedCompositeFieldContainer[_expression_pb2.Reference]
    orders: _containers.RepeatedCompositeFieldContainer[OrderByDesc]
    limit: int
    offset: int
    function_version: int

    def __init__(self, shuffleType: _Optional[_Union[ShuffleType, _Mapping]]=..., keys: _Optional[_Iterable[_Union[_expression_pb2.Reference, _Mapping]]]=..., orders: _Optional[_Iterable[_Union[OrderByDesc, _Mapping]]]=..., limit: _Optional[int]=..., offset: _Optional[int]=..., function_version: _Optional[int]=...) -> None:
        ...

class LocalSort(_message.Message):
    __slots__ = ('orders', 'limit', 'offset', 'sorted_prefix_cnt')
    ORDERS_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    SORTED_PREFIX_CNT_FIELD_NUMBER: _ClassVar[int]
    orders: _containers.RepeatedCompositeFieldContainer[OrderByDesc]
    limit: int
    offset: int
    sorted_prefix_cnt: int

    def __init__(self, orders: _Optional[_Iterable[_Union[OrderByDesc, _Mapping]]]=..., limit: _Optional[int]=..., offset: _Optional[int]=..., sorted_prefix_cnt: _Optional[int]=...) -> None:
        ...

class LogicalSort(_message.Message):
    __slots__ = ('keys', 'orders', 'limit', 'offset')
    KEYS_FIELD_NUMBER: _ClassVar[int]
    ORDERS_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_FIELD_NUMBER: _ClassVar[int]
    keys: _containers.RepeatedCompositeFieldContainer[_expression_pb2.Reference]
    orders: _containers.RepeatedCompositeFieldContainer[OrderByDesc]
    limit: _expression_pb2.ScalarExpression
    offset: _expression_pb2.ScalarExpression

    def __init__(self, keys: _Optional[_Iterable[_Union[_expression_pb2.Reference, _Mapping]]]=..., orders: _Optional[_Iterable[_Union[OrderByDesc, _Mapping]]]=..., limit: _Optional[_Union[_expression_pb2.ScalarExpression, _Mapping]]=..., offset: _Optional[_Union[_expression_pb2.ScalarExpression, _Mapping]]=..., **kwargs) -> None:
        ...

class SetOperator(_message.Message):
    __slots__ = ('type', 'all', 'input_references')
    TYPE_FIELD_NUMBER: _ClassVar[int]
    ALL_FIELD_NUMBER: _ClassVar[int]
    INPUT_REFERENCES_FIELD_NUMBER: _ClassVar[int]
    type: SetOpType
    all: bool
    input_references: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, type: _Optional[_Union[SetOpType, str]]=..., all: bool=..., input_references: _Optional[_Iterable[int]]=...) -> None:
        ...

class DeltaApplyStats(_message.Message):
    __slots__ = ('deleted_row_count', 'updated_row_count', 'copied_dest_row_count', 'copied_time_elapsed_us')
    DELETED_ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    COPIED_DEST_ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    COPIED_TIME_ELAPSED_US_FIELD_NUMBER: _ClassVar[int]
    deleted_row_count: int
    updated_row_count: int
    copied_dest_row_count: int
    copied_time_elapsed_us: int

    def __init__(self, deleted_row_count: _Optional[int]=..., updated_row_count: _Optional[int]=..., copied_dest_row_count: _Optional[int]=..., copied_time_elapsed_us: _Optional[int]=...) -> None:
        ...

class DataInputStats(_message.Message):
    __slots__ = ('raw_input_byte_count', 'row_count', 'file_input_stats', 'file_format_stats', 'time_elapsed_us')
    RAW_INPUT_BYTE_COUNT_FIELD_NUMBER: _ClassVar[int]
    ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    FILE_INPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    FILE_FORMAT_STATS_FIELD_NUMBER: _ClassVar[int]
    TIME_ELAPSED_US_FIELD_NUMBER: _ClassVar[int]
    raw_input_byte_count: int
    row_count: int
    file_input_stats: FileRangesInputStats
    file_format_stats: FileInputStats
    time_elapsed_us: int

    def __init__(self, raw_input_byte_count: _Optional[int]=..., row_count: _Optional[int]=..., file_input_stats: _Optional[_Union[FileRangesInputStats, _Mapping]]=..., file_format_stats: _Optional[_Union[FileInputStats, _Mapping]]=..., time_elapsed_us: _Optional[int]=...) -> None:
        ...

class FileRangesInputStats(_message.Message):
    __slots__ = ('file_input_stats', 'ppd_filter', 'pruned_file_count', 'prefetched_file_count')
    FILE_INPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    PPD_FILTER_FIELD_NUMBER: _ClassVar[int]
    PRUNED_FILE_COUNT_FIELD_NUMBER: _ClassVar[int]
    PREFETCHED_FILE_COUNT_FIELD_NUMBER: _ClassVar[int]
    file_input_stats: _containers.RepeatedCompositeFieldContainer[DataInputStats]
    ppd_filter: _containers.RepeatedScalarFieldContainer[str]
    pruned_file_count: int
    prefetched_file_count: int

    def __init__(self, file_input_stats: _Optional[_Iterable[_Union[DataInputStats, _Mapping]]]=..., ppd_filter: _Optional[_Iterable[str]]=..., pruned_file_count: _Optional[int]=..., prefetched_file_count: _Optional[int]=...) -> None:
        ...

class FileInputStats(_message.Message):
    __slots__ = ('format_type', 'range', 'text_input_stats', 'parquet_input_stats', 'memory_input_stats', 'orc_input_stats', 'dummy_input_stats', 'csv_input_stats', 'avro_input_stats', 'arrow_input_stats', 'io_stats', 'delta_file_stats', 'delta_apply_stats')
    FORMAT_TYPE_FIELD_NUMBER: _ClassVar[int]
    RANGE_FIELD_NUMBER: _ClassVar[int]
    TEXT_INPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    PARQUET_INPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    MEMORY_INPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    ORC_INPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    DUMMY_INPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    CSV_INPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    AVRO_INPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    ARROW_INPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    IO_STATS_FIELD_NUMBER: _ClassVar[int]
    DELTA_FILE_STATS_FIELD_NUMBER: _ClassVar[int]
    DELTA_APPLY_STATS_FIELD_NUMBER: _ClassVar[int]
    format_type: _file_format_type_pb2.FileFormatType
    range: _input_split_pb2.FileRange
    text_input_stats: TextInputStats
    parquet_input_stats: ParquetInputStats
    memory_input_stats: MemoryTableInputStats
    orc_input_stats: OrcInputStats
    dummy_input_stats: DummyInputStats
    csv_input_stats: CSVInputStats
    avro_input_stats: AvroInputStats
    arrow_input_stats: ArrowInputStats
    io_stats: FileIOInputStats
    delta_file_stats: _containers.RepeatedCompositeFieldContainer[DataInputStats]
    delta_apply_stats: DeltaApplyStats

    def __init__(self, format_type: _Optional[_Union[_file_format_type_pb2.FileFormatType, str]]=..., range: _Optional[_Union[_input_split_pb2.FileRange, _Mapping]]=..., text_input_stats: _Optional[_Union[TextInputStats, _Mapping]]=..., parquet_input_stats: _Optional[_Union[ParquetInputStats, _Mapping]]=..., memory_input_stats: _Optional[_Union[MemoryTableInputStats, _Mapping]]=..., orc_input_stats: _Optional[_Union[OrcInputStats, _Mapping]]=..., dummy_input_stats: _Optional[_Union[DummyInputStats, _Mapping]]=..., csv_input_stats: _Optional[_Union[CSVInputStats, _Mapping]]=..., avro_input_stats: _Optional[_Union[AvroInputStats, _Mapping]]=..., arrow_input_stats: _Optional[_Union[ArrowInputStats, _Mapping]]=..., io_stats: _Optional[_Union[FileIOInputStats, _Mapping]]=..., delta_file_stats: _Optional[_Iterable[_Union[DataInputStats, _Mapping]]]=..., delta_apply_stats: _Optional[_Union[DeltaApplyStats, _Mapping]]=...) -> None:
        ...

class FileIOInputStats(_message.Message):
    __slots__ = ('read_count', 'read_bytes', 'time_elapsed_us', 'prefetch_stats', 'input_stats')
    READ_COUNT_FIELD_NUMBER: _ClassVar[int]
    READ_BYTES_FIELD_NUMBER: _ClassVar[int]
    TIME_ELAPSED_US_FIELD_NUMBER: _ClassVar[int]
    PREFETCH_STATS_FIELD_NUMBER: _ClassVar[int]
    INPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    read_count: int
    read_bytes: int
    time_elapsed_us: int
    prefetch_stats: PrefetchStats
    input_stats: FileInputStreamStats

    def __init__(self, read_count: _Optional[int]=..., read_bytes: _Optional[int]=..., time_elapsed_us: _Optional[int]=..., prefetch_stats: _Optional[_Union[PrefetchStats, _Mapping]]=..., input_stats: _Optional[_Union[FileInputStreamStats, _Mapping]]=...) -> None:
        ...

class FileIOOutputStats(_message.Message):
    __slots__ = ('time_elapsed_us',)
    TIME_ELAPSED_US_FIELD_NUMBER: _ClassVar[int]
    time_elapsed_us: int

    def __init__(self, time_elapsed_us: _Optional[int]=...) -> None:
        ...

class PrefetchStats(_message.Message):
    __slots__ = ('driver_type', 'read_count', 'read_bytes', 'read_hit_cache', 'read_time_elapsed_us', 'io_count', 'io_bytes', 'io_time_elapsed_us')
    DRIVER_TYPE_FIELD_NUMBER: _ClassVar[int]
    READ_COUNT_FIELD_NUMBER: _ClassVar[int]
    READ_BYTES_FIELD_NUMBER: _ClassVar[int]
    READ_HIT_CACHE_FIELD_NUMBER: _ClassVar[int]
    READ_TIME_ELAPSED_US_FIELD_NUMBER: _ClassVar[int]
    IO_COUNT_FIELD_NUMBER: _ClassVar[int]
    IO_BYTES_FIELD_NUMBER: _ClassVar[int]
    IO_TIME_ELAPSED_US_FIELD_NUMBER: _ClassVar[int]
    driver_type: str
    read_count: int
    read_bytes: int
    read_hit_cache: int
    read_time_elapsed_us: int
    io_count: int
    io_bytes: int
    io_time_elapsed_us: int

    def __init__(self, driver_type: _Optional[str]=..., read_count: _Optional[int]=..., read_bytes: _Optional[int]=..., read_hit_cache: _Optional[int]=..., read_time_elapsed_us: _Optional[int]=..., io_count: _Optional[int]=..., io_bytes: _Optional[int]=..., io_time_elapsed_us: _Optional[int]=...) -> None:
        ...

class FileInputStreamStats(_message.Message):
    __slots__ = ('file_system_type', 'cache_file_input_stream_stats', 'cos_file_input_stream_stats')
    FILE_SYSTEM_TYPE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FILE_INPUT_STREAM_STATS_FIELD_NUMBER: _ClassVar[int]
    COS_FILE_INPUT_STREAM_STATS_FIELD_NUMBER: _ClassVar[int]
    file_system_type: _file_system_pb2.FileSystemType
    cache_file_input_stream_stats: CacheFileInputStreamStats
    cos_file_input_stream_stats: COSFileInputStreamStats

    def __init__(self, file_system_type: _Optional[_Union[_file_system_pb2.FileSystemType, str]]=..., cache_file_input_stream_stats: _Optional[_Union[CacheFileInputStreamStats, _Mapping]]=..., cos_file_input_stream_stats: _Optional[_Union[COSFileInputStreamStats, _Mapping]]=...) -> None:
        ...

class CacheFileInputStreamStats(_message.Message):
    __slots__ = ('cache_hit', 'short_circuit_stream_type', 'segment_mode', 'non_read_time_elapsed_us', 'rpc_read_bytes', 'rpc_read_time_elapsed_us', 'direct_read_bytes', 'direct_read_time_elapsed_us', 'base_stream_stats')
    CACHE_HIT_FIELD_NUMBER: _ClassVar[int]
    SHORT_CIRCUIT_STREAM_TYPE_FIELD_NUMBER: _ClassVar[int]
    SEGMENT_MODE_FIELD_NUMBER: _ClassVar[int]
    NON_READ_TIME_ELAPSED_US_FIELD_NUMBER: _ClassVar[int]
    RPC_READ_BYTES_FIELD_NUMBER: _ClassVar[int]
    RPC_READ_TIME_ELAPSED_US_FIELD_NUMBER: _ClassVar[int]
    DIRECT_READ_BYTES_FIELD_NUMBER: _ClassVar[int]
    DIRECT_READ_TIME_ELAPSED_US_FIELD_NUMBER: _ClassVar[int]
    BASE_STREAM_STATS_FIELD_NUMBER: _ClassVar[int]
    cache_hit: bool
    short_circuit_stream_type: str
    segment_mode: bool
    non_read_time_elapsed_us: int
    rpc_read_bytes: int
    rpc_read_time_elapsed_us: int
    direct_read_bytes: int
    direct_read_time_elapsed_us: int
    base_stream_stats: FileInputStreamStats

    def __init__(self, cache_hit: bool=..., short_circuit_stream_type: _Optional[str]=..., segment_mode: bool=..., non_read_time_elapsed_us: _Optional[int]=..., rpc_read_bytes: _Optional[int]=..., rpc_read_time_elapsed_us: _Optional[int]=..., direct_read_bytes: _Optional[int]=..., direct_read_time_elapsed_us: _Optional[int]=..., base_stream_stats: _Optional[_Union[FileInputStreamStats, _Mapping]]=...) -> None:
        ...

class COSFileInputStreamStats(_message.Message):
    __slots__ = ('retry_time',)
    RETRY_TIME_FIELD_NUMBER: _ClassVar[int]
    retry_time: int

    def __init__(self, retry_time: _Optional[int]=...) -> None:
        ...

class TextInputStats(_message.Message):
    __slots__ = ('missing_field_warned_count', 'extra_field_warned_count')
    MISSING_FIELD_WARNED_COUNT_FIELD_NUMBER: _ClassVar[int]
    EXTRA_FIELD_WARNED_COUNT_FIELD_NUMBER: _ClassVar[int]
    missing_field_warned_count: int
    extra_field_warned_count: int

    def __init__(self, missing_field_warned_count: _Optional[int]=..., extra_field_warned_count: _Optional[int]=...) -> None:
        ...

class MemoryTableInputStats(_message.Message):
    __slots__ = ('batch_count',)
    BATCH_COUNT_FIELD_NUMBER: _ClassVar[int]
    batch_count: int

    def __init__(self, batch_count: _Optional[int]=...) -> None:
        ...

class ParquetInputStats(_message.Message):
    __slots__ = ('batch_count', 'decompression_latency_ns', 'levels_decoding_latency_ns', 'data_loading_latency_ns', 'ppd_inclusive_latency_ns', 'reader_inclusive_latency_ns', 'requested_row_count', 'read_row_count', 'open_inclusive_latency_ns', 'open_blocking_latency_ns', 'file_bloom_filter_pruned', 'file_bitmap_filter_pruned', 'request_blocks', 'row_group_bloom_filter_pruned', 'row_group_stats_filter_pruned', 'row_group_dict_filter_pruned', 'apply_new_filter_stats')
    BATCH_COUNT_FIELD_NUMBER: _ClassVar[int]
    DECOMPRESSION_LATENCY_NS_FIELD_NUMBER: _ClassVar[int]
    LEVELS_DECODING_LATENCY_NS_FIELD_NUMBER: _ClassVar[int]
    DATA_LOADING_LATENCY_NS_FIELD_NUMBER: _ClassVar[int]
    PPD_INCLUSIVE_LATENCY_NS_FIELD_NUMBER: _ClassVar[int]
    READER_INCLUSIVE_LATENCY_NS_FIELD_NUMBER: _ClassVar[int]
    REQUESTED_ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    READ_ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    OPEN_INCLUSIVE_LATENCY_NS_FIELD_NUMBER: _ClassVar[int]
    OPEN_BLOCKING_LATENCY_NS_FIELD_NUMBER: _ClassVar[int]
    FILE_BLOOM_FILTER_PRUNED_FIELD_NUMBER: _ClassVar[int]
    FILE_BITMAP_FILTER_PRUNED_FIELD_NUMBER: _ClassVar[int]
    REQUEST_BLOCKS_FIELD_NUMBER: _ClassVar[int]
    ROW_GROUP_BLOOM_FILTER_PRUNED_FIELD_NUMBER: _ClassVar[int]
    ROW_GROUP_STATS_FILTER_PRUNED_FIELD_NUMBER: _ClassVar[int]
    ROW_GROUP_DICT_FILTER_PRUNED_FIELD_NUMBER: _ClassVar[int]
    APPLY_NEW_FILTER_STATS_FIELD_NUMBER: _ClassVar[int]
    batch_count: int
    decompression_latency_ns: int
    levels_decoding_latency_ns: int
    data_loading_latency_ns: int
    ppd_inclusive_latency_ns: int
    reader_inclusive_latency_ns: int
    requested_row_count: int
    read_row_count: int
    open_inclusive_latency_ns: int
    open_blocking_latency_ns: int
    file_bloom_filter_pruned: bool
    file_bitmap_filter_pruned: bool
    request_blocks: int
    row_group_bloom_filter_pruned: int
    row_group_stats_filter_pruned: int
    row_group_dict_filter_pruned: int
    apply_new_filter_stats: _containers.RepeatedCompositeFieldContainer[DataInputStats]

    def __init__(self, batch_count: _Optional[int]=..., decompression_latency_ns: _Optional[int]=..., levels_decoding_latency_ns: _Optional[int]=..., data_loading_latency_ns: _Optional[int]=..., ppd_inclusive_latency_ns: _Optional[int]=..., reader_inclusive_latency_ns: _Optional[int]=..., requested_row_count: _Optional[int]=..., read_row_count: _Optional[int]=..., open_inclusive_latency_ns: _Optional[int]=..., open_blocking_latency_ns: _Optional[int]=..., file_bloom_filter_pruned: bool=..., file_bitmap_filter_pruned: bool=..., request_blocks: _Optional[int]=..., row_group_bloom_filter_pruned: _Optional[int]=..., row_group_stats_filter_pruned: _Optional[int]=..., row_group_dict_filter_pruned: _Optional[int]=..., apply_new_filter_stats: _Optional[_Iterable[_Union[DataInputStats, _Mapping]]]=...) -> None:
        ...

class OrcInputStats(_message.Message):
    __slots__ = ('batch_count',)
    BATCH_COUNT_FIELD_NUMBER: _ClassVar[int]
    batch_count: int

    def __init__(self, batch_count: _Optional[int]=...) -> None:
        ...

class CSVInputStats(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class DummyInputStats(_message.Message):
    __slots__ = ('batch_count',)
    BATCH_COUNT_FIELD_NUMBER: _ClassVar[int]
    batch_count: int

    def __init__(self, batch_count: _Optional[int]=...) -> None:
        ...

class AvroInputStats(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class ArrowInputStats(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class DataOutputStats(_message.Message):
    __slots__ = ('raw_output_byte_count', 'row_count', 'file_output_stats', 'multiple_file_output_stats')
    RAW_OUTPUT_BYTE_COUNT_FIELD_NUMBER: _ClassVar[int]
    ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    FILE_OUTPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    MULTIPLE_FILE_OUTPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    raw_output_byte_count: int
    row_count: int
    file_output_stats: FileOutputStats
    multiple_file_output_stats: MultipleFileOutputStats

    def __init__(self, raw_output_byte_count: _Optional[int]=..., row_count: _Optional[int]=..., file_output_stats: _Optional[_Union[FileOutputStats, _Mapping]]=..., multiple_file_output_stats: _Optional[_Union[MultipleFileOutputStats, _Mapping]]=...) -> None:
        ...

class FileOutputStats(_message.Message):
    __slots__ = ('file_meta_data', 'text_output_stats', 'parquet_output_stats', 'orc_output_stats', 'avro_output_stats', 'arrow_output_stats', 'io_stats', 'delete_file_metas')
    FILE_META_DATA_FIELD_NUMBER: _ClassVar[int]
    TEXT_OUTPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    PARQUET_OUTPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    ORC_OUTPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    AVRO_OUTPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    ARROW_OUTPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    IO_STATS_FIELD_NUMBER: _ClassVar[int]
    DELETE_FILE_METAS_FIELD_NUMBER: _ClassVar[int]
    file_meta_data: _file_meta_data_pb2.FileMetaData
    text_output_stats: TextOutputStats
    parquet_output_stats: ParquetOutputStats
    orc_output_stats: OrcOutputStats
    avro_output_stats: AvroOutputStats
    arrow_output_stats: ArrowOutputStats
    io_stats: FileIOOutputStats
    delete_file_metas: _containers.RepeatedCompositeFieldContainer[_file_meta_data_pb2.FileMetaData]

    def __init__(self, file_meta_data: _Optional[_Union[_file_meta_data_pb2.FileMetaData, _Mapping]]=..., text_output_stats: _Optional[_Union[TextOutputStats, _Mapping]]=..., parquet_output_stats: _Optional[_Union[ParquetOutputStats, _Mapping]]=..., orc_output_stats: _Optional[_Union[OrcOutputStats, _Mapping]]=..., avro_output_stats: _Optional[_Union[AvroOutputStats, _Mapping]]=..., arrow_output_stats: _Optional[_Union[ArrowOutputStats, _Mapping]]=..., io_stats: _Optional[_Union[FileIOOutputStats, _Mapping]]=..., delete_file_metas: _Optional[_Iterable[_Union[_file_meta_data_pb2.FileMetaData, _Mapping]]]=...) -> None:
        ...

class MultipleFileOutputStats(_message.Message):
    __slots__ = ('file_output_stats',)
    FILE_OUTPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    file_output_stats: _containers.RepeatedCompositeFieldContainer[DataOutputStats]

    def __init__(self, file_output_stats: _Optional[_Iterable[_Union[DataOutputStats, _Mapping]]]=...) -> None:
        ...

class TextOutputStats(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class ParquetOutputStats(_message.Message):
    __slots__ = ('arrow_casting_time', 'page_compress_time', 'encoding_time')
    ARROW_CASTING_TIME_FIELD_NUMBER: _ClassVar[int]
    PAGE_COMPRESS_TIME_FIELD_NUMBER: _ClassVar[int]
    ENCODING_TIME_FIELD_NUMBER: _ClassVar[int]
    arrow_casting_time: int
    page_compress_time: int
    encoding_time: int

    def __init__(self, arrow_casting_time: _Optional[int]=..., page_compress_time: _Optional[int]=..., encoding_time: _Optional[int]=...) -> None:
        ...

class OrcOutputStats(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class AvroOutputStats(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class ArrowOutputStats(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class TableSinkStats(_message.Message):
    __slots__ = ('output_stats',)
    OUTPUT_STATS_FIELD_NUMBER: _ClassVar[int]
    output_stats: DataOutputStats

    def __init__(self, output_stats: _Optional[_Union[DataOutputStats, _Mapping]]=...) -> None:
        ...

class SpillStats(_message.Message):
    __slots__ = ('compressed_size', 'raw_size', 'spill_count', 'row_count', 'run_count', 'file_count', 'write_timing', 'read_timing')
    COMPRESSED_SIZE_FIELD_NUMBER: _ClassVar[int]
    RAW_SIZE_FIELD_NUMBER: _ClassVar[int]
    SPILL_COUNT_FIELD_NUMBER: _ClassVar[int]
    ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    RUN_COUNT_FIELD_NUMBER: _ClassVar[int]
    FILE_COUNT_FIELD_NUMBER: _ClassVar[int]
    WRITE_TIMING_FIELD_NUMBER: _ClassVar[int]
    READ_TIMING_FIELD_NUMBER: _ClassVar[int]
    compressed_size: int
    raw_size: int
    spill_count: int
    row_count: int
    run_count: int
    file_count: int
    write_timing: Timing
    read_timing: Timing

    def __init__(self, compressed_size: _Optional[int]=..., raw_size: _Optional[int]=..., spill_count: _Optional[int]=..., row_count: _Optional[int]=..., run_count: _Optional[int]=..., file_count: _Optional[int]=..., write_timing: _Optional[_Union[Timing, _Mapping]]=..., read_timing: _Optional[_Union[Timing, _Mapping]]=...) -> None:
        ...