import expression_pb2 as _expression_pb2
import file_meta_data_pb2 as _file_meta_data_pb2
import table_common_pb2 as _table_common_pb2
import statistics_pb2 as _statistics_pb2
import virtual_value_info_pb2 as _virtual_value_info_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class ManifestType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DATA: _ClassVar[ManifestType]
    DELTA: _ClassVar[ManifestType]
DATA: ManifestType
DELTA: ManifestType

class Manifest(_message.Message):
    __slots__ = ('cluster_spec_id', 'sort_order_spec_id', 'primary_key_spec_id', 'stats', 'base_snapshot_id', 'concurrency_level', 'added_data_files', 'deleted_data_files', 'added_delta_files', 'deleted_delta_files', 'deleted_partition', 'source_tables', 'stream_tables')

    class ConcurrencyLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        FILE: _ClassVar[Manifest.ConcurrencyLevel]
        TABLE: _ClassVar[Manifest.ConcurrencyLevel]
    FILE: Manifest.ConcurrencyLevel
    TABLE: Manifest.ConcurrencyLevel
    CLUSTER_SPEC_ID_FIELD_NUMBER: _ClassVar[int]
    SORT_ORDER_SPEC_ID_FIELD_NUMBER: _ClassVar[int]
    PRIMARY_KEY_SPEC_ID_FIELD_NUMBER: _ClassVar[int]
    STATS_FIELD_NUMBER: _ClassVar[int]
    BASE_SNAPSHOT_ID_FIELD_NUMBER: _ClassVar[int]
    CONCURRENCY_LEVEL_FIELD_NUMBER: _ClassVar[int]
    ADDED_DATA_FILES_FIELD_NUMBER: _ClassVar[int]
    DELETED_DATA_FILES_FIELD_NUMBER: _ClassVar[int]
    ADDED_DELTA_FILES_FIELD_NUMBER: _ClassVar[int]
    DELETED_DELTA_FILES_FIELD_NUMBER: _ClassVar[int]
    DELETED_PARTITION_FIELD_NUMBER: _ClassVar[int]
    SOURCE_TABLES_FIELD_NUMBER: _ClassVar[int]
    STREAM_TABLES_FIELD_NUMBER: _ClassVar[int]
    cluster_spec_id: int
    sort_order_spec_id: int
    primary_key_spec_id: int
    stats: _statistics_pb2.StatsData
    base_snapshot_id: int
    concurrency_level: Manifest.ConcurrencyLevel
    added_data_files: _containers.RepeatedCompositeFieldContainer[_file_meta_data_pb2.FileMetaData]
    deleted_data_files: _containers.RepeatedCompositeFieldContainer[_file_meta_data_pb2.FileMetaData]
    added_delta_files: _containers.RepeatedCompositeFieldContainer[_file_meta_data_pb2.FileMetaData]
    deleted_delta_files: _containers.RepeatedCompositeFieldContainer[_file_meta_data_pb2.FileMetaData]
    deleted_partition: _containers.RepeatedCompositeFieldContainer[_virtual_value_info_pb2.VirtualValueInfo]
    source_tables: _containers.RepeatedCompositeFieldContainer[_table_common_pb2.MVSource]
    stream_tables: _containers.RepeatedCompositeFieldContainer[_table_common_pb2.TableStreamState]

    def __init__(self, cluster_spec_id: _Optional[int]=..., sort_order_spec_id: _Optional[int]=..., primary_key_spec_id: _Optional[int]=..., stats: _Optional[_Union[_statistics_pb2.StatsData, _Mapping]]=..., base_snapshot_id: _Optional[int]=..., concurrency_level: _Optional[_Union[Manifest.ConcurrencyLevel, str]]=..., added_data_files: _Optional[_Iterable[_Union[_file_meta_data_pb2.FileMetaData, _Mapping]]]=..., deleted_data_files: _Optional[_Iterable[_Union[_file_meta_data_pb2.FileMetaData, _Mapping]]]=..., added_delta_files: _Optional[_Iterable[_Union[_file_meta_data_pb2.FileMetaData, _Mapping]]]=..., deleted_delta_files: _Optional[_Iterable[_Union[_file_meta_data_pb2.FileMetaData, _Mapping]]]=..., deleted_partition: _Optional[_Iterable[_Union[_virtual_value_info_pb2.VirtualValueInfo, _Mapping]]]=..., source_tables: _Optional[_Iterable[_Union[_table_common_pb2.MVSource, _Mapping]]]=..., stream_tables: _Optional[_Iterable[_Union[_table_common_pb2.TableStreamState, _Mapping]]]=...) -> None:
        ...

class ManifestLayout(_message.Message):
    __slots__ = ('value_info', 'stats', 'data_source_ids')
    VALUE_INFO_FIELD_NUMBER: _ClassVar[int]
    STATS_FIELD_NUMBER: _ClassVar[int]
    DATA_SOURCE_IDS_FIELD_NUMBER: _ClassVar[int]
    value_info: _containers.RepeatedCompositeFieldContainer[_virtual_value_info_pb2.VirtualValueInfo]
    stats: _containers.RepeatedCompositeFieldContainer[_statistics_pb2.StatsData]
    data_source_ids: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, value_info: _Optional[_Iterable[_Union[_virtual_value_info_pb2.VirtualValueInfo, _Mapping]]]=..., stats: _Optional[_Iterable[_Union[_statistics_pb2.StatsData, _Mapping]]]=..., data_source_ids: _Optional[_Iterable[int]]=...) -> None:
        ...