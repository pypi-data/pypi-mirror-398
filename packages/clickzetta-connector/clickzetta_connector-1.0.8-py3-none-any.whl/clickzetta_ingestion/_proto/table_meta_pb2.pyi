import table_common_pb2 as _table_common_pb2
import object_identifier_pb2 as _object_identifier_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class TableSchemaList(_message.Message):
    __slots__ = ('schemas', 'highest_field_id')
    SCHEMAS_FIELD_NUMBER: _ClassVar[int]
    HIGHEST_FIELD_ID_FIELD_NUMBER: _ClassVar[int]
    schemas: _containers.RepeatedCompositeFieldContainer[_table_common_pb2.TableSchema]
    highest_field_id: int

    def __init__(self, schemas: _Optional[_Iterable[_Union[_table_common_pb2.TableSchema, _Mapping]]]=..., highest_field_id: _Optional[int]=...) -> None:
        ...

class FieldSpecList(_message.Message):
    __slots__ = ('specs', 'current_spec_id')
    SPECS_FIELD_NUMBER: _ClassVar[int]
    CURRENT_SPEC_ID_FIELD_NUMBER: _ClassVar[int]
    specs: _containers.RepeatedCompositeFieldContainer[_table_common_pb2.FieldSpec]
    current_spec_id: int

    def __init__(self, specs: _Optional[_Iterable[_Union[_table_common_pb2.FieldSpec, _Mapping]]]=..., current_spec_id: _Optional[int]=...) -> None:
        ...

class CompositeFieldSpecList(_message.Message):
    __slots__ = ('spec_list', 'current_spec_id')
    SPEC_LIST_FIELD_NUMBER: _ClassVar[int]
    CURRENT_SPEC_ID_FIELD_NUMBER: _ClassVar[int]
    spec_list: _containers.RepeatedCompositeFieldContainer[FieldSpecList]
    current_spec_id: int

    def __init__(self, spec_list: _Optional[_Iterable[_Union[FieldSpecList, _Mapping]]]=..., current_spec_id: _Optional[int]=...) -> None:
        ...

class DataFileInfo(_message.Message):
    __slots__ = ('file_path', 'file_size_in_bytes')
    FILE_PATH_FIELD_NUMBER: _ClassVar[int]
    FILE_SIZE_IN_BYTES_FIELD_NUMBER: _ClassVar[int]
    file_path: str
    file_size_in_bytes: int

    def __init__(self, file_path: _Optional[str]=..., file_size_in_bytes: _Optional[int]=...) -> None:
        ...

class DataFileSplitSource(_message.Message):
    __slots__ = ('table_identifier', 'data_file_info')
    TABLE_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    DATA_FILE_INFO_FIELD_NUMBER: _ClassVar[int]
    table_identifier: _object_identifier_pb2.ObjectIdentifier
    data_file_info: _containers.RepeatedCompositeFieldContainer[DataFileInfo]

    def __init__(self, table_identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., data_file_info: _Optional[_Iterable[_Union[DataFileInfo, _Mapping]]]=...) -> None:
        ...

class TableFormatInfo(_message.Message):
    __slots__ = ('snapshot_id', 'iceberg')

    class Iceberg(_message.Message):
        __slots__ = ('metadata_location', 'current_version')
        METADATA_LOCATION_FIELD_NUMBER: _ClassVar[int]
        CURRENT_VERSION_FIELD_NUMBER: _ClassVar[int]
        metadata_location: str
        current_version: int

        def __init__(self, metadata_location: _Optional[str]=..., current_version: _Optional[int]=...) -> None:
            ...
    SNAPSHOT_ID_FIELD_NUMBER: _ClassVar[int]
    ICEBERG_FIELD_NUMBER: _ClassVar[int]
    snapshot_id: int
    iceberg: TableFormatInfo.Iceberg

    def __init__(self, snapshot_id: _Optional[int]=..., iceberg: _Optional[_Union[TableFormatInfo.Iceberg, _Mapping]]=...) -> None:
        ...

class TableFormat(_message.Message):
    __slots__ = ('table_format_infos',)
    TABLE_FORMAT_INFOS_FIELD_NUMBER: _ClassVar[int]
    table_format_infos: _containers.RepeatedCompositeFieldContainer[TableFormatInfo]

    def __init__(self, table_format_infos: _Optional[_Iterable[_Union[TableFormatInfo, _Mapping]]]=...) -> None:
        ...

class TableMeta(_message.Message):
    __slots__ = ('table_id', 'table_type', 'table_schema', 'data_source', 'primary_key_spec', 'sort_order_spec', 'cluster_info_spec', 'unique_key_spec', 'index_spec', 'foreign_key_spec', 'view', 'current_snapshot_id', 'table_format', 'stream')
    TABLE_ID_FIELD_NUMBER: _ClassVar[int]
    TABLE_TYPE_FIELD_NUMBER: _ClassVar[int]
    TABLE_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    DATA_SOURCE_FIELD_NUMBER: _ClassVar[int]
    PRIMARY_KEY_SPEC_FIELD_NUMBER: _ClassVar[int]
    SORT_ORDER_SPEC_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_INFO_SPEC_FIELD_NUMBER: _ClassVar[int]
    UNIQUE_KEY_SPEC_FIELD_NUMBER: _ClassVar[int]
    INDEX_SPEC_FIELD_NUMBER: _ClassVar[int]
    FOREIGN_KEY_SPEC_FIELD_NUMBER: _ClassVar[int]
    VIEW_FIELD_NUMBER: _ClassVar[int]
    CURRENT_SNAPSHOT_ID_FIELD_NUMBER: _ClassVar[int]
    TABLE_FORMAT_FIELD_NUMBER: _ClassVar[int]
    STREAM_FIELD_NUMBER: _ClassVar[int]
    table_id: int
    table_type: _table_common_pb2.TableType
    table_schema: _table_common_pb2.TableSchema
    data_source: _table_common_pb2.DataSource
    primary_key_spec: _table_common_pb2.FieldSpec
    sort_order_spec: _table_common_pb2.FieldSpec
    cluster_info_spec: _containers.RepeatedCompositeFieldContainer[_table_common_pb2.FieldSpec]
    unique_key_spec: _containers.RepeatedCompositeFieldContainer[_table_common_pb2.FieldSpec]
    index_spec: _containers.RepeatedCompositeFieldContainer[_table_common_pb2.FieldSpec]
    foreign_key_spec: _containers.RepeatedCompositeFieldContainer[_table_common_pb2.FieldSpec]
    view: _table_common_pb2.View
    current_snapshot_id: int
    table_format: TableFormat
    stream: _table_common_pb2.TableStream

    def __init__(self, table_id: _Optional[int]=..., table_type: _Optional[_Union[_table_common_pb2.TableType, str]]=..., table_schema: _Optional[_Union[_table_common_pb2.TableSchema, _Mapping]]=..., data_source: _Optional[_Union[_table_common_pb2.DataSource, _Mapping]]=..., primary_key_spec: _Optional[_Union[_table_common_pb2.FieldSpec, _Mapping]]=..., sort_order_spec: _Optional[_Union[_table_common_pb2.FieldSpec, _Mapping]]=..., cluster_info_spec: _Optional[_Iterable[_Union[_table_common_pb2.FieldSpec, _Mapping]]]=..., unique_key_spec: _Optional[_Iterable[_Union[_table_common_pb2.FieldSpec, _Mapping]]]=..., index_spec: _Optional[_Iterable[_Union[_table_common_pb2.FieldSpec, _Mapping]]]=..., foreign_key_spec: _Optional[_Iterable[_Union[_table_common_pb2.FieldSpec, _Mapping]]]=..., view: _Optional[_Union[_table_common_pb2.View, _Mapping]]=..., current_snapshot_id: _Optional[int]=..., table_format: _Optional[_Union[TableFormat, _Mapping]]=..., stream: _Optional[_Union[_table_common_pb2.TableStream, _Mapping]]=...) -> None:
        ...