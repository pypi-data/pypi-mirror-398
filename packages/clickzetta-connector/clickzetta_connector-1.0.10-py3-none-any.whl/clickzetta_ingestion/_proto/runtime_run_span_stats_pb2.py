"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'runtime_run_span_stats.proto')
_sym_db = _symbol_database.Default()
from . import time_range_pb2 as time__range__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1cruntime_run_span_stats.proto\x12\x08cz.proto\x1a\x10time_range.proto"V\n\x13RuntimeRunSpanStats\x12,\n\x0fexecute_time_us\x18\x01 \x01(\x0b2\x13.cz.proto.TimeRange\x12\x11\n\trunner_id\x18\x02 \x01(\x04b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'runtime_run_span_stats_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_RUNTIMERUNSPANSTATS']._serialized_start = 60
    _globals['_RUNTIMERUNSPANSTATS']._serialized_end = 146