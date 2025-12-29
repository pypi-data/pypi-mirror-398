"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'account.proto')
_sym_db = _symbol_database.Default()
from . import object_identifier_pb2 as object__identifier__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\raccount.proto\x12\x08cz.proto\x1a\x17object_identifier.proto"V\n\x0fPolicyStatement\x12\x0e\n\x06Effect\x18\x01 \x01(\t\x12\x11\n\tPrincipal\x18\x02 \x03(\t\x12\x0e\n\x06Action\x18\x03 \x03(\t\x12\x10\n\x08Resource\x18\x04 \x03(\t"G\n\x06Policy\x12\x0f\n\x07Version\x18\x01 \x01(\t\x12,\n\tStatement\x18\x02 \x03(\x0b2\x19.cz.proto.PolicyStatement"\xa8\x01\n\x07Account\x12\x12\n\naccount_id\x18\x01 \x01(\x03\x12\x11\n\tuser_name\x18\x02 \x01(\t\x12\x0f\n\x07user_id\x18\x03 \x01(\x03\x12*\n\x04type\x18\x04 \x01(\x0e2\x17.cz.proto.PrincipalTypeH\x00\x88\x01\x01\x12%\n\x06policy\x18\x05 \x01(\x0b2\x10.cz.proto.PolicyH\x01\x88\x01\x01B\x07\n\x05_typeB\t\n\x07_policy"`\n\x08Instance\x12\x14\n\x0caccount_name\x18\x04 \x01(\t\x12\x12\n\naccount_id\x18\x01 \x01(\x03\x12\x13\n\x0binstance_id\x18\x02 \x01(\x03\x12\x15\n\rinstance_name\x18\x03 \x01(\t"Q\n\x0eUserIdentifier\x12.\n\nidentifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12\x0f\n\x07user_id\x18\x02 \x01(\x03"T\n\x04User\x12\x14\n\x07user_id\x18\x01 \x01(\x03H\x00\x88\x01\x01\x12\x12\n\ndefault_vc\x18\x02 \x01(\t\x12\x16\n\x0edefault_schema\x18\x03 \x01(\tB\n\n\x08_user_idb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'account_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_POLICYSTATEMENT']._serialized_start = 52
    _globals['_POLICYSTATEMENT']._serialized_end = 138
    _globals['_POLICY']._serialized_start = 140
    _globals['_POLICY']._serialized_end = 211
    _globals['_ACCOUNT']._serialized_start = 214
    _globals['_ACCOUNT']._serialized_end = 382
    _globals['_INSTANCE']._serialized_start = 384
    _globals['_INSTANCE']._serialized_end = 480
    _globals['_USERIDENTIFIER']._serialized_start = 482
    _globals['_USERIDENTIFIER']._serialized_end = 563
    _globals['_USER']._serialized_start = 565
    _globals['_USER']._serialized_end = 649