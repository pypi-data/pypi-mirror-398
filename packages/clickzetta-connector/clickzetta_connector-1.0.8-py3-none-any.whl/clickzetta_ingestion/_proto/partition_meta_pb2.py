"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'partition_meta.proto')
_sym_db = _symbol_database.Default()
from . import virtual_value_info_pb2 as virtual__value__info__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x14partition_meta.proto\x12\x08cz.proto\x1a\x18virtual_value_info.proto"[\n\tPartition\x126\n\x12virtual_value_info\x18\x01 \x01(\x0b2\x1a.cz.proto.VirtualValueInfo\x12\x16\n\x0epartition_keys\x18\x02 \x03(\tB\x0c\n\x08cz.protoP\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'partition_meta_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x08cz.protoP\x01'
    _globals['_PARTITION']._serialized_start = 60
    _globals['_PARTITION']._serialized_end = 151