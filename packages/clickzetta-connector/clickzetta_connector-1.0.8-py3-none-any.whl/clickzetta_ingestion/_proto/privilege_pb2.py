"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'privilege.proto')
_sym_db = _symbol_database.Default()
from . import object_identifier_pb2 as object__identifier__pb2
from . import account_pb2 as account__pb2
from . import metadata_entity_pb2 as metadata__entity__pb2
from . import table_common_pb2 as table__common__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0fprivilege.proto\x12\x0fcz.proto.access\x1a\x17object_identifier.proto\x1a\raccount.proto\x1a\x15metadata_entity.proto\x1a\x12table_common.proto"\\\n\x0bAccessToken\x12\x13\n\x0bexpire_time\x18\x01 \x01(\x03\x12\x0f\n\x07user_id\x18\x02 \x01(\x03\x12\'\n\raccess_policy\x18\n \x01(\x0b2\x10.cz.proto.Policy"\xa2\x03\n\x0fCheckPrivileges\x12+\n\tprincipal\x18\x01 \x01(\x0b2\x18.cz.proto.UserIdentifier\x12\x14\n\x0caccess_token\x18\x02 \x01(\t\x129\n\x07content\x18\x04 \x03(\x0b2(.cz.proto.access.CheckPrivileges.Content\x1a\x90\x02\n\x07Content\x12)\n\x04mode\x18\x01 \x01(\x0e2\x1b.cz.proto.access.EffectMode\x12+\n\x06action\x18\x02 \x03(\x0e2\x1b.cz.proto.access.ActionType\x12\x19\n\x11with_grant_option\x18\x03 \x01(\x08\x12*\n\x06object\x18\x04 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x127\n\x0cgranted_type\x18\x05 \x01(\x0e2!.cz.proto.access.GrantedType.Type\x12-\n\x0fsub_object_type\x18\x06 \x01(\x0e2\x14.cz.proto.ObjectType"X\n\x07Subject\x12.\n\nidentifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12\x11\n\x07user_id\x18\n \x01(\x03H\x00B\n\n\x08extended"\xa5\x01\n\x0bGrantEntity\x12)\n\x07subject\x18\x01 \x01(\x0b2\x18.cz.proto.access.Subject\x12*\n\x04role\x18\n \x01(\x0b2\x1a.cz.proto.access.GrantRoleH\x00\x124\n\tprivilege\x18\x0b \x01(\x0b2\x1f.cz.proto.access.GrantPrivilegeH\x00B\t\n\x07derived"Z\n\tGrantRole\x12.\n\nidentifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12\x1d\n\x15authorization_time_ms\x18\x02 \x01(\x03"D\n\x0eGrantPrivilege\x122\n\x07content\x18\x01 \x01(\x0b2!.cz.proto.access.PrivilegeContent"\xa8\x01\n\x0cRevokeEntity\x12)\n\x07subject\x18\x01 \x01(\x0b2\x18.cz.proto.access.Subject\x12+\n\x04role\x18\n \x01(\x0b2\x1b.cz.proto.access.RevokeRoleH\x00\x125\n\tprivilege\x18\x0b \x01(\x0b2 .cz.proto.access.RevokePrivilegeH\x00B\t\n\x07derived"[\n\nRevokeRole\x12.\n\nidentifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12\x1d\n\x15authorization_time_ms\x18\x02 \x01(\x03"E\n\x0fRevokePrivilege\x122\n\x07content\x18\x01 \x01(\x0b2!.cz.proto.access.PrivilegeContent"\xee\x01\n\x10PrivilegeContent\x12+\n\x06action\x18\x01 \x03(\x0e2\x1b.cz.proto.access.ActionType\x12*\n\x06object\x18\x02 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x127\n\x0cgranted_type\x18\x03 \x01(\x0e2!.cz.proto.access.GrantedType.Type\x12\x19\n\x11with_grant_option\x18\x05 \x01(\x08\x12-\n\x0fsub_object_type\x18\x06 \x01(\x0e2\x14.cz.proto.ObjectType"d\n\x0bGrantedType"U\n\x04Type\x12\r\n\tPRIVILEGE\x10\x00\x12\n\n\x06POLICY\x10\x01\x12\x08\n\x04ROLE\x10\x02\x12\x12\n\x0eOBJECT_CREATOR\x10\x03\x12\x14\n\x10OBJECT_HIERARCHY\x10\x04"\x8e\x01\n\x0fPrivilegeAction\x12-\n\x06action\x18\n \x01(\x0e2\x1b.cz.proto.access.ActionTypeH\x00\x12\x15\n\x0bpolicy_name\x18\x0b \x01(\tH\x00\x12*\n\x04role\x18\x0c \x01(\x0b2\x1a.cz.proto.ObjectIdentifierH\x00B\t\n\x07derived"(\n\x12PrivilegeCondition\x12\x12\n\nconditions\x18\x01 \x03(\t"\xf0\x03\n\tPrivilege\x127\n\x0cgranted_type\x18\x01 \x01(\x0e2!.cz.proto.access.GrantedType.Type\x123\n\tprivilege\x18\x02 \x01(\x0b2 .cz.proto.access.PrivilegeAction\x127\n\nconditions\x18\x03 \x01(\x0b2#.cz.proto.access.PrivilegeCondition\x12.\n\ngranted_on\x18\x04 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12+\n\x07grantee\x18\x05 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12+\n\x07grantor\x18\x06 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12\x14\n\x0cgrant_option\x18\x07 \x01(\x08\x12\x17\n\x0fgranted_time_ms\x18\x08 \x01(\x03\x12,\n\ntable_type\x18\t \x01(\x0e2\x13.cz.proto.TableTypeH\x00\x88\x01\x01\x122\n\x0fsub_object_type\x18\n \x01(\x0e2\x14.cz.proto.ObjectTypeH\x01\x88\x01\x01B\r\n\x0b_table_typeB\x12\n\x10_sub_object_type"?\n\rPrivilegeList\x12.\n\nprivileges\x18\x01 \x03(\x0b2\x1a.cz.proto.access.Privilege"\xa2\x01\n\x08UserRole\x12&\n\x04user\x18\x01 \x01(\x0b2\x18.cz.proto.UserIdentifier\x12(\n\x04role\x18\x02 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12+\n\x07grantor\x18\x03 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12\x17\n\x0fgranted_time_ms\x18\x04 \x01(\x03"=\n\x0cUserRoleList\x12-\n\nuser_roles\x18\x01 \x03(\x0b2\x19.cz.proto.access.UserRole"&\n\x0eAccessTypeList\x12\x14\n\x0caccess_types\x18\x01 \x03(\t*O\n\nSystemRole\x12\x0f\n\x0bSystemAdmin\x10\x00\x12\r\n\tUserAdmin\x10\x01\x12\x11\n\rSecurityAdmin\x10\x02\x12\x0e\n\nAuditAdmin\x10\x03*\xef\r\n\nActionType\x12\x0c\n\x08AT_KNOWN\x10\x00\x12\n\n\x06AT_ALL\x10\x01\x12\x11\n\rAT_CREATE_ALL\x10\x02\x12\x10\n\x0cAT_ALTER_ALL\x10\x03\x12\x11\n\rAT_UPDATE_ALL\x10\x04\x12\x11\n\rAT_SELECT_ALL\x10\x05\x12\x0f\n\x0bAT_DROP_ALL\x10\x06\x12\x0e\n\nAT_ALL_FIN\x10\x07\x12\x12\n\x0eAT_CREATE_ROLE\x10d\x12\x11\n\rAT_ALTER_ROLE\x10e\x12\x10\n\x0cAT_DROP_ROLE\x10f\x12\x17\n\x12AT_GRANT_PRIVILEGE\x10\xc8\x01\x12\x18\n\x13AT_REVOKE_PRIVILEGE\x10\xc9\x01\x12\x16\n\x11AT_SHOW_PRIVILEGE\x10\xca\x01\x12\x17\n\x12AT_CREATE_VCLUSTER\x10\x90\x03\x12\x16\n\x11AT_ALTER_VCLUSTER\x10\x91\x03\x12\x15\n\x10AT_DROP_VCLUSTER\x10\x92\x03\x12\x14\n\x0fAT_USE_VCLUSTER\x10\x96\x03\x12\x15\n\x10AT_CREATE_SCHEMA\x10\xf4\x03\x12\x14\n\x0fAT_ALTER_SCHEMA\x10\xf5\x03\x12\x13\n\x0eAT_DROP_SCHEMA\x10\xf6\x03\x12\x14\n\x0fAT_CREATE_TABLE\x10\xd8\x04\x12\x13\n\x0eAT_ALTER_TABLE\x10\xd9\x04\x12\x12\n\rAT_DROP_TABLE\x10\xda\x04\x12\x14\n\x0fAT_SELECT_TABLE\x10\xdf\x04\x12\x14\n\x0fAT_INSERT_TABLE\x10\xe0\x04\x12\x16\n\x11AT_TRUNCATE_TABLE\x10\xe2\x04\x12\x14\n\x0fAT_UPDATE_TABLE\x10\xe3\x04\x12\x14\n\x0fAT_DELETE_TABLE\x10\xe5\x04\x12\x13\n\x0eAT_CREATE_VIEW\x10\xbc\x05\x12\x11\n\x0cAT_DROP_VIEW\x10\xbd\x05\x12\x13\n\x0eAT_SELECT_VIEW\x10\xbf\x05\x12\x12\n\rAT_ALTER_VIEW\x10\xc0\x05\x12 \n\x1bAT_CREATE_MATERIALIZED_VIEW\x10\xa0\x06\x12\x1e\n\x19AT_DROP_MATERIALIZED_VIEW\x10\xa1\x06\x12 \n\x1bAT_SELECT_MATERIALIZED_VIEW\x10\xa2\x06\x12\x1f\n\x1aAT_ALTER_MATERIALIZED_VIEW\x10\xa4\x06\x12\x17\n\x12AT_CREATE_FUNCTION\x10\x84\x07\x12\x15\n\x10AT_DROP_FUNCTION\x10\x85\x07\x12\x14\n\x0fAT_USE_FUNCTION\x10\x86\x07\x12\x16\n\x11AT_ALTER_FUNCTION\x10\x87\x07\x12\x17\n\x12AT_CREATE_DATALAKE\x10\xe8\x07\x12\x16\n\x11AT_ALTER_DATALAKE\x10\xe9\x07\x12\x15\n\x10AT_DROP_DATALAKE\x10\xea\x07\x12\x1c\n\x17AT_CREATE_SCHEDULE_TASK\x10\xcc\x08\x12\x1b\n\x16AT_ALTER_SCHEDULE_TASK\x10\xcd\x08\x12\x1a\n\x15AT_DROP_SCHEDULE_TASK\x10\xce\x08\x12\x1b\n\x16AT_CLONE_SCHEDULE_TASK\x10\xcf\x08\x12\x13\n\x0eAT_CREATE_USER\x10\xb0\t\x12\x11\n\x0cAT_DROP_USER\x10\xb1\t\x12\x12\n\rAT_ALTER_USER\x10\xb2\t\x12\x16\n\x11AT_READ_AUDIT_LOG\x10\x94\n\x12\x1a\n\x15AT_DOWNLOAD_AUDIT_LOG\x10\x95\n\x12\x16\n\x11AT_COPY_AUDIT_LOG\x10\x96\n\x12\x11\n\x0cAT_ALTER_JOB\x10\xf8\n\x12\x15\n\x10AT_TERMINATE_JOB\x10\xf9\n\x12\x15\n\x10AT_READ_METADATA\x10\xdc\x0b\x12\x14\n\x0fAT_CREATE_SHARE\x10\xc0\x0c\x12\x13\n\x0eAT_ALTER_SHARE\x10\xc1\x0c\x12\x12\n\rAT_DROP_SHARE\x10\xc2\x0c\x12\x19\n\x14AT_CREATE_CONNECTION\x10\xa4\r\x12\x18\n\x13AT_ALTER_CONNECTION\x10\xa5\r\x12\x17\n\x12AT_DROP_CONNECTION\x10\xa6\r\x12\x17\n\x12AT_CREATE_LOCATION\x10\x88\x0e\x12\x16\n\x11AT_ALTER_LOCATION\x10\x89\x0e\x12\x15\n\x10AT_DROP_LOCATION\x10\x8a\x0e\x12\x14\n\x0fAT_USE_LOCATION\x10\x8e\x0e\x12\x18\n\x13AT_CREATE_WORKSPACE\x10\xec\x0e\x12\x17\n\x12AT_ALTER_WORKSPACE\x10\xed\x0e\x12\x16\n\x11AT_DROP_WORKSPACE\x10\xee\x0e\x12\x1b\n\x16AT_CREATE_TABLE_STREAM\x10\xd0\x0f\x12\x19\n\x14AT_DROP_TABLE_STREAM\x10\xd1\x0f\x12\x1b\n\x16AT_SELECT_TABLE_STREAM\x10\xd3\x0f\x12\x1a\n\x15AT_ALTER_TABLE_STREAM\x10\xd4\x0f\x12\x14\n\x0fAT_CREATE_INDEX\x10\xb4\x10\x12\x12\n\rAT_DROP_INDEX\x10\xb5\x10*!\n\nEffectType\x12\t\n\x05ALLOW\x10\x00\x12\x08\n\x04DENY\x10\x01*3\n\nEffectMode\x12\x11\n\rDENY_OVERRIDE\x10\x00\x12\x12\n\x0eALLOW_OVERRIDE\x10\x01B\x02P\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'privilege_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'P\x01'
    _globals['_SYSTEMROLE']._serialized_start = 2751
    _globals['_SYSTEMROLE']._serialized_end = 2830
    _globals['_ACTIONTYPE']._serialized_start = 2833
    _globals['_ACTIONTYPE']._serialized_end = 4608
    _globals['_EFFECTTYPE']._serialized_start = 4610
    _globals['_EFFECTTYPE']._serialized_end = 4643
    _globals['_EFFECTMODE']._serialized_start = 4645
    _globals['_EFFECTMODE']._serialized_end = 4696
    _globals['_ACCESSTOKEN']._serialized_start = 119
    _globals['_ACCESSTOKEN']._serialized_end = 211
    _globals['_CHECKPRIVILEGES']._serialized_start = 214
    _globals['_CHECKPRIVILEGES']._serialized_end = 632
    _globals['_CHECKPRIVILEGES_CONTENT']._serialized_start = 360
    _globals['_CHECKPRIVILEGES_CONTENT']._serialized_end = 632
    _globals['_SUBJECT']._serialized_start = 634
    _globals['_SUBJECT']._serialized_end = 722
    _globals['_GRANTENTITY']._serialized_start = 725
    _globals['_GRANTENTITY']._serialized_end = 890
    _globals['_GRANTROLE']._serialized_start = 892
    _globals['_GRANTROLE']._serialized_end = 982
    _globals['_GRANTPRIVILEGE']._serialized_start = 984
    _globals['_GRANTPRIVILEGE']._serialized_end = 1052
    _globals['_REVOKEENTITY']._serialized_start = 1055
    _globals['_REVOKEENTITY']._serialized_end = 1223
    _globals['_REVOKEROLE']._serialized_start = 1225
    _globals['_REVOKEROLE']._serialized_end = 1316
    _globals['_REVOKEPRIVILEGE']._serialized_start = 1318
    _globals['_REVOKEPRIVILEGE']._serialized_end = 1387
    _globals['_PRIVILEGECONTENT']._serialized_start = 1390
    _globals['_PRIVILEGECONTENT']._serialized_end = 1628
    _globals['_GRANTEDTYPE']._serialized_start = 1630
    _globals['_GRANTEDTYPE']._serialized_end = 1730
    _globals['_GRANTEDTYPE_TYPE']._serialized_start = 1645
    _globals['_GRANTEDTYPE_TYPE']._serialized_end = 1730
    _globals['_PRIVILEGEACTION']._serialized_start = 1733
    _globals['_PRIVILEGEACTION']._serialized_end = 1875
    _globals['_PRIVILEGECONDITION']._serialized_start = 1877
    _globals['_PRIVILEGECONDITION']._serialized_end = 1917
    _globals['_PRIVILEGE']._serialized_start = 1920
    _globals['_PRIVILEGE']._serialized_end = 2416
    _globals['_PRIVILEGELIST']._serialized_start = 2418
    _globals['_PRIVILEGELIST']._serialized_end = 2481
    _globals['_USERROLE']._serialized_start = 2484
    _globals['_USERROLE']._serialized_end = 2646
    _globals['_USERROLELIST']._serialized_start = 2648
    _globals['_USERROLELIST']._serialized_end = 2709
    _globals['_ACCESSTYPELIST']._serialized_start = 2711
    _globals['_ACCESSTYPELIST']._serialized_end = 2749