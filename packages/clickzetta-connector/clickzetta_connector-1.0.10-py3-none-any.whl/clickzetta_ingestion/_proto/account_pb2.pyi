import object_identifier_pb2 as _object_identifier_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class PolicyStatement(_message.Message):
    __slots__ = ('Effect', 'Principal', 'Action', 'Resource')
    EFFECT_FIELD_NUMBER: _ClassVar[int]
    PRINCIPAL_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    Effect: str
    Principal: _containers.RepeatedScalarFieldContainer[str]
    Action: _containers.RepeatedScalarFieldContainer[str]
    Resource: _containers.RepeatedScalarFieldContainer[str]

    def __init__(self, Effect: _Optional[str]=..., Principal: _Optional[_Iterable[str]]=..., Action: _Optional[_Iterable[str]]=..., Resource: _Optional[_Iterable[str]]=...) -> None:
        ...

class Policy(_message.Message):
    __slots__ = ('Version', 'Statement')
    VERSION_FIELD_NUMBER: _ClassVar[int]
    STATEMENT_FIELD_NUMBER: _ClassVar[int]
    Version: str
    Statement: _containers.RepeatedCompositeFieldContainer[PolicyStatement]

    def __init__(self, Version: _Optional[str]=..., Statement: _Optional[_Iterable[_Union[PolicyStatement, _Mapping]]]=...) -> None:
        ...

class Account(_message.Message):
    __slots__ = ('account_id', 'user_name', 'user_id', 'type', 'policy')
    ACCOUNT_ID_FIELD_NUMBER: _ClassVar[int]
    USER_NAME_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    POLICY_FIELD_NUMBER: _ClassVar[int]
    account_id: int
    user_name: str
    user_id: int
    type: _object_identifier_pb2.PrincipalType
    policy: Policy

    def __init__(self, account_id: _Optional[int]=..., user_name: _Optional[str]=..., user_id: _Optional[int]=..., type: _Optional[_Union[_object_identifier_pb2.PrincipalType, str]]=..., policy: _Optional[_Union[Policy, _Mapping]]=...) -> None:
        ...

class Instance(_message.Message):
    __slots__ = ('account_name', 'account_id', 'instance_id', 'instance_name')
    ACCOUNT_NAME_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_ID_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_NAME_FIELD_NUMBER: _ClassVar[int]
    account_name: str
    account_id: int
    instance_id: int
    instance_name: str

    def __init__(self, account_name: _Optional[str]=..., account_id: _Optional[int]=..., instance_id: _Optional[int]=..., instance_name: _Optional[str]=...) -> None:
        ...

class UserIdentifier(_message.Message):
    __slots__ = ('identifier', 'user_id')
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier
    user_id: int

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., user_id: _Optional[int]=...) -> None:
        ...

class User(_message.Message):
    __slots__ = ('user_id', 'default_vc', 'default_schema')
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_VC_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    user_id: int
    default_vc: str
    default_schema: str

    def __init__(self, user_id: _Optional[int]=..., default_vc: _Optional[str]=..., default_schema: _Optional[str]=...) -> None:
        ...