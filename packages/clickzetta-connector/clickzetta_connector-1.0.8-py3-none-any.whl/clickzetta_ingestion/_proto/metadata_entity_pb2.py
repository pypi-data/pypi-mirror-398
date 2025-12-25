"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'metadata_entity.proto')
_sym_db = _symbol_database.Default()
from . import object_identifier_pb2 as object__identifier__pb2
from . import workspace_meta_pb2 as workspace__meta__pb2
from . import schema_pb2 as schema__pb2
from . import table_common_pb2 as table__common__pb2
from . import table_meta_pb2 as table__meta__pb2
from . import account_pb2 as account__pb2
from . import role_meta_pb2 as role__meta__pb2
from . import job_meta_pb2 as job__meta__pb2
from . import property_pb2 as property__pb2
from . import virtual_cluster_meta_pb2 as virtual__cluster__meta__pb2
from . import file_meta_data_pb2 as file__meta__data__pb2
from . import rm_app_meta_pb2 as rm__app__meta__pb2
from . import virtual_cluster_size_pb2 as virtual__cluster__size__pb2
from . import share_meta_pb2 as share__meta__pb2
from . import function_meta_pb2 as function__meta__pb2
from . import connection_meta_pb2 as connection__meta__pb2
from . import network_policy_pb2 as network__policy__pb2
from . import storage_location_pb2 as storage__location__pb2
from . import partition_meta_pb2 as partition__meta__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x15metadata_entity.proto\x12\x08cz.proto\x1a\x17object_identifier.proto\x1a\x14workspace_meta.proto\x1a\x0cschema.proto\x1a\x12table_common.proto\x1a\x10table_meta.proto\x1a\raccount.proto\x1a\x0frole_meta.proto\x1a\x0ejob_meta.proto\x1a\x0eproperty.proto\x1a\x1avirtual_cluster_meta.proto\x1a\x14file_meta_data.proto\x1a\x11rm_app_meta.proto\x1a\x1avirtual_cluster_size.proto\x1a\x10share_meta.proto\x1a\x13function_meta.proto\x1a\x15connection_meta.proto\x1a\x14network_policy.proto\x1a\x16storage_location.proto\x1a\x14partition_meta.proto"\xc5\x08\n\x06Entity\x123\n\nidentifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifierH\x01\x88\x01\x01\x12\x0f\n\x07creator\x18\x02 \x01(\x03\x12-\n\x0ccreator_type\x18\x03 \x01(\x0e2\x17.cz.proto.PrincipalType\x12\x14\n\x07comment\x18\x04 \x01(\tH\x02\x88\x01\x01\x12&\n\nproperties\x18\x05 \x03(\x0b2\x12.cz.proto.Property\x12\x13\n\x0bcreate_time\x18\x06 \x01(\x03\x12\x18\n\x10last_modify_time\x18\x07 \x01(\x03\x12)\n\x05state\x18\x08 \x01(\x0e2\x1a.cz.proto.ObjectState.Type\x12+\n\x08category\x18\t \x01(\x0e2\x19.cz.proto.Entity.Category\x12(\n\tworkspace\x18\n \x01(\x0b2\x13.cz.proto.WorkspaceH\x00\x12"\n\x06schema\x18\x0b \x01(\x0b2\x10.cz.proto.SchemaH\x00\x12$\n\x05table\x18\x0c \x01(\x0b2\x13.cz.proto.TableMetaH\x00\x12\x1e\n\x04user\x18\r \x01(\x0b2\x0e.cz.proto.UserH\x00\x12\x1e\n\x04role\x18\x0e \x01(\x0b2\x0e.cz.proto.RoleH\x00\x12 \n\x03job\x18\x0f \x01(\x0b2\x11.cz.proto.JobMetaH\x00\x127\n\x0fvirtual_cluster\x18\x10 \x01(\x0b2\x1c.cz.proto.VirtualClusterMetaH\x00\x12&\n\x04file\x18\x11 \x01(\x0b2\x16.cz.proto.FileMetaDataH\x00\x12N\n\x19virtual_cluster_size_spec\x18\x12 \x01(\x0b2).com.clickzetta.rm.VirtualClusterSizeSpecH\x00\x12 \n\x05share\x18\x13 \x01(\x0b2\x0f.cz.proto.ShareH\x00\x12&\n\x08function\x18\x14 \x01(\x0b2\x12.cz.proto.FunctionH\x00\x12*\n\nconnection\x18\x15 \x01(\x0b2\x14.cz.proto.ConnectionH\x00\x121\n\x0enetwork_policy\x18\x16 \x01(\x0b2\x17.cz.proto.NetworkPolicyH\x00\x12 \n\x05index\x18\x17 \x01(\x0b2\x0f.cz.proto.IndexH\x00\x12-\n\x08location\x18\x18 \x01(\x0b2\x19.cz.proto.StorageLocationH\x00\x12(\n\tpartition\x18\x19 \x01(\x0b2\x13.cz.proto.PartitionH\x00"1\n\x08Category\x12\x0b\n\x07MANAGED\x10\x00\x12\x0c\n\x08EXTERNAL\x10\x01\x12\n\n\x06SHARED\x10\x02B\x08\n\x06entityB\r\n\x0b_identifierB\n\n\x08_comment"0\n\nEntityList\x12"\n\x08entities\x18\x01 \x03(\x0b2\x10.cz.proto.Entityb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'metadata_entity_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_ENTITY']._serialized_start = 426
    _globals['_ENTITY']._serialized_end = 1519
    _globals['_ENTITY_CATEGORY']._serialized_start = 1433
    _globals['_ENTITY_CATEGORY']._serialized_end = 1482
    _globals['_ENTITYLIST']._serialized_start = 1521
    _globals['_ENTITYLIST']._serialized_end = 1569