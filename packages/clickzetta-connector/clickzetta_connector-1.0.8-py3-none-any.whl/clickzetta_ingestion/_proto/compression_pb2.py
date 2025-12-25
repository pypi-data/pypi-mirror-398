"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'compression.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11compression.proto\x12\x04kudu*w\n\x0fCompressionType\x12\x18\n\x13UNKNOWN_COMPRESSION\x10\xe7\x07\x12\x17\n\x13DEFAULT_COMPRESSION\x10\x00\x12\x12\n\x0eNO_COMPRESSION\x10\x01\x12\n\n\x06SNAPPY\x10\x02\x12\x07\n\x03LZ4\x10\x03\x12\x08\n\x04ZLIB\x10\x04B\x11\n\x0forg.apache.kudu')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'compression_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x0forg.apache.kudu'
    _globals['_COMPRESSIONTYPE']._serialized_start = 27
    _globals['_COMPRESSIONTYPE']._serialized_end = 146