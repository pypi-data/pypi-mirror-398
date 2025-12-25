"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'data_type.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0fdata_type.proto\x12\x08cz.proto"\x1e\n\x0cCharTypeInfo\x12\x0e\n\x06length\x18\x01 \x01(\x04"!\n\x0fVarCharTypeInfo\x12\x0e\n\x06length\x18\x01 \x01(\x04"3\n\x0fDecimalTypeInfo\x12\x11\n\tprecision\x18\x01 \x01(\x04\x12\r\n\x05scale\x18\x02 \x01(\x04"\x8b\x01\n\x13IntervalDayTimeInfo\x12$\n\x04from\x18\x01 \x01(\x0e2\x16.cz.proto.IntervalUnit\x12"\n\x02to\x18\x02 \x01(\x0e2\x16.cz.proto.IntervalUnit\x12*\n\tprecision\x18\x03 \x01(\x0e2\x17.cz.proto.TimestampUnit"a\n\x15IntervalYearMonthInfo\x12$\n\x04from\x18\x01 \x01(\x0e2\x16.cz.proto.IntervalUnit\x12"\n\x02to\x18\x02 \x01(\x0e2\x16.cz.proto.IntervalUnit"S\n\x0eVectorTypeInfo\x12.\n\nnumberType\x18\x01 \x01(\x0e2\x1a.cz.proto.VectorNumberType\x12\x11\n\tdimension\x18\x02 \x01(\r"8\n\rArrayTypeInfo\x12\'\n\x0belementType\x18\x01 \x01(\x0b2\x12.cz.proto.DataType"Y\n\x0bMapTypeInfo\x12#\n\x07keyType\x18\x01 \x01(\x0b2\x12.cz.proto.DataType\x12%\n\tvalueType\x18\x02 \x01(\x0b2\x12.cz.proto.DataType"\x91\x01\n\x0eStructTypeInfo\x12.\n\x06fields\x18\x01 \x03(\x0b2\x1e.cz.proto.StructTypeInfo.Field\x1aO\n\x05Field\x12\x0c\n\x04name\x18\x01 \x01(\t\x12 \n\x04type\x18\x02 \x01(\x0b2\x12.cz.proto.DataType\x12\x16\n\x0etype_reference\x18\x03 \x01(\r"]\n\x10FunctionTypeInfo\x12 \n\x04args\x18\x01 \x03(\x0b2\x12.cz.proto.DataType\x12\'\n\x0breturn_type\x18\x02 \x01(\x0b2\x12.cz.proto.DataType"8\n\rTimestampInfo\x12\'\n\x06tsUnit\x18\x01 \x01(\x0e2\x17.cz.proto.TimestampUnit"\xb3\x05\n\x08DataType\x12,\n\x08category\x18\x01 \x01(\x0e2\x1a.cz.proto.DataTypeCategory\x12\x10\n\x08nullable\x18\x02 \x01(\x08\x12\x10\n\x08field_id\x18\x0b \x01(\r\x12.\n\x0ccharTypeInfo\x18\x03 \x01(\x0b2\x16.cz.proto.CharTypeInfoH\x00\x124\n\x0fvarCharTypeInfo\x18\x04 \x01(\x0b2\x19.cz.proto.VarCharTypeInfoH\x00\x124\n\x0fdecimalTypeInfo\x18\x05 \x01(\x0b2\x19.cz.proto.DecimalTypeInfoH\x00\x120\n\rarrayTypeInfo\x18\x06 \x01(\x0b2\x17.cz.proto.ArrayTypeInfoH\x00\x12,\n\x0bmapTypeInfo\x18\x07 \x01(\x0b2\x15.cz.proto.MapTypeInfoH\x00\x122\n\x0estructTypeInfo\x18\x08 \x01(\x0b2\x18.cz.proto.StructTypeInfoH\x00\x12?\n\x16interval_day_time_info\x18\t \x01(\x0b2\x1d.cz.proto.IntervalDayTimeInfoH\x00\x12C\n\x18interval_year_month_info\x18\n \x01(\x0b2\x1f.cz.proto.IntervalYearMonthInfoH\x00\x121\n\x0etimestamp_info\x18\x0c \x01(\x0b2\x17.cz.proto.TimestampInfoH\x00\x123\n\rfunction_info\x18\r \x01(\x0b2\x1a.cz.proto.FunctionTypeInfoH\x00\x12/\n\x0bvector_info\x18\x0e \x01(\x0b2\x18.cz.proto.VectorTypeInfoH\x00B\x06\n\x04info*\xef\x02\n\x10DataTypeCategory\x12\x08\n\x04NONE\x10\x00\x12\x08\n\x04INT8\x10\x01\x12\t\n\x05INT16\x10\x02\x12\t\n\x05INT32\x10\x03\x12\t\n\x05INT64\x10\x04\x12\x0b\n\x07FLOAT32\x10\x05\x12\x0b\n\x07FLOAT64\x10\x06\x12\x0b\n\x07DECIMAL\x10\x07\x12\x0b\n\x07BOOLEAN\x10\x08\x12\x08\n\x04CHAR\x10\t\x12\x0b\n\x07VARCHAR\x10\n\x12\n\n\x06STRING\x10\x0b\x12\n\n\x06BINARY\x10\x0c\x12\x08\n\x04DATE\x10\r\x12\x11\n\rTIMESTAMP_LTZ\x10\x0e\x12\x17\n\x13INTERVAL_YEAR_MONTH\x10\x0f\x12\x15\n\x11INTERVAL_DAY_TIME\x10\x10\x12\x11\n\rTIMESTAMP_NTZ\x10\x11\x12\n\n\x06BITMAP\x102\x12\t\n\x05ARRAY\x10d\x12\x07\n\x03MAP\x10e\x12\n\n\x06STRUCT\x10f\x12\x11\n\rFUNCTION_TYPE\x10g\x12\x08\n\x04JSON\x10h\x12\x0f\n\x0bVECTOR_TYPE\x10i\x12\t\n\x04VOID\x10\xc8\x01*f\n\x0cIntervalUnit\x12\x16\n\x12NONE_INTERVAL_UNIT\x10\x00\x12\x08\n\x04YEAR\x10\x01\x12\t\n\x05MONTH\x10\x02\x12\x07\n\x03DAY\x10\x03\x12\x08\n\x04HOUR\x10\x04\x12\n\n\x06MINUTE\x10\x05\x12\n\n\x06SECOND\x10\x06*Q\n\rTimestampUnit\x12\x0b\n\x07SECONDS\x10\x00\x12\x10\n\x0cMILLISECONDS\x10\x03\x12\x10\n\x0cMICROSECONDS\x10\x06\x12\x0f\n\x0bNANOSECONDS\x10\t*Z\n\x10VectorNumberType\x12\x06\n\x02I8\x10\x00\x12\x07\n\x03I16\x10\x01\x12\x07\n\x03I32\x10\x02\x12\x07\n\x03I64\x10\x03\x12\x07\n\x03F16\x10\x04\x12\x07\n\x03F32\x10\x05\x12\x07\n\x03F64\x10\x06\x12\x08\n\x04BF64\x10\x07B\x0c\n\x08cz.protoP\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'data_type_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x08cz.protoP\x01'
    _globals['_DATATYPECATEGORY']._serialized_start = 1620
    _globals['_DATATYPECATEGORY']._serialized_end = 1987
    _globals['_INTERVALUNIT']._serialized_start = 1989
    _globals['_INTERVALUNIT']._serialized_end = 2091
    _globals['_TIMESTAMPUNIT']._serialized_start = 2093
    _globals['_TIMESTAMPUNIT']._serialized_end = 2174
    _globals['_VECTORNUMBERTYPE']._serialized_start = 2176
    _globals['_VECTORNUMBERTYPE']._serialized_end = 2266
    _globals['_CHARTYPEINFO']._serialized_start = 29
    _globals['_CHARTYPEINFO']._serialized_end = 59
    _globals['_VARCHARTYPEINFO']._serialized_start = 61
    _globals['_VARCHARTYPEINFO']._serialized_end = 94
    _globals['_DECIMALTYPEINFO']._serialized_start = 96
    _globals['_DECIMALTYPEINFO']._serialized_end = 147
    _globals['_INTERVALDAYTIMEINFO']._serialized_start = 150
    _globals['_INTERVALDAYTIMEINFO']._serialized_end = 289
    _globals['_INTERVALYEARMONTHINFO']._serialized_start = 291
    _globals['_INTERVALYEARMONTHINFO']._serialized_end = 388
    _globals['_VECTORTYPEINFO']._serialized_start = 390
    _globals['_VECTORTYPEINFO']._serialized_end = 473
    _globals['_ARRAYTYPEINFO']._serialized_start = 475
    _globals['_ARRAYTYPEINFO']._serialized_end = 531
    _globals['_MAPTYPEINFO']._serialized_start = 533
    _globals['_MAPTYPEINFO']._serialized_end = 622
    _globals['_STRUCTTYPEINFO']._serialized_start = 625
    _globals['_STRUCTTYPEINFO']._serialized_end = 770
    _globals['_STRUCTTYPEINFO_FIELD']._serialized_start = 691
    _globals['_STRUCTTYPEINFO_FIELD']._serialized_end = 770
    _globals['_FUNCTIONTYPEINFO']._serialized_start = 772
    _globals['_FUNCTIONTYPEINFO']._serialized_end = 865
    _globals['_TIMESTAMPINFO']._serialized_start = 867
    _globals['_TIMESTAMPINFO']._serialized_end = 923
    _globals['_DATATYPE']._serialized_start = 926
    _globals['_DATATYPE']._serialized_end = 1617