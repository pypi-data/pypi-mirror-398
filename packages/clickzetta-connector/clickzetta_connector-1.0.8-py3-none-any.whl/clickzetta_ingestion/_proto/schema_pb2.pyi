from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional
DESCRIPTOR: _descriptor.FileDescriptor

class Schema(_message.Message):
    __slots__ = ('location',)
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    location: str

    def __init__(self, location: _Optional[str]=...) -> None:
        ...