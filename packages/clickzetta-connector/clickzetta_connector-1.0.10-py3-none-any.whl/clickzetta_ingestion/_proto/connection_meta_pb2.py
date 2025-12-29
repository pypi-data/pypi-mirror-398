"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'connection_meta.proto')
_sym_db = _symbol_database.Default()
from . import property_pb2 as property__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x15connection_meta.proto\x12\x08cz.proto\x1a\x0eproperty.proto"g\n\x18FileSystemConnectionInfo\x12\x18\n\x10file_system_type\x18\x01 \x01(\t\x12&\n\x06config\x182 \x01(\x0b2\x14.cz.proto.PropertiesH\x00B\t\n\x07derived"f\n\x0eConnectionInfo\x12I\n\x1bfile_system_connection_info\x182 \x01(\x0b2".cz.proto.FileSystemConnectionInfoH\x00B\t\n\x07derived"\xbe\x01\n\nConnection\x121\n\x0fconnection_type\x18\x01 \x01(\x0e2\x18.cz.proto.ConnectionType\x129\n\x13connection_category\x18\x02 \x01(\x0e2\x1c.cz.proto.ConnectionCategory\x12\x0f\n\x07enabled\x18\x03 \x01(\x08\x121\n\x0fconnection_info\x18\x04 \x01(\x0b2\x18.cz.proto.ConnectionInfo*5\n\x0eConnectionType\x12\x12\n\x0eCLOUD_FUNCTION\x10\x00\x12\x0f\n\x0bFILE_SYSTEM\x10\x01*=\n\x12ConnectionCategory\x12\x13\n\x0fDATA_CONNECTION\x10\x00\x12\x12\n\x0eAPI_CONNECTION\x10\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'connection_meta_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_CONNECTIONTYPE']._serialized_start = 453
    _globals['_CONNECTIONTYPE']._serialized_end = 506
    _globals['_CONNECTIONCATEGORY']._serialized_start = 508
    _globals['_CONNECTIONCATEGORY']._serialized_end = 569
    _globals['_FILESYSTEMCONNECTIONINFO']._serialized_start = 51
    _globals['_FILESYSTEMCONNECTIONINFO']._serialized_end = 154
    _globals['_CONNECTIONINFO']._serialized_start = 156
    _globals['_CONNECTIONINFO']._serialized_end = 258
    _globals['_CONNECTION']._serialized_start = 261
    _globals['_CONNECTION']._serialized_end = 451