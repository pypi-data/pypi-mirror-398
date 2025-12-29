"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'expression.proto')
_sym_db = _symbol_database.Default()
from . import data_type_pb2 as data__type__pb2
from . import property_pb2 as property__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10expression.proto\x12\x08cz.proto\x1a\x0fdata_type.proto\x1a\x0eproperty.proto"\xaf\x01\n\rParseTreeInfo\x123\n\x05start\x18\x01 \x01(\x0b2$.cz.proto.ParseTreeInfo.LocationInfo\x121\n\x03end\x18\x02 \x01(\x0b2$.cz.proto.ParseTreeInfo.LocationInfo\x1a6\n\x0cLocationInfo\x12\x0c\n\x04line\x18\x01 \x01(\r\x12\x0b\n\x03col\x18\x02 \x01(\r\x12\x0b\n\x03pos\x18\x03 \x01(\r"1\n\x0fIntervalDayTime\x12\x0f\n\x07seconds\x18\x01 \x01(\x03\x12\r\n\x05nanos\x18\x02 \x01(\x05"2\n\nArrayValue\x12$\n\x08elements\x18\x01 \x03(\x0b2\x12.cz.proto.Constant"P\n\x08MapValue\x12 \n\x04keys\x18\x01 \x03(\x0b2\x12.cz.proto.Constant\x12"\n\x06values\x18\x02 \x03(\x0b2\x12.cz.proto.Constant"1\n\x0bStructValue\x12"\n\x06fields\x18\x01 \x03(\x0b2\x12.cz.proto.Constant"\x1c\n\x0bBitmapValue\x12\r\n\x05value\x18\x01 \x01(\x0c"\x8f\x04\n\x08Constant\x12\x0e\n\x04null\x18\x01 \x01(\x08H\x00\x12\x11\n\x07tinyint\x18\x02 \x01(\x05H\x00\x12\x12\n\x08smallInt\x18\x03 \x01(\x05H\x00\x12\r\n\x03int\x18\x04 \x01(\x05H\x00\x12\x10\n\x06bigint\x18\x05 \x01(\x03H\x00\x12\x0f\n\x05float\x18\x06 \x01(\x02H\x00\x12\x10\n\x06double\x18\x07 \x01(\x01H\x00\x12\x11\n\x07decimal\x18\x08 \x01(\tH\x00\x12\x11\n\x07boolean\x18\t \x01(\x08H\x00\x12\x0e\n\x04char\x18\n \x01(\tH\x00\x12\x11\n\x07varchar\x18\x0b \x01(\tH\x00\x12\x10\n\x06string\x18\x0c \x01(\tH\x00\x12\x10\n\x06binary\x18\r \x01(\x0cH\x00\x12\x0e\n\x04date\x18\x0e \x01(\x05H\x00\x12\x13\n\ttimestamp\x18\x0f \x01(\x03H\x00\x12\x1b\n\x11IntervalYearMonth\x18\x10 \x01(\x03H\x00\x124\n\x0fIntervalDayTime\x18\x11 \x01(\x0b2\x19.cz.proto.IntervalDayTimeH\x00\x12%\n\x05array\x18d \x01(\x0b2\x14.cz.proto.ArrayValueH\x00\x12!\n\x03map\x18e \x01(\x0b2\x12.cz.proto.MapValueH\x00\x12\'\n\x06struct\x18f \x01(\x0b2\x15.cz.proto.StructValueH\x00\x12\'\n\x06bitmap\x18g \x01(\x0b2\x15.cz.proto.BitmapValueH\x00B\x07\n\x05value"`\n\x0fSubFieldPruning\x12\x1e\n\x02id\x18\x01 \x01(\x0b2\x12.cz.proto.Constant\x12-\n\tsubfields\x18\x02 \x01(\x0b2\x1a.cz.proto.SubFieldsPruning"S\n\x10SubFieldsPruning\x12)\n\x06fields\x18\x01 \x03(\x0b2\x19.cz.proto.SubFieldPruning\x12\x14\n\x0creserve_size\x18\x02 \x01(\x08"m\n\tReference\x12\n\n\x02id\x18\x01 \x01(\x04\x12\r\n\x05local\x18\x02 \x01(\x08\x12\x0c\n\x04from\x18\x03 \x01(\t\x12\x0c\n\x04name\x18\x04 \x01(\t\x12)\n\x08ref_type\x18\x05 \x01(\x0e2\x17.cz.proto.ReferenceType"8\n\x03Udf\x12\x12\n\ninstanceId\x18\x01 \x01(\x03\x12\x0c\n\x04path\x18\x02 \x03(\t\x12\x0f\n\x07creator\x18\x03 \x01(\x03"\x83\x02\n\x0eScalarFunction\x12\x0c\n\x04from\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x0f\n\x07builtIn\x18\x03 \x01(\x08\x12-\n\targuments\x18\x04 \x03(\x0b2\x1a.cz.proto.ScalarExpression\x12(\n\nproperties\x18\x05 \x01(\x0b2\x14.cz.proto.Properties\x12\x10\n\x08execDesc\x18\x06 \x01(\t\x120\n\x12functionProperties\x18\x07 \x01(\x0b2\x14.cz.proto.Properties\x12\x1c\n\x03udf\x18\n \x01(\x0b2\r.cz.proto.UdfH\x00B\t\n\x07derived";\n\x0bVariableDef\x12 \n\x04type\x18\x01 \x01(\x0b2\x12.cz.proto.DataType\x12\n\n\x02id\x18\x02 \x01(\x04"a\n\x0eLambdaFunction\x12%\n\x06params\x18\x01 \x03(\x0b2\x15.cz.proto.VariableDef\x12(\n\x04impl\x18\x02 \x01(\x0b2\x1a.cz.proto.ScalarExpression"\x8e\x02\n\x10ScalarExpression\x12 \n\x04type\x18\x01 \x01(\x0b2\x12.cz.proto.DataType\x12&\n\x08constant\x18\x02 \x01(\x0b2\x12.cz.proto.ConstantH\x00\x12(\n\treference\x18\x03 \x01(\x0b2\x13.cz.proto.ReferenceH\x00\x12,\n\x08function\x18\x05 \x01(\x0b2\x18.cz.proto.ScalarFunctionH\x00\x12*\n\x06lambda\x18\x06 \x01(\x0b2\x18.cz.proto.LambdaFunctionH\x00\x12#\n\x02pt\x18\n \x01(\x0b2\x17.cz.proto.ParseTreeInfoB\x07\n\x05value*W\n\rReferenceType\x12\x11\n\rLOGICAL_FIELD\x10\x00\x12\r\n\tREF_LOCAL\x10\x01\x12\x12\n\x0ePHYSICAL_FIELD\x10\x02\x12\x10\n\x0cREF_VARIABLE\x10\x03b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'expression_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_REFERENCETYPE']._serialized_start = 2084
    _globals['_REFERENCETYPE']._serialized_end = 2171
    _globals['_PARSETREEINFO']._serialized_start = 64
    _globals['_PARSETREEINFO']._serialized_end = 239
    _globals['_PARSETREEINFO_LOCATIONINFO']._serialized_start = 185
    _globals['_PARSETREEINFO_LOCATIONINFO']._serialized_end = 239
    _globals['_INTERVALDAYTIME']._serialized_start = 241
    _globals['_INTERVALDAYTIME']._serialized_end = 290
    _globals['_ARRAYVALUE']._serialized_start = 292
    _globals['_ARRAYVALUE']._serialized_end = 342
    _globals['_MAPVALUE']._serialized_start = 344
    _globals['_MAPVALUE']._serialized_end = 424
    _globals['_STRUCTVALUE']._serialized_start = 426
    _globals['_STRUCTVALUE']._serialized_end = 475
    _globals['_BITMAPVALUE']._serialized_start = 477
    _globals['_BITMAPVALUE']._serialized_end = 505
    _globals['_CONSTANT']._serialized_start = 508
    _globals['_CONSTANT']._serialized_end = 1035
    _globals['_SUBFIELDPRUNING']._serialized_start = 1037
    _globals['_SUBFIELDPRUNING']._serialized_end = 1133
    _globals['_SUBFIELDSPRUNING']._serialized_start = 1135
    _globals['_SUBFIELDSPRUNING']._serialized_end = 1218
    _globals['_REFERENCE']._serialized_start = 1220
    _globals['_REFERENCE']._serialized_end = 1329
    _globals['_UDF']._serialized_start = 1331
    _globals['_UDF']._serialized_end = 1387
    _globals['_SCALARFUNCTION']._serialized_start = 1390
    _globals['_SCALARFUNCTION']._serialized_end = 1649
    _globals['_VARIABLEDEF']._serialized_start = 1651
    _globals['_VARIABLEDEF']._serialized_end = 1710
    _globals['_LAMBDAFUNCTION']._serialized_start = 1712
    _globals['_LAMBDAFUNCTION']._serialized_end = 1809
    _globals['_SCALAREXPRESSION']._serialized_start = 1812
    _globals['_SCALAREXPRESSION']._serialized_end = 2082