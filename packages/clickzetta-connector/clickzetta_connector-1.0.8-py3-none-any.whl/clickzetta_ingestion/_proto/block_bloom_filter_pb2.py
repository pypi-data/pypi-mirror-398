"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'block_bloom_filter.proto')
_sym_db = _symbol_database.Default()
from . import hash_pb2 as hash__pb2
from . import pb_util_pb2 as pb__util__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x18block_bloom_filter.proto\x12\x04kudu\x1a\nhash.proto\x1a\rpb_util.proto"\xab\x01\n\x12BlockBloomFilterPB\x12\x17\n\x0flog_space_bytes\x18\x01 \x01(\x05\x12\x18\n\nbloom_data\x18\x02 \x01(\x0cB\x04\x88\xb5\x18\x01\x12\x14\n\x0calways_false\x18\x03 \x01(\x08\x126\n\x0ehash_algorithm\x18\x04 \x01(\x0e2\x13.kudu.HashAlgorithm:\tFAST_HASH\x12\x14\n\thash_seed\x18\x05 \x01(\r:\x010B\x11\n\x0forg.apache.kudu')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'block_bloom_filter_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x0forg.apache.kudu'
    _globals['_BLOCKBLOOMFILTERPB'].fields_by_name['bloom_data']._loaded_options = None
    _globals['_BLOCKBLOOMFILTERPB'].fields_by_name['bloom_data']._serialized_options = b'\x88\xb5\x18\x01'
    _globals['_BLOCKBLOOMFILTERPB']._serialized_start = 62
    _globals['_BLOCKBLOOMFILTERPB']._serialized_end = 233