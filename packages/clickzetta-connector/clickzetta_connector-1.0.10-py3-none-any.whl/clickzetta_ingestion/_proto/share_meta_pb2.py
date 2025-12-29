"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'share_meta.proto')
_sym_db = _symbol_database.Default()
from . import object_identifier_pb2 as object__identifier__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10share_meta.proto\x12\x08cz.proto\x1a\x17object_identifier.proto"\xce\x01\n\x05Share\x126\n\x12provider_workspace\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12"\n\x04kind\x18\x02 \x01(\x0e2\x14.cz.proto.Share.Kind\x12$\n\x05scope\x18\x03 \x01(\x0e2\x15.cz.proto.Share.Scope"!\n\x04Kind\x12\x0b\n\x07INBOUND\x10\x00\x12\x0c\n\x08OUTBOUND\x10\x01" \n\x05Scope\x12\x0b\n\x07PRIVATE\x10\x00\x12\n\n\x06PUBLIC\x10\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'share_meta_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_SHARE']._serialized_start = 56
    _globals['_SHARE']._serialized_end = 262
    _globals['_SHARE_KIND']._serialized_start = 195
    _globals['_SHARE_KIND']._serialized_end = 228
    _globals['_SHARE_SCOPE']._serialized_start = 230
    _globals['_SHARE_SCOPE']._serialized_end = 262