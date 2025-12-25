import time_range_pb2 as _time_range_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class RuntimeRunSpanStats(_message.Message):
    __slots__ = ('execute_time_us', 'runner_id')
    EXECUTE_TIME_US_FIELD_NUMBER: _ClassVar[int]
    RUNNER_ID_FIELD_NUMBER: _ClassVar[int]
    execute_time_us: _time_range_pb2.TimeRange
    runner_id: int

    def __init__(self, execute_time_us: _Optional[_Union[_time_range_pb2.TimeRange, _Mapping]]=..., runner_id: _Optional[int]=...) -> None:
        ...