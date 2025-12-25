"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'virtual_value_info.proto')
_sym_db = _symbol_database.Default()
from . import expression_pb2 as expression__pb2
from . import data_type_pb2 as data__type__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x18virtual_value_info.proto\x12\x08cz.proto\x1a\x10expression.proto\x1a\x0fdata_type.proto"\x8e\x01\n\rConstantField\x12\x10\n\x08field_id\x18\x01 \x01(\r\x12 \n\x04type\x18\x02 \x01(\x0b2\x12.cz.proto.DataType\x12!\n\x05value\x18\x03 \x01(\x0b2\x12.cz.proto.Constant\x12\x17\n\nfield_name\x18\n \x01(\tH\x00\x88\x01\x01B\r\n\x0b_field_name"Q\n\x13VirtualColumnValues\x12\'\n\x06values\x18\x01 \x03(\x0b2\x17.cz.proto.ConstantField\x12\x11\n\tblock_ids\x18\x02 \x03(\r"I\n\x10VirtualValueInfo\x125\n\x0evirtual_values\x18\x01 \x01(\x0b2\x1d.cz.proto.VirtualColumnValuesB\n\n\x08cz.protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'virtual_value_info_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x08cz.proto'
    _globals['_CONSTANTFIELD']._serialized_start = 74
    _globals['_CONSTANTFIELD']._serialized_end = 216
    _globals['_VIRTUALCOLUMNVALUES']._serialized_start = 218
    _globals['_VIRTUALCOLUMNVALUES']._serialized_end = 299
    _globals['_VIRTUALVALUEINFO']._serialized_start = 301
    _globals['_VIRTUALVALUEINFO']._serialized_end = 374