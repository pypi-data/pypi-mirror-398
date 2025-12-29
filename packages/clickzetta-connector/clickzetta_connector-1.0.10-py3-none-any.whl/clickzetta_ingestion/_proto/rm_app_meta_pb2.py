"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'rm_app_meta.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11rm_app_meta.proto\x12\x11com.clickzetta.rm"\xaa\x02\n\tRMAppMeta\x12\x13\n\x06app_id\x18\x01 \x01(\tH\x00\x88\x01\x01\x12\x15\n\x08app_name\x18\x02 \x01(\tH\x01\x88\x01\x01\x12\x15\n\x08priority\x18\x03 \x01(\x05H\x02\x88\x01\x01\x12\x12\n\x05vc_id\x18\x04 \x01(\x03H\x03\x88\x01\x01\x125\n\tapp_state\x18\x05 \x01(\x0e2\x1d.com.clickzetta.rm.RMAppStateH\x04\x88\x01\x01\x12\x18\n\x0bsubmit_time\x18\x06 \x01(\x03H\x05\x88\x01\x01\x12\x18\n\x0bfinish_time\x18\x07 \x01(\x03H\x06\x88\x01\x01B\t\n\x07_app_idB\x0b\n\t_app_nameB\x0b\n\t_priorityB\x08\n\x06_vc_idB\x0c\n\n_app_stateB\x0e\n\x0c_submit_timeB\x0e\n\x0c_finish_time*G\n\nRMAppState\x12\x12\n\x0eRM_APP_RUNNING\x10\x00\x12\x12\n\x0eRM_APP_SUCCESS\x10\x01\x12\x11\n\rRM_APP_FAILED\x10\x02B(\n\x17com.clickzetta.rm.protoB\x0bRMAppProtosP\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'rm_app_meta_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x17com.clickzetta.rm.protoB\x0bRMAppProtosP\x01'
    _globals['_RMAPPSTATE']._serialized_start = 341
    _globals['_RMAPPSTATE']._serialized_end = 412
    _globals['_RMAPPMETA']._serialized_start = 41
    _globals['_RMAPPMETA']._serialized_end = 339