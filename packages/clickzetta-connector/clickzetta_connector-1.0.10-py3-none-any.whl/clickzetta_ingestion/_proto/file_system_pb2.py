"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'file_system.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11file_system.proto\x12\x08cz.proto*n\n\x0eFileSystemType\x12\t\n\x05LOCAL\x10\x00\x12\x07\n\x03OSS\x10\x01\x12\t\n\x05CACHE\x10\x02\x12\x07\n\x03RPC\x10\x03\x12\x07\n\x03COS\x10\x04\x12\x08\n\x04HDFS\x10\x05\x12\x06\n\x02S3\x10\x06\x12\x07\n\x03GCS\x10\x07\x12\x07\n\x03OBS\x10\x08\x12\x07\n\x03TOS\x10\tb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'file_system_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_FILESYSTEMTYPE']._serialized_start = 31
    _globals['_FILESYSTEMTYPE']._serialized_end = 141