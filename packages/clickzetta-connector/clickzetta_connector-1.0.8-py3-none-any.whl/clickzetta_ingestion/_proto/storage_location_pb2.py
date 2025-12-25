"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'storage_location.proto')
_sym_db = _symbol_database.Default()
from . import object_identifier_pb2 as object__identifier__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x16storage_location.proto\x12\x08cz.proto\x1a\x17object_identifier.proto"E\n\x12FileSystemLocation\x12/\n\x0bfile_format\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier"\x12\n\x10DatabaseLocation"~\n\x0cLocationInfo\x123\n\x0bfile_system\x18\x14 \x01(\x0b2\x1c.cz.proto.FileSystemLocationH\x00\x12.\n\x08database\x18\x15 \x01(\x0b2\x1a.cz.proto.DatabaseLocationH\x00B\t\n\x07derived"\xd1\x02\n\x0fStorageLocation\x12\x10\n\x08external\x18\x01 \x01(\x08\x12\x0b\n\x03url\x18\x02 \x01(\t\x12.\n\nconnection\x18\x03 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12A\n\x0fmeta_collection\x18\x04 \x01(\x0b2(.cz.proto.StorageLocation.MetaCollection\x12\x11\n\trecursive\x18\x05 \x01(\x08\x122\n\x0efilemeta_table\x18\x06 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12-\n\rlocation_info\x18\x07 \x01(\x0b2\x16.cz.proto.LocationInfo\x1a6\n\x0eMetaCollection\x12\x0e\n\x06enable\x18\x01 \x01(\x08\x12\x14\n\x0cauto_refresh\x18\x02 \x01(\x08b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'storage_location_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_FILESYSTEMLOCATION']._serialized_start = 61
    _globals['_FILESYSTEMLOCATION']._serialized_end = 130
    _globals['_DATABASELOCATION']._serialized_start = 132
    _globals['_DATABASELOCATION']._serialized_end = 150
    _globals['_LOCATIONINFO']._serialized_start = 152
    _globals['_LOCATIONINFO']._serialized_end = 278
    _globals['_STORAGELOCATION']._serialized_start = 281
    _globals['_STORAGELOCATION']._serialized_end = 618
    _globals['_STORAGELOCATION_METACOLLECTION']._serialized_start = 564
    _globals['_STORAGELOCATION_METACOLLECTION']._serialized_end = 618