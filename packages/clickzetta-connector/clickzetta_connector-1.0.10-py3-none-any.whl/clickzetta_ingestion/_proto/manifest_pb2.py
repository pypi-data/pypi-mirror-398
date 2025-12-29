"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'manifest.proto')
_sym_db = _symbol_database.Default()
from . import expression_pb2 as expression__pb2
from . import file_meta_data_pb2 as file__meta__data__pb2
from . import table_common_pb2 as table__common__pb2
from . import statistics_pb2 as statistics__pb2
from . import virtual_value_info_pb2 as virtual__value__info__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0emanifest.proto\x12\x08cz.proto\x1a\x10expression.proto\x1a\x14file_meta_data.proto\x1a\x12table_common.proto\x1a\x10statistics.proto\x1a\x18virtual_value_info.proto"\x9b\x05\n\x08Manifest\x12\x17\n\x0fcluster_spec_id\x18\x07 \x01(\r\x12\x1a\n\x12sort_order_spec_id\x18\x08 \x01(\r\x12\x1b\n\x13primary_key_spec_id\x18\t \x01(\r\x12"\n\x05stats\x18\n \x01(\x0b2\x13.cz.proto.StatsData\x12\x1d\n\x10base_snapshot_id\x18\x0e \x01(\x03H\x00\x88\x01\x01\x12C\n\x11concurrency_level\x18\x15 \x01(\x0e2#.cz.proto.Manifest.ConcurrencyLevelH\x01\x88\x01\x01\x120\n\x10added_data_files\x18\x0f \x03(\x0b2\x16.cz.proto.FileMetaData\x122\n\x12deleted_data_files\x18\x11 \x03(\x0b2\x16.cz.proto.FileMetaData\x121\n\x11added_delta_files\x18\x12 \x03(\x0b2\x16.cz.proto.FileMetaData\x123\n\x13deleted_delta_files\x18\x13 \x03(\x0b2\x16.cz.proto.FileMetaData\x125\n\x11deleted_partition\x18\x05 \x03(\x0b2\x1a.cz.proto.VirtualValueInfo\x12)\n\rsource_tables\x18\x14 \x03(\x0b2\x12.cz.proto.MVSource\x121\n\rstream_tables\x18\x16 \x03(\x0b2\x1a.cz.proto.TableStreamState"\'\n\x10ConcurrencyLevel\x12\x08\n\x04FILE\x10\x00\x12\t\n\x05TABLE\x10\x01B\x13\n\x11_base_snapshot_idB\x14\n\x12_concurrency_level"}\n\x0eManifestLayout\x12.\n\nvalue_info\x18\x01 \x03(\x0b2\x1a.cz.proto.VirtualValueInfo\x12"\n\x05stats\x18\x02 \x03(\x0b2\x13.cz.proto.StatsData\x12\x17\n\x0fdata_source_ids\x18\x03 \x03(\x03*#\n\x0cManifestType\x12\x08\n\x04DATA\x10\x00\x12\t\n\x05DELTA\x10\x01B\x11B\rManifestProtoP\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'manifest_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'B\rManifestProtoP\x01'
    _globals['_MANIFESTTYPE']._serialized_start = 929
    _globals['_MANIFESTTYPE']._serialized_end = 964
    _globals['_MANIFEST']._serialized_start = 133
    _globals['_MANIFEST']._serialized_end = 800
    _globals['_MANIFEST_CONCURRENCYLEVEL']._serialized_start = 718
    _globals['_MANIFEST_CONCURRENCYLEVEL']._serialized_end = 757
    _globals['_MANIFESTLAYOUT']._serialized_start = 802
    _globals['_MANIFESTLAYOUT']._serialized_end = 927