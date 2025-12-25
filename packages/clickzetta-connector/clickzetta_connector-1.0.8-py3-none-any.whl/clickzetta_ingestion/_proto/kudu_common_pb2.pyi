import row_operations_pb2 as _row_operations_pb2
import block_bloom_filter_pb2 as _block_bloom_filter_pb2
import compression_pb2 as _compression_pb2
import hash_pb2 as _hash_pb2
import pb_util_pb2 as _pb_util_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class DataType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN_DATA: _ClassVar[DataType]
    UINT8: _ClassVar[DataType]
    INT8: _ClassVar[DataType]
    UINT16: _ClassVar[DataType]
    INT16: _ClassVar[DataType]
    UINT32: _ClassVar[DataType]
    INT32: _ClassVar[DataType]
    UINT64: _ClassVar[DataType]
    INT64: _ClassVar[DataType]
    STRING: _ClassVar[DataType]
    BOOL: _ClassVar[DataType]
    FLOAT: _ClassVar[DataType]
    DOUBLE: _ClassVar[DataType]
    BINARY: _ClassVar[DataType]
    UNIXTIME_MICROS: _ClassVar[DataType]
    INT128: _ClassVar[DataType]
    DECIMAL32: _ClassVar[DataType]
    DECIMAL64: _ClassVar[DataType]
    DECIMAL128: _ClassVar[DataType]
    IS_DELETED: _ClassVar[DataType]
    VARCHAR: _ClassVar[DataType]
    DATE: _ClassVar[DataType]

class EncodingType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN_ENCODING: _ClassVar[EncodingType]
    AUTO_ENCODING: _ClassVar[EncodingType]
    PLAIN_ENCODING: _ClassVar[EncodingType]
    PREFIX_ENCODING: _ClassVar[EncodingType]
    GROUP_VARINT: _ClassVar[EncodingType]
    RLE: _ClassVar[EncodingType]
    DICT_ENCODING: _ClassVar[EncodingType]
    BIT_SHUFFLE: _ClassVar[EncodingType]

class HmsMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NONE: _ClassVar[HmsMode]
    DISABLE_HIVE_METASTORE: _ClassVar[HmsMode]
    ENABLE_HIVE_METASTORE: _ClassVar[HmsMode]
    ENABLE_METASTORE_INTEGRATION: _ClassVar[HmsMode]

class ExternalConsistencyMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN_EXTERNAL_CONSISTENCY_MODE: _ClassVar[ExternalConsistencyMode]
    CLIENT_PROPAGATED: _ClassVar[ExternalConsistencyMode]
    COMMIT_WAIT: _ClassVar[ExternalConsistencyMode]

class ReadMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN_READ_MODE: _ClassVar[ReadMode]
    READ_LATEST: _ClassVar[ReadMode]
    READ_AT_SNAPSHOT: _ClassVar[ReadMode]
    READ_YOUR_WRITES: _ClassVar[ReadMode]

class OrderMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN_ORDER_MODE: _ClassVar[OrderMode]
    UNORDERED: _ClassVar[OrderMode]
    ORDERED: _ClassVar[OrderMode]

class ReplicaSelection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN_REPLICA_SELECTION: _ClassVar[ReplicaSelection]
    LEADER_ONLY: _ClassVar[ReplicaSelection]
    CLOSEST_REPLICA: _ClassVar[ReplicaSelection]

class TableTypePB(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEFAULT_TABLE: _ClassVar[TableTypePB]
    TXN_STATUS_TABLE: _ClassVar[TableTypePB]
UNKNOWN_DATA: DataType
UINT8: DataType
INT8: DataType
UINT16: DataType
INT16: DataType
UINT32: DataType
INT32: DataType
UINT64: DataType
INT64: DataType
STRING: DataType
BOOL: DataType
FLOAT: DataType
DOUBLE: DataType
BINARY: DataType
UNIXTIME_MICROS: DataType
INT128: DataType
DECIMAL32: DataType
DECIMAL64: DataType
DECIMAL128: DataType
IS_DELETED: DataType
VARCHAR: DataType
DATE: DataType
UNKNOWN_ENCODING: EncodingType
AUTO_ENCODING: EncodingType
PLAIN_ENCODING: EncodingType
PREFIX_ENCODING: EncodingType
GROUP_VARINT: EncodingType
RLE: EncodingType
DICT_ENCODING: EncodingType
BIT_SHUFFLE: EncodingType
NONE: HmsMode
DISABLE_HIVE_METASTORE: HmsMode
ENABLE_HIVE_METASTORE: HmsMode
ENABLE_METASTORE_INTEGRATION: HmsMode
UNKNOWN_EXTERNAL_CONSISTENCY_MODE: ExternalConsistencyMode
CLIENT_PROPAGATED: ExternalConsistencyMode
COMMIT_WAIT: ExternalConsistencyMode
UNKNOWN_READ_MODE: ReadMode
READ_LATEST: ReadMode
READ_AT_SNAPSHOT: ReadMode
READ_YOUR_WRITES: ReadMode
UNKNOWN_ORDER_MODE: OrderMode
UNORDERED: OrderMode
ORDERED: OrderMode
UNKNOWN_REPLICA_SELECTION: ReplicaSelection
LEADER_ONLY: ReplicaSelection
CLOSEST_REPLICA: ReplicaSelection
DEFAULT_TABLE: TableTypePB
TXN_STATUS_TABLE: TableTypePB

class ColumnTypeAttributesPB(_message.Message):
    __slots__ = ('precision', 'scale', 'length', 'specialColCode')
    PRECISION_FIELD_NUMBER: _ClassVar[int]
    SCALE_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    SPECIALCOLCODE_FIELD_NUMBER: _ClassVar[int]
    precision: int
    scale: int
    length: int
    specialColCode: int

    def __init__(self, precision: _Optional[int]=..., scale: _Optional[int]=..., length: _Optional[int]=..., specialColCode: _Optional[int]=...) -> None:
        ...

class ColumnSchemaPB(_message.Message):
    __slots__ = ('id', 'name', 'type', 'is_key', 'is_nullable', 'read_default_value', 'write_default_value', 'encoding', 'compression', 'cfile_block_size', 'type_attributes', 'comment')
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    IS_KEY_FIELD_NUMBER: _ClassVar[int]
    IS_NULLABLE_FIELD_NUMBER: _ClassVar[int]
    READ_DEFAULT_VALUE_FIELD_NUMBER: _ClassVar[int]
    WRITE_DEFAULT_VALUE_FIELD_NUMBER: _ClassVar[int]
    ENCODING_FIELD_NUMBER: _ClassVar[int]
    COMPRESSION_FIELD_NUMBER: _ClassVar[int]
    CFILE_BLOCK_SIZE_FIELD_NUMBER: _ClassVar[int]
    TYPE_ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    type: DataType
    is_key: bool
    is_nullable: bool
    read_default_value: bytes
    write_default_value: bytes
    encoding: EncodingType
    compression: _compression_pb2.CompressionType
    cfile_block_size: int
    type_attributes: ColumnTypeAttributesPB
    comment: str

    def __init__(self, id: _Optional[int]=..., name: _Optional[str]=..., type: _Optional[_Union[DataType, str]]=..., is_key: bool=..., is_nullable: bool=..., read_default_value: _Optional[bytes]=..., write_default_value: _Optional[bytes]=..., encoding: _Optional[_Union[EncodingType, str]]=..., compression: _Optional[_Union[_compression_pb2.CompressionType, str]]=..., cfile_block_size: _Optional[int]=..., type_attributes: _Optional[_Union[ColumnTypeAttributesPB, _Mapping]]=..., comment: _Optional[str]=...) -> None:
        ...

class ColumnSchemaDeltaPB(_message.Message):
    __slots__ = ('name', 'new_name', 'default_value', 'remove_default', 'encoding', 'compression', 'block_size', 'new_comment')
    NAME_FIELD_NUMBER: _ClassVar[int]
    NEW_NAME_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_VALUE_FIELD_NUMBER: _ClassVar[int]
    REMOVE_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    ENCODING_FIELD_NUMBER: _ClassVar[int]
    COMPRESSION_FIELD_NUMBER: _ClassVar[int]
    BLOCK_SIZE_FIELD_NUMBER: _ClassVar[int]
    NEW_COMMENT_FIELD_NUMBER: _ClassVar[int]
    name: str
    new_name: str
    default_value: bytes
    remove_default: bool
    encoding: EncodingType
    compression: _compression_pb2.CompressionType
    block_size: int
    new_comment: str

    def __init__(self, name: _Optional[str]=..., new_name: _Optional[str]=..., default_value: _Optional[bytes]=..., remove_default: bool=..., encoding: _Optional[_Union[EncodingType, str]]=..., compression: _Optional[_Union[_compression_pb2.CompressionType, str]]=..., block_size: _Optional[int]=..., new_comment: _Optional[str]=...) -> None:
        ...

class SchemaPB(_message.Message):
    __slots__ = ('columns',)
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    columns: _containers.RepeatedCompositeFieldContainer[ColumnSchemaPB]

    def __init__(self, columns: _Optional[_Iterable[_Union[ColumnSchemaPB, _Mapping]]]=...) -> None:
        ...

class HostPortPB(_message.Message):
    __slots__ = ('host', 'port')
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    host: str
    port: int

    def __init__(self, host: _Optional[str]=..., port: _Optional[int]=...) -> None:
        ...

class PartitionSchemaPB(_message.Message):
    __slots__ = ('hash_schema', 'range_schema', 'custom_hash_schema_ranges')

    class ColumnIdentifierPB(_message.Message):
        __slots__ = ('id', 'name')
        ID_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        id: int
        name: str

        def __init__(self, id: _Optional[int]=..., name: _Optional[str]=...) -> None:
            ...

    class RangeSchemaPB(_message.Message):
        __slots__ = ('columns',)
        COLUMNS_FIELD_NUMBER: _ClassVar[int]
        columns: _containers.RepeatedCompositeFieldContainer[PartitionSchemaPB.ColumnIdentifierPB]

        def __init__(self, columns: _Optional[_Iterable[_Union[PartitionSchemaPB.ColumnIdentifierPB, _Mapping]]]=...) -> None:
            ...

    class HashBucketSchemaPB(_message.Message):
        __slots__ = ('columns', 'num_buckets', 'seed', 'hash_algorithm')
        COLUMNS_FIELD_NUMBER: _ClassVar[int]
        NUM_BUCKETS_FIELD_NUMBER: _ClassVar[int]
        SEED_FIELD_NUMBER: _ClassVar[int]
        HASH_ALGORITHM_FIELD_NUMBER: _ClassVar[int]
        columns: _containers.RepeatedCompositeFieldContainer[PartitionSchemaPB.ColumnIdentifierPB]
        num_buckets: int
        seed: int
        hash_algorithm: _hash_pb2.HashAlgorithm

        def __init__(self, columns: _Optional[_Iterable[_Union[PartitionSchemaPB.ColumnIdentifierPB, _Mapping]]]=..., num_buckets: _Optional[int]=..., seed: _Optional[int]=..., hash_algorithm: _Optional[_Union[_hash_pb2.HashAlgorithm, str]]=...) -> None:
            ...

    class RangeWithHashSchemaPB(_message.Message):
        __slots__ = ('range_bounds', 'hash_schema')
        RANGE_BOUNDS_FIELD_NUMBER: _ClassVar[int]
        HASH_SCHEMA_FIELD_NUMBER: _ClassVar[int]
        range_bounds: _row_operations_pb2.RowOperationsPB
        hash_schema: _containers.RepeatedCompositeFieldContainer[PartitionSchemaPB.HashBucketSchemaPB]

        def __init__(self, range_bounds: _Optional[_Union[_row_operations_pb2.RowOperationsPB, _Mapping]]=..., hash_schema: _Optional[_Iterable[_Union[PartitionSchemaPB.HashBucketSchemaPB, _Mapping]]]=...) -> None:
            ...
    HASH_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    RANGE_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_HASH_SCHEMA_RANGES_FIELD_NUMBER: _ClassVar[int]
    hash_schema: _containers.RepeatedCompositeFieldContainer[PartitionSchemaPB.HashBucketSchemaPB]
    range_schema: PartitionSchemaPB.RangeSchemaPB
    custom_hash_schema_ranges: _containers.RepeatedCompositeFieldContainer[PartitionSchemaPB.RangeWithHashSchemaPB]

    def __init__(self, hash_schema: _Optional[_Iterable[_Union[PartitionSchemaPB.HashBucketSchemaPB, _Mapping]]]=..., range_schema: _Optional[_Union[PartitionSchemaPB.RangeSchemaPB, _Mapping]]=..., custom_hash_schema_ranges: _Optional[_Iterable[_Union[PartitionSchemaPB.RangeWithHashSchemaPB, _Mapping]]]=...) -> None:
        ...

class PartitionPB(_message.Message):
    __slots__ = ('hash_buckets', 'partition_key_start', 'partition_key_end')
    HASH_BUCKETS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_KEY_START_FIELD_NUMBER: _ClassVar[int]
    PARTITION_KEY_END_FIELD_NUMBER: _ClassVar[int]
    hash_buckets: _containers.RepeatedScalarFieldContainer[int]
    partition_key_start: bytes
    partition_key_end: bytes

    def __init__(self, hash_buckets: _Optional[_Iterable[int]]=..., partition_key_start: _Optional[bytes]=..., partition_key_end: _Optional[bytes]=...) -> None:
        ...

class ColumnPredicatePB(_message.Message):
    __slots__ = ('column', 'range', 'equality', 'is_not_null', 'in_list', 'is_null', 'in_bloom_filter')

    class Range(_message.Message):
        __slots__ = ('lower', 'upper')
        LOWER_FIELD_NUMBER: _ClassVar[int]
        UPPER_FIELD_NUMBER: _ClassVar[int]
        lower: bytes
        upper: bytes

        def __init__(self, lower: _Optional[bytes]=..., upper: _Optional[bytes]=...) -> None:
            ...

    class Equality(_message.Message):
        __slots__ = ('value',)
        VALUE_FIELD_NUMBER: _ClassVar[int]
        value: bytes

        def __init__(self, value: _Optional[bytes]=...) -> None:
            ...

    class InList(_message.Message):
        __slots__ = ('values',)
        VALUES_FIELD_NUMBER: _ClassVar[int]
        values: _containers.RepeatedScalarFieldContainer[bytes]

        def __init__(self, values: _Optional[_Iterable[bytes]]=...) -> None:
            ...

    class IsNotNull(_message.Message):
        __slots__ = ()

        def __init__(self) -> None:
            ...

    class IsNull(_message.Message):
        __slots__ = ()

        def __init__(self) -> None:
            ...

    class InBloomFilter(_message.Message):
        __slots__ = ('bloom_filters', 'lower', 'upper')
        BLOOM_FILTERS_FIELD_NUMBER: _ClassVar[int]
        LOWER_FIELD_NUMBER: _ClassVar[int]
        UPPER_FIELD_NUMBER: _ClassVar[int]
        bloom_filters: _containers.RepeatedCompositeFieldContainer[_block_bloom_filter_pb2.BlockBloomFilterPB]
        lower: bytes
        upper: bytes

        def __init__(self, bloom_filters: _Optional[_Iterable[_Union[_block_bloom_filter_pb2.BlockBloomFilterPB, _Mapping]]]=..., lower: _Optional[bytes]=..., upper: _Optional[bytes]=...) -> None:
            ...
    COLUMN_FIELD_NUMBER: _ClassVar[int]
    RANGE_FIELD_NUMBER: _ClassVar[int]
    EQUALITY_FIELD_NUMBER: _ClassVar[int]
    IS_NOT_NULL_FIELD_NUMBER: _ClassVar[int]
    IN_LIST_FIELD_NUMBER: _ClassVar[int]
    IS_NULL_FIELD_NUMBER: _ClassVar[int]
    IN_BLOOM_FILTER_FIELD_NUMBER: _ClassVar[int]
    column: str
    range: ColumnPredicatePB.Range
    equality: ColumnPredicatePB.Equality
    is_not_null: ColumnPredicatePB.IsNotNull
    in_list: ColumnPredicatePB.InList
    is_null: ColumnPredicatePB.IsNull
    in_bloom_filter: ColumnPredicatePB.InBloomFilter

    def __init__(self, column: _Optional[str]=..., range: _Optional[_Union[ColumnPredicatePB.Range, _Mapping]]=..., equality: _Optional[_Union[ColumnPredicatePB.Equality, _Mapping]]=..., is_not_null: _Optional[_Union[ColumnPredicatePB.IsNotNull, _Mapping]]=..., in_list: _Optional[_Union[ColumnPredicatePB.InList, _Mapping]]=..., is_null: _Optional[_Union[ColumnPredicatePB.IsNull, _Mapping]]=..., in_bloom_filter: _Optional[_Union[ColumnPredicatePB.InBloomFilter, _Mapping]]=...) -> None:
        ...

class KeyRangePB(_message.Message):
    __slots__ = ('start_primary_key', 'stop_primary_key', 'size_bytes_estimates')
    START_PRIMARY_KEY_FIELD_NUMBER: _ClassVar[int]
    STOP_PRIMARY_KEY_FIELD_NUMBER: _ClassVar[int]
    SIZE_BYTES_ESTIMATES_FIELD_NUMBER: _ClassVar[int]
    start_primary_key: bytes
    stop_primary_key: bytes
    size_bytes_estimates: int

    def __init__(self, start_primary_key: _Optional[bytes]=..., stop_primary_key: _Optional[bytes]=..., size_bytes_estimates: _Optional[int]=...) -> None:
        ...

class TableExtraConfigPB(_message.Message):
    __slots__ = ('history_max_age_sec', 'maintenance_priority', 'disable_compaction')
    HISTORY_MAX_AGE_SEC_FIELD_NUMBER: _ClassVar[int]
    MAINTENANCE_PRIORITY_FIELD_NUMBER: _ClassVar[int]
    DISABLE_COMPACTION_FIELD_NUMBER: _ClassVar[int]
    history_max_age_sec: int
    maintenance_priority: int
    disable_compaction: bool

    def __init__(self, history_max_age_sec: _Optional[int]=..., maintenance_priority: _Optional[int]=..., disable_compaction: bool=...) -> None:
        ...