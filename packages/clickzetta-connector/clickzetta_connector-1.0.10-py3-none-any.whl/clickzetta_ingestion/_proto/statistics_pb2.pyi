import expression_pb2 as _expression_pb2
import data_type_pb2 as _data_type_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class SortKeys(_message.Message):
    __slots__ = ('keys',)
    KEYS_FIELD_NUMBER: _ClassVar[int]
    keys: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, keys: _Optional[_Iterable[int]]=...) -> None:
        ...

class FieldBounds(_message.Message):
    __slots__ = ('bounds',)

    class BoundsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: _expression_pb2.Constant

        def __init__(self, key: _Optional[int]=..., value: _Optional[_Union[_expression_pb2.Constant, _Mapping]]=...) -> None:
            ...
    BOUNDS_FIELD_NUMBER: _ClassVar[int]
    bounds: _containers.MessageMap[int, _expression_pb2.Constant]

    def __init__(self, bounds: _Optional[_Mapping[int, _expression_pb2.Constant]]=...) -> None:
        ...

class DeltaUpdatedInfo(_message.Message):
    __slots__ = ('updated_columns',)
    UPDATED_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    updated_columns: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, updated_columns: _Optional[_Iterable[int]]=...) -> None:
        ...

class StatsData(_message.Message):
    __slots__ = ('snapshot_id', 'size_in_bytes', 'record_count', 'estimated_record_count', 'delta_row_count_change', 'updated_info', 'fields_stats', 'sort_key_lower_bounds', 'sort_key_upper_bounds')
    SNAPSHOT_ID_FIELD_NUMBER: _ClassVar[int]
    SIZE_IN_BYTES_FIELD_NUMBER: _ClassVar[int]
    RECORD_COUNT_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_RECORD_COUNT_FIELD_NUMBER: _ClassVar[int]
    DELTA_ROW_COUNT_CHANGE_FIELD_NUMBER: _ClassVar[int]
    UPDATED_INFO_FIELD_NUMBER: _ClassVar[int]
    FIELDS_STATS_FIELD_NUMBER: _ClassVar[int]
    SORT_KEY_LOWER_BOUNDS_FIELD_NUMBER: _ClassVar[int]
    SORT_KEY_UPPER_BOUNDS_FIELD_NUMBER: _ClassVar[int]
    snapshot_id: int
    size_in_bytes: int
    record_count: int
    estimated_record_count: int
    delta_row_count_change: int
    updated_info: DeltaUpdatedInfo
    fields_stats: FieldsStats
    sort_key_lower_bounds: FieldBounds
    sort_key_upper_bounds: FieldBounds

    def __init__(self, snapshot_id: _Optional[int]=..., size_in_bytes: _Optional[int]=..., record_count: _Optional[int]=..., estimated_record_count: _Optional[int]=..., delta_row_count_change: _Optional[int]=..., updated_info: _Optional[_Union[DeltaUpdatedInfo, _Mapping]]=..., fields_stats: _Optional[_Union[FieldsStats, _Mapping]]=..., sort_key_lower_bounds: _Optional[_Union[FieldBounds, _Mapping]]=..., sort_key_upper_bounds: _Optional[_Union[FieldBounds, _Mapping]]=...) -> None:
        ...

class FieldsStats(_message.Message):
    __slots__ = ('field_stats',)
    FIELD_STATS_FIELD_NUMBER: _ClassVar[int]
    field_stats: _containers.RepeatedCompositeFieldContainer[FieldStats]

    def __init__(self, field_stats: _Optional[_Iterable[_Union[FieldStats, _Mapping]]]=...) -> None:
        ...

class FieldStats(_message.Message):
    __slots__ = ('field_id', 'stats_value')
    FIELD_ID_FIELD_NUMBER: _ClassVar[int]
    STATS_VALUE_FIELD_NUMBER: _ClassVar[int]
    field_id: _containers.RepeatedScalarFieldContainer[int]
    stats_value: _containers.RepeatedCompositeFieldContainer[FieldStatsValue]

    def __init__(self, field_id: _Optional[_Iterable[int]]=..., stats_value: _Optional[_Iterable[_Union[FieldStatsValue, _Mapping]]]=...) -> None:
        ...

class FieldStatsValue(_message.Message):
    __slots__ = ('nan_count', 'value_count', 'null_count', 'lower_bounds', 'upper_bounds', 'avg_size', 'max_size', 'compressed_size', 'distinct_number', 'top_k', 'histogram', 'raw_size_in_bytes')
    NAN_COUNT_FIELD_NUMBER: _ClassVar[int]
    VALUE_COUNT_FIELD_NUMBER: _ClassVar[int]
    NULL_COUNT_FIELD_NUMBER: _ClassVar[int]
    LOWER_BOUNDS_FIELD_NUMBER: _ClassVar[int]
    UPPER_BOUNDS_FIELD_NUMBER: _ClassVar[int]
    AVG_SIZE_FIELD_NUMBER: _ClassVar[int]
    MAX_SIZE_FIELD_NUMBER: _ClassVar[int]
    COMPRESSED_SIZE_FIELD_NUMBER: _ClassVar[int]
    DISTINCT_NUMBER_FIELD_NUMBER: _ClassVar[int]
    TOP_K_FIELD_NUMBER: _ClassVar[int]
    HISTOGRAM_FIELD_NUMBER: _ClassVar[int]
    RAW_SIZE_IN_BYTES_FIELD_NUMBER: _ClassVar[int]
    nan_count: int
    value_count: int
    null_count: int
    lower_bounds: _expression_pb2.Constant
    upper_bounds: _expression_pb2.Constant
    avg_size: float
    max_size: int
    compressed_size: int
    distinct_number: int
    top_k: TopK
    histogram: Histogram
    raw_size_in_bytes: int

    def __init__(self, nan_count: _Optional[int]=..., value_count: _Optional[int]=..., null_count: _Optional[int]=..., lower_bounds: _Optional[_Union[_expression_pb2.Constant, _Mapping]]=..., upper_bounds: _Optional[_Union[_expression_pb2.Constant, _Mapping]]=..., avg_size: _Optional[float]=..., max_size: _Optional[int]=..., compressed_size: _Optional[int]=..., distinct_number: _Optional[int]=..., top_k: _Optional[_Union[TopK, _Mapping]]=..., histogram: _Optional[_Union[Histogram, _Mapping]]=..., raw_size_in_bytes: _Optional[int]=...) -> None:
        ...

class TopK(_message.Message):
    __slots__ = ('top_k',)
    TOP_K_FIELD_NUMBER: _ClassVar[int]
    top_k: _containers.RepeatedCompositeFieldContainer[_expression_pb2.Constant]

    def __init__(self, top_k: _Optional[_Iterable[_Union[_expression_pb2.Constant, _Mapping]]]=...) -> None:
        ...

class HistogramBucket(_message.Message):
    __slots__ = ('lower_bound', 'upper_bound', 'value_count')
    LOWER_BOUND_FIELD_NUMBER: _ClassVar[int]
    UPPER_BOUND_FIELD_NUMBER: _ClassVar[int]
    VALUE_COUNT_FIELD_NUMBER: _ClassVar[int]
    lower_bound: _expression_pb2.Constant
    upper_bound: _expression_pb2.Constant
    value_count: int

    def __init__(self, lower_bound: _Optional[_Union[_expression_pb2.Constant, _Mapping]]=..., upper_bound: _Optional[_Union[_expression_pb2.Constant, _Mapping]]=..., value_count: _Optional[int]=...) -> None:
        ...

class Histogram(_message.Message):
    __slots__ = ('buckets',)
    BUCKETS_FIELD_NUMBER: _ClassVar[int]
    buckets: _containers.RepeatedCompositeFieldContainer[HistogramBucket]

    def __init__(self, buckets: _Optional[_Iterable[_Union[HistogramBucket, _Mapping]]]=...) -> None:
        ...

class ValuePoint(_message.Message):
    __slots__ = ('values',)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedCompositeFieldContainer[_expression_pb2.Constant]

    def __init__(self, values: _Optional[_Iterable[_Union[_expression_pb2.Constant, _Mapping]]]=...) -> None:
        ...

class BoundaryPoint(_message.Message):
    __slots__ = ('included', 'unbounded', 'value_point')
    INCLUDED_FIELD_NUMBER: _ClassVar[int]
    UNBOUNDED_FIELD_NUMBER: _ClassVar[int]
    VALUE_POINT_FIELD_NUMBER: _ClassVar[int]
    included: bool
    unbounded: bool
    value_point: ValuePoint

    def __init__(self, included: bool=..., unbounded: bool=..., value_point: _Optional[_Union[ValuePoint, _Mapping]]=...) -> None:
        ...

class Boundary(_message.Message):
    __slots__ = ('lower', 'upper')
    LOWER_FIELD_NUMBER: _ClassVar[int]
    UPPER_FIELD_NUMBER: _ClassVar[int]
    lower: BoundaryPoint
    upper: BoundaryPoint

    def __init__(self, lower: _Optional[_Union[BoundaryPoint, _Mapping]]=..., upper: _Optional[_Union[BoundaryPoint, _Mapping]]=...) -> None:
        ...

class RangeBoundary(_message.Message):
    __slots__ = ('id', 'types', 'ranges')
    ID_FIELD_NUMBER: _ClassVar[int]
    TYPES_FIELD_NUMBER: _ClassVar[int]
    RANGES_FIELD_NUMBER: _ClassVar[int]
    id: int
    types: _containers.RepeatedCompositeFieldContainer[_data_type_pb2.DataType]
    ranges: _containers.RepeatedCompositeFieldContainer[Boundary]

    def __init__(self, id: _Optional[int]=..., types: _Optional[_Iterable[_Union[_data_type_pb2.DataType, _Mapping]]]=..., ranges: _Optional[_Iterable[_Union[Boundary, _Mapping]]]=...) -> None:
        ...

class EnforceBoundary(_message.Message):
    __slots__ = ('table_name', 'boundaries')
    TABLE_NAME_FIELD_NUMBER: _ClassVar[int]
    BOUNDARIES_FIELD_NUMBER: _ClassVar[int]
    table_name: str
    boundaries: RangeBoundary

    def __init__(self, table_name: _Optional[str]=..., boundaries: _Optional[_Union[RangeBoundary, _Mapping]]=...) -> None:
        ...

class TableBoundary(_message.Message):
    __slots__ = ('table_boundaries',)
    TABLE_BOUNDARIES_FIELD_NUMBER: _ClassVar[int]
    table_boundaries: _containers.RepeatedCompositeFieldContainer[EnforceBoundary]

    def __init__(self, table_boundaries: _Optional[_Iterable[_Union[EnforceBoundary, _Mapping]]]=...) -> None:
        ...

class FieldRange(_message.Message):
    __slots__ = ('field_id', 'type', 'range')
    FIELD_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    RANGE_FIELD_NUMBER: _ClassVar[int]
    field_id: int
    type: _data_type_pb2.DataType
    range: Boundary

    def __init__(self, field_id: _Optional[int]=..., type: _Optional[_Union[_data_type_pb2.DataType, _Mapping]]=..., range: _Optional[_Union[Boundary, _Mapping]]=...) -> None:
        ...