"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'ddl.proto')
_sym_db = _symbol_database.Default()
from . import metadata_entity_pb2 as metadata__entity__pb2
from . import account_pb2 as account__pb2
from . import object_identifier_pb2 as object__identifier__pb2
from . import privilege_pb2 as privilege__pb2
from . import property_pb2 as property__pb2
from . import job_meta_pb2 as job__meta__pb2
from . import virtual_cluster_pb2 as virtual__cluster__pb2
from . import virtual_cluster_management_pb2 as virtual__cluster__management__pb2
from . import manifest_pb2 as manifest__pb2
from . import table_common_pb2 as table__common__pb2
from . import expression_pb2 as expression__pb2
from . import table_meta_pb2 as table__meta__pb2
from . import data_type_pb2 as data__type__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\tddl.proto\x12\x0fcz.proto.access\x1a\x15metadata_entity.proto\x1a\raccount.proto\x1a\x17object_identifier.proto\x1a\x0fprivilege.proto\x1a\x0eproperty.proto\x1a\x0ejob_meta.proto\x1a\x15virtual_cluster.proto\x1a virtual_cluster_management.proto\x1a\x0emanifest.proto\x1a\x12table_common.proto\x1a\x10expression.proto\x1a\x10table_meta.proto\x1a\x0fdata_type.proto"d\n\x0cCreateEntity\x12\x11\n\x07replace\x18\x01 \x01(\x08H\x00\x12\x17\n\rif_not_exists\x18\x02 \x01(\x08H\x00\x12 \n\x06entity\x18\x03 \x01(\x0b2\x10.cz.proto.EntityB\x06\n\x04mode"\xd4\x04\n\x0bAlterEntity\x12\x11\n\tif_exists\x18\x01 \x01(\x08\x12.\n\nidentifier\x18\x02 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12\x16\n\x0echange_comment\x18\x03 \x01(\x08\x12 \n\x06entity\x18\x04 \x01(\x0b2\x10.cz.proto.Entity\x12*\n\x04role\x18\n \x01(\x0b2\x1a.cz.proto.access.AlterRoleH\x00\x12(\n\x03job\x18\x0b \x01(\x0b2\x19.cz.proto.access.AlterJobH\x00\x12?\n\x0fvirtual_cluster\x18\x0c \x01(\x0b2$.cz.proto.access.AlterVirtualClusterH\x00\x122\n\x08vcluster\x18\r \x01(\x0b2\x1e.cz.proto.access.AlterVClusterH\x00\x12,\n\x05share\x18\x0e \x01(\x0b2\x1b.cz.proto.access.AlterShareH\x00\x126\n\nconnection\x18\x0f \x01(\x0b2 .cz.proto.access.AlterConnectionH\x00\x122\n\x08function\x18\x10 \x01(\x0b2\x1e.cz.proto.access.AlterFunctionH\x00\x12*\n\x04user\x18\x11 \x01(\x0b2\x1a.cz.proto.access.AlterUserH\x00\x12,\n\x05table\x18\x12 \x01(\x0b2\x1b.cz.proto.access.AlterTableH\x00B\t\n\x07derived"\xa1\x01\n\nColumnMove\x12-\n\x04type\x18\x01 \x01(\x0e2\x1f.cz.proto.access.ColumnMoveType\x12\x13\n\x0bcolumn_name\x18\x02 \x01(\t\x12"\n\x15reference_column_name\x18\x03 \x01(\tH\x00\x88\x01\x01\x12\x11\n\tancestors\x18\x04 \x03(\tB\x18\n\x16_reference_column_name";\n\nAlterTable\x12-\n\x07updates\x18\x01 \x03(\x0b2\x1c.cz.proto.access.TableChange"\x9b\x03\n\x0bTableChange\x120\n\ncolumn_add\x18\x01 \x01(\x0b2\x1a.cz.proto.access.ColumnAddH\x00\x122\n\x0bcolumn_drop\x18\x03 \x01(\x0b2\x1b.cz.proto.access.ColumnDropH\x00\x12+\n\x04move\x18\x02 \x01(\x0b2\x1b.cz.proto.access.ColumnMoveH\x00\x126\n\rcolumn_change\x18\x04 \x01(\x0b2\x1d.cz.proto.access.ColumnChangeH\x00\x129\n\x0fdata_source_add\x18\x05 \x01(\x0b2\x1e.cz.proto.access.DataSourceAddH\x00\x12;\n\x10data_source_drop\x18\x06 \x01(\x0b2\x1f.cz.proto.access.DataSourceDropH\x00\x12?\n\x12data_source_change\x18\x07 \x01(\x0b2!.cz.proto.access.DataSourceChangeH\x00B\x08\n\x06update"8\n\rDataSourceAdd\x12\'\n\x05infos\x18\x01 \x03(\x0b2\x18.cz.proto.DataSourceInfo"\x94\x01\n\x10DataSourceChange\x12\x16\n\x0edata_source_id\x18\x01 \x01(\r\x12+\n\x0bnew_options\x18\n \x01(\x0b2\x14.cz.proto.PropertiesH\x00\x121\n\x0cdrop_options\x18\x0b \x01(\x0b2\x19.cz.proto.PropertyKeyListH\x00B\x08\n\x06change")\n\x0eDataSourceDrop\x12\x17\n\x0fdata_source_ids\x18\x01 \x03(\r"O\n\x0bStructField\x12\x11\n\tancestors\x18\x01 \x03(\t\x12-\n\x05field\x18\x02 \x01(\x0b2\x1e.cz.proto.StructTypeInfo.Field"\x88\x01\n\tColumnAdd\x12\'\n\x06column\x18\x01 \x01(\x0b2\x15.cz.proto.FieldSchemaH\x00\x124\n\x0cstruct_field\x18\x02 \x01(\x0b2\x1c.cz.proto.access.StructFieldH\x00\x12\x15\n\rif_not_exists\x18\x0b \x01(\x08B\x05\n\x03add"@\n\nColumnDrop\x12\x11\n\tancestors\x18\x01 \x03(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x11\n\tif_exists\x18\x0b \x01(\x08"\x8c\x01\n\x0cColumnChange\x12\x11\n\tancestors\x18\x01 \x03(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x12\n\x08new_name\x18\x03 \x01(\tH\x00\x12&\n\x08new_type\x18\x04 \x01(\x0b2\x12.cz.proto.DataTypeH\x00\x12\x15\n\x0bnew_comment\x18\x05 \x01(\tH\x00B\x08\n\x06change"\xa2\x01\n\x13AlterVirtualCluster\x12\x0f\n\x05start\x18\x01 \x01(\x08H\x00\x12\x0e\n\x04stop\x18\x02 \x01(\x08H\x00\x12\x18\n\x0eabort_all_jobs\x18\x03 \x01(\x08H\x00\x12\x13\n\tterminate\x18\x06 \x01(\x08H\x00\x12\x14\n\nif_stopped\x18\x04 \x01(\x08H\x01\x12\x0f\n\x05force\x18\x05 \x01(\x08H\x01B\t\n\x07derivedB\t\n\x07options"o\n\nAlterShare\x12\x10\n\x06public\x18\x01 \x01(\x08H\x00\x12\x16\n\x0cadd_instance\x18\x02 \x01(\x08H\x00\x12\x19\n\x0fremove_instance\x18\x03 \x01(\x08H\x00\x12\x11\n\tinstances\x18\n \x03(\tB\t\n\x07derived"-\n\x1bAlterConnectionAvailability\x12\x0e\n\x06enable\x18\x01 \x01(\x08"P\n\x19AlterConnectionProperties\x12\x0b\n\x03set\x18\x01 \x01(\x08\x12&\n\nproperties\x18\x02 \x03(\x0b2\x12.cz.proto.Property"\xb6\x01\n\x0fAlterConnection\x12\x10\n\x06enable\x18\x01 \x01(\x08H\x00\x12D\n\x0cavailability\x18\x02 \x01(\x0b2,.cz.proto.access.AlterConnectionAvailabilityH\x00\x12@\n\nproperties\x18\x03 \x01(\x0b2*.cz.proto.access.AlterConnectionPropertiesH\x00B\t\n\x07derived"-\n\rAlterFunction\x12\x11\n\x07comment\x18\x01 \x01(\tH\x00B\t\n\x07derived"\xcd\x06\n\nDropEntity\x12.\n\nidentifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12\x11\n\tif_exists\x18\x02 \x01(\x08\x12\x14\n\x0cdrop_time_ms\x18\x03 \x01(\x03\x12+\n\x05table\x18\n \x01(\x0b2\x1a.cz.proto.access.DropTableH\x00\x12)\n\x04view\x18\x0b \x01(\x0b2\x19.cz.proto.access.DropViewH\x00\x123\n\x02mv\x18\x0c \x01(\x0b2%.cz.proto.access.DropMaterializedViewH\x00\x12-\n\x06schema\x18\r \x01(\x0b2\x1b.cz.proto.access.DropSchemaH\x00\x12/\n\x07catalog\x18\x0e \x01(\x0b2\x1c.cz.proto.access.DropCatalogH\x00\x12)\n\x04user\x18\x0f \x01(\x0b2\x19.cz.proto.access.DropUserH\x00\x12)\n\x04role\x18\x10 \x01(\x0b2\x19.cz.proto.access.DropRoleH\x00\x128\n\x0fvirtual_cluster\x18\x11 \x01(\x0b2\x1d.cz.proto.access.DropVClusterH\x00\x12+\n\x05share\x18\x12 \x01(\x0b2\x1a.cz.proto.access.DropShareH\x00\x121\n\x08function\x18\x13 \x01(\x0b2\x1d.cz.proto.access.DropFunctionH\x00\x125\n\nconnection\x18\x14 \x01(\x0b2\x1f.cz.proto.access.DropConnectionH\x00\x121\n\x08location\x18\x15 \x01(\x0b2\x1d.cz.proto.access.DropLocationH\x00\x128\n\x0cstream_table\x18\x16 \x01(\x0b2 .cz.proto.access.DropStreamTableH\x00\x12+\n\x05index\x18\x17 \x01(\x0b2\x1a.cz.proto.access.DropIndexH\x00\x12-\n\x06volume\x18\x18 \x01(\x0b2\x1b.cz.proto.access.DropVolumeH\x00B\t\n\x07derived"\x1a\n\tDropTable\x12\r\n\x05purge\x18\x01 \x01(\x08"\x11\n\x0fDropStreamTable"\x1d\n\nDropSchema\x12\x0f\n\x07cascade\x18\x01 \x01(\x08"\x1c\n\tDropShare\x12\x0f\n\x07cascade\x18\x01 \x01(\x08"\x1e\n\x0bDropCatalog\x12\x0f\n\x07cascade\x18\x01 \x01(\x08"\n\n\x08DropView"\x16\n\x14DropMaterializedView",\n\x08DropUser\x12\x14\n\x07user_id\x18\x01 \x01(\x03H\x00\x88\x01\x01B\n\n\x08_user_id"\n\n\x08DropRole"B\n\x0cDropVCluster\x12\x14\n\x0cworkspace_id\x18\x01 \x01(\x03\x12\r\n\x05vc_id\x18\x02 \x01(\x03\x12\r\n\x05force\x18\x03 \x01(\x08"\x0e\n\x0cDropFunction"\x10\n\x0eDropConnection"\x0e\n\x0cDropLocation"\x0b\n\tDropIndex"\x0c\n\nDropVolume">\n\x0cUndropEntity\x12.\n\nidentifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier"\x97\x01\n\tAlterRole\x12\x14\n\x07comment\x18\x02 \x01(\tH\x00\x88\x01\x01\x12\x12\n\x05alias\x18\x03 \x01(\tH\x01\x88\x01\x01\x12\x15\n\x08new_name\x18\x04 \x01(\tH\x02\x88\x01\x01\x12&\n\nproperties\x18\x05 \x03(\x0b2\x12.cz.proto.PropertyB\n\n\x08_commentB\x08\n\x06_aliasB\x0b\n\t_new_name"\xf9\x01\n\x08AlterJob\x12%\n\x07history\x18\x02 \x01(\x0b2\x14.cz.proto.JobHistory\x12(\n\x06status\x18\x03 \x01(\x0e2\x13.cz.proto.JobStatusH\x00\x88\x01\x01\x12\x15\n\x08end_time\x18\x04 \x01(\x03H\x01\x88\x01\x01\x12\x13\n\x06result\x18\x05 \x01(\tH\x02\x88\x01\x01\x12-\n\x07summary\x18\x06 \x01(\x0b2\x1c.cz.proto.JobSummaryLocation\x12\x13\n\x06cancel\x18\x07 \x01(\x08H\x03\x88\x01\x01B\t\n\x07_statusB\x0b\n\t_end_timeB\t\n\x07_resultB\t\n\x07_cancel"\x8c\x02\n\rAlterVCluster\x12\x12\n\x05vc_id\x18\x01 \x01(\x03H\x00\x88\x01\x01\x12\x19\n\x0cworkspace_id\x18\x02 \x01(\x03H\x01\x88\x01\x01\x12D\n\nproperties\x18\x03 \x01(\x0b2+.com.clickzetta.rm.VirtualClusterPropertiesH\x02\x88\x01\x01\x12>\n\x05state\x18\x04 \x01(\x0b2*.com.clickzetta.rm.VirtualClusterStateInfoH\x03\x88\x01\x01\x12\x12\n\nunset_tags\x18\x05 \x03(\tB\x08\n\x06_vc_idB\x0f\n\r_workspace_idB\r\n\x0b_propertiesB\x08\n\x06_state"\x85\x01\n\tAlterUser\x12\x14\n\x07user_id\x18\x01 \x01(\x03H\x00\x88\x01\x01\x12\x17\n\ndefault_vc\x18\x02 \x01(\tH\x01\x88\x01\x01\x12\x1b\n\x0edefault_schema\x18\x03 \x01(\tH\x02\x88\x01\x01B\n\n\x08_user_idB\r\n\x0b_default_vcB\x11\n\x0f_default_schema"L\n\x0eTruncateEntity\x12/\n\x05table\x18\n \x01(\x0b2\x1e.cz.proto.access.TruncateTableH\x00B\t\n\x07derived"e\n\rTruncateTable\x12.\n\nidentifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12$\n\x08manifest\x18\x02 \x01(\x0b2\x12.cz.proto.Manifest"\xb6\x08\n\nShowEntity\x12\x13\n\x06offset\x18\x01 \x01(\x03H\x01\x88\x01\x01\x12\x12\n\x05limit\x18\x02 \x01(\x05H\x02\x88\x01\x01\x12-\n\x04type\x18\x03 \x01(\x0e2\x1f.cz.proto.access.ShowEntityType\x12)\n\x04user\x18\n \x01(\x0b2\x19.cz.proto.access.ShowUserH\x00\x12)\n\x04role\x18\x0b \x01(\x0b2\x19.cz.proto.access.ShowRoleH\x00\x123\n\tprivilege\x18\x0c \x01(\x0b2\x1e.cz.proto.access.ShowPrivilegeH\x00\x12+\n\x05table\x18\r \x01(\x0b2\x1a.cz.proto.access.ShowTableH\x00\x12-\n\x06schema\x18\x0e \x01(\x0b2\x1b.cz.proto.access.ShowSchemaH\x00\x12\'\n\x03job\x18\x0f \x01(\x0b2\x18.cz.proto.access.ShowJobH\x00\x121\n\x08vcluster\x18\x10 \x01(\x0b2\x1d.cz.proto.access.ShowVClusterH\x00\x123\n\tworkspace\x18\x11 \x01(\x0b2\x1e.cz.proto.access.ShowWorkspaceH\x00\x12)\n\x04file\x18\x12 \x01(\x0b2\x19.cz.proto.access.ShowFileH\x00\x12%\n\x02mv\x18\x13 \x01(\x0b2\x17.cz.proto.access.ShowMVH\x00\x12E\n\rvcluster_spec\x18\x14 \x01(\x0b2,.cz.proto.access.ShowVirtualClusterSizeSpecsH\x00\x12+\n\x05share\x18\x15 \x01(\x0b2\x1a.cz.proto.access.ShowShareH\x00\x121\n\x08function\x18\x16 \x01(\x0b2\x1d.cz.proto.access.ShowFunctionH\x00\x125\n\nconnection\x18\x17 \x01(\x0b2\x1f.cz.proto.access.ShowConnectionH\x00\x122\n\tuser_role\x18\x18 \x01(\x0b2\x1d.cz.proto.access.ShowUserRoleH\x00\x126\n\x0baccess_type\x18\x19 \x01(\x0b2\x1f.cz.proto.access.ShowAccessTypeH\x00\x12@\n\x10storage_location\x18\x1a \x01(\x0b2$.cz.proto.access.ShowStorageLocationH\x00\x12+\n\x05index\x18\x1b \x01(\x0b2\x1a.cz.proto.access.ShowIndexH\x00\x12-\n\x06volume\x18\x1c \x01(\x0b2\x1b.cz.proto.access.ShowVolumeH\x00B\t\n\x07derivedB\t\n\x07_offsetB\x08\n\x06_limit"\x1d\n\x1bShowVirtualClusterSizeSpecs"$\n\rShowWorkspace\x12\x13\n\x0binstance_id\x18\x01 \x01(\x03"<\n\x08ShowUser\x120\n\x0cworkspace_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier"<\n\x08ShowRole\x120\n\x0cworkspace_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier"D\n\x12ShowGroupPrivilege\x12.\n\nidentifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier"A\n\x11ShowUserPrivilege\x12,\n\nidentifier\x18\x01 \x01(\x0b2\x18.cz.proto.UserIdentifier"p\n\x13ShowObjectPrivilege\x12.\n\nidentifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12)\n\x07subject\x18\x02 \x01(\x0b2\x18.cz.proto.access.Subject"\xbc\x01\n\rShowPrivilege\x122\n\x04user\x18\n \x01(\x0b2".cz.proto.access.ShowUserPrivilegeH\x00\x124\n\x05group\x18\x0b \x01(\x0b2#.cz.proto.access.ShowGroupPrivilegeH\x00\x126\n\x06object\x18\x0c \x01(\x0b2$.cz.proto.access.ShowObjectPrivilegeH\x00B\t\n\x07derived"\xeb\x02\n\tShowTable\x12-\n\tschema_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12\x16\n\ttimestamp\x18\x02 \x01(\x03H\x00\x88\x01\x01\x12,\n\ntable_type\x18\x03 \x01(\x0e2\x13.cz.proto.TableTypeH\x01\x88\x01\x01\x12B\n\rlist_order_by\x18\x04 \x01(\x0e2&.cz.proto.access.ShowTable.ListOrderbyH\x02\x88\x01\x01\x12\x16\n\tascending\x18\x05 \x01(\x08H\x03\x88\x01\x01\x12\x18\n\x0bwith_schema\x18\x06 \x01(\x08H\x04\x88\x01\x01"&\n\x0bListOrderby\x12\x17\n\x13ORDER_BY_TABLE_NAME\x10\x00B\x0c\n\n_timestampB\r\n\x0b_table_typeB\x10\n\x0e_list_order_byB\x0c\n\n_ascendingB\x0e\n\x0c_with_schema"\x9a\x01\n\x06ShowMV\x12\x14\n\x07mv_type\x18\x01 \x01(\tH\x01\x88\x01\x01\x12+\n\x05table\x18\n \x01(\x0b2\x1a.cz.proto.ObjectIdentifierH\x00\x126\n\x0cbatch_tables\x18\x0b \x01(\x0b2\x1e.cz.proto.ObjectIdentifierListH\x00B\t\n\x07derivedB\n\n\x08_mv_type">\n\nShowSchema\x120\n\x0cworkspace_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier";\n\x07ShowJob\x120\n\x0cworkspace_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier"o\n\x12ShowVClusterFilter\x12\x11\n\x07pattern\x18\x01 \x01(\tH\x00\x12<\n\x05where\x18\x02 \x01(\x0b2+.com.clickzetta.rm.ListVirtualClusterFilterH\x00B\x08\n\x06filter"\x85\x01\n\x0cShowVCluster\x120\n\x0cworkspace_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x128\n\x06filter\x18\x03 \x01(\x0b2#.cz.proto.access.ShowVClusterFilterH\x00\x88\x01\x01B\t\n\x07_filter"\x80\x01\n\x08ShowFile\x12+\n\x05table\x18\n \x01(\x0b2\x1a.cz.proto.ObjectIdentifierH\x00\x12<\n\x10table_partitions\x18\x0b \x01(\x0b2 .cz.proto.access.TablePartitionsH\x00B\t\n\x07derived"G\n\x13ShowStorageLocation\x120\n\x0cworkspace_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier";\n\nShowVolume\x12-\n\tschema_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier"t\n\x0fTablePartitions\x12)\n\x05table\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x126\n\npartitions\x18\x02 \x03(\x0b2".cz.proto.access.PartitionConstant"V\n\x11PartitionConstant\x12A\n\x10partition_fields\x18\x01 \x03(\x0b2\'.cz.proto.access.PartitionFieldConstant"W\n\x16PartitionFieldConstant\x12\x12\n\nfield_name\x18\x01 \x01(\t\x12)\n\x05value\x18\x02 \x01(\x0b2\x1a.cz.proto.ScalarExpression" \n\tShowShare\x12\x13\n\x0binstance_id\x18\x01 \x01(\x03"=\n\x0cShowFunction\x12-\n\tschema_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier"B\n\x0eShowConnection\x120\n\x0cworkspace_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier"\xae\x01\n\x0cShowUserRole\x120\n\x0cworkspace_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12+\n\x04user\x18\x02 \x01(\x0b2\x18.cz.proto.UserIdentifierH\x00\x88\x01\x01\x12-\n\x04role\x18\x03 \x01(\x0b2\x1a.cz.proto.ObjectIdentifierH\x01\x88\x01\x01B\x07\n\x05_userB\x07\n\x05_role"]\n\x0eShowAccessType\x12\x14\n\x07service\x18\x01 \x01(\tH\x00\x88\x01\x01\x12)\n\x0bentity_type\x18\x02 \x01(\x0e2\x14.cz.proto.ObjectTypeB\n\n\x08_service"9\n\tShowIndex\x12,\n\x08table_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier"\x82\x02\n\tGetEntity\x12.\n\nidentifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12(\n\x04user\x18\n \x01(\x0b2\x18.cz.proto.access.GetUserH\x00\x120\n\x02vc\x18\x0b \x01(\x0b2".cz.proto.access.GetVirtualClusterH\x00\x122\n\tworkspace\x18\x0c \x01(\x0b2\x1d.cz.proto.access.GetWorkspaceH\x00\x12*\n\x05table\x18\r \x01(\x0b2\x19.cz.proto.access.GetTableH\x00B\t\n\x07derived"\x1a\n\x07GetUser\x12\x0f\n\x07user_id\x18\x01 \x01(\x03"8\n\x11GetVirtualCluster\x12\x14\n\x0cworkspace_id\x18\x01 \x01(\x03\x12\r\n\x05vc_id\x18\x02 \x01(\x03":\n\x0cGetWorkspace\x12\x19\n\x0cworkspace_id\x18\x01 \x01(\x03H\x00\x88\x01\x01B\x0f\n\r_workspace_id".\n\x08GetTable\x12\x15\n\x08for_read\x18\x02 \x01(\x08H\x00\x88\x01\x01B\x0b\n\t_for_read"@\n\x0eGetEntityStats\x12.\n\nidentifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier"\x81\x01\n\x13BatchGetEntityStats\x12*\n\x06parent\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12)\n\x0bentity_type\x18\x02 \x01(\x0e2\x14.cz.proto.ObjectType\x12\x13\n\x0bentity_name\x18\x03 \x03(\t"\xe6\x01\n\x0eBatchGetEntity\x12*\n\x06parent\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12)\n\x0bentity_type\x18\x02 \x01(\x0e2\x14.cz.proto.ObjectType\x12\x13\n\x0bentity_name\x18\x03 \x03(\t\x12-\n\x04user\x18\n \x01(\x0b2\x1d.cz.proto.access.BatchGetUserH\x00\x12/\n\x05table\x18\x0b \x01(\x0b2\x1e.cz.proto.access.BatchGetTableH\x00B\x08\n\x06entity"\x1f\n\x0cBatchGetUser\x12\x0f\n\x07user_id\x18\x01 \x03(\x03"3\n\rBatchGetTable\x12\x15\n\x08for_read\x18\x01 \x01(\x08H\x00\x88\x01\x01B\x0b\n\t_for_read"\xa6\x02\n\x03DDL\x126\n\rcreate_entity\x18\n \x01(\x0b2\x1d.cz.proto.access.CreateEntityH\x00\x122\n\x0bdrop_entity\x18\x0b \x01(\x0b2\x1b.cz.proto.access.DropEntityH\x00\x124\n\x0calter_entity\x18\x0c \x01(\x0b2\x1c.cz.proto.access.AlterEntityH\x00\x12:\n\x0ftruncate_entity\x18\r \x01(\x0b2\x1f.cz.proto.access.TruncateEntityH\x00\x126\n\rundrop_entity\x18\x0e \x01(\x0b2\x1d.cz.proto.access.UndropEntityH\x00B\t\n\x07command"\xa3\x01\n\x03DCL\x12-\n\x05grant\x18\n \x01(\x0b2\x1c.cz.proto.access.GrantEntityH\x00\x12/\n\x06revoke\x18\x0b \x01(\x0b2\x1d.cz.proto.access.RevokeEntityH\x00\x121\n\x05check\x18\x0c \x01(\x0b2 .cz.proto.access.CheckPrivilegesH\x00B\t\n\x07command"\xb8\x02\n\x03DQL\x122\n\x0bshow_entity\x18\n \x01(\x0b2\x1b.cz.proto.access.ShowEntityH\x00\x120\n\nget_entity\x18\x0b \x01(\x0b2\x1a.cz.proto.access.GetEntityH\x00\x12;\n\x10get_entity_stats\x18\x0c \x01(\x0b2\x1f.cz.proto.access.GetEntityStatsH\x00\x12;\n\x10batch_get_entity\x18d \x01(\x0b2\x1f.cz.proto.access.BatchGetEntityH\x00\x12F\n\x16batch_get_entity_stats\x18e \x01(\x0b2$.cz.proto.access.BatchGetEntityStatsH\x00B\t\n\x07command"3\n\x0bAppendTable\x12$\n\x08manifest\x18\x01 \x01(\x0b2\x12.cz.proto.Manifest"\x7f\n\x0cAppendEntity\x12.\n\nidentifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x124\n\x0cappend_table\x18\n \x01(\x0b2\x1c.cz.proto.access.AppendTableH\x00B\t\n\x07derived"4\n\x0cRewriteTable\x12$\n\x08manifest\x18\x01 \x01(\x0b2\x12.cz.proto.Manifest"\x82\x01\n\rRewriteEntity\x12.\n\nidentifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x126\n\rrewrite_table\x18\n \x01(\x0b2\x1d.cz.proto.access.RewriteTableH\x00B\t\n\x07derived"6\n\x0eOverwriteTable\x12$\n\x08manifest\x18\x01 \x01(\x0b2\x12.cz.proto.Manifest"\x88\x01\n\x0fOverwriteEntity\x12.\n\nidentifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12:\n\x0foverwrite_table\x18\n \x01(\x0b2\x1f.cz.proto.access.OverwriteTableH\x00B\t\n\x07derived"\xc0\x01\n\x03DML\x126\n\rappend_entity\x18\n \x01(\x0b2\x1d.cz.proto.access.AppendEntityH\x00\x12<\n\x10overwrite_entity\x18\x0b \x01(\x0b2 .cz.proto.access.OverwriteEntityH\x00\x128\n\x0erewrite_entity\x18\x0c \x01(\x0b2\x1e.cz.proto.access.RewriteEntityH\x00B\t\n\x07command"\xb3\x02\n\x0fAccessStatement\x12/\n\x08operator\x18\x01 \x01(\x0b2\x18.cz.proto.UserIdentifierH\x01\x88\x01\x01\x12)\n\x04type\x18\x02 \x01(\x0e2\x1b.cz.proto.access.AccessType\x12#\n\x03ddl\x18\n \x01(\x0b2\x14.cz.proto.access.DDLH\x00\x12#\n\x03dcl\x18\x0b \x01(\x0b2\x14.cz.proto.access.DCLH\x00\x12#\n\x03dql\x18\x0c \x01(\x0b2\x14.cz.proto.access.DQLH\x00\x12#\n\x03dml\x18\r \x01(\x0b2\x14.cz.proto.access.DMLH\x00\x12\x16\n\x0ein_transaction\x18d \x01(\x08B\x0b\n\tstatementB\x0b\n\t_operator*2\n\x0eColumnMoveType\x12\t\n\x05FIRST\x10\x00\x12\n\n\x06BEFORE\x10\x01\x12\t\n\x05AFTER\x10\x02*X\n\x0eShowEntityType\x12\x0f\n\x0bSHOW_ENTITY\x10\x00\x12\r\n\tSHOW_NAME\x10\x01\x12\x0b\n\x07SHOW_ID\x10\x02\x12\x19\n\x15SHOW_ENTITIES_HISTORY\x10\x03*&\n\nAccessType\x12\x08\n\x04META\x10\x00\x12\x0e\n\nVC_MANAGER\x10\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'ddl_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_COLUMNMOVETYPE']._serialized_start = 11721
    _globals['_COLUMNMOVETYPE']._serialized_end = 11771
    _globals['_SHOWENTITYTYPE']._serialized_start = 11773
    _globals['_SHOWENTITYTYPE']._serialized_end = 11861
    _globals['_ACCESSTYPE']._serialized_start = 11863
    _globals['_ACCESSTYPE']._serialized_end = 11901
    _globals['_CREATEENTITY']._serialized_start = 288
    _globals['_CREATEENTITY']._serialized_end = 388
    _globals['_ALTERENTITY']._serialized_start = 391
    _globals['_ALTERENTITY']._serialized_end = 987
    _globals['_COLUMNMOVE']._serialized_start = 990
    _globals['_COLUMNMOVE']._serialized_end = 1151
    _globals['_ALTERTABLE']._serialized_start = 1153
    _globals['_ALTERTABLE']._serialized_end = 1212
    _globals['_TABLECHANGE']._serialized_start = 1215
    _globals['_TABLECHANGE']._serialized_end = 1626
    _globals['_DATASOURCEADD']._serialized_start = 1628
    _globals['_DATASOURCEADD']._serialized_end = 1684
    _globals['_DATASOURCECHANGE']._serialized_start = 1687
    _globals['_DATASOURCECHANGE']._serialized_end = 1835
    _globals['_DATASOURCEDROP']._serialized_start = 1837
    _globals['_DATASOURCEDROP']._serialized_end = 1878
    _globals['_STRUCTFIELD']._serialized_start = 1880
    _globals['_STRUCTFIELD']._serialized_end = 1959
    _globals['_COLUMNADD']._serialized_start = 1962
    _globals['_COLUMNADD']._serialized_end = 2098
    _globals['_COLUMNDROP']._serialized_start = 2100
    _globals['_COLUMNDROP']._serialized_end = 2164
    _globals['_COLUMNCHANGE']._serialized_start = 2167
    _globals['_COLUMNCHANGE']._serialized_end = 2307
    _globals['_ALTERVIRTUALCLUSTER']._serialized_start = 2310
    _globals['_ALTERVIRTUALCLUSTER']._serialized_end = 2472
    _globals['_ALTERSHARE']._serialized_start = 2474
    _globals['_ALTERSHARE']._serialized_end = 2585
    _globals['_ALTERCONNECTIONAVAILABILITY']._serialized_start = 2587
    _globals['_ALTERCONNECTIONAVAILABILITY']._serialized_end = 2632
    _globals['_ALTERCONNECTIONPROPERTIES']._serialized_start = 2634
    _globals['_ALTERCONNECTIONPROPERTIES']._serialized_end = 2714
    _globals['_ALTERCONNECTION']._serialized_start = 2717
    _globals['_ALTERCONNECTION']._serialized_end = 2899
    _globals['_ALTERFUNCTION']._serialized_start = 2901
    _globals['_ALTERFUNCTION']._serialized_end = 2946
    _globals['_DROPENTITY']._serialized_start = 2949
    _globals['_DROPENTITY']._serialized_end = 3794
    _globals['_DROPTABLE']._serialized_start = 3796
    _globals['_DROPTABLE']._serialized_end = 3822
    _globals['_DROPSTREAMTABLE']._serialized_start = 3824
    _globals['_DROPSTREAMTABLE']._serialized_end = 3841
    _globals['_DROPSCHEMA']._serialized_start = 3843
    _globals['_DROPSCHEMA']._serialized_end = 3872
    _globals['_DROPSHARE']._serialized_start = 3874
    _globals['_DROPSHARE']._serialized_end = 3902
    _globals['_DROPCATALOG']._serialized_start = 3904
    _globals['_DROPCATALOG']._serialized_end = 3934
    _globals['_DROPVIEW']._serialized_start = 3936
    _globals['_DROPVIEW']._serialized_end = 3946
    _globals['_DROPMATERIALIZEDVIEW']._serialized_start = 3948
    _globals['_DROPMATERIALIZEDVIEW']._serialized_end = 3970
    _globals['_DROPUSER']._serialized_start = 3972
    _globals['_DROPUSER']._serialized_end = 4016
    _globals['_DROPROLE']._serialized_start = 4018
    _globals['_DROPROLE']._serialized_end = 4028
    _globals['_DROPVCLUSTER']._serialized_start = 4030
    _globals['_DROPVCLUSTER']._serialized_end = 4096
    _globals['_DROPFUNCTION']._serialized_start = 4098
    _globals['_DROPFUNCTION']._serialized_end = 4112
    _globals['_DROPCONNECTION']._serialized_start = 4114
    _globals['_DROPCONNECTION']._serialized_end = 4130
    _globals['_DROPLOCATION']._serialized_start = 4132
    _globals['_DROPLOCATION']._serialized_end = 4146
    _globals['_DROPINDEX']._serialized_start = 4148
    _globals['_DROPINDEX']._serialized_end = 4159
    _globals['_DROPVOLUME']._serialized_start = 4161
    _globals['_DROPVOLUME']._serialized_end = 4173
    _globals['_UNDROPENTITY']._serialized_start = 4175
    _globals['_UNDROPENTITY']._serialized_end = 4237
    _globals['_ALTERROLE']._serialized_start = 4240
    _globals['_ALTERROLE']._serialized_end = 4391
    _globals['_ALTERJOB']._serialized_start = 4394
    _globals['_ALTERJOB']._serialized_end = 4643
    _globals['_ALTERVCLUSTER']._serialized_start = 4646
    _globals['_ALTERVCLUSTER']._serialized_end = 4914
    _globals['_ALTERUSER']._serialized_start = 4917
    _globals['_ALTERUSER']._serialized_end = 5050
    _globals['_TRUNCATEENTITY']._serialized_start = 5052
    _globals['_TRUNCATEENTITY']._serialized_end = 5128
    _globals['_TRUNCATETABLE']._serialized_start = 5130
    _globals['_TRUNCATETABLE']._serialized_end = 5231
    _globals['_SHOWENTITY']._serialized_start = 5234
    _globals['_SHOWENTITY']._serialized_end = 6312
    _globals['_SHOWVIRTUALCLUSTERSIZESPECS']._serialized_start = 6314
    _globals['_SHOWVIRTUALCLUSTERSIZESPECS']._serialized_end = 6343
    _globals['_SHOWWORKSPACE']._serialized_start = 6345
    _globals['_SHOWWORKSPACE']._serialized_end = 6381
    _globals['_SHOWUSER']._serialized_start = 6383
    _globals['_SHOWUSER']._serialized_end = 6443
    _globals['_SHOWROLE']._serialized_start = 6445
    _globals['_SHOWROLE']._serialized_end = 6505
    _globals['_SHOWGROUPPRIVILEGE']._serialized_start = 6507
    _globals['_SHOWGROUPPRIVILEGE']._serialized_end = 6575
    _globals['_SHOWUSERPRIVILEGE']._serialized_start = 6577
    _globals['_SHOWUSERPRIVILEGE']._serialized_end = 6642
    _globals['_SHOWOBJECTPRIVILEGE']._serialized_start = 6644
    _globals['_SHOWOBJECTPRIVILEGE']._serialized_end = 6756
    _globals['_SHOWPRIVILEGE']._serialized_start = 6759
    _globals['_SHOWPRIVILEGE']._serialized_end = 6947
    _globals['_SHOWTABLE']._serialized_start = 6950
    _globals['_SHOWTABLE']._serialized_end = 7313
    _globals['_SHOWTABLE_LISTORDERBY']._serialized_start = 7198
    _globals['_SHOWTABLE_LISTORDERBY']._serialized_end = 7236
    _globals['_SHOWMV']._serialized_start = 7316
    _globals['_SHOWMV']._serialized_end = 7470
    _globals['_SHOWSCHEMA']._serialized_start = 7472
    _globals['_SHOWSCHEMA']._serialized_end = 7534
    _globals['_SHOWJOB']._serialized_start = 7536
    _globals['_SHOWJOB']._serialized_end = 7595
    _globals['_SHOWVCLUSTERFILTER']._serialized_start = 7597
    _globals['_SHOWVCLUSTERFILTER']._serialized_end = 7708
    _globals['_SHOWVCLUSTER']._serialized_start = 7711
    _globals['_SHOWVCLUSTER']._serialized_end = 7844
    _globals['_SHOWFILE']._serialized_start = 7847
    _globals['_SHOWFILE']._serialized_end = 7975
    _globals['_SHOWSTORAGELOCATION']._serialized_start = 7977
    _globals['_SHOWSTORAGELOCATION']._serialized_end = 8048
    _globals['_SHOWVOLUME']._serialized_start = 8050
    _globals['_SHOWVOLUME']._serialized_end = 8109
    _globals['_TABLEPARTITIONS']._serialized_start = 8111
    _globals['_TABLEPARTITIONS']._serialized_end = 8227
    _globals['_PARTITIONCONSTANT']._serialized_start = 8229
    _globals['_PARTITIONCONSTANT']._serialized_end = 8315
    _globals['_PARTITIONFIELDCONSTANT']._serialized_start = 8317
    _globals['_PARTITIONFIELDCONSTANT']._serialized_end = 8404
    _globals['_SHOWSHARE']._serialized_start = 8406
    _globals['_SHOWSHARE']._serialized_end = 8438
    _globals['_SHOWFUNCTION']._serialized_start = 8440
    _globals['_SHOWFUNCTION']._serialized_end = 8501
    _globals['_SHOWCONNECTION']._serialized_start = 8503
    _globals['_SHOWCONNECTION']._serialized_end = 8569
    _globals['_SHOWUSERROLE']._serialized_start = 8572
    _globals['_SHOWUSERROLE']._serialized_end = 8746
    _globals['_SHOWACCESSTYPE']._serialized_start = 8748
    _globals['_SHOWACCESSTYPE']._serialized_end = 8841
    _globals['_SHOWINDEX']._serialized_start = 8843
    _globals['_SHOWINDEX']._serialized_end = 8900
    _globals['_GETENTITY']._serialized_start = 8903
    _globals['_GETENTITY']._serialized_end = 9161
    _globals['_GETUSER']._serialized_start = 9163
    _globals['_GETUSER']._serialized_end = 9189
    _globals['_GETVIRTUALCLUSTER']._serialized_start = 9191
    _globals['_GETVIRTUALCLUSTER']._serialized_end = 9247
    _globals['_GETWORKSPACE']._serialized_start = 9249
    _globals['_GETWORKSPACE']._serialized_end = 9307
    _globals['_GETTABLE']._serialized_start = 9309
    _globals['_GETTABLE']._serialized_end = 9355
    _globals['_GETENTITYSTATS']._serialized_start = 9357
    _globals['_GETENTITYSTATS']._serialized_end = 9421
    _globals['_BATCHGETENTITYSTATS']._serialized_start = 9424
    _globals['_BATCHGETENTITYSTATS']._serialized_end = 9553
    _globals['_BATCHGETENTITY']._serialized_start = 9556
    _globals['_BATCHGETENTITY']._serialized_end = 9786
    _globals['_BATCHGETUSER']._serialized_start = 9788
    _globals['_BATCHGETUSER']._serialized_end = 9819
    _globals['_BATCHGETTABLE']._serialized_start = 9821
    _globals['_BATCHGETTABLE']._serialized_end = 9872
    _globals['_DDL']._serialized_start = 9875
    _globals['_DDL']._serialized_end = 10169
    _globals['_DCL']._serialized_start = 10172
    _globals['_DCL']._serialized_end = 10335
    _globals['_DQL']._serialized_start = 10338
    _globals['_DQL']._serialized_end = 10650
    _globals['_APPENDTABLE']._serialized_start = 10652
    _globals['_APPENDTABLE']._serialized_end = 10703
    _globals['_APPENDENTITY']._serialized_start = 10705
    _globals['_APPENDENTITY']._serialized_end = 10832
    _globals['_REWRITETABLE']._serialized_start = 10834
    _globals['_REWRITETABLE']._serialized_end = 10886
    _globals['_REWRITEENTITY']._serialized_start = 10889
    _globals['_REWRITEENTITY']._serialized_end = 11019
    _globals['_OVERWRITETABLE']._serialized_start = 11021
    _globals['_OVERWRITETABLE']._serialized_end = 11075
    _globals['_OVERWRITEENTITY']._serialized_start = 11078
    _globals['_OVERWRITEENTITY']._serialized_end = 11214
    _globals['_DML']._serialized_start = 11217
    _globals['_DML']._serialized_end = 11409
    _globals['_ACCESSSTATEMENT']._serialized_start = 11412
    _globals['_ACCESSSTATEMENT']._serialized_end = 11719