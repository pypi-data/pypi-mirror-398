"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'file_meta_data.proto')
_sym_db = _symbol_database.Default()
from . import bucket_info_pb2 as bucket__info__pb2
from . import file_format_type_pb2 as file__format__type__pb2
from . import statistics_pb2 as statistics__pb2
from . import virtual_value_info_pb2 as virtual__value__info__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x14file_meta_data.proto\x12\x08cz.proto\x1a\x11bucket_info.proto\x1a\x16file_format_type.proto\x1a\x10statistics.proto\x1a\x18virtual_value_info.proto"+\n\tBlockInfo\x12\x0e\n\x06offset\x18\x01 \x01(\x04\x12\x0e\n\x06length\x18\x02 \x01(\x04"\xf1\x02\n\nDataLayout\x12#\n\x06footer\x18\x01 \x01(\x0b2\x13.cz.proto.BlockInfo\x12#\n\x06blocks\x18\x02 \x03(\x0b2\x13.cz.proto.BlockInfo\x12%\n\x07buckets\x18\x03 \x03(\x0b2\x14.cz.proto.BucketInfo\x12.\n\nvalue_info\x18\x04 \x03(\x0b2\x1a.cz.proto.VirtualValueInfo\x12)\n\x1coriginal_virtual_value_count\x18\x08 \x01(\rH\x00\x88\x01\x01\x12\x1d\n\x10row_index_stride\x18\x05 \x01(\x05H\x01\x88\x01\x01\x12\x18\n\x10block_row_counts\x18\x06 \x03(\x03\x12\x18\n\x0bdata_sealed\x18\t \x01(\x08H\x02\x88\x01\x01B\x1f\n\x1d_original_virtual_value_countB\x13\n\x11_row_index_strideB\x0e\n\x0c_data_sealed"\x80\x01\n\x10ExtendedMetaData\x12;\n\tkey_value\x18\x01 \x03(\x0b2(.cz.proto.ExtendedMetaData.KeyValueEntry\x1a/\n\rKeyValueEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"\xb5\x04\n\x0cFileMetaData\x12\x1b\n\x0edata_source_id\x18\x14 \x01(\rH\x00\x88\x01\x01\x12\x11\n\tfile_path\x18\x01 \x01(\t\x12-\n\x0bfile_format\x18\x02 \x01(\x0e2\x18.cz.proto.FileFormatType\x12%\n\tfile_type\x18\x03 \x01(\x0e2\x12.cz.proto.FileType\x12\x15\n\rfile_slice_id\x18\x04 \x01(\x03\x12\x1f\n\x12file_slice_version\x18\x05 \x01(\x03H\x01\x88\x01\x01\x12\x18\n\x10compaction_level\x18\x06 \x01(\x05\x12\x1c\n\x0fcluster_spec_id\x18\x07 \x01(\rH\x02\x88\x01\x01\x12\x1f\n\x12sort_order_spec_id\x18\x08 \x01(\rH\x03\x88\x01\x01\x12 \n\x13primary_key_spec_id\x18\t \x01(\rH\x04\x88\x01\x01\x12$\n\x06layout\x18\n \x01(\x0b2\x14.cz.proto.DataLayout\x125\n\x11extended_metadata\x18\x0b \x01(\x0b2\x1a.cz.proto.ExtendedMetaData\x12"\n\x05stats\x18\x10 \x01(\x0b2\x13.cz.proto.StatsDataB\x11\n\x0f_data_source_idB\x15\n\x13_file_slice_versionB\x12\n\x10_cluster_spec_idB\x15\n\x13_sort_order_spec_idB\x16\n\x14_primary_key_spec_id*;\n\x08FileType\x12\x10\n\x0cUNKNOWN_FILE\x10\x00\x12\r\n\tDATA_FILE\x10\x01\x12\x0e\n\nDELTA_FILE\x10\x02B\x1f\n\x08cz.protoB\x11FileMetaDataProtoP\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'file_meta_data_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x08cz.protoB\x11FileMetaDataProtoP\x01'
    _globals['_EXTENDEDMETADATA_KEYVALUEENTRY']._loaded_options = None
    _globals['_EXTENDEDMETADATA_KEYVALUEENTRY']._serialized_options = b'8\x01'
    _globals['_FILETYPE']._serialized_start = 1237
    _globals['_FILETYPE']._serialized_end = 1296
    _globals['_BLOCKINFO']._serialized_start = 121
    _globals['_BLOCKINFO']._serialized_end = 164
    _globals['_DATALAYOUT']._serialized_start = 167
    _globals['_DATALAYOUT']._serialized_end = 536
    _globals['_EXTENDEDMETADATA']._serialized_start = 539
    _globals['_EXTENDEDMETADATA']._serialized_end = 667
    _globals['_EXTENDEDMETADATA_KEYVALUEENTRY']._serialized_start = 620
    _globals['_EXTENDEDMETADATA_KEYVALUEENTRY']._serialized_end = 667
    _globals['_FILEMETADATA']._serialized_start = 670
    _globals['_FILEMETADATA']._serialized_end = 1235