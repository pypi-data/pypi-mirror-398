import object_identifier_pb2 as _object_identifier_pb2
import account_pb2 as _account_pb2
import metadata_entity_pb2 as _metadata_entity_pb2
import table_common_pb2 as _table_common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class SystemRole(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SystemAdmin: _ClassVar[SystemRole]
    UserAdmin: _ClassVar[SystemRole]
    SecurityAdmin: _ClassVar[SystemRole]
    AuditAdmin: _ClassVar[SystemRole]

class ActionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    AT_KNOWN: _ClassVar[ActionType]
    AT_ALL: _ClassVar[ActionType]
    AT_CREATE_ALL: _ClassVar[ActionType]
    AT_ALTER_ALL: _ClassVar[ActionType]
    AT_UPDATE_ALL: _ClassVar[ActionType]
    AT_SELECT_ALL: _ClassVar[ActionType]
    AT_DROP_ALL: _ClassVar[ActionType]
    AT_ALL_FIN: _ClassVar[ActionType]
    AT_CREATE_ROLE: _ClassVar[ActionType]
    AT_ALTER_ROLE: _ClassVar[ActionType]
    AT_DROP_ROLE: _ClassVar[ActionType]
    AT_GRANT_PRIVILEGE: _ClassVar[ActionType]
    AT_REVOKE_PRIVILEGE: _ClassVar[ActionType]
    AT_SHOW_PRIVILEGE: _ClassVar[ActionType]
    AT_CREATE_VCLUSTER: _ClassVar[ActionType]
    AT_ALTER_VCLUSTER: _ClassVar[ActionType]
    AT_DROP_VCLUSTER: _ClassVar[ActionType]
    AT_USE_VCLUSTER: _ClassVar[ActionType]
    AT_CREATE_SCHEMA: _ClassVar[ActionType]
    AT_ALTER_SCHEMA: _ClassVar[ActionType]
    AT_DROP_SCHEMA: _ClassVar[ActionType]
    AT_CREATE_TABLE: _ClassVar[ActionType]
    AT_ALTER_TABLE: _ClassVar[ActionType]
    AT_DROP_TABLE: _ClassVar[ActionType]
    AT_SELECT_TABLE: _ClassVar[ActionType]
    AT_INSERT_TABLE: _ClassVar[ActionType]
    AT_TRUNCATE_TABLE: _ClassVar[ActionType]
    AT_UPDATE_TABLE: _ClassVar[ActionType]
    AT_DELETE_TABLE: _ClassVar[ActionType]
    AT_CREATE_VIEW: _ClassVar[ActionType]
    AT_DROP_VIEW: _ClassVar[ActionType]
    AT_SELECT_VIEW: _ClassVar[ActionType]
    AT_ALTER_VIEW: _ClassVar[ActionType]
    AT_CREATE_MATERIALIZED_VIEW: _ClassVar[ActionType]
    AT_DROP_MATERIALIZED_VIEW: _ClassVar[ActionType]
    AT_SELECT_MATERIALIZED_VIEW: _ClassVar[ActionType]
    AT_ALTER_MATERIALIZED_VIEW: _ClassVar[ActionType]
    AT_CREATE_FUNCTION: _ClassVar[ActionType]
    AT_DROP_FUNCTION: _ClassVar[ActionType]
    AT_USE_FUNCTION: _ClassVar[ActionType]
    AT_ALTER_FUNCTION: _ClassVar[ActionType]
    AT_CREATE_DATALAKE: _ClassVar[ActionType]
    AT_ALTER_DATALAKE: _ClassVar[ActionType]
    AT_DROP_DATALAKE: _ClassVar[ActionType]
    AT_CREATE_SCHEDULE_TASK: _ClassVar[ActionType]
    AT_ALTER_SCHEDULE_TASK: _ClassVar[ActionType]
    AT_DROP_SCHEDULE_TASK: _ClassVar[ActionType]
    AT_CLONE_SCHEDULE_TASK: _ClassVar[ActionType]
    AT_CREATE_USER: _ClassVar[ActionType]
    AT_DROP_USER: _ClassVar[ActionType]
    AT_ALTER_USER: _ClassVar[ActionType]
    AT_READ_AUDIT_LOG: _ClassVar[ActionType]
    AT_DOWNLOAD_AUDIT_LOG: _ClassVar[ActionType]
    AT_COPY_AUDIT_LOG: _ClassVar[ActionType]
    AT_ALTER_JOB: _ClassVar[ActionType]
    AT_TERMINATE_JOB: _ClassVar[ActionType]
    AT_READ_METADATA: _ClassVar[ActionType]
    AT_CREATE_SHARE: _ClassVar[ActionType]
    AT_ALTER_SHARE: _ClassVar[ActionType]
    AT_DROP_SHARE: _ClassVar[ActionType]
    AT_CREATE_CONNECTION: _ClassVar[ActionType]
    AT_ALTER_CONNECTION: _ClassVar[ActionType]
    AT_DROP_CONNECTION: _ClassVar[ActionType]
    AT_CREATE_LOCATION: _ClassVar[ActionType]
    AT_ALTER_LOCATION: _ClassVar[ActionType]
    AT_DROP_LOCATION: _ClassVar[ActionType]
    AT_USE_LOCATION: _ClassVar[ActionType]
    AT_CREATE_WORKSPACE: _ClassVar[ActionType]
    AT_ALTER_WORKSPACE: _ClassVar[ActionType]
    AT_DROP_WORKSPACE: _ClassVar[ActionType]
    AT_CREATE_TABLE_STREAM: _ClassVar[ActionType]
    AT_DROP_TABLE_STREAM: _ClassVar[ActionType]
    AT_SELECT_TABLE_STREAM: _ClassVar[ActionType]
    AT_ALTER_TABLE_STREAM: _ClassVar[ActionType]
    AT_CREATE_INDEX: _ClassVar[ActionType]
    AT_DROP_INDEX: _ClassVar[ActionType]

class EffectType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ALLOW: _ClassVar[EffectType]
    DENY: _ClassVar[EffectType]

class EffectMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DENY_OVERRIDE: _ClassVar[EffectMode]
    ALLOW_OVERRIDE: _ClassVar[EffectMode]
SystemAdmin: SystemRole
UserAdmin: SystemRole
SecurityAdmin: SystemRole
AuditAdmin: SystemRole
AT_KNOWN: ActionType
AT_ALL: ActionType
AT_CREATE_ALL: ActionType
AT_ALTER_ALL: ActionType
AT_UPDATE_ALL: ActionType
AT_SELECT_ALL: ActionType
AT_DROP_ALL: ActionType
AT_ALL_FIN: ActionType
AT_CREATE_ROLE: ActionType
AT_ALTER_ROLE: ActionType
AT_DROP_ROLE: ActionType
AT_GRANT_PRIVILEGE: ActionType
AT_REVOKE_PRIVILEGE: ActionType
AT_SHOW_PRIVILEGE: ActionType
AT_CREATE_VCLUSTER: ActionType
AT_ALTER_VCLUSTER: ActionType
AT_DROP_VCLUSTER: ActionType
AT_USE_VCLUSTER: ActionType
AT_CREATE_SCHEMA: ActionType
AT_ALTER_SCHEMA: ActionType
AT_DROP_SCHEMA: ActionType
AT_CREATE_TABLE: ActionType
AT_ALTER_TABLE: ActionType
AT_DROP_TABLE: ActionType
AT_SELECT_TABLE: ActionType
AT_INSERT_TABLE: ActionType
AT_TRUNCATE_TABLE: ActionType
AT_UPDATE_TABLE: ActionType
AT_DELETE_TABLE: ActionType
AT_CREATE_VIEW: ActionType
AT_DROP_VIEW: ActionType
AT_SELECT_VIEW: ActionType
AT_ALTER_VIEW: ActionType
AT_CREATE_MATERIALIZED_VIEW: ActionType
AT_DROP_MATERIALIZED_VIEW: ActionType
AT_SELECT_MATERIALIZED_VIEW: ActionType
AT_ALTER_MATERIALIZED_VIEW: ActionType
AT_CREATE_FUNCTION: ActionType
AT_DROP_FUNCTION: ActionType
AT_USE_FUNCTION: ActionType
AT_ALTER_FUNCTION: ActionType
AT_CREATE_DATALAKE: ActionType
AT_ALTER_DATALAKE: ActionType
AT_DROP_DATALAKE: ActionType
AT_CREATE_SCHEDULE_TASK: ActionType
AT_ALTER_SCHEDULE_TASK: ActionType
AT_DROP_SCHEDULE_TASK: ActionType
AT_CLONE_SCHEDULE_TASK: ActionType
AT_CREATE_USER: ActionType
AT_DROP_USER: ActionType
AT_ALTER_USER: ActionType
AT_READ_AUDIT_LOG: ActionType
AT_DOWNLOAD_AUDIT_LOG: ActionType
AT_COPY_AUDIT_LOG: ActionType
AT_ALTER_JOB: ActionType
AT_TERMINATE_JOB: ActionType
AT_READ_METADATA: ActionType
AT_CREATE_SHARE: ActionType
AT_ALTER_SHARE: ActionType
AT_DROP_SHARE: ActionType
AT_CREATE_CONNECTION: ActionType
AT_ALTER_CONNECTION: ActionType
AT_DROP_CONNECTION: ActionType
AT_CREATE_LOCATION: ActionType
AT_ALTER_LOCATION: ActionType
AT_DROP_LOCATION: ActionType
AT_USE_LOCATION: ActionType
AT_CREATE_WORKSPACE: ActionType
AT_ALTER_WORKSPACE: ActionType
AT_DROP_WORKSPACE: ActionType
AT_CREATE_TABLE_STREAM: ActionType
AT_DROP_TABLE_STREAM: ActionType
AT_SELECT_TABLE_STREAM: ActionType
AT_ALTER_TABLE_STREAM: ActionType
AT_CREATE_INDEX: ActionType
AT_DROP_INDEX: ActionType
ALLOW: EffectType
DENY: EffectType
DENY_OVERRIDE: EffectMode
ALLOW_OVERRIDE: EffectMode

class AccessToken(_message.Message):
    __slots__ = ('expire_time', 'user_id', 'access_policy')
    EXPIRE_TIME_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ACCESS_POLICY_FIELD_NUMBER: _ClassVar[int]
    expire_time: int
    user_id: int
    access_policy: _account_pb2.Policy

    def __init__(self, expire_time: _Optional[int]=..., user_id: _Optional[int]=..., access_policy: _Optional[_Union[_account_pb2.Policy, _Mapping]]=...) -> None:
        ...

class CheckPrivileges(_message.Message):
    __slots__ = ('principal', 'access_token', 'content')

    class Content(_message.Message):
        __slots__ = ('mode', 'action', 'with_grant_option', 'object', 'granted_type', 'sub_object_type')
        MODE_FIELD_NUMBER: _ClassVar[int]
        ACTION_FIELD_NUMBER: _ClassVar[int]
        WITH_GRANT_OPTION_FIELD_NUMBER: _ClassVar[int]
        OBJECT_FIELD_NUMBER: _ClassVar[int]
        GRANTED_TYPE_FIELD_NUMBER: _ClassVar[int]
        SUB_OBJECT_TYPE_FIELD_NUMBER: _ClassVar[int]
        mode: EffectMode
        action: _containers.RepeatedScalarFieldContainer[ActionType]
        with_grant_option: bool
        object: _object_identifier_pb2.ObjectIdentifier
        granted_type: GrantedType.Type
        sub_object_type: _object_identifier_pb2.ObjectType

        def __init__(self, mode: _Optional[_Union[EffectMode, str]]=..., action: _Optional[_Iterable[_Union[ActionType, str]]]=..., with_grant_option: bool=..., object: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., granted_type: _Optional[_Union[GrantedType.Type, str]]=..., sub_object_type: _Optional[_Union[_object_identifier_pb2.ObjectType, str]]=...) -> None:
            ...
    PRINCIPAL_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    principal: _account_pb2.UserIdentifier
    access_token: str
    content: _containers.RepeatedCompositeFieldContainer[CheckPrivileges.Content]

    def __init__(self, principal: _Optional[_Union[_account_pb2.UserIdentifier, _Mapping]]=..., access_token: _Optional[str]=..., content: _Optional[_Iterable[_Union[CheckPrivileges.Content, _Mapping]]]=...) -> None:
        ...

class Subject(_message.Message):
    __slots__ = ('identifier', 'user_id')
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier
    user_id: int

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., user_id: _Optional[int]=...) -> None:
        ...

class GrantEntity(_message.Message):
    __slots__ = ('subject', 'role', 'privilege')
    SUBJECT_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    PRIVILEGE_FIELD_NUMBER: _ClassVar[int]
    subject: Subject
    role: GrantRole
    privilege: GrantPrivilege

    def __init__(self, subject: _Optional[_Union[Subject, _Mapping]]=..., role: _Optional[_Union[GrantRole, _Mapping]]=..., privilege: _Optional[_Union[GrantPrivilege, _Mapping]]=...) -> None:
        ...

class GrantRole(_message.Message):
    __slots__ = ('identifier', 'authorization_time_ms')
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    AUTHORIZATION_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier
    authorization_time_ms: int

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., authorization_time_ms: _Optional[int]=...) -> None:
        ...

class GrantPrivilege(_message.Message):
    __slots__ = ('content',)
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    content: PrivilegeContent

    def __init__(self, content: _Optional[_Union[PrivilegeContent, _Mapping]]=...) -> None:
        ...

class RevokeEntity(_message.Message):
    __slots__ = ('subject', 'role', 'privilege')
    SUBJECT_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    PRIVILEGE_FIELD_NUMBER: _ClassVar[int]
    subject: Subject
    role: RevokeRole
    privilege: RevokePrivilege

    def __init__(self, subject: _Optional[_Union[Subject, _Mapping]]=..., role: _Optional[_Union[RevokeRole, _Mapping]]=..., privilege: _Optional[_Union[RevokePrivilege, _Mapping]]=...) -> None:
        ...

class RevokeRole(_message.Message):
    __slots__ = ('identifier', 'authorization_time_ms')
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    AUTHORIZATION_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier
    authorization_time_ms: int

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., authorization_time_ms: _Optional[int]=...) -> None:
        ...

class RevokePrivilege(_message.Message):
    __slots__ = ('content',)
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    content: PrivilegeContent

    def __init__(self, content: _Optional[_Union[PrivilegeContent, _Mapping]]=...) -> None:
        ...

class PrivilegeContent(_message.Message):
    __slots__ = ('action', 'object', 'granted_type', 'with_grant_option', 'sub_object_type')
    ACTION_FIELD_NUMBER: _ClassVar[int]
    OBJECT_FIELD_NUMBER: _ClassVar[int]
    GRANTED_TYPE_FIELD_NUMBER: _ClassVar[int]
    WITH_GRANT_OPTION_FIELD_NUMBER: _ClassVar[int]
    SUB_OBJECT_TYPE_FIELD_NUMBER: _ClassVar[int]
    action: _containers.RepeatedScalarFieldContainer[ActionType]
    object: _object_identifier_pb2.ObjectIdentifier
    granted_type: GrantedType.Type
    with_grant_option: bool
    sub_object_type: _object_identifier_pb2.ObjectType

    def __init__(self, action: _Optional[_Iterable[_Union[ActionType, str]]]=..., object: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., granted_type: _Optional[_Union[GrantedType.Type, str]]=..., with_grant_option: bool=..., sub_object_type: _Optional[_Union[_object_identifier_pb2.ObjectType, str]]=...) -> None:
        ...

class GrantedType(_message.Message):
    __slots__ = ()

    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        PRIVILEGE: _ClassVar[GrantedType.Type]
        POLICY: _ClassVar[GrantedType.Type]
        ROLE: _ClassVar[GrantedType.Type]
        OBJECT_CREATOR: _ClassVar[GrantedType.Type]
        OBJECT_HIERARCHY: _ClassVar[GrantedType.Type]
    PRIVILEGE: GrantedType.Type
    POLICY: GrantedType.Type
    ROLE: GrantedType.Type
    OBJECT_CREATOR: GrantedType.Type
    OBJECT_HIERARCHY: GrantedType.Type

    def __init__(self) -> None:
        ...

class PrivilegeAction(_message.Message):
    __slots__ = ('action', 'policy_name', 'role')
    ACTION_FIELD_NUMBER: _ClassVar[int]
    POLICY_NAME_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    action: ActionType
    policy_name: str
    role: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, action: _Optional[_Union[ActionType, str]]=..., policy_name: _Optional[str]=..., role: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class PrivilegeCondition(_message.Message):
    __slots__ = ('conditions',)
    CONDITIONS_FIELD_NUMBER: _ClassVar[int]
    conditions: _containers.RepeatedScalarFieldContainer[str]

    def __init__(self, conditions: _Optional[_Iterable[str]]=...) -> None:
        ...

class Privilege(_message.Message):
    __slots__ = ('granted_type', 'privilege', 'conditions', 'granted_on', 'grantee', 'grantor', 'grant_option', 'granted_time_ms', 'table_type', 'sub_object_type')
    GRANTED_TYPE_FIELD_NUMBER: _ClassVar[int]
    PRIVILEGE_FIELD_NUMBER: _ClassVar[int]
    CONDITIONS_FIELD_NUMBER: _ClassVar[int]
    GRANTED_ON_FIELD_NUMBER: _ClassVar[int]
    GRANTEE_FIELD_NUMBER: _ClassVar[int]
    GRANTOR_FIELD_NUMBER: _ClassVar[int]
    GRANT_OPTION_FIELD_NUMBER: _ClassVar[int]
    GRANTED_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    TABLE_TYPE_FIELD_NUMBER: _ClassVar[int]
    SUB_OBJECT_TYPE_FIELD_NUMBER: _ClassVar[int]
    granted_type: GrantedType.Type
    privilege: PrivilegeAction
    conditions: PrivilegeCondition
    granted_on: _object_identifier_pb2.ObjectIdentifier
    grantee: _object_identifier_pb2.ObjectIdentifier
    grantor: _object_identifier_pb2.ObjectIdentifier
    grant_option: bool
    granted_time_ms: int
    table_type: _table_common_pb2.TableType
    sub_object_type: _object_identifier_pb2.ObjectType

    def __init__(self, granted_type: _Optional[_Union[GrantedType.Type, str]]=..., privilege: _Optional[_Union[PrivilegeAction, _Mapping]]=..., conditions: _Optional[_Union[PrivilegeCondition, _Mapping]]=..., granted_on: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., grantee: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., grantor: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., grant_option: bool=..., granted_time_ms: _Optional[int]=..., table_type: _Optional[_Union[_table_common_pb2.TableType, str]]=..., sub_object_type: _Optional[_Union[_object_identifier_pb2.ObjectType, str]]=...) -> None:
        ...

class PrivilegeList(_message.Message):
    __slots__ = ('privileges',)
    PRIVILEGES_FIELD_NUMBER: _ClassVar[int]
    privileges: _containers.RepeatedCompositeFieldContainer[Privilege]

    def __init__(self, privileges: _Optional[_Iterable[_Union[Privilege, _Mapping]]]=...) -> None:
        ...

class UserRole(_message.Message):
    __slots__ = ('user', 'role', 'grantor', 'granted_time_ms')
    USER_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    GRANTOR_FIELD_NUMBER: _ClassVar[int]
    GRANTED_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    user: _account_pb2.UserIdentifier
    role: _object_identifier_pb2.ObjectIdentifier
    grantor: _object_identifier_pb2.ObjectIdentifier
    granted_time_ms: int

    def __init__(self, user: _Optional[_Union[_account_pb2.UserIdentifier, _Mapping]]=..., role: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., grantor: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., granted_time_ms: _Optional[int]=...) -> None:
        ...

class UserRoleList(_message.Message):
    __slots__ = ('user_roles',)
    USER_ROLES_FIELD_NUMBER: _ClassVar[int]
    user_roles: _containers.RepeatedCompositeFieldContainer[UserRole]

    def __init__(self, user_roles: _Optional[_Iterable[_Union[UserRole, _Mapping]]]=...) -> None:
        ...

class AccessTypeList(_message.Message):
    __slots__ = ('access_types',)
    ACCESS_TYPES_FIELD_NUMBER: _ClassVar[int]
    access_types: _containers.RepeatedScalarFieldContainer[str]

    def __init__(self, access_types: _Optional[_Iterable[str]]=...) -> None:
        ...