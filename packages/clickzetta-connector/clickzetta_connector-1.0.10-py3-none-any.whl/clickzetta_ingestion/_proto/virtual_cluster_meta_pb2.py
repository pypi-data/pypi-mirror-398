"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'virtual_cluster_meta.proto')
_sym_db = _symbol_database.Default()
from . import virtual_cluster_pb2 as virtual__cluster__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1avirtual_cluster_meta.proto\x12\x08cz.proto\x1a\x15virtual_cluster.proto"\xdf\x02\n\x13AnalyticsProperties\x12\x19\n\x0cmin_replicas\x18\x01 \x01(\x05H\x00\x88\x01\x01\x12\x19\n\x0cmax_replicas\x18\x02 \x01(\x05H\x01\x88\x01\x01\x12(\n\x1bmax_concurrency_per_replica\x18\x03 \x01(\x05H\x02\x88\x01\x01\x129\n\x0cscale_policy\x18\x04 \x01(\x0e2\x1e.com.clickzetta.rm.ScalePolicyH\x03\x88\x01\x01\x12\x19\n\x0ccur_replicas\x18\x05 \x01(\x05H\x04\x88\x01\x01\x12\x1b\n\x0epreload_tables\x18\x06 \x01(\tH\x05\x88\x01\x01B\x0f\n\r_min_replicasB\x0f\n\r_max_replicasB\x1e\n\x1c_max_concurrency_per_replicaB\x0f\n\r_scale_policyB\x0f\n\r_cur_replicasB\x11\n\x0f_preload_tables"h\n\x11GeneralProperties\x12>\n\x10cluster_max_size\x18\x01 \x01(\x0e2\x1f.com.clickzetta.rm.VClusterSizeH\x00\x88\x01\x01B\x13\n\x11_cluster_max_size"c\n\x07JobInfo\x12\x19\n\x0cjobs_running\x18\x01 \x01(\x05H\x00\x88\x01\x01\x12\x1a\n\rjobs_in_queue\x18\x02 \x01(\x05H\x01\x88\x01\x01B\x0f\n\r_jobs_runningB\x10\n\x0e_jobs_in_queue"\xcb\x07\n\x12VirtualClusterMeta\x125\n\x0ccluster_type\x18\x01 \x01(\x0e2\x1f.com.clickzetta.rm.VClusterType\x12:\n\x0ccluster_size\x18\x02 \x01(\x0e2\x1f.com.clickzetta.rm.VClusterSizeH\x01\x88\x01\x01\x12=\n\x14analytics_properties\x18\x03 \x01(\x0b2\x1d.cz.proto.AnalyticsPropertiesH\x00\x129\n\x12general_properties\x18\x04 \x01(\x0b2\x1b.cz.proto.GeneralPropertiesH\x00\x12"\n\x15auto_stop_latency_sec\x18\x05 \x01(\x05H\x02\x88\x01\x01\x12\x1f\n\x12auto_start_enabled\x18\x06 \x01(\x08H\x03\x88\x01\x01\x122\n\x03tag\x18\x07 \x03(\x0b2%.cz.proto.VirtualClusterMeta.TagEntry\x12)\n\x1cquery_process_time_limit_sec\x18\t \x01(\x05H\x04\x88\x01\x01\x12:\n\x05state\x18\n \x01(\x0e2&.com.clickzetta.rm.VirtualClusterStateH\x05\x88\x01\x01\x12>\n\tpre_state\x18\x0b \x01(\x0e2&.com.clickzetta.rm.VirtualClusterStateH\x06\x88\x01\x01\x12\x16\n\terror_msg\x18\x0c \x01(\tH\x07\x88\x01\x01\x12(\n\x08job_info\x18\r \x01(\x0b2\x11.cz.proto.JobInfoH\x08\x88\x01\x01\x12\x19\n\x0cworkspace_id\x18\x0e \x01(\x03H\t\x88\x01\x01\x12\x12\n\x05vc_id\x18\x0f \x01(\x03H\n\x88\x01\x01\x12\x17\n\nstate_info\x18\x10 \x01(\tH\x0b\x88\x01\x01\x12\x14\n\x07version\x18\x11 \x01(\tH\x0c\x88\x01\x01\x1a*\n\x08TagEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01B\x10\n\x0eresource_oneofB\x0f\n\r_cluster_sizeB\x18\n\x16_auto_stop_latency_secB\x15\n\x13_auto_start_enabledB\x1f\n\x1d_query_process_time_limit_secB\x08\n\x06_stateB\x0c\n\n_pre_stateB\x0c\n\n_error_msgB\x0b\n\t_job_infoB\x0f\n\r_workspace_idB\x08\n\x06_vc_idB\r\n\x0b_state_infoB\n\n\x08_versionb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'virtual_cluster_meta_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_VIRTUALCLUSTERMETA_TAGENTRY']._loaded_options = None
    _globals['_VIRTUALCLUSTERMETA_TAGENTRY']._serialized_options = b'8\x01'
    _globals['_ANALYTICSPROPERTIES']._serialized_start = 64
    _globals['_ANALYTICSPROPERTIES']._serialized_end = 415
    _globals['_GENERALPROPERTIES']._serialized_start = 417
    _globals['_GENERALPROPERTIES']._serialized_end = 521
    _globals['_JOBINFO']._serialized_start = 523
    _globals['_JOBINFO']._serialized_end = 622
    _globals['_VIRTUALCLUSTERMETA']._serialized_start = 625
    _globals['_VIRTUALCLUSTERMETA']._serialized_end = 1596
    _globals['_VIRTUALCLUSTERMETA_TAGENTRY']._serialized_start = 1332
    _globals['_VIRTUALCLUSTERMETA_TAGENTRY']._serialized_end = 1374