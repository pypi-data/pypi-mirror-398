"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'file_format_type.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x16file_format_type.proto\x12\x08cz.proto*\x83\x01\n\x0eFileFormatType\x12\x08\n\x04TEXT\x10\x00\x12\x0b\n\x07PARQUET\x10\x01\x12\x07\n\x03ORC\x10\x02\x12\x08\n\x04AVRO\x10\x03\x12\x07\n\x03CSV\x10\x04\x12\t\n\x05ARROW\x10\x05\x12\x0f\n\x0bHIVE_RESULT\x10`\x12\t\n\x05DUMMY\x10a\x12\n\n\x06MEMORY\x10b\x12\x0b\n\x07ICEBERG\x10cb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'file_format_type_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_FILEFORMATTYPE']._serialized_start = 37
    _globals['_FILEFORMATTYPE']._serialized_end = 168