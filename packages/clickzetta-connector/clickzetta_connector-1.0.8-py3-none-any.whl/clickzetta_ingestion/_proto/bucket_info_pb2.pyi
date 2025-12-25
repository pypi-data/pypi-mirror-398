from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class BucketInfo(_message.Message):
    __slots__ = ('bucket_id', 'block_ids')
    BUCKET_ID_FIELD_NUMBER: _ClassVar[int]
    BLOCK_IDS_FIELD_NUMBER: _ClassVar[int]
    bucket_id: int
    block_ids: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, bucket_id: _Optional[int]=..., block_ids: _Optional[_Iterable[int]]=...) -> None:
        ...

class BucketIds(_message.Message):
    __slots__ = ('range', 'list')

    class Range(_message.Message):
        __slots__ = ('start', 'end')
        START_FIELD_NUMBER: _ClassVar[int]
        END_FIELD_NUMBER: _ClassVar[int]
        start: int
        end: int

        def __init__(self, start: _Optional[int]=..., end: _Optional[int]=...) -> None:
            ...

    class List(_message.Message):
        __slots__ = ('values',)
        VALUES_FIELD_NUMBER: _ClassVar[int]
        values: _containers.RepeatedScalarFieldContainer[int]

        def __init__(self, values: _Optional[_Iterable[int]]=...) -> None:
            ...
    RANGE_FIELD_NUMBER: _ClassVar[int]
    LIST_FIELD_NUMBER: _ClassVar[int]
    range: BucketIds.Range
    list: BucketIds.List

    def __init__(self, range: _Optional[_Union[BucketIds.Range, _Mapping]]=..., list: _Optional[_Union[BucketIds.List, _Mapping]]=...) -> None:
        ...