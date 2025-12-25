import object_identifier_pb2 as _object_identifier_pb2
import workspace_meta_pb2 as _workspace_meta_pb2
import schema_pb2 as _schema_pb2
import table_common_pb2 as _table_common_pb2
import table_meta_pb2 as _table_meta_pb2
import account_pb2 as _account_pb2
import role_meta_pb2 as _role_meta_pb2
import job_meta_pb2 as _job_meta_pb2
import property_pb2 as _property_pb2
import virtual_cluster_meta_pb2 as _virtual_cluster_meta_pb2
import file_meta_data_pb2 as _file_meta_data_pb2
import rm_app_meta_pb2 as _rm_app_meta_pb2
import virtual_cluster_size_pb2 as _virtual_cluster_size_pb2
import share_meta_pb2 as _share_meta_pb2
import function_meta_pb2 as _function_meta_pb2
import connection_meta_pb2 as _connection_meta_pb2
import network_policy_pb2 as _network_policy_pb2
import storage_location_pb2 as _storage_location_pb2
import partition_meta_pb2 as _partition_meta_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class Entity(_message.Message):
    __slots__ = ('identifier', 'creator', 'creator_type', 'comment', 'properties', 'create_time', 'last_modify_time', 'state', 'category', 'workspace', 'schema', 'table', 'user', 'role', 'job', 'virtual_cluster', 'file', 'virtual_cluster_size_spec', 'share', 'function', 'connection', 'network_policy', 'index', 'location', 'partition')

    class Category(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        MANAGED: _ClassVar[Entity.Category]
        EXTERNAL: _ClassVar[Entity.Category]
        SHARED: _ClassVar[Entity.Category]
    MANAGED: Entity.Category
    EXTERNAL: Entity.Category
    SHARED: Entity.Category
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    CREATOR_FIELD_NUMBER: _ClassVar[int]
    CREATOR_TYPE_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    CREATE_TIME_FIELD_NUMBER: _ClassVar[int]
    LAST_MODIFY_TIME_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    JOB_FIELD_NUMBER: _ClassVar[int]
    VIRTUAL_CLUSTER_FIELD_NUMBER: _ClassVar[int]
    FILE_FIELD_NUMBER: _ClassVar[int]
    VIRTUAL_CLUSTER_SIZE_SPEC_FIELD_NUMBER: _ClassVar[int]
    SHARE_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_FIELD_NUMBER: _ClassVar[int]
    NETWORK_POLICY_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    identifier: _object_identifier_pb2.ObjectIdentifier
    creator: int
    creator_type: _object_identifier_pb2.PrincipalType
    comment: str
    properties: _containers.RepeatedCompositeFieldContainer[_property_pb2.Property]
    create_time: int
    last_modify_time: int
    state: _object_identifier_pb2.ObjectState.Type
    category: Entity.Category
    workspace: _workspace_meta_pb2.Workspace
    schema: _schema_pb2.Schema
    table: _table_meta_pb2.TableMeta
    user: _account_pb2.User
    role: _role_meta_pb2.Role
    job: _job_meta_pb2.JobMeta
    virtual_cluster: _virtual_cluster_meta_pb2.VirtualClusterMeta
    file: _file_meta_data_pb2.FileMetaData
    virtual_cluster_size_spec: _virtual_cluster_size_pb2.VirtualClusterSizeSpec
    share: _share_meta_pb2.Share
    function: _function_meta_pb2.Function
    connection: _connection_meta_pb2.Connection
    network_policy: _network_policy_pb2.NetworkPolicy
    index: _table_common_pb2.Index
    location: _storage_location_pb2.StorageLocation
    partition: _partition_meta_pb2.Partition

    def __init__(self, identifier: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., creator: _Optional[int]=..., creator_type: _Optional[_Union[_object_identifier_pb2.PrincipalType, str]]=..., comment: _Optional[str]=..., properties: _Optional[_Iterable[_Union[_property_pb2.Property, _Mapping]]]=..., create_time: _Optional[int]=..., last_modify_time: _Optional[int]=..., state: _Optional[_Union[_object_identifier_pb2.ObjectState.Type, str]]=..., category: _Optional[_Union[Entity.Category, str]]=..., workspace: _Optional[_Union[_workspace_meta_pb2.Workspace, _Mapping]]=..., schema: _Optional[_Union[_schema_pb2.Schema, _Mapping]]=..., table: _Optional[_Union[_table_meta_pb2.TableMeta, _Mapping]]=..., user: _Optional[_Union[_account_pb2.User, _Mapping]]=..., role: _Optional[_Union[_role_meta_pb2.Role, _Mapping]]=..., job: _Optional[_Union[_job_meta_pb2.JobMeta, _Mapping]]=..., virtual_cluster: _Optional[_Union[_virtual_cluster_meta_pb2.VirtualClusterMeta, _Mapping]]=..., file: _Optional[_Union[_file_meta_data_pb2.FileMetaData, _Mapping]]=..., virtual_cluster_size_spec: _Optional[_Union[_virtual_cluster_size_pb2.VirtualClusterSizeSpec, _Mapping]]=..., share: _Optional[_Union[_share_meta_pb2.Share, _Mapping]]=..., function: _Optional[_Union[_function_meta_pb2.Function, _Mapping]]=..., connection: _Optional[_Union[_connection_meta_pb2.Connection, _Mapping]]=..., network_policy: _Optional[_Union[_network_policy_pb2.NetworkPolicy, _Mapping]]=..., index: _Optional[_Union[_table_common_pb2.Index, _Mapping]]=..., location: _Optional[_Union[_storage_location_pb2.StorageLocation, _Mapping]]=..., partition: _Optional[_Union[_partition_meta_pb2.Partition, _Mapping]]=...) -> None:
        ...

class EntityList(_message.Message):
    __slots__ = ('entities',)
    ENTITIES_FIELD_NUMBER: _ClassVar[int]
    entities: _containers.RepeatedCompositeFieldContainer[Entity]

    def __init__(self, entities: _Optional[_Iterable[_Union[Entity, _Mapping]]]=...) -> None:
        ...