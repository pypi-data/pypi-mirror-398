"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'virtual_cluster_size.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1avirtual_cluster_size.proto\x12\x11com.clickzetta.rm"\xba\x01\n\x16VirtualClusterSizeSpec\x12\n\n\x02id\x18\x01 \x01(\x03\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x14\n\x07alias_1\x18\x03 \x01(\tH\x00\x88\x01\x01\x12\x14\n\x07alias_2\x18\x04 \x01(\tH\x01\x88\x01\x01\x12\x14\n\x07alias_3\x18\x05 \x01(\tH\x02\x88\x01\x01\x12\x10\n\x08cpu_core\x18\x06 \x01(\x01\x12\x0e\n\x06mem_gb\x18\x07 \x01(\x03B\n\n\x08_alias_1B\n\n\x08_alias_2B\n\n\x08_alias_3b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'virtual_cluster_size_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_VIRTUALCLUSTERSIZESPEC']._serialized_start = 50
    _globals['_VIRTUALCLUSTERSIZESPEC']._serialized_end = 236