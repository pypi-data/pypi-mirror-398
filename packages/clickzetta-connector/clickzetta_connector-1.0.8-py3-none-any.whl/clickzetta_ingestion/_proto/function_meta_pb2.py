"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'function_meta.proto')
_sym_db = _symbol_database.Default()
from . import object_identifier_pb2 as object__identifier__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x13function_meta.proto\x12\x08cz.proto\x1a\x17object_identifier.proto"K\n\x10FunctionResource\x12\x0c\n\x04type\x18\x01 \x01(\t\x12\r\n\x03uri\x18\x02 \x01(\tH\x00\x12\x11\n\x07content\x18\x03 \x01(\tH\x00B\x07\n\x05value"E\n\x14FunctionResourceList\x12-\n\tresources\x18\x01 \x03(\x0b2\x1a.cz.proto.FunctionResource"\xd2\x01\n\x10RemoteEntrypoint\x12\x14\n\x0cinternal_url\x18\x01 \x01(\t\x12\x14\n\x0cexternal_url\x18\x02 \x01(\t\x12\x10\n\x08protocol\x18\x03 \x01(\t\x12\x13\n\x0bvendor_type\x18\x04 \x01(\t\x12:\n\x0bvendor_info\x18\x05 \x01(\x0b2%.cz.proto.RemoteEntrypoint.VendorInfo\x1a/\n\nVendorInfo\x12\x0f\n\x07service\x18\x01 \x01(\t\x12\x10\n\x08function\x18\x02 \x01(\t"\x81\x02\n\x08Function\x12\x10\n\x08category\x18\x01 \x01(\t\x12\x11\n\texec_type\x18\x02 \x01(\t\x12\x11\n\tsignature\x18\x03 \x01(\t\x12\x0f\n\x07handler\x18\x04 \x01(\t\x123\n\nconnection\x18\x08 \x01(\x0b2\x1a.cz.proto.ObjectIdentifierH\x00\x88\x01\x01\x121\n\tresources\x18\x06 \x01(\x0b2\x1e.cz.proto.FunctionResourceList\x125\n\x11remote_entrypoint\x18\x07 \x01(\x0b2\x1a.cz.proto.RemoteEntrypointB\r\n\x0b_connectionb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'function_meta_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_FUNCTIONRESOURCE']._serialized_start = 58
    _globals['_FUNCTIONRESOURCE']._serialized_end = 133
    _globals['_FUNCTIONRESOURCELIST']._serialized_start = 135
    _globals['_FUNCTIONRESOURCELIST']._serialized_end = 204
    _globals['_REMOTEENTRYPOINT']._serialized_start = 207
    _globals['_REMOTEENTRYPOINT']._serialized_end = 417
    _globals['_REMOTEENTRYPOINT_VENDORINFO']._serialized_start = 370
    _globals['_REMOTEENTRYPOINT_VENDORINFO']._serialized_end = 417
    _globals['_FUNCTION']._serialized_start = 420
    _globals['_FUNCTION']._serialized_end = 677