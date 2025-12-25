from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class NetworkPolicy(_message.Message):
    __slots__ = ('content',)
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    content: NetworkPolicyData

    def __init__(self, content: _Optional[_Union[NetworkPolicyData, _Mapping]]=...) -> None:
        ...

class NetworkPolicyData(_message.Message):
    __slots__ = ('workspaceList', 'usernameList', 'blockedList', 'allowedList')
    WORKSPACELIST_FIELD_NUMBER: _ClassVar[int]
    USERNAMELIST_FIELD_NUMBER: _ClassVar[int]
    BLOCKEDLIST_FIELD_NUMBER: _ClassVar[int]
    ALLOWEDLIST_FIELD_NUMBER: _ClassVar[int]
    workspaceList: _containers.RepeatedScalarFieldContainer[str]
    usernameList: _containers.RepeatedScalarFieldContainer[str]
    blockedList: _containers.RepeatedScalarFieldContainer[str]
    allowedList: _containers.RepeatedScalarFieldContainer[str]

    def __init__(self, workspaceList: _Optional[_Iterable[str]]=..., usernameList: _Optional[_Iterable[str]]=..., blockedList: _Optional[_Iterable[str]]=..., allowedList: _Optional[_Iterable[str]]=...) -> None:
        ...