import bucket_info_pb2 as _bucket_info_pb2
import file_format_type_pb2 as _file_format_type_pb2
import statistics_pb2 as _statistics_pb2
import virtual_value_info_pb2 as _virtual_value_info_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class FileType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN_FILE: _ClassVar[FileType]
    DATA_FILE: _ClassVar[FileType]
    DELTA_FILE: _ClassVar[FileType]
UNKNOWN_FILE: FileType
DATA_FILE: FileType
DELTA_FILE: FileType

class BlockInfo(_message.Message):
    __slots__ = ('offset', 'length')
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    offset: int
    length: int

    def __init__(self, offset: _Optional[int]=..., length: _Optional[int]=...) -> None:
        ...

class DataLayout(_message.Message):
    __slots__ = ('footer', 'blocks', 'buckets', 'value_info', 'original_virtual_value_count', 'row_index_stride', 'block_row_counts', 'data_sealed')
    FOOTER_FIELD_NUMBER: _ClassVar[int]
    BLOCKS_FIELD_NUMBER: _ClassVar[int]
    BUCKETS_FIELD_NUMBER: _ClassVar[int]
    VALUE_INFO_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_VIRTUAL_VALUE_COUNT_FIELD_NUMBER: _ClassVar[int]
    ROW_INDEX_STRIDE_FIELD_NUMBER: _ClassVar[int]
    BLOCK_ROW_COUNTS_FIELD_NUMBER: _ClassVar[int]
    DATA_SEALED_FIELD_NUMBER: _ClassVar[int]
    footer: BlockInfo
    blocks: _containers.RepeatedCompositeFieldContainer[BlockInfo]
    buckets: _containers.RepeatedCompositeFieldContainer[_bucket_info_pb2.BucketInfo]
    value_info: _containers.RepeatedCompositeFieldContainer[_virtual_value_info_pb2.VirtualValueInfo]
    original_virtual_value_count: int
    row_index_stride: int
    block_row_counts: _containers.RepeatedScalarFieldContainer[int]
    data_sealed: bool

    def __init__(self, footer: _Optional[_Union[BlockInfo, _Mapping]]=..., blocks: _Optional[_Iterable[_Union[BlockInfo, _Mapping]]]=..., buckets: _Optional[_Iterable[_Union[_bucket_info_pb2.BucketInfo, _Mapping]]]=..., value_info: _Optional[_Iterable[_Union[_virtual_value_info_pb2.VirtualValueInfo, _Mapping]]]=..., original_virtual_value_count: _Optional[int]=..., row_index_stride: _Optional[int]=..., block_row_counts: _Optional[_Iterable[int]]=..., data_sealed: bool=...) -> None:
        ...

class ExtendedMetaData(_message.Message):
    __slots__ = ('key_value',)

    class KeyValueEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    KEY_VALUE_FIELD_NUMBER: _ClassVar[int]
    key_value: _containers.ScalarMap[str, str]

    def __init__(self, key_value: _Optional[_Mapping[str, str]]=...) -> None:
        ...

class FileMetaData(_message.Message):
    __slots__ = ('data_source_id', 'file_path', 'file_format', 'file_type', 'file_slice_id', 'file_slice_version', 'compaction_level', 'cluster_spec_id', 'sort_order_spec_id', 'primary_key_spec_id', 'layout', 'extended_metadata', 'stats')
    DATA_SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    FILE_PATH_FIELD_NUMBER: _ClassVar[int]
    FILE_FORMAT_FIELD_NUMBER: _ClassVar[int]
    FILE_TYPE_FIELD_NUMBER: _ClassVar[int]
    FILE_SLICE_ID_FIELD_NUMBER: _ClassVar[int]
    FILE_SLICE_VERSION_FIELD_NUMBER: _ClassVar[int]
    COMPACTION_LEVEL_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_SPEC_ID_FIELD_NUMBER: _ClassVar[int]
    SORT_ORDER_SPEC_ID_FIELD_NUMBER: _ClassVar[int]
    PRIMARY_KEY_SPEC_ID_FIELD_NUMBER: _ClassVar[int]
    LAYOUT_FIELD_NUMBER: _ClassVar[int]
    EXTENDED_METADATA_FIELD_NUMBER: _ClassVar[int]
    STATS_FIELD_NUMBER: _ClassVar[int]
    data_source_id: int
    file_path: str
    file_format: _file_format_type_pb2.FileFormatType
    file_type: FileType
    file_slice_id: int
    file_slice_version: int
    compaction_level: int
    cluster_spec_id: int
    sort_order_spec_id: int
    primary_key_spec_id: int
    layout: DataLayout
    extended_metadata: ExtendedMetaData
    stats: _statistics_pb2.StatsData

    def __init__(self, data_source_id: _Optional[int]=..., file_path: _Optional[str]=..., file_format: _Optional[_Union[_file_format_type_pb2.FileFormatType, str]]=..., file_type: _Optional[_Union[FileType, str]]=..., file_slice_id: _Optional[int]=..., file_slice_version: _Optional[int]=..., compaction_level: _Optional[int]=..., cluster_spec_id: _Optional[int]=..., sort_order_spec_id: _Optional[int]=..., primary_key_spec_id: _Optional[int]=..., layout: _Optional[_Union[DataLayout, _Mapping]]=..., extended_metadata: _Optional[_Union[ExtendedMetaData, _Mapping]]=..., stats: _Optional[_Union[_statistics_pb2.StatsData, _Mapping]]=...) -> None:
        ...