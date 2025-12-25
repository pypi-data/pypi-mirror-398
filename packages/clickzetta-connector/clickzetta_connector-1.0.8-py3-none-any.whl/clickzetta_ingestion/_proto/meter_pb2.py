"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'meter.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0bmeter.proto\x12\x0ecz.proto.meter"\x88\x03\n\x05Meter\x12\x12\n\naccount_id\x18\x01 \x01(\x03\x12\x13\n\x0binstance_id\x18\x02 \x01(\x03\x12\x10\n\x08sku_code\x18\x03 \x01(\t\x12\x13\n\x0bresource_id\x18\x04 \x01(\x03\x12\x15\n\rresource_name\x18\x0b \x01(\t\x12\x19\n\x11measurement_start\x18\x05 \x01(\x03\x12\x17\n\x0fmeasurement_end\x18\x06 \x01(\x03\x121\n\x0cmeasurements\x18\x07 \x03(\x0b2\x1b.cz.proto.meter.Measurement\x12J\n\x13resource_properties\x18\x08 \x03(\x0b2-.cz.proto.meter.Meter.ResourcePropertiesEntry\x12\x12\n\nidempotent\x18\t \x01(\t\x12\x16\n\x0eis_obj_dropped\x18\n \x01(\x08\x1a9\n\x17ResourcePropertiesEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"7\n\x0bMeasurement\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x0c\n\x04unit\x18\x02 \x01(\t\x12\r\n\x05value\x18\x03 \x01(\t"\xdb\x02\n\nMeterEvent\x12\x12\n\naccount_id\x18\x01 \x01(\x03\x12\x13\n\x0binstance_id\x18\x02 \x01(\x03\x12\x10\n\x08sku_code\x18\x03 \x01(\t\x12\x13\n\x0bresource_id\x18\x04 \x01(\x03\x12\x15\n\rresource_name\x18\x05 \x01(\t\x12\x1a\n\x12event_timestamp_ms\x18\x06 \x01(\x03\x12\x12\n\nevent_type\x18\x07 \x01(\x05\x12O\n\x13resource_properties\x18\x08 \x03(\x0b22.cz.proto.meter.MeterEvent.ResourcePropertiesEntry\x12\x12\n\nidempotent\x18\t \x01(\t\x12\x16\n\x0eis_obj_dropped\x18\n \x01(\x08\x1a9\n\x17ResourcePropertiesEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'meter_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_METER_RESOURCEPROPERTIESENTRY']._loaded_options = None
    _globals['_METER_RESOURCEPROPERTIESENTRY']._serialized_options = b'8\x01'
    _globals['_METEREVENT_RESOURCEPROPERTIESENTRY']._loaded_options = None
    _globals['_METEREVENT_RESOURCEPROPERTIESENTRY']._serialized_options = b'8\x01'
    _globals['_METER']._serialized_start = 32
    _globals['_METER']._serialized_end = 424
    _globals['_METER_RESOURCEPROPERTIESENTRY']._serialized_start = 367
    _globals['_METER_RESOURCEPROPERTIESENTRY']._serialized_end = 424
    _globals['_MEASUREMENT']._serialized_start = 426
    _globals['_MEASUREMENT']._serialized_end = 481
    _globals['_METEREVENT']._serialized_start = 484
    _globals['_METEREVENT']._serialized_end = 831
    _globals['_METEREVENT_RESOURCEPROPERTIESENTRY']._serialized_start = 367
    _globals['_METEREVENT_RESOURCEPROPERTIESENTRY']._serialized_end = 424