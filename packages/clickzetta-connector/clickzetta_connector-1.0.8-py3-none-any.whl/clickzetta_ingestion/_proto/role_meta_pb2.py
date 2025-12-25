"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'role_meta.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0frole_meta.proto\x12\x08cz.proto"[\n\x04Role\x12\r\n\x05alias\x18\x01 \x01(\t\x12 \n\x04type\x18\x02 \x01(\x0e2\x12.cz.proto.RoleType\x12"\n\x05level\x18\x03 \x01(\x0e2\x13.cz.proto.RoleLevel*+\n\x08RoleType\x12\r\n\tRT_SYSTEM\x10\x00\x12\x10\n\x0cRT_CUSTOMIZE\x10\x01*,\n\tRoleLevel\x12\r\n\tRL_SYSTEM\x10\x00\x12\x10\n\x0cRL_WORKSPACE\x10\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'role_meta_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_ROLETYPE']._serialized_start = 122
    _globals['_ROLETYPE']._serialized_end = 165
    _globals['_ROLELEVEL']._serialized_start = 167
    _globals['_ROLELEVEL']._serialized_end = 211
    _globals['_ROLE']._serialized_start = 29
    _globals['_ROLE']._serialized_end = 120