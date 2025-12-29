"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'bucket_info.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11bucket_info.proto\x12\x08cz.proto"2\n\nBucketInfo\x12\x11\n\tbucket_id\x18\x01 \x01(\r\x12\x11\n\tblock_ids\x18\x02 \x03(\r"\xac\x01\n\tBucketIds\x12*\n\x05range\x18\x01 \x01(\x0b2\x19.cz.proto.BucketIds.RangeH\x00\x12(\n\x04list\x18\x02 \x01(\x0b2\x18.cz.proto.BucketIds.ListH\x00\x1a#\n\x05Range\x12\r\n\x05start\x18\x01 \x01(\r\x12\x0b\n\x03end\x18\x02 \x01(\r\x1a\x16\n\x04List\x12\x0e\n\x06values\x18\x01 \x03(\rB\x0c\n\nbucket_idsB\n\n\x08cz.protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bucket_info_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x08cz.proto'
    _globals['_BUCKETINFO']._serialized_start = 31
    _globals['_BUCKETINFO']._serialized_end = 81
    _globals['_BUCKETIDS']._serialized_start = 84
    _globals['_BUCKETIDS']._serialized_end = 256
    _globals['_BUCKETIDS_RANGE']._serialized_start = 183
    _globals['_BUCKETIDS_RANGE']._serialized_end = 218
    _globals['_BUCKETIDS_LIST']._serialized_start = 220
    _globals['_BUCKETIDS_LIST']._serialized_end = 242