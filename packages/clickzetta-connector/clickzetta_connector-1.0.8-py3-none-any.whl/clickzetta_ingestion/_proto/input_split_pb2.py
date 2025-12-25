"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'input_split.proto')
_sym_db = _symbol_database.Default()
from . import virtual_value_info_pb2 as virtual__value__info__pb2
from . import statistics_pb2 as statistics__pb2
from . import bit_set_pb2 as bit__set__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11input_split.proto\x12\x08cz.proto\x1a\x18virtual_value_info.proto\x1a\x10statistics.proto\x1a\rbit_set.proto"\xc1\x01\n\nInputSplit\x12&\n\x04type\x18\x01 \x01(\x0e2\x18.cz.proto.InputSplitType\x12\x12\n\noperatorId\x18\x02 \x01(\t\x124\n\nfileRanges\x18\x03 \x01(\x0b2\x1e.cz.proto.FileRangesInputSplitH\x00\x128\n\x0cfileRowRange\x18\x04 \x01(\x0b2 .cz.proto.FileRowRangeInputSplitH\x00B\x07\n\x05split"<\n\x0eFileFieldStats\x12*\n\x0cfield_ranges\x18\x01 \x03(\x0b2\x14.cz.proto.FieldRange"\x99\x02\n\tFileRange\x12\x0c\n\x04path\x18\x01 \x01(\t\x12\x0e\n\x06offset\x18\x02 \x01(\x03\x12\x0c\n\x04size\x18\x03 \x01(\x03\x12.\n\nvalue_info\x18\x04 \x01(\x0b2\x1a.cz.proto.VirtualValueInfo\x12(\n\x0bdelta_files\x18\x05 \x03(\x0b2\x13.cz.proto.FileRange\x12%\n\x04type\x18\x06 \x01(\x0e2\x17.cz.proto.FileRangeType\x12-\n\x0bfield_stats\x18\x07 \x01(\x0b2\x18.cz.proto.FileFieldStats\x12\x1c\n\x0ftotal_file_size\x18\x08 \x01(\x03H\x00\x88\x01\x01B\x12\n\x10_total_file_size"\x84\x02\n\x14FileRangesInputSplit\x12#\n\x06ranges\x18\x02 \x03(\x0b2\x13.cz.proto.FileRange\x12\x14\n\x0cbucket_count\x18\x03 \x01(\r\x12\x11\n\tbucket_id\x18\x04 \x01(\r\x126\n\x07workers\x18\x05 \x03(\x0b2%.cz.proto.FileRangesInputSplit.Worker\x12)\n\x0fworker_of_range\x18\x06 \x03(\x0b2\x10.cz.proto.BitSet\x1a;\n\x06Worker\x12\x0c\n\x04host\x18\x01 \x01(\t\x12\x10\n\x08rpc_port\x18\x02 \x01(\x05\x12\x11\n\tdata_port\x18\x03 \x01(\x05"J\n\x16FileRowRangeInputSplit\x12\x0c\n\x04path\x18\x01 \x01(\t\x12\x11\n\tstart_row\x18\x02 \x01(\x03\x12\x0f\n\x07end_row\x18\x03 \x01(\x03"\x95\x01\n\tRangeFile\x12\x11\n\x04path\x18\x01 \x01(\tH\x00\x88\x01\x01\x12\x16\n\trecordCnt\x18\x02 \x01(\x03H\x01\x88\x01\x01\x12\x15\n\x08fileSize\x18\x03 \x01(\x03H\x02\x88\x01\x01\x12\x15\n\x08location\x18\x04 \x01(\tH\x03\x88\x01\x01B\x07\n\x05_pathB\x0c\n\n_recordCntB\x0b\n\t_fileSizeB\x0b\n\t_location"K\n\x0cRangeLiteral\x12\x0e\n\x04intV\x18\x01 \x01(\x05H\x00\x12\x0f\n\x05longV\x18\x02 \x01(\x03H\x00\x12\x11\n\x07stringV\x18\x03 \x01(\tH\x00B\x07\n\x05value"\xa9\x01\n\x0eRangePartition\x12\x14\n\x07rangeId\x18\x01 \x01(\x05H\x00\x88\x01\x01\x12\'\n\nrangeFiles\x18\x02 \x03(\x0b2\x13.cz.proto.RangeFile\x12%\n\x05lower\x18\x03 \x03(\x0b2\x16.cz.proto.RangeLiteral\x12%\n\x05upper\x18\x04 \x03(\x0b2\x16.cz.proto.RangeLiteralB\n\n\x08_rangeId"#\n\x0fOutputSplitType"\x10\n\x04Type\x12\x08\n\x04FILE\x10\x00"\x83\x01\n\x0bOutputSplit\x12,\n\x04type\x18\x01 \x01(\x0e2\x1e.cz.proto.OutputSplitType.Type\x12\x12\n\noperatorId\x18\x02 \x01(\t\x12)\n\x04file\x18\x04 \x01(\x0b2\x19.cz.proto.FileOutputSplitH\x00B\x07\n\x05split"\x1f\n\x0fFileOutputSplit\x12\x0c\n\x04path\x18\x01 \x01(\t"\x98\x01\n\rFileSplitMeta\x12\x12\n\nsplit_file\x18\x03 \x01(\t\x12.\n\x06offset\x18\x04 \x03(\x0b2\x1e.cz.proto.FileSplitMeta.Offset\x1aC\n\x06Offset\x12\x0f\n\x07task_id\x18\x01 \x01(\x03\x12\x14\n\x0cstart_offset\x18\x02 \x01(\x03\x12\x12\n\nend_offset\x18\x03 \x01(\x03"\xb0\x01\n\x11EmbeddedSplitMeta\x120\n\x06splits\x18\x03 \x03(\x0b2 .cz.proto.EmbeddedSplitMeta.Pair\x1ai\n\x04Pair\x12\x0f\n\x07task_id\x18\x01 \x01(\x03\x12#\n\x05split\x18\x02 \x01(\x0b2\x14.cz.proto.InputSplit\x12+\n\x0coutput_split\x18\x03 \x01(\x0b2\x15.cz.proto.OutputSplit"\x97\x01\n\tSplitMeta\x12\x10\n\x08stage_id\x18\x01 \x01(\t\x12\x13\n\x0boperator_id\x18\x02 \x01(\t\x12\'\n\x04file\x18\x03 \x01(\x0b2\x17.cz.proto.FileSplitMetaH\x00\x12/\n\x08embedded\x18\x04 \x01(\x0b2\x1b.cz.proto.EmbeddedSplitMetaH\x00B\t\n\x07content"\xb6\x01\n\x13CompactionSplitFile\x12\x0c\n\x04path\x18\x01 \x01(\t\x12\x0e\n\x06offset\x18\x02 \x01(\x03\x12\x0c\n\x04size\x18\x03 \x01(\x03\x12\x0f\n\x07sliceId\x18\x04 \x01(\x03\x12.\n\nvalue_info\x18\x05 \x01(\x0b2\x1a.cz.proto.VirtualValueInfo\x122\n\x0bdelta_files\x18\x06 \x03(\x0b2\x1d.cz.proto.CompactionSplitFile"?\n\x0fCompactionSplit\x12,\n\x05files\x18\x01 \x03(\x0b2\x1d.cz.proto.CompactionSplitFile"=\n\x10CompactionSplits\x12)\n\x06splits\x18\x01 \x03(\x0b2\x19.cz.proto.CompactionSplit*/\n\x0eInputSplitType\x12\x0e\n\nFILE_RANGE\x10\x00\x12\r\n\tROW_RANGE\x10\x01*B\n\rFileRangeType\x12\x0f\n\x0bNORMAL_FILE\x10\x00\x12\x0e\n\nADDED_FILE\x10\x01\x12\x10\n\x0cDELETED_FILE\x10\x02B\x13B\x0fInputSplitProtoP\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'input_split_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'B\x0fInputSplitProtoP\x01'
    _globals['_INPUTSPLITTYPE']._serialized_start = 2377
    _globals['_INPUTSPLITTYPE']._serialized_end = 2424
    _globals['_FILERANGETYPE']._serialized_start = 2426
    _globals['_FILERANGETYPE']._serialized_end = 2492
    _globals['_INPUTSPLIT']._serialized_start = 91
    _globals['_INPUTSPLIT']._serialized_end = 284
    _globals['_FILEFIELDSTATS']._serialized_start = 286
    _globals['_FILEFIELDSTATS']._serialized_end = 346
    _globals['_FILERANGE']._serialized_start = 349
    _globals['_FILERANGE']._serialized_end = 630
    _globals['_FILERANGESINPUTSPLIT']._serialized_start = 633
    _globals['_FILERANGESINPUTSPLIT']._serialized_end = 893
    _globals['_FILERANGESINPUTSPLIT_WORKER']._serialized_start = 834
    _globals['_FILERANGESINPUTSPLIT_WORKER']._serialized_end = 893
    _globals['_FILEROWRANGEINPUTSPLIT']._serialized_start = 895
    _globals['_FILEROWRANGEINPUTSPLIT']._serialized_end = 969
    _globals['_RANGEFILE']._serialized_start = 972
    _globals['_RANGEFILE']._serialized_end = 1121
    _globals['_RANGELITERAL']._serialized_start = 1123
    _globals['_RANGELITERAL']._serialized_end = 1198
    _globals['_RANGEPARTITION']._serialized_start = 1201
    _globals['_RANGEPARTITION']._serialized_end = 1370
    _globals['_OUTPUTSPLITTYPE']._serialized_start = 1372
    _globals['_OUTPUTSPLITTYPE']._serialized_end = 1407
    _globals['_OUTPUTSPLITTYPE_TYPE']._serialized_start = 1391
    _globals['_OUTPUTSPLITTYPE_TYPE']._serialized_end = 1407
    _globals['_OUTPUTSPLIT']._serialized_start = 1410
    _globals['_OUTPUTSPLIT']._serialized_end = 1541
    _globals['_FILEOUTPUTSPLIT']._serialized_start = 1543
    _globals['_FILEOUTPUTSPLIT']._serialized_end = 1574
    _globals['_FILESPLITMETA']._serialized_start = 1577
    _globals['_FILESPLITMETA']._serialized_end = 1729
    _globals['_FILESPLITMETA_OFFSET']._serialized_start = 1662
    _globals['_FILESPLITMETA_OFFSET']._serialized_end = 1729
    _globals['_EMBEDDEDSPLITMETA']._serialized_start = 1732
    _globals['_EMBEDDEDSPLITMETA']._serialized_end = 1908
    _globals['_EMBEDDEDSPLITMETA_PAIR']._serialized_start = 1803
    _globals['_EMBEDDEDSPLITMETA_PAIR']._serialized_end = 1908
    _globals['_SPLITMETA']._serialized_start = 1911
    _globals['_SPLITMETA']._serialized_end = 2062
    _globals['_COMPACTIONSPLITFILE']._serialized_start = 2065
    _globals['_COMPACTIONSPLITFILE']._serialized_end = 2247
    _globals['_COMPACTIONSPLIT']._serialized_start = 2249
    _globals['_COMPACTIONSPLIT']._serialized_end = 2312
    _globals['_COMPACTIONSPLITS']._serialized_start = 2314
    _globals['_COMPACTIONSPLITS']._serialized_end = 2375