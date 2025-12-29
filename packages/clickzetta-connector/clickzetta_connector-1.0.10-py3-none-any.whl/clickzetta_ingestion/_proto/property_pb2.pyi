from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class Property(_message.Message):
    __slots__ = ('key', 'value')
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: str

    def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
        ...

class Properties(_message.Message):
    __slots__ = ('properties',)
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    properties: _containers.RepeatedCompositeFieldContainer[Property]

    def __init__(self, properties: _Optional[_Iterable[_Union[Property, _Mapping]]]=...) -> None:
        ...

class PropertyKeyList(_message.Message):
    __slots__ = ('keys',)
    KEYS_FIELD_NUMBER: _ClassVar[int]
    keys: _containers.RepeatedScalarFieldContainer[str]

    def __init__(self, keys: _Optional[_Iterable[str]]=...) -> None:
        ...