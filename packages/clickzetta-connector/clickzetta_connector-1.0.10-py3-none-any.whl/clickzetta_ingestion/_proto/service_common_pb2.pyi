from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional
DESCRIPTOR: _descriptor.FileDescriptor

class ResponseStatus(_message.Message):
    __slots__ = ('request_id', 'error_code', 'error_msg')
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    ERROR_MSG_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    error_code: str
    error_msg: str

    def __init__(self, request_id: _Optional[str]=..., error_code: _Optional[str]=..., error_msg: _Optional[str]=...) -> None:
        ...