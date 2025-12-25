"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'network_policy.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x14network_policy.proto\x12\x08cz.proto"=\n\rNetworkPolicy\x12,\n\x07content\x18\x01 \x01(\x0b2\x1b.cz.proto.NetworkPolicyData"j\n\x11NetworkPolicyData\x12\x15\n\rworkspaceList\x18\x01 \x03(\t\x12\x14\n\x0cusernameList\x18\x02 \x03(\t\x12\x13\n\x0bblockedList\x18\x03 \x03(\t\x12\x13\n\x0ballowedList\x18\x04 \x03(\tb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'network_policy_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_NETWORKPOLICY']._serialized_start = 34
    _globals['_NETWORKPOLICY']._serialized_end = 95
    _globals['_NETWORKPOLICYDATA']._serialized_start = 97
    _globals['_NETWORKPOLICYDATA']._serialized_end = 203