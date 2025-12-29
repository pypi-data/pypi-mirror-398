"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'statistics.proto')
_sym_db = _symbol_database.Default()
from . import expression_pb2 as expression__pb2
from . import data_type_pb2 as data__type__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10statistics.proto\x12\x08cz.proto\x1a\x10expression.proto\x1a\x0fdata_type.proto"\x18\n\x08SortKeys\x12\x0c\n\x04keys\x18\x01 \x03(\r"\x83\x01\n\x0bFieldBounds\x121\n\x06bounds\x18\x01 \x03(\x0b2!.cz.proto.FieldBounds.BoundsEntry\x1aA\n\x0bBoundsEntry\x12\x0b\n\x03key\x18\x01 \x01(\r\x12!\n\x05value\x18\x02 \x01(\x0b2\x12.cz.proto.Constant:\x028\x01"+\n\x10DeltaUpdatedInfo\x12\x17\n\x0fupdated_columns\x18\x01 \x03(\r"\xdb\x03\n\tStatsData\x12\x13\n\x0bsnapshot_id\x18\x01 \x01(\x03\x12\x1a\n\rsize_in_bytes\x18\x02 \x01(\x03H\x00\x88\x01\x01\x12\x19\n\x0crecord_count\x18\x03 \x01(\x03H\x01\x88\x01\x01\x12#\n\x16estimated_record_count\x18\x10 \x01(\x03H\x02\x88\x01\x01\x12#\n\x16delta_row_count_change\x18\x0e \x01(\x03H\x03\x88\x01\x01\x125\n\x0cupdated_info\x18\x0f \x01(\x0b2\x1a.cz.proto.DeltaUpdatedInfoH\x04\x88\x01\x01\x12+\n\x0cfields_stats\x18\x05 \x01(\x0b2\x15.cz.proto.FieldsStats\x124\n\x15sort_key_lower_bounds\x18\x0c \x01(\x0b2\x15.cz.proto.FieldBounds\x124\n\x15sort_key_upper_bounds\x18\r \x01(\x0b2\x15.cz.proto.FieldBoundsB\x10\n\x0e_size_in_bytesB\x0f\n\r_record_countB\x19\n\x17_estimated_record_countB\x19\n\x17_delta_row_count_changeB\x0f\n\r_updated_info"8\n\x0bFieldsStats\x12)\n\x0bfield_stats\x18\x01 \x03(\x0b2\x14.cz.proto.FieldStats"N\n\nFieldStats\x12\x10\n\x08field_id\x18\x01 \x03(\r\x12.\n\x0bstats_value\x18\x02 \x03(\x0b2\x19.cz.proto.FieldStatsValue"\xfa\x02\n\x0fFieldStatsValue\x12\x13\n\tnan_count\x18\x01 \x01(\x03H\x00\x12\x15\n\x0bvalue_count\x18\x02 \x01(\x03H\x00\x12\x14\n\nnull_count\x18\x03 \x01(\x03H\x00\x12*\n\x0clower_bounds\x18\x04 \x01(\x0b2\x12.cz.proto.ConstantH\x00\x12*\n\x0cupper_bounds\x18\x05 \x01(\x0b2\x12.cz.proto.ConstantH\x00\x12\x12\n\x08avg_size\x18\x06 \x01(\x01H\x00\x12\x12\n\x08max_size\x18\x07 \x01(\x03H\x00\x12\x19\n\x0fcompressed_size\x18\x08 \x01(\x03H\x00\x12\x19\n\x0fdistinct_number\x18\t \x01(\x03H\x00\x12\x1f\n\x05top_k\x18\n \x01(\x0b2\x0e.cz.proto.TopKH\x00\x12(\n\thistogram\x18\x0b \x01(\x0b2\x13.cz.proto.HistogramH\x00\x12\x1b\n\x11raw_size_in_bytes\x18\x0c \x01(\x03H\x00B\x07\n\x05value")\n\x04TopK\x12!\n\x05top_k\x18\x01 \x03(\x0b2\x12.cz.proto.Constant"x\n\x0fHistogramBucket\x12\'\n\x0blower_bound\x18\x01 \x01(\x0b2\x12.cz.proto.Constant\x12\'\n\x0bupper_bound\x18\x02 \x01(\x0b2\x12.cz.proto.Constant\x12\x13\n\x0bvalue_count\x18\x03 \x01(\x03"7\n\tHistogram\x12*\n\x07buckets\x18\x01 \x03(\x0b2\x19.cz.proto.HistogramBucket"0\n\nValuePoint\x12"\n\x06values\x18\x01 \x03(\x0b2\x12.cz.proto.Constant"l\n\rBoundaryPoint\x12\x10\n\x08included\x18\x01 \x01(\x08\x12\x13\n\tunbounded\x18\x02 \x01(\x08H\x00\x12+\n\x0bvalue_point\x18\x03 \x01(\x0b2\x14.cz.proto.ValuePointH\x00B\x07\n\x05value"Z\n\x08Boundary\x12&\n\x05lower\x18\x01 \x01(\x0b2\x17.cz.proto.BoundaryPoint\x12&\n\x05upper\x18\x02 \x01(\x0b2\x17.cz.proto.BoundaryPoint"b\n\rRangeBoundary\x12\n\n\x02id\x18\x01 \x01(\x04\x12!\n\x05types\x18\x02 \x03(\x0b2\x12.cz.proto.DataType\x12"\n\x06ranges\x18\x03 \x03(\x0b2\x12.cz.proto.Boundary"R\n\x0fEnforceBoundary\x12\x12\n\ntable_name\x18\x01 \x01(\t\x12+\n\nboundaries\x18\x02 \x01(\x0b2\x17.cz.proto.RangeBoundary"D\n\rTableBoundary\x123\n\x10table_boundaries\x18\x01 \x03(\x0b2\x19.cz.proto.EnforceBoundary"c\n\nFieldRange\x12\x10\n\x08field_id\x18\x01 \x01(\r\x12 \n\x04type\x18\x02 \x01(\x0b2\x12.cz.proto.DataType\x12!\n\x05range\x18\x03 \x01(\x0b2\x12.cz.proto.BoundaryB\x02P\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'statistics_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'P\x01'
    _globals['_FIELDBOUNDS_BOUNDSENTRY']._loaded_options = None
    _globals['_FIELDBOUNDS_BOUNDSENTRY']._serialized_options = b'8\x01'
    _globals['_SORTKEYS']._serialized_start = 65
    _globals['_SORTKEYS']._serialized_end = 89
    _globals['_FIELDBOUNDS']._serialized_start = 92
    _globals['_FIELDBOUNDS']._serialized_end = 223
    _globals['_FIELDBOUNDS_BOUNDSENTRY']._serialized_start = 158
    _globals['_FIELDBOUNDS_BOUNDSENTRY']._serialized_end = 223
    _globals['_DELTAUPDATEDINFO']._serialized_start = 225
    _globals['_DELTAUPDATEDINFO']._serialized_end = 268
    _globals['_STATSDATA']._serialized_start = 271
    _globals['_STATSDATA']._serialized_end = 746
    _globals['_FIELDSSTATS']._serialized_start = 748
    _globals['_FIELDSSTATS']._serialized_end = 804
    _globals['_FIELDSTATS']._serialized_start = 806
    _globals['_FIELDSTATS']._serialized_end = 884
    _globals['_FIELDSTATSVALUE']._serialized_start = 887
    _globals['_FIELDSTATSVALUE']._serialized_end = 1265
    _globals['_TOPK']._serialized_start = 1267
    _globals['_TOPK']._serialized_end = 1308
    _globals['_HISTOGRAMBUCKET']._serialized_start = 1310
    _globals['_HISTOGRAMBUCKET']._serialized_end = 1430
    _globals['_HISTOGRAM']._serialized_start = 1432
    _globals['_HISTOGRAM']._serialized_end = 1487
    _globals['_VALUEPOINT']._serialized_start = 1489
    _globals['_VALUEPOINT']._serialized_end = 1537
    _globals['_BOUNDARYPOINT']._serialized_start = 1539
    _globals['_BOUNDARYPOINT']._serialized_end = 1647
    _globals['_BOUNDARY']._serialized_start = 1649
    _globals['_BOUNDARY']._serialized_end = 1739
    _globals['_RANGEBOUNDARY']._serialized_start = 1741
    _globals['_RANGEBOUNDARY']._serialized_end = 1839
    _globals['_ENFORCEBOUNDARY']._serialized_start = 1841
    _globals['_ENFORCEBOUNDARY']._serialized_end = 1923
    _globals['_TABLEBOUNDARY']._serialized_start = 1925
    _globals['_TABLEBOUNDARY']._serialized_end = 1993
    _globals['_FIELDRANGE']._serialized_start = 1995
    _globals['_FIELDRANGE']._serialized_end = 2094