"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'hash.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nhash.proto\x12\x04kudu*R\n\rHashAlgorithm\x12\x10\n\x0cUNKNOWN_HASH\x10\x00\x12\x11\n\rMURMUR_HASH_2\x10\x01\x12\r\n\tCITY_HASH\x10\x02\x12\r\n\tFAST_HASH\x10\x03B\x11\n\x0forg.apache.kudu')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'hash_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x0forg.apache.kudu'
    _globals['_HASHALGORITHM']._serialized_start = 20
    _globals['_HASHALGORITHM']._serialized_end = 102