"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'service_common.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x14service_common.proto\x12\x08cz.proto"K\n\x0eResponseStatus\x12\x12\n\nrequest_id\x18\x01 \x01(\t\x12\x12\n\nerror_code\x18\x02 \x01(\t\x12\x11\n\terror_msg\x18\x03 \x01(\tb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'service_common_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_RESPONSESTATUS']._serialized_start = 34
    _globals['_RESPONSESTATUS']._serialized_end = 109