"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'property.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0eproperty.proto\x12\x08cz.proto"&\n\x08Property\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t"4\n\nProperties\x12&\n\nproperties\x18\x01 \x03(\x0b2\x12.cz.proto.Property"\x1f\n\x0fPropertyKeyList\x12\x0c\n\x04keys\x18\x01 \x03(\tb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'property_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_PROPERTY']._serialized_start = 28
    _globals['_PROPERTY']._serialized_end = 66
    _globals['_PROPERTIES']._serialized_start = 68
    _globals['_PROPERTIES']._serialized_end = 120
    _globals['_PROPERTYKEYLIST']._serialized_start = 122
    _globals['_PROPERTYKEYLIST']._serialized_end = 153