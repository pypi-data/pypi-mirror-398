"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'job_result_cache_meta.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1bjob_result_cache_meta.proto\x12\x17com.clickzetta.jobcache"\xa8\x02\n\x12JobResultCacheMeta\x12\x18\n\x0binstance_id\x18\x01 \x01(\x04H\x00\x88\x01\x01\x12\x19\n\x0cworkspace_id\x18\x02 \x01(\x04H\x01\x88\x01\x01\x12\x1a\n\rjob_signature\x18\x03 \x01(\tH\x02\x88\x01\x01\x12\x1e\n\x11preprocessed_plan\x18\x04 \x01(\tH\x03\x88\x01\x01\x12\x19\n\x0cresult_files\x18\x05 \x01(\tH\x04\x88\x01\x01\x12\x1a\n\rstart_time_ms\x18\x06 \x01(\x04H\x05\x88\x01\x01B\x0e\n\x0c_instance_idB\x0f\n\r_workspace_idB\x10\n\x0e_job_signatureB\x14\n\x12_preprocessed_planB\x0f\n\r_result_filesB\x10\n\x0e_start_time_msB1\n\x1dcom.clickzetta.jobcache.protoB\x0eJobCacheProtosP\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'job_result_cache_meta_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x1dcom.clickzetta.jobcache.protoB\x0eJobCacheProtosP\x01'
    _globals['_JOBRESULTCACHEMETA']._serialized_start = 57
    _globals['_JOBRESULTCACHEMETA']._serialized_end = 353