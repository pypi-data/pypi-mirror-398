"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'pb_util.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import descriptor_pb2 as google_dot_protobuf_dot_descriptor__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rpb_util.proto\x12\x04kudu\x1a google/protobuf/descriptor.proto"[\n\x14ContainerSupHeaderPB\x122\n\x06protos\x18\x01 \x02(\x0b2".google.protobuf.FileDescriptorSet\x12\x0f\n\x07pb_type\x18\x02 \x02(\t:6\n\x06REDACT\x12\x1d.google.protobuf.FieldOptions\x18\xd1\x86\x03 \x01(\x08:\x05falseB\x11\n\x0forg.apache.kudu')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'pb_util_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x0forg.apache.kudu'
    _globals['_CONTAINERSUPHEADERPB']._serialized_start = 57
    _globals['_CONTAINERSUPHEADERPB']._serialized_end = 148