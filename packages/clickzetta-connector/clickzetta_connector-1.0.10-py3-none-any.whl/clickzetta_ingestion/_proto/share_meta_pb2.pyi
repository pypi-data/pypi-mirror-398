import object_identifier_pb2 as _object_identifier_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class Share(_message.Message):
    __slots__ = ('provider_workspace', 'kind', 'scope')

    class Kind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        INBOUND: _ClassVar[Share.Kind]
        OUTBOUND: _ClassVar[Share.Kind]
    INBOUND: Share.Kind
    OUTBOUND: Share.Kind

    class Scope(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        PRIVATE: _ClassVar[Share.Scope]
        PUBLIC: _ClassVar[Share.Scope]
    PRIVATE: Share.Scope
    PUBLIC: Share.Scope
    PROVIDER_WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    provider_workspace: _object_identifier_pb2.ObjectIdentifier
    kind: Share.Kind
    scope: Share.Scope

    def __init__(self, provider_workspace: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., kind: _Optional[_Union[Share.Kind, str]]=..., scope: _Optional[_Union[Share.Scope, str]]=...) -> None:
        ...