from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional
DESCRIPTOR: _descriptor.FileDescriptor

class JobResultCacheMeta(_message.Message):
    __slots__ = ('instance_id', 'workspace_id', 'job_signature', 'preprocessed_plan', 'result_files', 'start_time_ms')
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    JOB_SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    PREPROCESSED_PLAN_FIELD_NUMBER: _ClassVar[int]
    RESULT_FILES_FIELD_NUMBER: _ClassVar[int]
    START_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    instance_id: int
    workspace_id: int
    job_signature: str
    preprocessed_plan: str
    result_files: str
    start_time_ms: int

    def __init__(self, instance_id: _Optional[int]=..., workspace_id: _Optional[int]=..., job_signature: _Optional[str]=..., preprocessed_plan: _Optional[str]=..., result_files: _Optional[str]=..., start_time_ms: _Optional[int]=...) -> None:
        ...