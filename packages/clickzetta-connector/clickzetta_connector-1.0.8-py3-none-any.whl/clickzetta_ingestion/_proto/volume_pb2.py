"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'volume.proto')
_sym_db = _symbol_database.Default()
from . import object_identifier_pb2 as object__identifier__pb2
from . import storage_location_pb2 as storage__location__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0cvolume.proto\x12\x08cz.proto\x1a\x17object_identifier.proto\x1a\x16storage_location.proto"\xec\x02\n\x06Volume\x12)\n\x0bvolume_type\x18\x01 \x01(\x0e2\x14.cz.proto.VolumeType\x12\x0b\n\x03url\x18\x02 \x01(\t\x123\n\nconnection\x18\x03 \x01(\x0b2\x1a.cz.proto.ObjectIdentifierH\x00\x88\x01\x01\x128\n\x0fmeta_collection\x18\x04 \x01(\x0b2\x1f.cz.proto.Volume.MetaCollection\x12\x11\n\trecursive\x18\x05 \x01(\x08\x122\n\x0efilemeta_table\x18\x06 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12-\n\rlocation_info\x18\x07 \x01(\x0b2\x16.cz.proto.LocationInfo\x1a6\n\x0eMetaCollection\x12\x0e\n\x06enable\x18\x01 \x01(\x08\x12\x14\n\x0cauto_refresh\x18\x02 \x01(\x08B\r\n\x0b_connection"\x98\x02\n\x19VolumeFileTransferRequest\x12\x0f\n\x07command\x18\x01 \x01(\t\x12\x13\n\x0blocal_paths\x18\x02 \x03(\t\x12\x0e\n\x06volume\x18\x03 \x01(\t\x12\x19\n\x11volume_identifier\x18\x07 \x01(\t\x12\x19\n\x0csubdirectory\x18\x04 \x01(\tH\x00\x88\x01\x01\x12\x11\n\x04file\x18\x05 \x01(\tH\x01\x88\x01\x01\x12;\n\x07options\x18\x06 \x03(\x0b2*.cz.proto.VolumeFileTransferRequest.Option\x1a%\n\x06Option\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\tB\x0f\n\r_subdirectoryB\x07\n\x05_file"2\n\x18VolumeFileTransferTicket\x12\x16\n\x0epresigned_urls\x18\x01 \x03(\t"\xab\x02\n\x19VolumeFileTransferOutcome\x12:\n\x06status\x18\x01 \x01(\x0e2*.cz.proto.VolumeFileTransferOutcome.Status\x12\r\n\x05error\x18\x02 \x01(\t\x124\n\x07request\x18\x03 \x01(\x0b2#.cz.proto.VolumeFileTransferRequest\x122\n\x06ticket\x18\x04 \x01(\x0b2".cz.proto.VolumeFileTransferTicket\x12\x18\n\x0bnext_marker\x18\x05 \x01(\tH\x00\x88\x01\x01"/\n\x06Status\x12\x0b\n\x07SUCCESS\x10\x00\x12\n\n\x06FAILED\x10\x01\x12\x0c\n\x08CONTINUE\x10\x02B\x0e\n\x0c_next_marker*-\n\nVolumeType\x12\x0e\n\nVT_MANAGED\x10\x00\x12\x0f\n\x0bVT_EXTERNAL\x10\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'volume_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_VOLUMETYPE']._serialized_start = 1079
    _globals['_VOLUMETYPE']._serialized_end = 1124
    _globals['_VOLUME']._serialized_start = 76
    _globals['_VOLUME']._serialized_end = 440
    _globals['_VOLUME_METACOLLECTION']._serialized_start = 371
    _globals['_VOLUME_METACOLLECTION']._serialized_end = 425
    _globals['_VOLUMEFILETRANSFERREQUEST']._serialized_start = 443
    _globals['_VOLUMEFILETRANSFERREQUEST']._serialized_end = 723
    _globals['_VOLUMEFILETRANSFERREQUEST_OPTION']._serialized_start = 660
    _globals['_VOLUMEFILETRANSFERREQUEST_OPTION']._serialized_end = 697
    _globals['_VOLUMEFILETRANSFERTICKET']._serialized_start = 725
    _globals['_VOLUMEFILETRANSFERTICKET']._serialized_end = 775
    _globals['_VOLUMEFILETRANSFEROUTCOME']._serialized_start = 778
    _globals['_VOLUMEFILETRANSFEROUTCOME']._serialized_end = 1077
    _globals['_VOLUMEFILETRANSFEROUTCOME_STATUS']._serialized_start = 1014
    _globals['_VOLUMEFILETRANSFEROUTCOME_STATUS']._serialized_end = 1061