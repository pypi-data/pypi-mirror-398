import data_type_pb2 as _data_type_pb2
import file_format_type_pb2 as _file_format_type_pb2
import file_system_pb2 as _file_system_pb2
import object_identifier_pb2 as _object_identifier_pb2
import storage_location_pb2 as _storage_location_pb2
import connection_meta_pb2 as _connection_meta_pb2
import expression_pb2 as _expression_pb2
import property_pb2 as _property_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class Order(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ASC: _ClassVar[Order]
    DESC: _ClassVar[Order]

class NullOrder(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LOW: _ClassVar[NullOrder]
    FIRST: _ClassVar[NullOrder]
    LAST: _ClassVar[NullOrder]

class ClusterType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NORMAL: _ClassVar[ClusterType]
    RANGE: _ClassVar[ClusterType]
    HASH: _ClassVar[ClusterType]

class HashBucketType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    HASH_MOD: _ClassVar[HashBucketType]
    HASH_RANGE: _ClassVar[HashBucketType]

class TableType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MANAGED_TABLE: _ClassVar[TableType]
    EXTERNAL_TABLE: _ClassVar[TableType]
    VIRTUAL_VIEW: _ClassVar[TableType]
    MATERIALIZED_VIEW: _ClassVar[TableType]
    STREAM: _ClassVar[TableType]
    UNKNOWN_TABLE: _ClassVar[TableType]

class IndexType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BLOOM_FILTER: _ClassVar[IndexType]
    BITSET: _ClassVar[IndexType]

class RangeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    FIXED_POINT: _ClassVar[RangeType]
    FIXED_RANGE: _ClassVar[RangeType]
    DYNAMIC_RANGE: _ClassVar[RangeType]
ASC: Order
DESC: Order
LOW: NullOrder
FIRST: NullOrder
LAST: NullOrder
NORMAL: ClusterType
RANGE: ClusterType
HASH: ClusterType
HASH_MOD: HashBucketType
HASH_RANGE: HashBucketType
MANAGED_TABLE: TableType
EXTERNAL_TABLE: TableType
VIRTUAL_VIEW: TableType
MATERIALIZED_VIEW: TableType
STREAM: TableType
UNKNOWN_TABLE: TableType
BLOOM_FILTER: IndexType
BITSET: IndexType
FIXED_POINT: RangeType
FIXED_RANGE: RangeType
DYNAMIC_RANGE: RangeType

class FieldRef(_message.Message):
    __slots__ = ('field_id', 'field_name')
    FIELD_ID_FIELD_NUMBER: _ClassVar[int]
    FIELD_NAME_FIELD_NUMBER: _ClassVar[int]
    field_id: int
    field_name: str

    def __init__(self, field_id: _Optional[int]=..., field_name: _Optional[str]=...) -> None:
        ...

class SortedField(_message.Message):
    __slots__ = ('field', 'sort_order')
    FIELD_FIELD_NUMBER: _ClassVar[int]
    SORT_ORDER_FIELD_NUMBER: _ClassVar[int]
    field: FieldRef
    sort_order: Order

    def __init__(self, field: _Optional[_Union[FieldRef, _Mapping]]=..., sort_order: _Optional[_Union[Order, str]]=...) -> None:
        ...

class HashCluster(_message.Message):
    __slots__ = ('function_version', 'bucket_type')
    FUNCTION_VERSION_FIELD_NUMBER: _ClassVar[int]
    BUCKET_TYPE_FIELD_NUMBER: _ClassVar[int]
    function_version: int
    bucket_type: HashBucketType

    def __init__(self, function_version: _Optional[int]=..., bucket_type: _Optional[_Union[HashBucketType, str]]=...) -> None:
        ...

class RangeCluster(_message.Message):
    __slots__ = ('range_type',)
    RANGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    range_type: RangeType

    def __init__(self, range_type: _Optional[_Union[RangeType, str]]=...) -> None:
        ...

class ClusterInfo(_message.Message):
    __slots__ = ('cluster_type', 'clustered_fields', 'buckets_count', 'path_pattern', 'hash', 'range')
    CLUSTER_TYPE_FIELD_NUMBER: _ClassVar[int]
    CLUSTERED_FIELDS_FIELD_NUMBER: _ClassVar[int]
    BUCKETS_COUNT_FIELD_NUMBER: _ClassVar[int]
    PATH_PATTERN_FIELD_NUMBER: _ClassVar[int]
    HASH_FIELD_NUMBER: _ClassVar[int]
    RANGE_FIELD_NUMBER: _ClassVar[int]
    cluster_type: ClusterType
    clustered_fields: _containers.RepeatedCompositeFieldContainer[FieldRef]
    buckets_count: int
    path_pattern: str
    hash: HashCluster
    range: RangeCluster

    def __init__(self, cluster_type: _Optional[_Union[ClusterType, str]]=..., clustered_fields: _Optional[_Iterable[_Union[FieldRef, _Mapping]]]=..., buckets_count: _Optional[int]=..., path_pattern: _Optional[str]=..., hash: _Optional[_Union[HashCluster, _Mapping]]=..., range: _Optional[_Union[RangeCluster, _Mapping]]=...) -> None:
        ...

class SortOrder(_message.Message):
    __slots__ = ('sorted_fields',)
    SORTED_FIELDS_FIELD_NUMBER: _ClassVar[int]
    sorted_fields: _containers.RepeatedCompositeFieldContainer[SortedField]

    def __init__(self, sorted_fields: _Optional[_Iterable[_Union[SortedField, _Mapping]]]=...) -> None:
        ...

class UniqueKey(_message.Message):
    __slots__ = ('unique_fields', 'enable', 'validate', 'rely')
    UNIQUE_FIELDS_FIELD_NUMBER: _ClassVar[int]
    ENABLE_FIELD_NUMBER: _ClassVar[int]
    VALIDATE_FIELD_NUMBER: _ClassVar[int]
    RELY_FIELD_NUMBER: _ClassVar[int]
    unique_fields: _containers.RepeatedCompositeFieldContainer[FieldRef]
    enable: bool
    validate: bool
    rely: bool

    def __init__(self, unique_fields: _Optional[_Iterable[_Union[FieldRef, _Mapping]]]=..., enable: bool=..., validate: bool=..., rely: bool=...) -> None:
        ...

class PrimaryKey(_message.Message):
    __slots__ = ('fields', 'enable', 'validate', 'rely')
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    ENABLE_FIELD_NUMBER: _ClassVar[int]
    VALIDATE_FIELD_NUMBER: _ClassVar[int]
    RELY_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[FieldRef]
    enable: bool
    validate: bool
    rely: bool

    def __init__(self, fields: _Optional[_Iterable[_Union[FieldRef, _Mapping]]]=..., enable: bool=..., validate: bool=..., rely: bool=...) -> None:
        ...

class ForeignKey(_message.Message):
    __slots__ = ('fields', 'ref_table', 'ref_fields', 'enable', 'validate', 'rely')
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    REF_TABLE_FIELD_NUMBER: _ClassVar[int]
    REF_FIELDS_FIELD_NUMBER: _ClassVar[int]
    ENABLE_FIELD_NUMBER: _ClassVar[int]
    VALIDATE_FIELD_NUMBER: _ClassVar[int]
    RELY_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[FieldRef]
    ref_table: _object_identifier_pb2.ObjectIdentifier
    ref_fields: _containers.RepeatedCompositeFieldContainer[FieldRef]
    enable: bool
    validate: bool
    rely: bool

    def __init__(self, fields: _Optional[_Iterable[_Union[FieldRef, _Mapping]]]=..., ref_table: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., ref_fields: _Optional[_Iterable[_Union[FieldRef, _Mapping]]]=..., enable: bool=..., validate: bool=..., rely: bool=...) -> None:
        ...

class IndexKey(_message.Message):
    __slots__ = ('fields',)
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[FieldRef]

    def __init__(self, fields: _Optional[_Iterable[_Union[FieldRef, _Mapping]]]=...) -> None:
        ...

class Index(_message.Message):
    __slots__ = ('type', 'key', 'table')
    TYPE_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    type: IndexType
    key: IndexKey
    table: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, type: _Optional[_Union[IndexType, str]]=..., key: _Optional[_Union[IndexKey, _Mapping]]=..., table: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class FieldSpec(_message.Message):
    __slots__ = ('spec_id', 'cluster_info', 'sort_order', 'unique_key', 'primary_key', 'index', 'foreign_key')
    SPEC_ID_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_INFO_FIELD_NUMBER: _ClassVar[int]
    SORT_ORDER_FIELD_NUMBER: _ClassVar[int]
    UNIQUE_KEY_FIELD_NUMBER: _ClassVar[int]
    PRIMARY_KEY_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    FOREIGN_KEY_FIELD_NUMBER: _ClassVar[int]
    spec_id: int
    cluster_info: ClusterInfo
    sort_order: SortOrder
    unique_key: UniqueKey
    primary_key: PrimaryKey
    index: Index
    foreign_key: ForeignKey

    def __init__(self, spec_id: _Optional[int]=..., cluster_info: _Optional[_Union[ClusterInfo, _Mapping]]=..., sort_order: _Optional[_Union[SortOrder, _Mapping]]=..., unique_key: _Optional[_Union[UniqueKey, _Mapping]]=..., primary_key: _Optional[_Union[PrimaryKey, _Mapping]]=..., index: _Optional[_Union[Index, _Mapping]]=..., foreign_key: _Optional[_Union[ForeignKey, _Mapping]]=...) -> None:
        ...

class FieldSchema(_message.Message):
    __slots__ = ('name', 'type', 'virtual', 'hidden', 'un_output', 'comment', 'expr', 'transform')
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    VIRTUAL_FIELD_NUMBER: _ClassVar[int]
    HIDDEN_FIELD_NUMBER: _ClassVar[int]
    UN_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    EXPR_FIELD_NUMBER: _ClassVar[int]
    TRANSFORM_FIELD_NUMBER: _ClassVar[int]
    name: str
    type: _data_type_pb2.DataType
    virtual: bool
    hidden: bool
    un_output: bool
    comment: str
    expr: _expression_pb2.ScalarExpression
    transform: str

    def __init__(self, name: _Optional[str]=..., type: _Optional[_Union[_data_type_pb2.DataType, _Mapping]]=..., virtual: bool=..., hidden: bool=..., un_output: bool=..., comment: _Optional[str]=..., expr: _Optional[_Union[_expression_pb2.ScalarExpression, _Mapping]]=..., transform: _Optional[str]=...) -> None:
        ...

class TableSchema(_message.Message):
    __slots__ = ('fields', 'schema_id', 'type')
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[FieldSchema]
    schema_id: int
    type: str

    def __init__(self, fields: _Optional[_Iterable[_Union[FieldSchema, _Mapping]]]=..., schema_id: _Optional[int]=..., type: _Optional[str]=...) -> None:
        ...

class TextFileFormat(_message.Message):
    __slots__ = ('options',)

    class OptionsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    options: _containers.ScalarMap[str, str]

    def __init__(self, options: _Optional[_Mapping[str, str]]=...) -> None:
        ...

class ParquetFileFormat(_message.Message):
    __slots__ = ('row_group_size_bytes', 'page_size_bytes', 'dict_size_bytes')
    ROW_GROUP_SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    DICT_SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    row_group_size_bytes: int
    page_size_bytes: int
    dict_size_bytes: int

    def __init__(self, row_group_size_bytes: _Optional[int]=..., page_size_bytes: _Optional[int]=..., dict_size_bytes: _Optional[int]=...) -> None:
        ...

class OrcFileFormat(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class CsvFileFormat(_message.Message):
    __slots__ = ('options',)

    class OptionsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    options: _containers.ScalarMap[str, str]

    def __init__(self, options: _Optional[_Mapping[str, str]]=...) -> None:
        ...

class HiveResultFileFormat(_message.Message):
    __slots__ = ('options',)

    class OptionsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    options: _containers.ScalarMap[str, str]

    def __init__(self, options: _Optional[_Mapping[str, str]]=...) -> None:
        ...

class AvroFileFormat(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class ArrowFileFormat(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class FileFormat(_message.Message):
    __slots__ = ('type', 'textFile', 'parquet_file', 'orc_file', 'csv_file', 'hive_result_file', 'avro_file', 'arrow_file')
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TEXTFILE_FIELD_NUMBER: _ClassVar[int]
    PARQUET_FILE_FIELD_NUMBER: _ClassVar[int]
    ORC_FILE_FIELD_NUMBER: _ClassVar[int]
    CSV_FILE_FIELD_NUMBER: _ClassVar[int]
    HIVE_RESULT_FILE_FIELD_NUMBER: _ClassVar[int]
    AVRO_FILE_FIELD_NUMBER: _ClassVar[int]
    ARROW_FILE_FIELD_NUMBER: _ClassVar[int]
    type: _file_format_type_pb2.FileFormatType
    textFile: TextFileFormat
    parquet_file: ParquetFileFormat
    orc_file: OrcFileFormat
    csv_file: CsvFileFormat
    hive_result_file: HiveResultFileFormat
    avro_file: AvroFileFormat
    arrow_file: ArrowFileFormat

    def __init__(self, type: _Optional[_Union[_file_format_type_pb2.FileFormatType, str]]=..., textFile: _Optional[_Union[TextFileFormat, _Mapping]]=..., parquet_file: _Optional[_Union[ParquetFileFormat, _Mapping]]=..., orc_file: _Optional[_Union[OrcFileFormat, _Mapping]]=..., csv_file: _Optional[_Union[CsvFileFormat, _Mapping]]=..., hive_result_file: _Optional[_Union[HiveResultFileFormat, _Mapping]]=..., avro_file: _Optional[_Union[AvroFileFormat, _Mapping]]=..., arrow_file: _Optional[_Union[ArrowFileFormat, _Mapping]]=...) -> None:
        ...

class FileDataSourceInfo(_message.Message):
    __slots__ = ('fileSystemType', 'path', 'format')
    FILESYSTEMTYPE_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    fileSystemType: _file_system_pb2.FileSystemType
    path: str
    format: FileFormat

    def __init__(self, fileSystemType: _Optional[_Union[_file_system_pb2.FileSystemType, str]]=..., path: _Optional[str]=..., format: _Optional[_Union[FileFormat, _Mapping]]=...) -> None:
        ...

class DqlDataSourceInfo(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class LocationDirectoryDataSourceInfo(_message.Message):
    __slots__ = ('storage_location', 'connection_info', 'properties')
    STORAGE_LOCATION_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_INFO_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    storage_location: _storage_location_pb2.StorageLocation
    connection_info: _connection_meta_pb2.FileSystemConnectionInfo
    properties: _containers.RepeatedCompositeFieldContainer[_property_pb2.Property]

    def __init__(self, storage_location: _Optional[_Union[_storage_location_pb2.StorageLocation, _Mapping]]=..., connection_info: _Optional[_Union[_connection_meta_pb2.FileSystemConnectionInfo, _Mapping]]=..., properties: _Optional[_Iterable[_Union[_property_pb2.Property, _Mapping]]]=...) -> None:
        ...

class DataProperties(_message.Message):
    __slots__ = ('cluster_info_spec', 'sort_order_spec')
    CLUSTER_INFO_SPEC_FIELD_NUMBER: _ClassVar[int]
    SORT_ORDER_SPEC_FIELD_NUMBER: _ClassVar[int]
    cluster_info_spec: _containers.RepeatedCompositeFieldContainer[FieldSpec]
    sort_order_spec: FieldSpec

    def __init__(self, cluster_info_spec: _Optional[_Iterable[_Union[FieldSpec, _Mapping]]]=..., sort_order_spec: _Optional[_Union[FieldSpec, _Mapping]]=...) -> None:
        ...

class DataSourceInfo(_message.Message):
    __slots__ = ('data_source_type', 'file', 'dql', 'location_directory', 'options', 'location', 'data_source_id', 'data_props')

    class OptionsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    DATA_SOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    FILE_FIELD_NUMBER: _ClassVar[int]
    DQL_FIELD_NUMBER: _ClassVar[int]
    LOCATION_DIRECTORY_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    DATA_SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    DATA_PROPS_FIELD_NUMBER: _ClassVar[int]
    data_source_type: int
    file: FileDataSourceInfo
    dql: DqlDataSourceInfo
    location_directory: LocationDirectoryDataSourceInfo
    options: _containers.ScalarMap[str, str]
    location: str
    data_source_id: int
    data_props: DataProperties

    def __init__(self, data_source_type: _Optional[int]=..., file: _Optional[_Union[FileDataSourceInfo, _Mapping]]=..., dql: _Optional[_Union[DqlDataSourceInfo, _Mapping]]=..., location_directory: _Optional[_Union[LocationDirectoryDataSourceInfo, _Mapping]]=..., options: _Optional[_Mapping[str, str]]=..., location: _Optional[str]=..., data_source_id: _Optional[int]=..., data_props: _Optional[_Union[DataProperties, _Mapping]]=...) -> None:
        ...

class DataSource(_message.Message):
    __slots__ = ('data_source_infos', 'default_data_source_id', 'next_data_source_id')
    DATA_SOURCE_INFOS_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_DATA_SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    NEXT_DATA_SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    data_source_infos: _containers.RepeatedCompositeFieldContainer[DataSourceInfo]
    default_data_source_id: int
    next_data_source_id: int

    def __init__(self, data_source_infos: _Optional[_Iterable[_Union[DataSourceInfo, _Mapping]]]=..., default_data_source_id: _Optional[int]=..., next_data_source_id: _Optional[int]=...) -> None:
        ...

class MVSource(_message.Message):
    __slots__ = ('table_identifier', 'snapshot')
    TABLE_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOT_FIELD_NUMBER: _ClassVar[int]
    table_identifier: _object_identifier_pb2.ObjectIdentifier
    snapshot: int

    def __init__(self, table_identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., snapshot: _Optional[int]=...) -> None:
        ...

class RefreshOption(_message.Message):
    __slots__ = ('type', 'start_time', 'interval_in_minute')

    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ON_DEMAND: _ClassVar[RefreshOption.Type]
        ON_COMMIT: _ClassVar[RefreshOption.Type]
        ON_SCHEDULE: _ClassVar[RefreshOption.Type]
    ON_DEMAND: RefreshOption.Type
    ON_COMMIT: RefreshOption.Type
    ON_SCHEDULE: RefreshOption.Type
    TYPE_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_IN_MINUTE_FIELD_NUMBER: _ClassVar[int]
    type: RefreshOption.Type
    start_time: int
    interval_in_minute: int

    def __init__(self, type: _Optional[_Union[RefreshOption.Type, str]]=..., start_time: _Optional[int]=..., interval_in_minute: _Optional[int]=...) -> None:
        ...

class IncrementalExtension(_message.Message):
    __slots__ = ('isValueSemantics', 'formatVersion')
    ISVALUESEMANTICS_FIELD_NUMBER: _ClassVar[int]
    FORMATVERSION_FIELD_NUMBER: _ClassVar[int]
    isValueSemantics: bool
    formatVersion: int

    def __init__(self, isValueSemantics: bool=..., formatVersion: _Optional[int]=...) -> None:
        ...

class MVExtension(_message.Message):
    __slots__ = ('mv_plan', 'mv_source_tables', 'refresh_option', 'mv_snapshot_id', 'incremental_extension')
    MV_PLAN_FIELD_NUMBER: _ClassVar[int]
    MV_SOURCE_TABLES_FIELD_NUMBER: _ClassVar[int]
    REFRESH_OPTION_FIELD_NUMBER: _ClassVar[int]
    MV_SNAPSHOT_ID_FIELD_NUMBER: _ClassVar[int]
    INCREMENTAL_EXTENSION_FIELD_NUMBER: _ClassVar[int]
    mv_plan: str
    mv_source_tables: _containers.RepeatedCompositeFieldContainer[MVSource]
    refresh_option: RefreshOption
    mv_snapshot_id: int
    incremental_extension: IncrementalExtension

    def __init__(self, mv_plan: _Optional[str]=..., mv_source_tables: _Optional[_Iterable[_Union[MVSource, _Mapping]]]=..., refresh_option: _Optional[_Union[RefreshOption, _Mapping]]=..., mv_snapshot_id: _Optional[int]=..., incremental_extension: _Optional[_Union[IncrementalExtension, _Mapping]]=...) -> None:
        ...

class View(_message.Message):
    __slots__ = ('view_expanded_text', 'view_original_text', 'mv_extension')
    VIEW_EXPANDED_TEXT_FIELD_NUMBER: _ClassVar[int]
    VIEW_ORIGINAL_TEXT_FIELD_NUMBER: _ClassVar[int]
    MV_EXTENSION_FIELD_NUMBER: _ClassVar[int]
    view_expanded_text: str
    view_original_text: str
    mv_extension: MVExtension

    def __init__(self, view_expanded_text: _Optional[str]=..., view_original_text: _Optional[str]=..., mv_extension: _Optional[_Union[MVExtension, _Mapping]]=...) -> None:
        ...

class TableStream(_message.Message):
    __slots__ = ('provider', 'at_timestamp', 'offset')
    PROVIDER_FIELD_NUMBER: _ClassVar[int]
    AT_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    provider: _object_identifier_pb2.ObjectIdentifier
    at_timestamp: int
    offset: int

    def __init__(self, provider: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., at_timestamp: _Optional[int]=..., offset: _Optional[int]=...) -> None:
        ...

class TableStreamState(_message.Message):
    __slots__ = ('stream', 'from_snapshot', 'to_snapshot')
    STREAM_FIELD_NUMBER: _ClassVar[int]
    FROM_SNAPSHOT_FIELD_NUMBER: _ClassVar[int]
    TO_SNAPSHOT_FIELD_NUMBER: _ClassVar[int]
    stream: _object_identifier_pb2.ObjectIdentifier
    from_snapshot: int
    to_snapshot: int

    def __init__(self, stream: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., from_snapshot: _Optional[int]=..., to_snapshot: _Optional[int]=...) -> None:
        ...