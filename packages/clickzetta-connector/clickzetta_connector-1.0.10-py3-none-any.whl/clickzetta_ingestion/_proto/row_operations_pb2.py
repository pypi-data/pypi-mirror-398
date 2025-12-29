"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'row_operations.proto')
_sym_db = _symbol_database.Default()
from . import pb_util_pb2 as pb__util__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x14row_operations.proto\x12\x04kudu\x1a\rpb_util.proto"\xd1\x02\n\x0fRowOperationsPB\x12\x12\n\x04rows\x18\x02 \x01(\x0cB\x04\x88\xb5\x18\x01\x12\x1b\n\rindirect_data\x18\x03 \x01(\x0cB\x04\x88\xb5\x18\x01"\x8c\x02\n\x04Type\x12\x0b\n\x07UNKNOWN\x10\x00\x12\n\n\x06INSERT\x10\x01\x12\n\n\x06UPDATE\x10\x02\x12\n\n\x06DELETE\x10\x03\x12\n\n\x06UPSERT\x10\x05\x12\x11\n\rINSERT_IGNORE\x10\n\x12\x11\n\rUPDATE_IGNORE\x10\x0b\x12\x11\n\rDELETE_IGNORE\x10\x0c\x12\r\n\tSPLIT_ROW\x10\x04\x12\x15\n\x11RANGE_LOWER_BOUND\x10\x06\x12\x15\n\x11RANGE_UPPER_BOUND\x10\x07\x12\x1f\n\x1bEXCLUSIVE_RANGE_LOWER_BOUND\x10\x08\x12\x1f\n\x1bINCLUSIVE_RANGE_UPPER_BOUND\x10\t\x12\x0f\n\x0bREPLY_DETLA\x10\rB\x11\n\x0forg.apache.kudu')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'row_operations_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x0forg.apache.kudu'
    _globals['_ROWOPERATIONSPB'].fields_by_name['rows']._loaded_options = None
    _globals['_ROWOPERATIONSPB'].fields_by_name['rows']._serialized_options = b'\x88\xb5\x18\x01'
    _globals['_ROWOPERATIONSPB'].fields_by_name['indirect_data']._loaded_options = None
    _globals['_ROWOPERATIONSPB'].fields_by_name['indirect_data']._serialized_options = b'\x88\xb5\x18\x01'
    _globals['_ROWOPERATIONSPB']._serialized_start = 46
    _globals['_ROWOPERATIONSPB']._serialized_end = 383
    _globals['_ROWOPERATIONSPB_TYPE']._serialized_start = 115
    _globals['_ROWOPERATIONSPB_TYPE']._serialized_end = 383