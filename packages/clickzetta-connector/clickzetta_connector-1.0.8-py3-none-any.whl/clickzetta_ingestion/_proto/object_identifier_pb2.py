"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'object_identifier.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x17object_identifier.proto\x12\x08cz.proto":\n\x0bObjectState"+\n\x04Type\x12\n\n\x06ONLINE\x10\x00\x12\x0b\n\x07DELETED\x10\x01\x12\n\n\x06STAGED\x10\x02"\x95\x03\n\x10ObjectIdentifier\x12"\n\x04type\x18\x01 \x01(\x0e2\x14.cz.proto.ObjectType\x12\x17\n\naccount_id\x18\x06 \x01(\x03H\x00\x88\x01\x01\x12\x19\n\x0caccount_name\x18\x07 \x01(\tH\x01\x88\x01\x01\x12\x13\n\x0binstance_id\x18\x02 \x01(\x03\x12\x1a\n\rinstance_name\x18\x05 \x01(\tH\x02\x88\x01\x01\x12\x11\n\tnamespace\x18\x03 \x03(\t\x12\x14\n\x0cnamespace_id\x18\n \x03(\x03\x12,\n\x0enamespace_type\x18\x0c \x03(\x0e2\x14.cz.proto.ObjectType\x12\x0c\n\x04name\x18\x04 \x01(\t\x12\n\n\x02id\x18\t \x01(\x03\x12\x0f\n\x07version\x18\x0b \x01(\t\x121\n\x0ereference_type\x18\r \x01(\x0e2\x14.cz.proto.ObjectTypeH\x03\x88\x01\x01B\r\n\x0b_account_idB\x0f\n\r_account_nameB\x10\n\x0e_instance_nameB\x11\n\x0f_reference_type"G\n\x14ObjectIdentifierList\x12/\n\x0bidentifiers\x18\x01 \x03(\x0b2\x1a.cz.proto.ObjectIdentifier"\xb7\x01\n\x17ObjectModificationEvent\x12.\n\nidentifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12\x14\n\x07version\x18\x02 \x01(\x03H\x00\x88\x01\x01\x12\x15\n\x08sequence\x18\x03 \x01(\x04H\x01\x88\x01\x01\x12\x17\n\noccur_time\x18\x04 \x01(\x03H\x02\x88\x01\x01B\n\n\x08_versionB\x0b\n\t_sequenceB\r\n\x0b_occur_time"P\n\x1bObjectModificationEventList\x121\n\x06events\x18\x01 \x03(\x0b2!.cz.proto.ObjectModificationEvent*\xe5\x02\n\nObjectType\x12\x0b\n\x07UNKNOWN\x10\x00\x12\x0c\n\x08INSTANCE\x10\x01\x12\x12\n\x0eNETWORK_POLICY\x10\x02\x12\r\n\tWORKSPACE\x10d\x12\t\n\x05SHARE\x10e\x12\x10\n\x0cCOMPUTE_POOL\x10f\x12\x0b\n\x06SCHEMA\x10\xc8\x01\x12\r\n\x08DATALAKE\x10\xc9\x01\x12\t\n\x04USER\x10\xca\x01\x12\t\n\x04ROLE\x10\xcb\x01\x12\x13\n\x0fVIRTUAL_CLUSTER\x10h\x12\x08\n\x03JOB\x10\xcd\x01\x12\x0f\n\nCONNECTION\x10\xce\x01\x12\r\n\x08LOCATION\x10\xcf\x01\x12\n\n\x05TABLE\x10\xac\x02\x12\r\n\x08FUNCTION\x10\xad\x02\x12\x0b\n\x06VOLUME\x10\xae\x02\x12\x14\n\x0fINTERNAL_VOLUME\x10\xaf\x02\x12\x0c\n\x07SYNONYM\x10\xb0\x02\x12\x0e\n\tPIPE_TASK\x10\xdf\x02\x12\n\n\x05INDEX\x10\x90\x03\x12\x0e\n\tPARTITION\x10\x91\x03\x12\t\n\x04FILE\x10\xf4\x03\x12\x08\n\x03ALL\x10\xe8\x07*[\n\rPrincipalType\x12\x0b\n\x07PT_USER\x10\x00\x12\r\n\tPT_SYSTEM\x10\x01\x12\x15\n\x11PT_SERVICE_SYSTEM\x10\x02\x12\x17\n\x13PT_SERVICE_CUSTOMER\x10\x04B\x0c\n\x08cz.protoP\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'object_identifier_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x08cz.protoP\x01'
    _globals['_OBJECTTYPE']._serialized_start = 847
    _globals['_OBJECTTYPE']._serialized_end = 1204
    _globals['_PRINCIPALTYPE']._serialized_start = 1206
    _globals['_PRINCIPALTYPE']._serialized_end = 1297
    _globals['_OBJECTSTATE']._serialized_start = 37
    _globals['_OBJECTSTATE']._serialized_end = 95
    _globals['_OBJECTSTATE_TYPE']._serialized_start = 52
    _globals['_OBJECTSTATE_TYPE']._serialized_end = 95
    _globals['_OBJECTIDENTIFIER']._serialized_start = 98
    _globals['_OBJECTIDENTIFIER']._serialized_end = 503
    _globals['_OBJECTIDENTIFIERLIST']._serialized_start = 505
    _globals['_OBJECTIDENTIFIERLIST']._serialized_end = 576
    _globals['_OBJECTMODIFICATIONEVENT']._serialized_start = 579
    _globals['_OBJECTMODIFICATIONEVENT']._serialized_end = 762
    _globals['_OBJECTMODIFICATIONEVENTLIST']._serialized_start = 764
    _globals['_OBJECTMODIFICATIONEVENTLIST']._serialized_end = 844