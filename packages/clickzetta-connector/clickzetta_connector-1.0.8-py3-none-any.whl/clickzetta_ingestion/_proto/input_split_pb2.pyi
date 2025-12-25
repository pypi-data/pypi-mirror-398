import virtual_value_info_pb2 as _virtual_value_info_pb2
import statistics_pb2 as _statistics_pb2
import bit_set_pb2 as _bit_set_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class InputSplitType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    FILE_RANGE: _ClassVar[InputSplitType]
    ROW_RANGE: _ClassVar[InputSplitType]

class FileRangeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NORMAL_FILE: _ClassVar[FileRangeType]
    ADDED_FILE: _ClassVar[FileRangeType]
    DELETED_FILE: _ClassVar[FileRangeType]
FILE_RANGE: InputSplitType
ROW_RANGE: InputSplitType
NORMAL_FILE: FileRangeType
ADDED_FILE: FileRangeType
DELETED_FILE: FileRangeType

class InputSplit(_message.Message):
    __slots__ = ('type', 'operatorId', 'fileRanges', 'fileRowRange')
    TYPE_FIELD_NUMBER: _ClassVar[int]
    OPERATORID_FIELD_NUMBER: _ClassVar[int]
    FILERANGES_FIELD_NUMBER: _ClassVar[int]
    FILEROWRANGE_FIELD_NUMBER: _ClassVar[int]
    type: InputSplitType
    operatorId: str
    fileRanges: FileRangesInputSplit
    fileRowRange: FileRowRangeInputSplit

    def __init__(self, type: _Optional[_Union[InputSplitType, str]]=..., operatorId: _Optional[str]=..., fileRanges: _Optional[_Union[FileRangesInputSplit, _Mapping]]=..., fileRowRange: _Optional[_Union[FileRowRangeInputSplit, _Mapping]]=...) -> None:
        ...

class FileFieldStats(_message.Message):
    __slots__ = ('field_ranges',)
    FIELD_RANGES_FIELD_NUMBER: _ClassVar[int]
    field_ranges: _containers.RepeatedCompositeFieldContainer[_statistics_pb2.FieldRange]

    def __init__(self, field_ranges: _Optional[_Iterable[_Union[_statistics_pb2.FieldRange, _Mapping]]]=...) -> None:
        ...

class FileRange(_message.Message):
    __slots__ = ('path', 'offset', 'size', 'value_info', 'delta_files', 'type', 'field_stats', 'total_file_size')
    PATH_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    VALUE_INFO_FIELD_NUMBER: _ClassVar[int]
    DELTA_FILES_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    FIELD_STATS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FILE_SIZE_FIELD_NUMBER: _ClassVar[int]
    path: str
    offset: int
    size: int
    value_info: _virtual_value_info_pb2.VirtualValueInfo
    delta_files: _containers.RepeatedCompositeFieldContainer[FileRange]
    type: FileRangeType
    field_stats: FileFieldStats
    total_file_size: int

    def __init__(self, path: _Optional[str]=..., offset: _Optional[int]=..., size: _Optional[int]=..., value_info: _Optional[_Union[_virtual_value_info_pb2.VirtualValueInfo, _Mapping]]=..., delta_files: _Optional[_Iterable[_Union[FileRange, _Mapping]]]=..., type: _Optional[_Union[FileRangeType, str]]=..., field_stats: _Optional[_Union[FileFieldStats, _Mapping]]=..., total_file_size: _Optional[int]=...) -> None:
        ...

class FileRangesInputSplit(_message.Message):
    __slots__ = ('ranges', 'bucket_count', 'bucket_id', 'workers', 'worker_of_range')

    class Worker(_message.Message):
        __slots__ = ('host', 'rpc_port', 'data_port')
        HOST_FIELD_NUMBER: _ClassVar[int]
        RPC_PORT_FIELD_NUMBER: _ClassVar[int]
        DATA_PORT_FIELD_NUMBER: _ClassVar[int]
        host: str
        rpc_port: int
        data_port: int

        def __init__(self, host: _Optional[str]=..., rpc_port: _Optional[int]=..., data_port: _Optional[int]=...) -> None:
            ...
    RANGES_FIELD_NUMBER: _ClassVar[int]
    BUCKET_COUNT_FIELD_NUMBER: _ClassVar[int]
    BUCKET_ID_FIELD_NUMBER: _ClassVar[int]
    WORKERS_FIELD_NUMBER: _ClassVar[int]
    WORKER_OF_RANGE_FIELD_NUMBER: _ClassVar[int]
    ranges: _containers.RepeatedCompositeFieldContainer[FileRange]
    bucket_count: int
    bucket_id: int
    workers: _containers.RepeatedCompositeFieldContainer[FileRangesInputSplit.Worker]
    worker_of_range: _containers.RepeatedCompositeFieldContainer[_bit_set_pb2.BitSet]

    def __init__(self, ranges: _Optional[_Iterable[_Union[FileRange, _Mapping]]]=..., bucket_count: _Optional[int]=..., bucket_id: _Optional[int]=..., workers: _Optional[_Iterable[_Union[FileRangesInputSplit.Worker, _Mapping]]]=..., worker_of_range: _Optional[_Iterable[_Union[_bit_set_pb2.BitSet, _Mapping]]]=...) -> None:
        ...

class FileRowRangeInputSplit(_message.Message):
    __slots__ = ('path', 'start_row', 'end_row')
    PATH_FIELD_NUMBER: _ClassVar[int]
    START_ROW_FIELD_NUMBER: _ClassVar[int]
    END_ROW_FIELD_NUMBER: _ClassVar[int]
    path: str
    start_row: int
    end_row: int

    def __init__(self, path: _Optional[str]=..., start_row: _Optional[int]=..., end_row: _Optional[int]=...) -> None:
        ...

class RangeFile(_message.Message):
    __slots__ = ('path', 'recordCnt', 'fileSize', 'location')
    PATH_FIELD_NUMBER: _ClassVar[int]
    RECORDCNT_FIELD_NUMBER: _ClassVar[int]
    FILESIZE_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    path: str
    recordCnt: int
    fileSize: int
    location: str

    def __init__(self, path: _Optional[str]=..., recordCnt: _Optional[int]=..., fileSize: _Optional[int]=..., location: _Optional[str]=...) -> None:
        ...

class RangeLiteral(_message.Message):
    __slots__ = ('intV', 'longV', 'stringV')
    INTV_FIELD_NUMBER: _ClassVar[int]
    LONGV_FIELD_NUMBER: _ClassVar[int]
    STRINGV_FIELD_NUMBER: _ClassVar[int]
    intV: int
    longV: int
    stringV: str

    def __init__(self, intV: _Optional[int]=..., longV: _Optional[int]=..., stringV: _Optional[str]=...) -> None:
        ...

class RangePartition(_message.Message):
    __slots__ = ('rangeId', 'rangeFiles', 'lower', 'upper')
    RANGEID_FIELD_NUMBER: _ClassVar[int]
    RANGEFILES_FIELD_NUMBER: _ClassVar[int]
    LOWER_FIELD_NUMBER: _ClassVar[int]
    UPPER_FIELD_NUMBER: _ClassVar[int]
    rangeId: int
    rangeFiles: _containers.RepeatedCompositeFieldContainer[RangeFile]
    lower: _containers.RepeatedCompositeFieldContainer[RangeLiteral]
    upper: _containers.RepeatedCompositeFieldContainer[RangeLiteral]

    def __init__(self, rangeId: _Optional[int]=..., rangeFiles: _Optional[_Iterable[_Union[RangeFile, _Mapping]]]=..., lower: _Optional[_Iterable[_Union[RangeLiteral, _Mapping]]]=..., upper: _Optional[_Iterable[_Union[RangeLiteral, _Mapping]]]=...) -> None:
        ...

class OutputSplitType(_message.Message):
    __slots__ = ()

    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        FILE: _ClassVar[OutputSplitType.Type]
    FILE: OutputSplitType.Type

    def __init__(self) -> None:
        ...

class OutputSplit(_message.Message):
    __slots__ = ('type', 'operatorId', 'file')
    TYPE_FIELD_NUMBER: _ClassVar[int]
    OPERATORID_FIELD_NUMBER: _ClassVar[int]
    FILE_FIELD_NUMBER: _ClassVar[int]
    type: OutputSplitType.Type
    operatorId: str
    file: FileOutputSplit

    def __init__(self, type: _Optional[_Union[OutputSplitType.Type, str]]=..., operatorId: _Optional[str]=..., file: _Optional[_Union[FileOutputSplit, _Mapping]]=...) -> None:
        ...

class FileOutputSplit(_message.Message):
    __slots__ = ('path',)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: str

    def __init__(self, path: _Optional[str]=...) -> None:
        ...

class FileSplitMeta(_message.Message):
    __slots__ = ('split_file', 'offset')

    class Offset(_message.Message):
        __slots__ = ('task_id', 'start_offset', 'end_offset')
        TASK_ID_FIELD_NUMBER: _ClassVar[int]
        START_OFFSET_FIELD_NUMBER: _ClassVar[int]
        END_OFFSET_FIELD_NUMBER: _ClassVar[int]
        task_id: int
        start_offset: int
        end_offset: int

        def __init__(self, task_id: _Optional[int]=..., start_offset: _Optional[int]=..., end_offset: _Optional[int]=...) -> None:
            ...
    SPLIT_FILE_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    split_file: str
    offset: _containers.RepeatedCompositeFieldContainer[FileSplitMeta.Offset]

    def __init__(self, split_file: _Optional[str]=..., offset: _Optional[_Iterable[_Union[FileSplitMeta.Offset, _Mapping]]]=...) -> None:
        ...

class EmbeddedSplitMeta(_message.Message):
    __slots__ = ('splits',)

    class Pair(_message.Message):
        __slots__ = ('task_id', 'split', 'output_split')
        TASK_ID_FIELD_NUMBER: _ClassVar[int]
        SPLIT_FIELD_NUMBER: _ClassVar[int]
        OUTPUT_SPLIT_FIELD_NUMBER: _ClassVar[int]
        task_id: int
        split: InputSplit
        output_split: OutputSplit

        def __init__(self, task_id: _Optional[int]=..., split: _Optional[_Union[InputSplit, _Mapping]]=..., output_split: _Optional[_Union[OutputSplit, _Mapping]]=...) -> None:
            ...
    SPLITS_FIELD_NUMBER: _ClassVar[int]
    splits: _containers.RepeatedCompositeFieldContainer[EmbeddedSplitMeta.Pair]

    def __init__(self, splits: _Optional[_Iterable[_Union[EmbeddedSplitMeta.Pair, _Mapping]]]=...) -> None:
        ...

class SplitMeta(_message.Message):
    __slots__ = ('stage_id', 'operator_id', 'file', 'embedded')
    STAGE_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATOR_ID_FIELD_NUMBER: _ClassVar[int]
    FILE_FIELD_NUMBER: _ClassVar[int]
    EMBEDDED_FIELD_NUMBER: _ClassVar[int]
    stage_id: str
    operator_id: str
    file: FileSplitMeta
    embedded: EmbeddedSplitMeta

    def __init__(self, stage_id: _Optional[str]=..., operator_id: _Optional[str]=..., file: _Optional[_Union[FileSplitMeta, _Mapping]]=..., embedded: _Optional[_Union[EmbeddedSplitMeta, _Mapping]]=...) -> None:
        ...

class CompactionSplitFile(_message.Message):
    __slots__ = ('path', 'offset', 'size', 'sliceId', 'value_info', 'delta_files')
    PATH_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    SLICEID_FIELD_NUMBER: _ClassVar[int]
    VALUE_INFO_FIELD_NUMBER: _ClassVar[int]
    DELTA_FILES_FIELD_NUMBER: _ClassVar[int]
    path: str
    offset: int
    size: int
    sliceId: int
    value_info: _virtual_value_info_pb2.VirtualValueInfo
    delta_files: _containers.RepeatedCompositeFieldContainer[CompactionSplitFile]

    def __init__(self, path: _Optional[str]=..., offset: _Optional[int]=..., size: _Optional[int]=..., sliceId: _Optional[int]=..., value_info: _Optional[_Union[_virtual_value_info_pb2.VirtualValueInfo, _Mapping]]=..., delta_files: _Optional[_Iterable[_Union[CompactionSplitFile, _Mapping]]]=...) -> None:
        ...

class CompactionSplit(_message.Message):
    __slots__ = ('files',)
    FILES_FIELD_NUMBER: _ClassVar[int]
    files: _containers.RepeatedCompositeFieldContainer[CompactionSplitFile]

    def __init__(self, files: _Optional[_Iterable[_Union[CompactionSplitFile, _Mapping]]]=...) -> None:
        ...

class CompactionSplits(_message.Message):
    __slots__ = ('splits',)
    SPLITS_FIELD_NUMBER: _ClassVar[int]
    splits: _containers.RepeatedCompositeFieldContainer[CompactionSplit]

    def __init__(self, splits: _Optional[_Iterable[_Union[CompactionSplit, _Mapping]]]=...) -> None:
        ...