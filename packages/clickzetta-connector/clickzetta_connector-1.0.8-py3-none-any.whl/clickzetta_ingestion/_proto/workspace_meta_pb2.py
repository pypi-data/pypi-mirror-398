"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'workspace_meta.proto')
_sym_db = _symbol_database.Default()
from . import object_identifier_pb2 as object__identifier__pb2
from . import encryption_pb2 as encryption__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x14workspace_meta.proto\x12\x08cz.proto\x1a\x17object_identifier.proto\x1a\x10encryption.proto"\xab\x01\n\tWorkspace\x12\x10\n\x08location\x18\x01 \x01(\t\x12\x1a\n\x12optional_locations\x18\x02 \x03(\t\x125\n\x11encryption_config\x18\x05 \x01(\x0b2\x1a.cz.proto.EncryptionConfig\x12+\n\x05share\x18\n \x01(\x0b2\x1a.cz.proto.ObjectIdentifierH\x00B\x0c\n\nconnectionb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'workspace_meta_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_WORKSPACE']._serialized_start = 78
    _globals['_WORKSPACE']._serialized_end = 249