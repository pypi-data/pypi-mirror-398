import metadata_entity_pb2 as _metadata_entity_pb2
import account_pb2 as _account_pb2
import object_identifier_pb2 as _object_identifier_pb2
import privilege_pb2 as _privilege_pb2
import property_pb2 as _property_pb2
import job_meta_pb2 as _job_meta_pb2
import virtual_cluster_pb2 as _virtual_cluster_pb2
import virtual_cluster_management_pb2 as _virtual_cluster_management_pb2
import manifest_pb2 as _manifest_pb2
import table_common_pb2 as _table_common_pb2
import expression_pb2 as _expression_pb2
import table_meta_pb2 as _table_meta_pb2
import data_type_pb2 as _data_type_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class ColumnMoveType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    FIRST: _ClassVar[ColumnMoveType]
    BEFORE: _ClassVar[ColumnMoveType]
    AFTER: _ClassVar[ColumnMoveType]

class ShowEntityType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SHOW_ENTITY: _ClassVar[ShowEntityType]
    SHOW_NAME: _ClassVar[ShowEntityType]
    SHOW_ID: _ClassVar[ShowEntityType]
    SHOW_ENTITIES_HISTORY: _ClassVar[ShowEntityType]

class AccessType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    META: _ClassVar[AccessType]
    VC_MANAGER: _ClassVar[AccessType]
FIRST: ColumnMoveType
BEFORE: ColumnMoveType
AFTER: ColumnMoveType
SHOW_ENTITY: ShowEntityType
SHOW_NAME: ShowEntityType
SHOW_ID: ShowEntityType
SHOW_ENTITIES_HISTORY: ShowEntityType
META: AccessType
VC_MANAGER: AccessType

class CreateEntity(_message.Message):
    __slots__ = ('replace', 'if_not_exists', 'entity')
    REPLACE_FIELD_NUMBER: _ClassVar[int]
    IF_NOT_EXISTS_FIELD_NUMBER: _ClassVar[int]
    ENTITY_FIELD_NUMBER: _ClassVar[int]
    replace: bool
    if_not_exists: bool
    entity: _metadata_entity_pb2.Entity

    def __init__(self, replace: bool=..., if_not_exists: bool=..., entity: _Optional[_Union[_metadata_entity_pb2.Entity, _Mapping]]=...) -> None:
        ...

class AlterEntity(_message.Message):
    __slots__ = ('if_exists', 'identifier', 'change_comment', 'entity', 'role', 'job', 'virtual_cluster', 'vcluster', 'share', 'connection', 'function', 'user', 'table')
    IF_EXISTS_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    CHANGE_COMMENT_FIELD_NUMBER: _ClassVar[int]
    ENTITY_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    JOB_FIELD_NUMBER: _ClassVar[int]
    VIRTUAL_CLUSTER_FIELD_NUMBER: _ClassVar[int]
    VCLUSTER_FIELD_NUMBER: _ClassVar[int]
    SHARE_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    if_exists: bool
    identifier: _object_identifier_pb2.ObjectIdentifier
    change_comment: bool
    entity: _metadata_entity_pb2.Entity
    role: AlterRole
    job: AlterJob
    virtual_cluster: AlterVirtualCluster
    vcluster: AlterVCluster
    share: AlterShare
    connection: AlterConnection
    function: AlterFunction
    user: AlterUser
    table: AlterTable

    def __init__(self, if_exists: bool=..., identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., change_comment: bool=..., entity: _Optional[_Union[_metadata_entity_pb2.Entity, _Mapping]]=..., role: _Optional[_Union[AlterRole, _Mapping]]=..., job: _Optional[_Union[AlterJob, _Mapping]]=..., virtual_cluster: _Optional[_Union[AlterVirtualCluster, _Mapping]]=..., vcluster: _Optional[_Union[AlterVCluster, _Mapping]]=..., share: _Optional[_Union[AlterShare, _Mapping]]=..., connection: _Optional[_Union[AlterConnection, _Mapping]]=..., function: _Optional[_Union[AlterFunction, _Mapping]]=..., user: _Optional[_Union[AlterUser, _Mapping]]=..., table: _Optional[_Union[AlterTable, _Mapping]]=...) -> None:
        ...

class ColumnMove(_message.Message):
    __slots__ = ('type', 'column_name', 'reference_column_name', 'ancestors')
    TYPE_FIELD_NUMBER: _ClassVar[int]
    COLUMN_NAME_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_COLUMN_NAME_FIELD_NUMBER: _ClassVar[int]
    ANCESTORS_FIELD_NUMBER: _ClassVar[int]
    type: ColumnMoveType
    column_name: str
    reference_column_name: str
    ancestors: _containers.RepeatedScalarFieldContainer[str]

    def __init__(self, type: _Optional[_Union[ColumnMoveType, str]]=..., column_name: _Optional[str]=..., reference_column_name: _Optional[str]=..., ancestors: _Optional[_Iterable[str]]=...) -> None:
        ...

class AlterTable(_message.Message):
    __slots__ = ('updates',)
    UPDATES_FIELD_NUMBER: _ClassVar[int]
    updates: _containers.RepeatedCompositeFieldContainer[TableChange]

    def __init__(self, updates: _Optional[_Iterable[_Union[TableChange, _Mapping]]]=...) -> None:
        ...

class TableChange(_message.Message):
    __slots__ = ('column_add', 'column_drop', 'move', 'column_change', 'data_source_add', 'data_source_drop', 'data_source_change')
    COLUMN_ADD_FIELD_NUMBER: _ClassVar[int]
    COLUMN_DROP_FIELD_NUMBER: _ClassVar[int]
    MOVE_FIELD_NUMBER: _ClassVar[int]
    COLUMN_CHANGE_FIELD_NUMBER: _ClassVar[int]
    DATA_SOURCE_ADD_FIELD_NUMBER: _ClassVar[int]
    DATA_SOURCE_DROP_FIELD_NUMBER: _ClassVar[int]
    DATA_SOURCE_CHANGE_FIELD_NUMBER: _ClassVar[int]
    column_add: ColumnAdd
    column_drop: ColumnDrop
    move: ColumnMove
    column_change: ColumnChange
    data_source_add: DataSourceAdd
    data_source_drop: DataSourceDrop
    data_source_change: DataSourceChange

    def __init__(self, column_add: _Optional[_Union[ColumnAdd, _Mapping]]=..., column_drop: _Optional[_Union[ColumnDrop, _Mapping]]=..., move: _Optional[_Union[ColumnMove, _Mapping]]=..., column_change: _Optional[_Union[ColumnChange, _Mapping]]=..., data_source_add: _Optional[_Union[DataSourceAdd, _Mapping]]=..., data_source_drop: _Optional[_Union[DataSourceDrop, _Mapping]]=..., data_source_change: _Optional[_Union[DataSourceChange, _Mapping]]=...) -> None:
        ...

class DataSourceAdd(_message.Message):
    __slots__ = ('infos',)
    INFOS_FIELD_NUMBER: _ClassVar[int]
    infos: _containers.RepeatedCompositeFieldContainer[_table_common_pb2.DataSourceInfo]

    def __init__(self, infos: _Optional[_Iterable[_Union[_table_common_pb2.DataSourceInfo, _Mapping]]]=...) -> None:
        ...

class DataSourceChange(_message.Message):
    __slots__ = ('data_source_id', 'new_options', 'drop_options')
    DATA_SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    NEW_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    DROP_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    data_source_id: int
    new_options: _property_pb2.Properties
    drop_options: _property_pb2.PropertyKeyList

    def __init__(self, data_source_id: _Optional[int]=..., new_options: _Optional[_Union[_property_pb2.Properties, _Mapping]]=..., drop_options: _Optional[_Union[_property_pb2.PropertyKeyList, _Mapping]]=...) -> None:
        ...

class DataSourceDrop(_message.Message):
    __slots__ = ('data_source_ids',)
    DATA_SOURCE_IDS_FIELD_NUMBER: _ClassVar[int]
    data_source_ids: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, data_source_ids: _Optional[_Iterable[int]]=...) -> None:
        ...

class StructField(_message.Message):
    __slots__ = ('ancestors', 'field')
    ANCESTORS_FIELD_NUMBER: _ClassVar[int]
    FIELD_FIELD_NUMBER: _ClassVar[int]
    ancestors: _containers.RepeatedScalarFieldContainer[str]
    field: _data_type_pb2.StructTypeInfo.Field

    def __init__(self, ancestors: _Optional[_Iterable[str]]=..., field: _Optional[_Union[_data_type_pb2.StructTypeInfo.Field, _Mapping]]=...) -> None:
        ...

class ColumnAdd(_message.Message):
    __slots__ = ('column', 'struct_field', 'if_not_exists')
    COLUMN_FIELD_NUMBER: _ClassVar[int]
    STRUCT_FIELD_FIELD_NUMBER: _ClassVar[int]
    IF_NOT_EXISTS_FIELD_NUMBER: _ClassVar[int]
    column: _table_common_pb2.FieldSchema
    struct_field: StructField
    if_not_exists: bool

    def __init__(self, column: _Optional[_Union[_table_common_pb2.FieldSchema, _Mapping]]=..., struct_field: _Optional[_Union[StructField, _Mapping]]=..., if_not_exists: bool=...) -> None:
        ...

class ColumnDrop(_message.Message):
    __slots__ = ('ancestors', 'name', 'if_exists')
    ANCESTORS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    IF_EXISTS_FIELD_NUMBER: _ClassVar[int]
    ancestors: _containers.RepeatedScalarFieldContainer[str]
    name: str
    if_exists: bool

    def __init__(self, ancestors: _Optional[_Iterable[str]]=..., name: _Optional[str]=..., if_exists: bool=...) -> None:
        ...

class ColumnChange(_message.Message):
    __slots__ = ('ancestors', 'name', 'new_name', 'new_type', 'new_comment')
    ANCESTORS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    NEW_NAME_FIELD_NUMBER: _ClassVar[int]
    NEW_TYPE_FIELD_NUMBER: _ClassVar[int]
    NEW_COMMENT_FIELD_NUMBER: _ClassVar[int]
    ancestors: _containers.RepeatedScalarFieldContainer[str]
    name: str
    new_name: str
    new_type: _data_type_pb2.DataType
    new_comment: str

    def __init__(self, ancestors: _Optional[_Iterable[str]]=..., name: _Optional[str]=..., new_name: _Optional[str]=..., new_type: _Optional[_Union[_data_type_pb2.DataType, _Mapping]]=..., new_comment: _Optional[str]=...) -> None:
        ...

class AlterVirtualCluster(_message.Message):
    __slots__ = ('start', 'stop', 'abort_all_jobs', 'terminate', 'if_stopped', 'force')
    START_FIELD_NUMBER: _ClassVar[int]
    STOP_FIELD_NUMBER: _ClassVar[int]
    ABORT_ALL_JOBS_FIELD_NUMBER: _ClassVar[int]
    TERMINATE_FIELD_NUMBER: _ClassVar[int]
    IF_STOPPED_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    start: bool
    stop: bool
    abort_all_jobs: bool
    terminate: bool
    if_stopped: bool
    force: bool

    def __init__(self, start: bool=..., stop: bool=..., abort_all_jobs: bool=..., terminate: bool=..., if_stopped: bool=..., force: bool=...) -> None:
        ...

class AlterShare(_message.Message):
    __slots__ = ('public', 'add_instance', 'remove_instance', 'instances')
    PUBLIC_FIELD_NUMBER: _ClassVar[int]
    ADD_INSTANCE_FIELD_NUMBER: _ClassVar[int]
    REMOVE_INSTANCE_FIELD_NUMBER: _ClassVar[int]
    INSTANCES_FIELD_NUMBER: _ClassVar[int]
    public: bool
    add_instance: bool
    remove_instance: bool
    instances: _containers.RepeatedScalarFieldContainer[str]

    def __init__(self, public: bool=..., add_instance: bool=..., remove_instance: bool=..., instances: _Optional[_Iterable[str]]=...) -> None:
        ...

class AlterConnectionAvailability(_message.Message):
    __slots__ = ('enable',)
    ENABLE_FIELD_NUMBER: _ClassVar[int]
    enable: bool

    def __init__(self, enable: bool=...) -> None:
        ...

class AlterConnectionProperties(_message.Message):
    __slots__ = ('set', 'properties')
    SET_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    set: bool
    properties: _containers.RepeatedCompositeFieldContainer[_property_pb2.Property]

    def __init__(self, set: bool=..., properties: _Optional[_Iterable[_Union[_property_pb2.Property, _Mapping]]]=...) -> None:
        ...

class AlterConnection(_message.Message):
    __slots__ = ('enable', 'availability', 'properties')
    ENABLE_FIELD_NUMBER: _ClassVar[int]
    AVAILABILITY_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    enable: bool
    availability: AlterConnectionAvailability
    properties: AlterConnectionProperties

    def __init__(self, enable: bool=..., availability: _Optional[_Union[AlterConnectionAvailability, _Mapping]]=..., properties: _Optional[_Union[AlterConnectionProperties, _Mapping]]=...) -> None:
        ...

class AlterFunction(_message.Message):
    __slots__ = ('comment',)
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    comment: str

    def __init__(self, comment: _Optional[str]=...) -> None:
        ...

class DropEntity(_message.Message):
    __slots__ = ('identifier', 'if_exists', 'drop_time_ms', 'table', 'view', 'mv', 'schema', 'catalog', 'user', 'role', 'virtual_cluster', 'share', 'function', 'connection', 'location', 'stream_table', 'index', 'volume')
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    IF_EXISTS_FIELD_NUMBER: _ClassVar[int]
    DROP_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    VIEW_FIELD_NUMBER: _ClassVar[int]
    MV_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    CATALOG_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    VIRTUAL_CLUSTER_FIELD_NUMBER: _ClassVar[int]
    SHARE_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    STREAM_TABLE_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier
    if_exists: bool
    drop_time_ms: int
    table: DropTable
    view: DropView
    mv: DropMaterializedView
    schema: DropSchema
    catalog: DropCatalog
    user: DropUser
    role: DropRole
    virtual_cluster: DropVCluster
    share: DropShare
    function: DropFunction
    connection: DropConnection
    location: DropLocation
    stream_table: DropStreamTable
    index: DropIndex
    volume: DropVolume

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., if_exists: bool=..., drop_time_ms: _Optional[int]=..., table: _Optional[_Union[DropTable, _Mapping]]=..., view: _Optional[_Union[DropView, _Mapping]]=..., mv: _Optional[_Union[DropMaterializedView, _Mapping]]=..., schema: _Optional[_Union[DropSchema, _Mapping]]=..., catalog: _Optional[_Union[DropCatalog, _Mapping]]=..., user: _Optional[_Union[DropUser, _Mapping]]=..., role: _Optional[_Union[DropRole, _Mapping]]=..., virtual_cluster: _Optional[_Union[DropVCluster, _Mapping]]=..., share: _Optional[_Union[DropShare, _Mapping]]=..., function: _Optional[_Union[DropFunction, _Mapping]]=..., connection: _Optional[_Union[DropConnection, _Mapping]]=..., location: _Optional[_Union[DropLocation, _Mapping]]=..., stream_table: _Optional[_Union[DropStreamTable, _Mapping]]=..., index: _Optional[_Union[DropIndex, _Mapping]]=..., volume: _Optional[_Union[DropVolume, _Mapping]]=...) -> None:
        ...

class DropTable(_message.Message):
    __slots__ = ('purge',)
    PURGE_FIELD_NUMBER: _ClassVar[int]
    purge: bool

    def __init__(self, purge: bool=...) -> None:
        ...

class DropStreamTable(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class DropSchema(_message.Message):
    __slots__ = ('cascade',)
    CASCADE_FIELD_NUMBER: _ClassVar[int]
    cascade: bool

    def __init__(self, cascade: bool=...) -> None:
        ...

class DropShare(_message.Message):
    __slots__ = ('cascade',)
    CASCADE_FIELD_NUMBER: _ClassVar[int]
    cascade: bool

    def __init__(self, cascade: bool=...) -> None:
        ...

class DropCatalog(_message.Message):
    __slots__ = ('cascade',)
    CASCADE_FIELD_NUMBER: _ClassVar[int]
    cascade: bool

    def __init__(self, cascade: bool=...) -> None:
        ...

class DropView(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class DropMaterializedView(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class DropUser(_message.Message):
    __slots__ = ('user_id',)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: int

    def __init__(self, user_id: _Optional[int]=...) -> None:
        ...

class DropRole(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class DropVCluster(_message.Message):
    __slots__ = ('workspace_id', 'vc_id', 'force')
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    workspace_id: int
    vc_id: int
    force: bool

    def __init__(self, workspace_id: _Optional[int]=..., vc_id: _Optional[int]=..., force: bool=...) -> None:
        ...

class DropFunction(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class DropConnection(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class DropLocation(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class DropIndex(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class DropVolume(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class UndropEntity(_message.Message):
    __slots__ = ('identifier',)
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class AlterRole(_message.Message):
    __slots__ = ('comment', 'alias', 'new_name', 'properties')
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    ALIAS_FIELD_NUMBER: _ClassVar[int]
    NEW_NAME_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    comment: str
    alias: str
    new_name: str
    properties: _containers.RepeatedCompositeFieldContainer[_property_pb2.Property]

    def __init__(self, comment: _Optional[str]=..., alias: _Optional[str]=..., new_name: _Optional[str]=..., properties: _Optional[_Iterable[_Union[_property_pb2.Property, _Mapping]]]=...) -> None:
        ...

class AlterJob(_message.Message):
    __slots__ = ('history', 'status', 'end_time', 'result', 'summary', 'cancel')
    HISTORY_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    CANCEL_FIELD_NUMBER: _ClassVar[int]
    history: _job_meta_pb2.JobHistory
    status: _job_meta_pb2.JobStatus
    end_time: int
    result: str
    summary: _job_meta_pb2.JobSummaryLocation
    cancel: bool

    def __init__(self, history: _Optional[_Union[_job_meta_pb2.JobHistory, _Mapping]]=..., status: _Optional[_Union[_job_meta_pb2.JobStatus, str]]=..., end_time: _Optional[int]=..., result: _Optional[str]=..., summary: _Optional[_Union[_job_meta_pb2.JobSummaryLocation, _Mapping]]=..., cancel: bool=...) -> None:
        ...

class AlterVCluster(_message.Message):
    __slots__ = ('vc_id', 'workspace_id', 'properties', 'state', 'unset_tags')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    UNSET_TAGS_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    workspace_id: int
    properties: _virtual_cluster_pb2.VirtualClusterProperties
    state: _virtual_cluster_management_pb2.VirtualClusterStateInfo
    unset_tags: _containers.RepeatedScalarFieldContainer[str]

    def __init__(self, vc_id: _Optional[int]=..., workspace_id: _Optional[int]=..., properties: _Optional[_Union[_virtual_cluster_pb2.VirtualClusterProperties, _Mapping]]=..., state: _Optional[_Union[_virtual_cluster_management_pb2.VirtualClusterStateInfo, _Mapping]]=..., unset_tags: _Optional[_Iterable[str]]=...) -> None:
        ...

class AlterUser(_message.Message):
    __slots__ = ('user_id', 'default_vc', 'default_schema')
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_VC_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    user_id: int
    default_vc: str
    default_schema: str

    def __init__(self, user_id: _Optional[int]=..., default_vc: _Optional[str]=..., default_schema: _Optional[str]=...) -> None:
        ...

class TruncateEntity(_message.Message):
    __slots__ = ('table',)
    TABLE_FIELD_NUMBER: _ClassVar[int]
    table: TruncateTable

    def __init__(self, table: _Optional[_Union[TruncateTable, _Mapping]]=...) -> None:
        ...

class TruncateTable(_message.Message):
    __slots__ = ('identifier', 'manifest')
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    MANIFEST_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier
    manifest: _manifest_pb2.Manifest

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., manifest: _Optional[_Union[_manifest_pb2.Manifest, _Mapping]]=...) -> None:
        ...

class ShowEntity(_message.Message):
    __slots__ = ('offset', 'limit', 'type', 'user', 'role', 'privilege', 'table', 'schema', 'job', 'vcluster', 'workspace', 'file', 'mv', 'vcluster_spec', 'share', 'function', 'connection', 'user_role', 'access_type', 'storage_location', 'index', 'volume')
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    PRIVILEGE_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    JOB_FIELD_NUMBER: _ClassVar[int]
    VCLUSTER_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    FILE_FIELD_NUMBER: _ClassVar[int]
    MV_FIELD_NUMBER: _ClassVar[int]
    VCLUSTER_SPEC_FIELD_NUMBER: _ClassVar[int]
    SHARE_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_FIELD_NUMBER: _ClassVar[int]
    USER_ROLE_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TYPE_FIELD_NUMBER: _ClassVar[int]
    STORAGE_LOCATION_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    offset: int
    limit: int
    type: ShowEntityType
    user: ShowUser
    role: ShowRole
    privilege: ShowPrivilege
    table: ShowTable
    schema: ShowSchema
    job: ShowJob
    vcluster: ShowVCluster
    workspace: ShowWorkspace
    file: ShowFile
    mv: ShowMV
    vcluster_spec: ShowVirtualClusterSizeSpecs
    share: ShowShare
    function: ShowFunction
    connection: ShowConnection
    user_role: ShowUserRole
    access_type: ShowAccessType
    storage_location: ShowStorageLocation
    index: ShowIndex
    volume: ShowVolume

    def __init__(self, offset: _Optional[int]=..., limit: _Optional[int]=..., type: _Optional[_Union[ShowEntityType, str]]=..., user: _Optional[_Union[ShowUser, _Mapping]]=..., role: _Optional[_Union[ShowRole, _Mapping]]=..., privilege: _Optional[_Union[ShowPrivilege, _Mapping]]=..., table: _Optional[_Union[ShowTable, _Mapping]]=..., schema: _Optional[_Union[ShowSchema, _Mapping]]=..., job: _Optional[_Union[ShowJob, _Mapping]]=..., vcluster: _Optional[_Union[ShowVCluster, _Mapping]]=..., workspace: _Optional[_Union[ShowWorkspace, _Mapping]]=..., file: _Optional[_Union[ShowFile, _Mapping]]=..., mv: _Optional[_Union[ShowMV, _Mapping]]=..., vcluster_spec: _Optional[_Union[ShowVirtualClusterSizeSpecs, _Mapping]]=..., share: _Optional[_Union[ShowShare, _Mapping]]=..., function: _Optional[_Union[ShowFunction, _Mapping]]=..., connection: _Optional[_Union[ShowConnection, _Mapping]]=..., user_role: _Optional[_Union[ShowUserRole, _Mapping]]=..., access_type: _Optional[_Union[ShowAccessType, _Mapping]]=..., storage_location: _Optional[_Union[ShowStorageLocation, _Mapping]]=..., index: _Optional[_Union[ShowIndex, _Mapping]]=..., volume: _Optional[_Union[ShowVolume, _Mapping]]=...) -> None:
        ...

class ShowVirtualClusterSizeSpecs(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class ShowWorkspace(_message.Message):
    __slots__ = ('instance_id',)
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    instance_id: int

    def __init__(self, instance_id: _Optional[int]=...) -> None:
        ...

class ShowUser(_message.Message):
    __slots__ = ('workspace_id',)
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    workspace_id: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, workspace_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class ShowRole(_message.Message):
    __slots__ = ('workspace_id',)
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    workspace_id: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, workspace_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class ShowGroupPrivilege(_message.Message):
    __slots__ = ('identifier',)
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class ShowUserPrivilege(_message.Message):
    __slots__ = ('identifier',)
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    identifier: _account_pb2.UserIdentifier

    def __init__(self, identifier: _Optional[_Union[_account_pb2.UserIdentifier, _Mapping]]=...) -> None:
        ...

class ShowObjectPrivilege(_message.Message):
    __slots__ = ('identifier', 'subject')
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    SUBJECT_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier
    subject: _privilege_pb2.Subject

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., subject: _Optional[_Union[_privilege_pb2.Subject, _Mapping]]=...) -> None:
        ...

class ShowPrivilege(_message.Message):
    __slots__ = ('user', 'group', 'object')
    USER_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    OBJECT_FIELD_NUMBER: _ClassVar[int]
    user: ShowUserPrivilege
    group: ShowGroupPrivilege
    object: ShowObjectPrivilege

    def __init__(self, user: _Optional[_Union[ShowUserPrivilege, _Mapping]]=..., group: _Optional[_Union[ShowGroupPrivilege, _Mapping]]=..., object: _Optional[_Union[ShowObjectPrivilege, _Mapping]]=...) -> None:
        ...

class ShowTable(_message.Message):
    __slots__ = ('schema_id', 'timestamp', 'table_type', 'list_order_by', 'ascending', 'with_schema')

    class ListOrderby(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ORDER_BY_TABLE_NAME: _ClassVar[ShowTable.ListOrderby]
    ORDER_BY_TABLE_NAME: ShowTable.ListOrderby
    SCHEMA_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TABLE_TYPE_FIELD_NUMBER: _ClassVar[int]
    LIST_ORDER_BY_FIELD_NUMBER: _ClassVar[int]
    ASCENDING_FIELD_NUMBER: _ClassVar[int]
    WITH_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    schema_id: _object_identifier_pb2.ObjectIdentifier
    timestamp: int
    table_type: _table_common_pb2.TableType
    list_order_by: ShowTable.ListOrderby
    ascending: bool
    with_schema: bool

    def __init__(self, schema_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., timestamp: _Optional[int]=..., table_type: _Optional[_Union[_table_common_pb2.TableType, str]]=..., list_order_by: _Optional[_Union[ShowTable.ListOrderby, str]]=..., ascending: bool=..., with_schema: bool=...) -> None:
        ...

class ShowMV(_message.Message):
    __slots__ = ('mv_type', 'table', 'batch_tables')
    MV_TYPE_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    BATCH_TABLES_FIELD_NUMBER: _ClassVar[int]
    mv_type: str
    table: _object_identifier_pb2.ObjectIdentifier
    batch_tables: _object_identifier_pb2.ObjectIdentifierList

    def __init__(self, mv_type: _Optional[str]=..., table: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., batch_tables: _Optional[_Union[_object_identifier_pb2.ObjectIdentifierList, _Mapping]]=...) -> None:
        ...

class ShowSchema(_message.Message):
    __slots__ = ('workspace_id',)
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    workspace_id: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, workspace_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class ShowJob(_message.Message):
    __slots__ = ('workspace_id',)
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    workspace_id: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, workspace_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class ShowVClusterFilter(_message.Message):
    __slots__ = ('pattern', 'where')
    PATTERN_FIELD_NUMBER: _ClassVar[int]
    WHERE_FIELD_NUMBER: _ClassVar[int]
    pattern: str
    where: _virtual_cluster_management_pb2.ListVirtualClusterFilter

    def __init__(self, pattern: _Optional[str]=..., where: _Optional[_Union[_virtual_cluster_management_pb2.ListVirtualClusterFilter, _Mapping]]=...) -> None:
        ...

class ShowVCluster(_message.Message):
    __slots__ = ('workspace_id', 'filter')
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    workspace_id: _object_identifier_pb2.ObjectIdentifier
    filter: ShowVClusterFilter

    def __init__(self, workspace_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., filter: _Optional[_Union[ShowVClusterFilter, _Mapping]]=...) -> None:
        ...

class ShowFile(_message.Message):
    __slots__ = ('table', 'table_partitions')
    TABLE_FIELD_NUMBER: _ClassVar[int]
    TABLE_PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    table: _object_identifier_pb2.ObjectIdentifier
    table_partitions: TablePartitions

    def __init__(self, table: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., table_partitions: _Optional[_Union[TablePartitions, _Mapping]]=...) -> None:
        ...

class ShowStorageLocation(_message.Message):
    __slots__ = ('workspace_id',)
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    workspace_id: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, workspace_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class ShowVolume(_message.Message):
    __slots__ = ('schema_id',)
    SCHEMA_ID_FIELD_NUMBER: _ClassVar[int]
    schema_id: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, schema_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class TablePartitions(_message.Message):
    __slots__ = ('table', 'partitions')
    TABLE_FIELD_NUMBER: _ClassVar[int]
    PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    table: _object_identifier_pb2.ObjectIdentifier
    partitions: _containers.RepeatedCompositeFieldContainer[PartitionConstant]

    def __init__(self, table: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., partitions: _Optional[_Iterable[_Union[PartitionConstant, _Mapping]]]=...) -> None:
        ...

class PartitionConstant(_message.Message):
    __slots__ = ('partition_fields',)
    PARTITION_FIELDS_FIELD_NUMBER: _ClassVar[int]
    partition_fields: _containers.RepeatedCompositeFieldContainer[PartitionFieldConstant]

    def __init__(self, partition_fields: _Optional[_Iterable[_Union[PartitionFieldConstant, _Mapping]]]=...) -> None:
        ...

class PartitionFieldConstant(_message.Message):
    __slots__ = ('field_name', 'value')
    FIELD_NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    field_name: str
    value: _expression_pb2.ScalarExpression

    def __init__(self, field_name: _Optional[str]=..., value: _Optional[_Union[_expression_pb2.ScalarExpression, _Mapping]]=...) -> None:
        ...

class ShowShare(_message.Message):
    __slots__ = ('instance_id',)
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    instance_id: int

    def __init__(self, instance_id: _Optional[int]=...) -> None:
        ...

class ShowFunction(_message.Message):
    __slots__ = ('schema_id',)
    SCHEMA_ID_FIELD_NUMBER: _ClassVar[int]
    schema_id: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, schema_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class ShowConnection(_message.Message):
    __slots__ = ('workspace_id',)
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    workspace_id: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, workspace_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class ShowUserRole(_message.Message):
    __slots__ = ('workspace_id', 'user', 'role')
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    workspace_id: _object_identifier_pb2.ObjectIdentifier
    user: _account_pb2.UserIdentifier
    role: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, workspace_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., user: _Optional[_Union[_account_pb2.UserIdentifier, _Mapping]]=..., role: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class ShowAccessType(_message.Message):
    __slots__ = ('service', 'entity_type')
    SERVICE_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    service: str
    entity_type: _object_identifier_pb2.ObjectType

    def __init__(self, service: _Optional[str]=..., entity_type: _Optional[_Union[_object_identifier_pb2.ObjectType, str]]=...) -> None:
        ...

class ShowIndex(_message.Message):
    __slots__ = ('table_id',)
    TABLE_ID_FIELD_NUMBER: _ClassVar[int]
    table_id: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, table_id: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class GetEntity(_message.Message):
    __slots__ = ('identifier', 'user', 'vc', 'workspace', 'table')
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    VC_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier
    user: GetUser
    vc: GetVirtualCluster
    workspace: GetWorkspace
    table: GetTable

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., user: _Optional[_Union[GetUser, _Mapping]]=..., vc: _Optional[_Union[GetVirtualCluster, _Mapping]]=..., workspace: _Optional[_Union[GetWorkspace, _Mapping]]=..., table: _Optional[_Union[GetTable, _Mapping]]=...) -> None:
        ...

class GetUser(_message.Message):
    __slots__ = ('user_id',)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: int

    def __init__(self, user_id: _Optional[int]=...) -> None:
        ...

class GetVirtualCluster(_message.Message):
    __slots__ = ('workspace_id', 'vc_id')
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    workspace_id: int
    vc_id: int

    def __init__(self, workspace_id: _Optional[int]=..., vc_id: _Optional[int]=...) -> None:
        ...

class GetWorkspace(_message.Message):
    __slots__ = ('workspace_id',)
    WORKSPACE_ID_FIELD_NUMBER: _ClassVar[int]
    workspace_id: int

    def __init__(self, workspace_id: _Optional[int]=...) -> None:
        ...

class GetTable(_message.Message):
    __slots__ = ('for_read',)
    FOR_READ_FIELD_NUMBER: _ClassVar[int]
    for_read: bool

    def __init__(self, for_read: bool=...) -> None:
        ...

class GetEntityStats(_message.Message):
    __slots__ = ('identifier',)
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=...) -> None:
        ...

class BatchGetEntityStats(_message.Message):
    __slots__ = ('parent', 'entity_type', 'entity_name')
    PARENT_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    ENTITY_NAME_FIELD_NUMBER: _ClassVar[int]
    parent: _object_identifier_pb2.ObjectIdentifier
    entity_type: _object_identifier_pb2.ObjectType
    entity_name: _containers.RepeatedScalarFieldContainer[str]

    def __init__(self, parent: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., entity_type: _Optional[_Union[_object_identifier_pb2.ObjectType, str]]=..., entity_name: _Optional[_Iterable[str]]=...) -> None:
        ...

class BatchGetEntity(_message.Message):
    __slots__ = ('parent', 'entity_type', 'entity_name', 'user', 'table')
    PARENT_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    ENTITY_NAME_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    parent: _object_identifier_pb2.ObjectIdentifier
    entity_type: _object_identifier_pb2.ObjectType
    entity_name: _containers.RepeatedScalarFieldContainer[str]
    user: BatchGetUser
    table: BatchGetTable

    def __init__(self, parent: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., entity_type: _Optional[_Union[_object_identifier_pb2.ObjectType, str]]=..., entity_name: _Optional[_Iterable[str]]=..., user: _Optional[_Union[BatchGetUser, _Mapping]]=..., table: _Optional[_Union[BatchGetTable, _Mapping]]=...) -> None:
        ...

class BatchGetUser(_message.Message):
    __slots__ = ('user_id',)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, user_id: _Optional[_Iterable[int]]=...) -> None:
        ...

class BatchGetTable(_message.Message):
    __slots__ = ('for_read',)
    FOR_READ_FIELD_NUMBER: _ClassVar[int]
    for_read: bool

    def __init__(self, for_read: bool=...) -> None:
        ...

class DDL(_message.Message):
    __slots__ = ('create_entity', 'drop_entity', 'alter_entity', 'truncate_entity', 'undrop_entity')
    CREATE_ENTITY_FIELD_NUMBER: _ClassVar[int]
    DROP_ENTITY_FIELD_NUMBER: _ClassVar[int]
    ALTER_ENTITY_FIELD_NUMBER: _ClassVar[int]
    TRUNCATE_ENTITY_FIELD_NUMBER: _ClassVar[int]
    UNDROP_ENTITY_FIELD_NUMBER: _ClassVar[int]
    create_entity: CreateEntity
    drop_entity: DropEntity
    alter_entity: AlterEntity
    truncate_entity: TruncateEntity
    undrop_entity: UndropEntity

    def __init__(self, create_entity: _Optional[_Union[CreateEntity, _Mapping]]=..., drop_entity: _Optional[_Union[DropEntity, _Mapping]]=..., alter_entity: _Optional[_Union[AlterEntity, _Mapping]]=..., truncate_entity: _Optional[_Union[TruncateEntity, _Mapping]]=..., undrop_entity: _Optional[_Union[UndropEntity, _Mapping]]=...) -> None:
        ...

class DCL(_message.Message):
    __slots__ = ('grant', 'revoke', 'check')
    GRANT_FIELD_NUMBER: _ClassVar[int]
    REVOKE_FIELD_NUMBER: _ClassVar[int]
    CHECK_FIELD_NUMBER: _ClassVar[int]
    grant: _privilege_pb2.GrantEntity
    revoke: _privilege_pb2.RevokeEntity
    check: _privilege_pb2.CheckPrivileges

    def __init__(self, grant: _Optional[_Union[_privilege_pb2.GrantEntity, _Mapping]]=..., revoke: _Optional[_Union[_privilege_pb2.RevokeEntity, _Mapping]]=..., check: _Optional[_Union[_privilege_pb2.CheckPrivileges, _Mapping]]=...) -> None:
        ...

class DQL(_message.Message):
    __slots__ = ('show_entity', 'get_entity', 'get_entity_stats', 'batch_get_entity', 'batch_get_entity_stats')
    SHOW_ENTITY_FIELD_NUMBER: _ClassVar[int]
    GET_ENTITY_FIELD_NUMBER: _ClassVar[int]
    GET_ENTITY_STATS_FIELD_NUMBER: _ClassVar[int]
    BATCH_GET_ENTITY_FIELD_NUMBER: _ClassVar[int]
    BATCH_GET_ENTITY_STATS_FIELD_NUMBER: _ClassVar[int]
    show_entity: ShowEntity
    get_entity: GetEntity
    get_entity_stats: GetEntityStats
    batch_get_entity: BatchGetEntity
    batch_get_entity_stats: BatchGetEntityStats

    def __init__(self, show_entity: _Optional[_Union[ShowEntity, _Mapping]]=..., get_entity: _Optional[_Union[GetEntity, _Mapping]]=..., get_entity_stats: _Optional[_Union[GetEntityStats, _Mapping]]=..., batch_get_entity: _Optional[_Union[BatchGetEntity, _Mapping]]=..., batch_get_entity_stats: _Optional[_Union[BatchGetEntityStats, _Mapping]]=...) -> None:
        ...

class AppendTable(_message.Message):
    __slots__ = ('manifest',)
    MANIFEST_FIELD_NUMBER: _ClassVar[int]
    manifest: _manifest_pb2.Manifest

    def __init__(self, manifest: _Optional[_Union[_manifest_pb2.Manifest, _Mapping]]=...) -> None:
        ...

class AppendEntity(_message.Message):
    __slots__ = ('identifier', 'append_table')
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    APPEND_TABLE_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier
    append_table: AppendTable

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., append_table: _Optional[_Union[AppendTable, _Mapping]]=...) -> None:
        ...

class RewriteTable(_message.Message):
    __slots__ = ('manifest',)
    MANIFEST_FIELD_NUMBER: _ClassVar[int]
    manifest: _manifest_pb2.Manifest

    def __init__(self, manifest: _Optional[_Union[_manifest_pb2.Manifest, _Mapping]]=...) -> None:
        ...

class RewriteEntity(_message.Message):
    __slots__ = ('identifier', 'rewrite_table')
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    REWRITE_TABLE_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier
    rewrite_table: RewriteTable

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., rewrite_table: _Optional[_Union[RewriteTable, _Mapping]]=...) -> None:
        ...

class OverwriteTable(_message.Message):
    __slots__ = ('manifest',)
    MANIFEST_FIELD_NUMBER: _ClassVar[int]
    manifest: _manifest_pb2.Manifest

    def __init__(self, manifest: _Optional[_Union[_manifest_pb2.Manifest, _Mapping]]=...) -> None:
        ...

class OverwriteEntity(_message.Message):
    __slots__ = ('identifier', 'overwrite_table')
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    OVERWRITE_TABLE_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier
    overwrite_table: OverwriteTable

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., overwrite_table: _Optional[_Union[OverwriteTable, _Mapping]]=...) -> None:
        ...

class DML(_message.Message):
    __slots__ = ('append_entity', 'overwrite_entity', 'rewrite_entity')
    APPEND_ENTITY_FIELD_NUMBER: _ClassVar[int]
    OVERWRITE_ENTITY_FIELD_NUMBER: _ClassVar[int]
    REWRITE_ENTITY_FIELD_NUMBER: _ClassVar[int]
    append_entity: AppendEntity
    overwrite_entity: OverwriteEntity
    rewrite_entity: RewriteEntity

    def __init__(self, append_entity: _Optional[_Union[AppendEntity, _Mapping]]=..., overwrite_entity: _Optional[_Union[OverwriteEntity, _Mapping]]=..., rewrite_entity: _Optional[_Union[RewriteEntity, _Mapping]]=...) -> None:
        ...

class AccessStatement(_message.Message):
    __slots__ = ('operator', 'type', 'ddl', 'dcl', 'dql', 'dml', 'in_transaction')
    OPERATOR_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    DDL_FIELD_NUMBER: _ClassVar[int]
    DCL_FIELD_NUMBER: _ClassVar[int]
    DQL_FIELD_NUMBER: _ClassVar[int]
    DML_FIELD_NUMBER: _ClassVar[int]
    IN_TRANSACTION_FIELD_NUMBER: _ClassVar[int]
    operator: _account_pb2.UserIdentifier
    type: AccessType
    ddl: DDL
    dcl: DCL
    dql: DQL
    dml: DML
    in_transaction: bool

    def __init__(self, operator: _Optional[_Union[_account_pb2.UserIdentifier, _Mapping]]=..., type: _Optional[_Union[AccessType, str]]=..., ddl: _Optional[_Union[DDL, _Mapping]]=..., dcl: _Optional[_Union[DCL, _Mapping]]=..., dql: _Optional[_Union[DQL, _Mapping]]=..., dml: _Optional[_Union[DML, _Mapping]]=..., in_transaction: bool=...) -> None:
        ...