from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional
DESCRIPTOR: _descriptor.FileDescriptor

class VirtualClusterSizeSpec(_message.Message):
    __slots__ = ('id', 'name', 'alias_1', 'alias_2', 'alias_3', 'cpu_core', 'mem_gb')
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ALIAS_1_FIELD_NUMBER: _ClassVar[int]
    ALIAS_2_FIELD_NUMBER: _ClassVar[int]
    ALIAS_3_FIELD_NUMBER: _ClassVar[int]
    CPU_CORE_FIELD_NUMBER: _ClassVar[int]
    MEM_GB_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    alias_1: str
    alias_2: str
    alias_3: str
    cpu_core: float
    mem_gb: int

    def __init__(self, id: _Optional[int]=..., name: _Optional[str]=..., alias_1: _Optional[str]=..., alias_2: _Optional[str]=..., alias_3: _Optional[str]=..., cpu_core: _Optional[float]=..., mem_gb: _Optional[int]=...) -> None:
        ...