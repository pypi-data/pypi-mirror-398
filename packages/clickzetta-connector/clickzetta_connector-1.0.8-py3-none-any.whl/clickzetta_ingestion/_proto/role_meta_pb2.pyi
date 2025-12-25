from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class RoleType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RT_SYSTEM: _ClassVar[RoleType]
    RT_CUSTOMIZE: _ClassVar[RoleType]

class RoleLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RL_SYSTEM: _ClassVar[RoleLevel]
    RL_WORKSPACE: _ClassVar[RoleLevel]
RT_SYSTEM: RoleType
RT_CUSTOMIZE: RoleType
RL_SYSTEM: RoleLevel
RL_WORKSPACE: RoleLevel

class Role(_message.Message):
    __slots__ = ('alias', 'type', 'level')
    ALIAS_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    alias: str
    type: RoleType
    level: RoleLevel

    def __init__(self, alias: _Optional[str]=..., type: _Optional[_Union[RoleType, str]]=..., level: _Optional[_Union[RoleLevel, str]]=...) -> None:
        ...