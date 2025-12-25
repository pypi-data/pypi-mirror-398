"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'table_common.proto')
_sym_db = _symbol_database.Default()
from . import data_type_pb2 as data__type__pb2
from . import file_format_type_pb2 as file__format__type__pb2
from . import file_system_pb2 as file__system__pb2
from . import object_identifier_pb2 as object__identifier__pb2
from . import storage_location_pb2 as storage__location__pb2
from . import connection_meta_pb2 as connection__meta__pb2
from . import expression_pb2 as expression__pb2
from . import property_pb2 as property__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x12table_common.proto\x12\x08cz.proto\x1a\x0fdata_type.proto\x1a\x16file_format_type.proto\x1a\x11file_system.proto\x1a\x17object_identifier.proto\x1a\x16storage_location.proto\x1a\x15connection_meta.proto\x1a\x10expression.proto\x1a\x0eproperty.proto"=\n\x08FieldRef\x12\x12\n\x08field_id\x18\x01 \x01(\rH\x00\x12\x14\n\nfield_name\x18\x02 \x01(\tH\x00B\x07\n\x05field"U\n\x0bSortedField\x12!\n\x05field\x18\x01 \x01(\x0b2\x12.cz.proto.FieldRef\x12#\n\nsort_order\x18\x02 \x01(\x0e2\x0f.cz.proto.Order"V\n\x0bHashCluster\x12\x18\n\x10function_version\x18\x01 \x01(\r\x12-\n\x0bbucket_type\x18\x02 \x01(\x0e2\x18.cz.proto.HashBucketType"7\n\x0cRangeCluster\x12\'\n\nrange_type\x18\x01 \x01(\x0e2\x13.cz.proto.RangeType"\x9d\x02\n\x0bClusterInfo\x12+\n\x0ccluster_type\x18\x01 \x01(\x0e2\x15.cz.proto.ClusterType\x12,\n\x10clustered_fields\x18\x02 \x03(\x0b2\x12.cz.proto.FieldRef\x12\x1a\n\rbuckets_count\x18\x03 \x01(\x04H\x01\x88\x01\x01\x12\x19\n\x0cpath_pattern\x18\x04 \x01(\tH\x02\x88\x01\x01\x12%\n\x04hash\x18\n \x01(\x0b2\x15.cz.proto.HashClusterH\x00\x12\'\n\x05range\x18\x0b \x01(\x0b2\x16.cz.proto.RangeClusterH\x00B\t\n\x07clusterB\x10\n\x0e_buckets_countB\x0f\n\r_path_pattern"9\n\tSortOrder\x12,\n\rsorted_fields\x18\x01 \x03(\x0b2\x15.cz.proto.SortedField"f\n\tUniqueKey\x12)\n\runique_fields\x18\x01 \x03(\x0b2\x12.cz.proto.FieldRef\x12\x0e\n\x06enable\x18\x02 \x01(\x08\x12\x10\n\x08validate\x18\x03 \x01(\x08\x12\x0c\n\x04rely\x18\x04 \x01(\x08"`\n\nPrimaryKey\x12"\n\x06fields\x18\x01 \x03(\x0b2\x12.cz.proto.FieldRef\x12\x0e\n\x06enable\x18\x02 \x01(\x08\x12\x10\n\x08validate\x18\x03 \x01(\x08\x12\x0c\n\x04rely\x18\x04 \x01(\x08"\xb7\x01\n\nForeignKey\x12"\n\x06fields\x18\x01 \x03(\x0b2\x12.cz.proto.FieldRef\x12-\n\tref_table\x18\x02 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12&\n\nref_fields\x18\x03 \x03(\x0b2\x12.cz.proto.FieldRef\x12\x0e\n\x06enable\x18\x04 \x01(\x08\x12\x10\n\x08validate\x18\x05 \x01(\x08\x12\x0c\n\x04rely\x18\x06 \x01(\x08".\n\x08IndexKey\x12"\n\x06fields\x18\x01 \x03(\x0b2\x12.cz.proto.FieldRef"v\n\x05Index\x12!\n\x04type\x18\x01 \x01(\x0e2\x13.cz.proto.IndexType\x12\x1f\n\x03key\x18\x02 \x01(\x0b2\x12.cz.proto.IndexKey\x12)\n\x05table\x18\x03 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier"\xa5\x02\n\tFieldSpec\x12\x0f\n\x07spec_id\x18\x01 \x01(\r\x12-\n\x0ccluster_info\x18\n \x01(\x0b2\x15.cz.proto.ClusterInfoH\x00\x12)\n\nsort_order\x18\x0b \x01(\x0b2\x13.cz.proto.SortOrderH\x00\x12)\n\nunique_key\x18\x0c \x01(\x0b2\x13.cz.proto.UniqueKeyH\x00\x12+\n\x0bprimary_key\x18\r \x01(\x0b2\x14.cz.proto.PrimaryKeyH\x00\x12 \n\x05index\x18\x0e \x01(\x0b2\x0f.cz.proto.IndexH\x00\x12+\n\x0bforeign_key\x18\x0f \x01(\x0b2\x14.cz.proto.ForeignKeyH\x00B\x06\n\x04spec"\x86\x02\n\x0bFieldSchema\x12\x0c\n\x04name\x18\x02 \x01(\t\x12 \n\x04type\x18\x03 \x01(\x0b2\x12.cz.proto.DataType\x12\x14\n\x07virtual\x18\x04 \x01(\x08H\x00\x88\x01\x01\x12\x13\n\x06hidden\x18\x05 \x01(\x08H\x01\x88\x01\x01\x12\x16\n\tun_output\x18\x06 \x01(\x08H\x02\x88\x01\x01\x12\x0f\n\x07comment\x18\x07 \x01(\t\x12(\n\x04expr\x18\x08 \x01(\x0b2\x1a.cz.proto.ScalarExpression\x12\x16\n\ttransform\x18\t \x01(\tH\x03\x88\x01\x01B\n\n\x08_virtualB\t\n\x07_hiddenB\x0c\n\n_un_outputB\x0c\n\n_transform"U\n\x0bTableSchema\x12%\n\x06fields\x18\x01 \x03(\x0b2\x15.cz.proto.FieldSchema\x12\x11\n\tschema_id\x18\x02 \x01(\r\x12\x0c\n\x04type\x18\x03 \x01(\t"x\n\x0eTextFileFormat\x126\n\x07options\x18\x01 \x03(\x0b2%.cz.proto.TextFileFormat.OptionsEntry\x1a.\n\x0cOptionsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"c\n\x11ParquetFileFormat\x12\x1c\n\x14row_group_size_bytes\x18\x01 \x01(\x03\x12\x17\n\x0fpage_size_bytes\x18\x02 \x01(\x03\x12\x17\n\x0fdict_size_bytes\x18\x03 \x01(\x03"\x0f\n\rOrcFileFormat"v\n\rCsvFileFormat\x125\n\x07options\x18\x01 \x03(\x0b2$.cz.proto.CsvFileFormat.OptionsEntry\x1a.\n\x0cOptionsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"\x84\x01\n\x14HiveResultFileFormat\x12<\n\x07options\x18\x01 \x03(\x0b2+.cz.proto.HiveResultFileFormat.OptionsEntry\x1a.\n\x0cOptionsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"\x10\n\x0eAvroFileFormat"\x11\n\x0fArrowFileFormat"\x97\x03\n\nFileFormat\x12&\n\x04type\x18\x01 \x01(\x0e2\x18.cz.proto.FileFormatType\x12,\n\x08textFile\x18\x02 \x01(\x0b2\x18.cz.proto.TextFileFormatH\x00\x123\n\x0cparquet_file\x18\x03 \x01(\x0b2\x1b.cz.proto.ParquetFileFormatH\x00\x12+\n\x08orc_file\x18\x04 \x01(\x0b2\x17.cz.proto.OrcFileFormatH\x00\x12+\n\x08csv_file\x18\x05 \x01(\x0b2\x17.cz.proto.CsvFileFormatH\x00\x12:\n\x10hive_result_file\x18\x06 \x01(\x0b2\x1e.cz.proto.HiveResultFileFormatH\x00\x12-\n\tavro_file\x18\x07 \x01(\x0b2\x18.cz.proto.AvroFileFormatH\x00\x12/\n\narrow_file\x18\x08 \x01(\x0b2\x19.cz.proto.ArrowFileFormatH\x00B\x08\n\x06format"z\n\x12FileDataSourceInfo\x120\n\x0efileSystemType\x18\x01 \x01(\x0e2\x18.cz.proto.FileSystemType\x12\x0c\n\x04path\x18\x02 \x01(\t\x12$\n\x06format\x18\x03 \x01(\x0b2\x14.cz.proto.FileFormat"\x13\n\x11DqlDataSourceInfo"\xbb\x01\n\x1fLocationDirectoryDataSourceInfo\x123\n\x10storage_location\x18\x01 \x01(\x0b2\x19.cz.proto.StorageLocation\x12;\n\x0fconnection_info\x18\x02 \x01(\x0b2".cz.proto.FileSystemConnectionInfo\x12&\n\nproperties\x18\x03 \x03(\x0b2\x12.cz.proto.Property"n\n\x0eDataProperties\x12.\n\x11cluster_info_spec\x18\x01 \x03(\x0b2\x13.cz.proto.FieldSpec\x12,\n\x0fsort_order_spec\x18\x02 \x01(\x0b2\x13.cz.proto.FieldSpec"\xcb\x03\n\x0eDataSourceInfo\x12\x18\n\x10data_source_type\x18\x07 \x01(\x05\x12,\n\x04file\x18\x01 \x01(\x0b2\x1c.cz.proto.FileDataSourceInfoH\x00\x12*\n\x03dql\x18\x05 \x01(\x0b2\x1b.cz.proto.DqlDataSourceInfoH\x00\x12G\n\x12location_directory\x18\x08 \x01(\x0b2).cz.proto.LocationDirectoryDataSourceInfoH\x00\x126\n\x07options\x18\x02 \x03(\x0b2%.cz.proto.DataSourceInfo.OptionsEntry\x12\x10\n\x08location\x18\x03 \x01(\t\x12\x1b\n\x0edata_source_id\x18\x04 \x01(\rH\x01\x88\x01\x01\x121\n\ndata_props\x18\x06 \x01(\x0b2\x18.cz.proto.DataPropertiesH\x02\x88\x01\x01\x1a.\n\x0cOptionsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01B\x10\n\x0edataSourceInfoB\x11\n\x0f_data_source_idB\r\n\x0b_data_props"\x9b\x01\n\nDataSource\x123\n\x11data_source_infos\x18\x11 \x03(\x0b2\x18.cz.proto.DataSourceInfo\x12\x1e\n\x16default_data_source_id\x18\x12 \x01(\r\x12 \n\x13next_data_source_id\x18\x13 \x01(\rH\x00\x88\x01\x01B\x16\n\x14_next_data_source_id"R\n\x08MVSource\x124\n\x10table_identifier\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12\x10\n\x08snapshot\x18\x02 \x01(\x03"\xa2\x01\n\rRefreshOption\x12*\n\x04type\x18\x01 \x01(\x0e2\x1c.cz.proto.RefreshOption.Type\x12\x12\n\nstart_time\x18\x02 \x01(\x03\x12\x1a\n\x12interval_in_minute\x18\x03 \x01(\x03"5\n\x04Type\x12\r\n\tON_DEMAND\x10\x00\x12\r\n\tON_COMMIT\x10\x01\x12\x0f\n\x0bON_SCHEDULE\x10\x02"G\n\x14IncrementalExtension\x12\x18\n\x10isValueSemantics\x18\x01 \x01(\x08\x12\x15\n\rformatVersion\x18\x02 \x01(\x03"\x8b\x02\n\x0bMVExtension\x12\x0f\n\x07mv_plan\x18\x01 \x01(\t\x12,\n\x10mv_source_tables\x18\x02 \x03(\x0b2\x12.cz.proto.MVSource\x12/\n\x0erefresh_option\x18\x03 \x01(\x0b2\x17.cz.proto.RefreshOption\x12\x1b\n\x0emv_snapshot_id\x18\x04 \x01(\x03H\x00\x88\x01\x01\x12B\n\x15incremental_extension\x18\x05 \x01(\x0b2\x1e.cz.proto.IncrementalExtensionH\x01\x88\x01\x01B\x11\n\x0f_mv_snapshot_idB\x18\n\x16_incremental_extension"k\n\x04View\x12\x1a\n\x12view_expanded_text\x18\x01 \x01(\t\x12\x1a\n\x12view_original_text\x18\x02 \x01(\t\x12+\n\x0cmv_extension\x18\x05 \x01(\x0b2\x15.cz.proto.MVExtension"w\n\x0bTableStream\x12,\n\x08provider\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12\x19\n\x0cat_timestamp\x18\x03 \x01(\x03H\x00\x88\x01\x01\x12\x0e\n\x06offset\x18\x04 \x01(\x03B\x0f\n\r_at_timestamp"j\n\x10TableStreamState\x12*\n\x06stream\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12\x15\n\rfrom_snapshot\x18\x02 \x01(\x03\x12\x13\n\x0bto_snapshot\x18\x03 \x01(\x03*\x1a\n\x05Order\x12\x07\n\x03ASC\x10\x00\x12\x08\n\x04DESC\x10\x01*)\n\tNullOrder\x12\x07\n\x03LOW\x10\x00\x12\t\n\x05FIRST\x10\x01\x12\x08\n\x04LAST\x10\x02*.\n\x0bClusterType\x12\n\n\x06NORMAL\x10\x00\x12\t\n\x05RANGE\x10\x01\x12\x08\n\x04HASH\x10\x02*.\n\x0eHashBucketType\x12\x0c\n\x08HASH_MOD\x10\x00\x12\x0e\n\nHASH_RANGE\x10\x01*z\n\tTableType\x12\x11\n\rMANAGED_TABLE\x10\x00\x12\x12\n\x0eEXTERNAL_TABLE\x10\x02\x12\x10\n\x0cVIRTUAL_VIEW\x10\x04\x12\x15\n\x11MATERIALIZED_VIEW\x10\x06\x12\n\n\x06STREAM\x10\x08\x12\x11\n\rUNKNOWN_TABLE\x10c*)\n\tIndexType\x12\x10\n\x0cBLOOM_FILTER\x10\x00\x12\n\n\x06BITSET\x10\x01*@\n\tRangeType\x12\x0f\n\x0bFIXED_POINT\x10\x00\x12\x0f\n\x0bFIXED_RANGE\x10\x02\x12\x11\n\rDYNAMIC_RANGE\x10\x04B\x0c\n\x08cz.protoP\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'table_common_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x08cz.protoP\x01'
    _globals['_TEXTFILEFORMAT_OPTIONSENTRY']._loaded_options = None
    _globals['_TEXTFILEFORMAT_OPTIONSENTRY']._serialized_options = b'8\x01'
    _globals['_CSVFILEFORMAT_OPTIONSENTRY']._loaded_options = None
    _globals['_CSVFILEFORMAT_OPTIONSENTRY']._serialized_options = b'8\x01'
    _globals['_HIVERESULTFILEFORMAT_OPTIONSENTRY']._loaded_options = None
    _globals['_HIVERESULTFILEFORMAT_OPTIONSENTRY']._serialized_options = b'8\x01'
    _globals['_DATASOURCEINFO_OPTIONSENTRY']._loaded_options = None
    _globals['_DATASOURCEINFO_OPTIONSENTRY']._serialized_options = b'8\x01'
    _globals['_ORDER']._serialized_start = 4983
    _globals['_ORDER']._serialized_end = 5009
    _globals['_NULLORDER']._serialized_start = 5011
    _globals['_NULLORDER']._serialized_end = 5052
    _globals['_CLUSTERTYPE']._serialized_start = 5054
    _globals['_CLUSTERTYPE']._serialized_end = 5100
    _globals['_HASHBUCKETTYPE']._serialized_start = 5102
    _globals['_HASHBUCKETTYPE']._serialized_end = 5148
    _globals['_TABLETYPE']._serialized_start = 5150
    _globals['_TABLETYPE']._serialized_end = 5272
    _globals['_INDEXTYPE']._serialized_start = 5274
    _globals['_INDEXTYPE']._serialized_end = 5315
    _globals['_RANGETYPE']._serialized_start = 5317
    _globals['_RANGETYPE']._serialized_end = 5381
    _globals['_FIELDREF']._serialized_start = 198
    _globals['_FIELDREF']._serialized_end = 259
    _globals['_SORTEDFIELD']._serialized_start = 261
    _globals['_SORTEDFIELD']._serialized_end = 346
    _globals['_HASHCLUSTER']._serialized_start = 348
    _globals['_HASHCLUSTER']._serialized_end = 434
    _globals['_RANGECLUSTER']._serialized_start = 436
    _globals['_RANGECLUSTER']._serialized_end = 491
    _globals['_CLUSTERINFO']._serialized_start = 494
    _globals['_CLUSTERINFO']._serialized_end = 779
    _globals['_SORTORDER']._serialized_start = 781
    _globals['_SORTORDER']._serialized_end = 838
    _globals['_UNIQUEKEY']._serialized_start = 840
    _globals['_UNIQUEKEY']._serialized_end = 942
    _globals['_PRIMARYKEY']._serialized_start = 944
    _globals['_PRIMARYKEY']._serialized_end = 1040
    _globals['_FOREIGNKEY']._serialized_start = 1043
    _globals['_FOREIGNKEY']._serialized_end = 1226
    _globals['_INDEXKEY']._serialized_start = 1228
    _globals['_INDEXKEY']._serialized_end = 1274
    _globals['_INDEX']._serialized_start = 1276
    _globals['_INDEX']._serialized_end = 1394
    _globals['_FIELDSPEC']._serialized_start = 1397
    _globals['_FIELDSPEC']._serialized_end = 1690
    _globals['_FIELDSCHEMA']._serialized_start = 1693
    _globals['_FIELDSCHEMA']._serialized_end = 1955
    _globals['_TABLESCHEMA']._serialized_start = 1957
    _globals['_TABLESCHEMA']._serialized_end = 2042
    _globals['_TEXTFILEFORMAT']._serialized_start = 2044
    _globals['_TEXTFILEFORMAT']._serialized_end = 2164
    _globals['_TEXTFILEFORMAT_OPTIONSENTRY']._serialized_start = 2118
    _globals['_TEXTFILEFORMAT_OPTIONSENTRY']._serialized_end = 2164
    _globals['_PARQUETFILEFORMAT']._serialized_start = 2166
    _globals['_PARQUETFILEFORMAT']._serialized_end = 2265
    _globals['_ORCFILEFORMAT']._serialized_start = 2267
    _globals['_ORCFILEFORMAT']._serialized_end = 2282
    _globals['_CSVFILEFORMAT']._serialized_start = 2284
    _globals['_CSVFILEFORMAT']._serialized_end = 2402
    _globals['_CSVFILEFORMAT_OPTIONSENTRY']._serialized_start = 2118
    _globals['_CSVFILEFORMAT_OPTIONSENTRY']._serialized_end = 2164
    _globals['_HIVERESULTFILEFORMAT']._serialized_start = 2405
    _globals['_HIVERESULTFILEFORMAT']._serialized_end = 2537
    _globals['_HIVERESULTFILEFORMAT_OPTIONSENTRY']._serialized_start = 2118
    _globals['_HIVERESULTFILEFORMAT_OPTIONSENTRY']._serialized_end = 2164
    _globals['_AVROFILEFORMAT']._serialized_start = 2539
    _globals['_AVROFILEFORMAT']._serialized_end = 2555
    _globals['_ARROWFILEFORMAT']._serialized_start = 2557
    _globals['_ARROWFILEFORMAT']._serialized_end = 2574
    _globals['_FILEFORMAT']._serialized_start = 2577
    _globals['_FILEFORMAT']._serialized_end = 2984
    _globals['_FILEDATASOURCEINFO']._serialized_start = 2986
    _globals['_FILEDATASOURCEINFO']._serialized_end = 3108
    _globals['_DQLDATASOURCEINFO']._serialized_start = 3110
    _globals['_DQLDATASOURCEINFO']._serialized_end = 3129
    _globals['_LOCATIONDIRECTORYDATASOURCEINFO']._serialized_start = 3132
    _globals['_LOCATIONDIRECTORYDATASOURCEINFO']._serialized_end = 3319
    _globals['_DATAPROPERTIES']._serialized_start = 3321
    _globals['_DATAPROPERTIES']._serialized_end = 3431
    _globals['_DATASOURCEINFO']._serialized_start = 3434
    _globals['_DATASOURCEINFO']._serialized_end = 3893
    _globals['_DATASOURCEINFO_OPTIONSENTRY']._serialized_start = 2118
    _globals['_DATASOURCEINFO_OPTIONSENTRY']._serialized_end = 2164
    _globals['_DATASOURCE']._serialized_start = 3896
    _globals['_DATASOURCE']._serialized_end = 4051
    _globals['_MVSOURCE']._serialized_start = 4053
    _globals['_MVSOURCE']._serialized_end = 4135
    _globals['_REFRESHOPTION']._serialized_start = 4138
    _globals['_REFRESHOPTION']._serialized_end = 4300
    _globals['_REFRESHOPTION_TYPE']._serialized_start = 4247
    _globals['_REFRESHOPTION_TYPE']._serialized_end = 4300
    _globals['_INCREMENTALEXTENSION']._serialized_start = 4302
    _globals['_INCREMENTALEXTENSION']._serialized_end = 4373
    _globals['_MVEXTENSION']._serialized_start = 4376
    _globals['_MVEXTENSION']._serialized_end = 4643
    _globals['_VIEW']._serialized_start = 4645
    _globals['_VIEW']._serialized_end = 4752
    _globals['_TABLESTREAM']._serialized_start = 4754
    _globals['_TABLESTREAM']._serialized_end = 4873
    _globals['_TABLESTREAMSTATE']._serialized_start = 4875
    _globals['_TABLESTREAMSTATE']._serialized_end = 4981