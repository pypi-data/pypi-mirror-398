from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class ObjectType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN: _ClassVar[ObjectType]
    INSTANCE: _ClassVar[ObjectType]
    NETWORK_POLICY: _ClassVar[ObjectType]
    WORKSPACE: _ClassVar[ObjectType]
    SHARE: _ClassVar[ObjectType]
    COMPUTE_POOL: _ClassVar[ObjectType]
    SCHEMA: _ClassVar[ObjectType]
    DATALAKE: _ClassVar[ObjectType]
    USER: _ClassVar[ObjectType]
    ROLE: _ClassVar[ObjectType]
    VIRTUAL_CLUSTER: _ClassVar[ObjectType]
    JOB: _ClassVar[ObjectType]
    CONNECTION: _ClassVar[ObjectType]
    LOCATION: _ClassVar[ObjectType]
    TABLE: _ClassVar[ObjectType]
    FUNCTION: _ClassVar[ObjectType]
    VOLUME: _ClassVar[ObjectType]
    INTERNAL_VOLUME: _ClassVar[ObjectType]
    SYNONYM: _ClassVar[ObjectType]
    PIPE_TASK: _ClassVar[ObjectType]
    INDEX: _ClassVar[ObjectType]
    PARTITION: _ClassVar[ObjectType]
    FILE: _ClassVar[ObjectType]
    ALL: _ClassVar[ObjectType]

class PrincipalType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PT_USER: _ClassVar[PrincipalType]
    PT_SYSTEM: _ClassVar[PrincipalType]
    PT_SERVICE_SYSTEM: _ClassVar[PrincipalType]
    PT_SERVICE_CUSTOMER: _ClassVar[PrincipalType]
UNKNOWN: ObjectType
INSTANCE: ObjectType
NETWORK_POLICY: ObjectType
WORKSPACE: ObjectType
SHARE: ObjectType
COMPUTE_POOL: ObjectType
SCHEMA: ObjectType
DATALAKE: ObjectType
USER: ObjectType
ROLE: ObjectType
VIRTUAL_CLUSTER: ObjectType
JOB: ObjectType
CONNECTION: ObjectType
LOCATION: ObjectType
TABLE: ObjectType
FUNCTION: ObjectType
VOLUME: ObjectType
INTERNAL_VOLUME: ObjectType
SYNONYM: ObjectType
PIPE_TASK: ObjectType
INDEX: ObjectType
PARTITION: ObjectType
FILE: ObjectType
ALL: ObjectType
PT_USER: PrincipalType
PT_SYSTEM: PrincipalType
PT_SERVICE_SYSTEM: PrincipalType
PT_SERVICE_CUSTOMER: PrincipalType

class ObjectState(_message.Message):
    __slots__ = ()

    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ONLINE: _ClassVar[ObjectState.Type]
        DELETED: _ClassVar[ObjectState.Type]
        STAGED: _ClassVar[ObjectState.Type]
    ONLINE: ObjectState.Type
    DELETED: ObjectState.Type
    STAGED: ObjectState.Type

    def __init__(self) -> None:
        ...

class ObjectIdentifier(_message.Message):
    __slots__ = ('type', 'account_id', 'account_name', 'instance_id', 'instance_name', 'namespace', 'namespace_id', 'namespace_type', 'name', 'id', 'version', 'reference_type')
    TYPE_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_ID_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_NAME_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_NAME_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_ID_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    type: ObjectType
    account_id: int
    account_name: str
    instance_id: int
    instance_name: str
    namespace: _containers.RepeatedScalarFieldContainer[str]
    namespace_id: _containers.RepeatedScalarFieldContainer[int]
    namespace_type: _containers.RepeatedScalarFieldContainer[ObjectType]
    name: str
    id: int
    version: str
    reference_type: ObjectType

    def __init__(self, type: _Optional[_Union[ObjectType, str]]=..., account_id: _Optional[int]=..., account_name: _Optional[str]=..., instance_id: _Optional[int]=..., instance_name: _Optional[str]=..., namespace: _Optional[_Iterable[str]]=..., namespace_id: _Optional[_Iterable[int]]=..., namespace_type: _Optional[_Iterable[_Union[ObjectType, str]]]=..., name: _Optional[str]=..., id: _Optional[int]=..., version: _Optional[str]=..., reference_type: _Optional[_Union[ObjectType, str]]=...) -> None:
        ...

class ObjectIdentifierList(_message.Message):
    __slots__ = ('identifiers',)
    IDENTIFIERS_FIELD_NUMBER: _ClassVar[int]
    identifiers: _containers.RepeatedCompositeFieldContainer[ObjectIdentifier]

    def __init__(self, identifiers: _Optional[_Iterable[_Union[ObjectIdentifier, _Mapping]]]=...) -> None:
        ...

class ObjectModificationEvent(_message.Message):
    __slots__ = ('identifier', 'version', 'sequence', 'occur_time')
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    OCCUR_TIME_FIELD_NUMBER: _ClassVar[int]
    identifier: ObjectIdentifier
    version: int
    sequence: int
    occur_time: int

    def __init__(self, identifier: _Optional[_Union[ObjectIdentifier, _Mapping]]=..., version: _Optional[int]=..., sequence: _Optional[int]=..., occur_time: _Optional[int]=...) -> None:
        ...

class ObjectModificationEventList(_message.Message):
    __slots__ = ('events',)
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[ObjectModificationEvent]

    def __init__(self, events: _Optional[_Iterable[_Union[ObjectModificationEvent, _Mapping]]]=...) -> None:
        ...