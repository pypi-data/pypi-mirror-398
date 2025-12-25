"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'table_meta.proto')
_sym_db = _symbol_database.Default()
from . import table_common_pb2 as table__common__pb2
from . import object_identifier_pb2 as object__identifier__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10table_meta.proto\x12\x08cz.proto\x1a\x12table_common.proto\x1a\x17object_identifier.proto"S\n\x0fTableSchemaList\x12&\n\x07schemas\x18\x01 \x03(\x0b2\x15.cz.proto.TableSchema\x12\x18\n\x10highest_field_id\x18\x03 \x01(\r"L\n\rFieldSpecList\x12"\n\x05specs\x18\x01 \x03(\x0b2\x13.cz.proto.FieldSpec\x12\x17\n\x0fcurrent_spec_id\x18\x02 \x01(\r"]\n\x16CompositeFieldSpecList\x12*\n\tspec_list\x18\x01 \x03(\x0b2\x17.cz.proto.FieldSpecList\x12\x17\n\x0fcurrent_spec_id\x18\x02 \x01(\r"=\n\x0cDataFileInfo\x12\x11\n\tfile_path\x18\x01 \x01(\t\x12\x1a\n\x12file_size_in_bytes\x18\x02 \x01(\x04"{\n\x13DataFileSplitSource\x124\n\x10table_identifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12.\n\x0edata_file_info\x18\x02 \x03(\x0b2\x16.cz.proto.DataFileInfo"\xa5\x01\n\x0fTableFormatInfo\x12\x13\n\x0bsnapshot_id\x18\x01 \x01(\x03\x124\n\x07iceberg\x18\n \x01(\x0b2!.cz.proto.TableFormatInfo.IcebergH\x00\x1a=\n\x07Iceberg\x12\x19\n\x11metadata_location\x18\x01 \x01(\t\x12\x17\n\x0fcurrent_version\x18\x02 \x01(\x03B\x08\n\x06format"D\n\x0bTableFormat\x125\n\x12table_format_infos\x18\x01 \x03(\x0b2\x19.cz.proto.TableFormatInfo"\xc0\x04\n\tTableMeta\x12\x10\n\x08table_id\x18\x01 \x01(\x03\x12\'\n\ntable_type\x18\x02 \x01(\x0e2\x13.cz.proto.TableType\x12+\n\x0ctable_schema\x18\x0f \x01(\x0b2\x15.cz.proto.TableSchema\x12)\n\x0bdata_source\x18\x10 \x01(\x0b2\x14.cz.proto.DataSource\x12-\n\x10primary_key_spec\x18\x15 \x01(\x0b2\x13.cz.proto.FieldSpec\x12,\n\x0fsort_order_spec\x18\x16 \x01(\x0b2\x13.cz.proto.FieldSpec\x12.\n\x11cluster_info_spec\x18\x17 \x03(\x0b2\x13.cz.proto.FieldSpec\x12,\n\x0funique_key_spec\x18\x18 \x03(\x0b2\x13.cz.proto.FieldSpec\x12\'\n\nindex_spec\x18\x1a \x03(\x0b2\x13.cz.proto.FieldSpec\x12-\n\x10foreign_key_spec\x18\x1f \x03(\x0b2\x13.cz.proto.FieldSpec\x12\x1c\n\x04view\x18\x19 \x01(\x0b2\x0e.cz.proto.View\x12\x1b\n\x13current_snapshot_id\x18\x1b \x01(\x03\x12+\n\x0ctable_format\x18\x1e \x01(\x0b2\x15.cz.proto.TableFormat\x12%\n\x06stream\x18  \x01(\x0b2\x15.cz.proto.TableStreamB\x0c\n\x08cz.protoP\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'table_meta_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x08cz.protoP\x01'
    _globals['_TABLESCHEMALIST']._serialized_start = 75
    _globals['_TABLESCHEMALIST']._serialized_end = 158
    _globals['_FIELDSPECLIST']._serialized_start = 160
    _globals['_FIELDSPECLIST']._serialized_end = 236
    _globals['_COMPOSITEFIELDSPECLIST']._serialized_start = 238
    _globals['_COMPOSITEFIELDSPECLIST']._serialized_end = 331
    _globals['_DATAFILEINFO']._serialized_start = 333
    _globals['_DATAFILEINFO']._serialized_end = 394
    _globals['_DATAFILESPLITSOURCE']._serialized_start = 396
    _globals['_DATAFILESPLITSOURCE']._serialized_end = 519
    _globals['_TABLEFORMATINFO']._serialized_start = 522
    _globals['_TABLEFORMATINFO']._serialized_end = 687
    _globals['_TABLEFORMATINFO_ICEBERG']._serialized_start = 616
    _globals['_TABLEFORMATINFO_ICEBERG']._serialized_end = 677
    _globals['_TABLEFORMAT']._serialized_start = 689
    _globals['_TABLEFORMAT']._serialized_end = 757
    _globals['_TABLEMETA']._serialized_start = 760
    _globals['_TABLEMETA']._serialized_end = 1336