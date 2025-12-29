"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'virtual_cluster.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x15virtual_cluster.proto\x12\x11com.clickzetta.rm"\xb3\x02\n\x13AnalyticsProperties\x12\x19\n\x0cmin_replicas\x18\x01 \x01(\x05H\x00\x88\x01\x01\x12\x19\n\x0cmax_replicas\x18\x02 \x01(\x05H\x01\x88\x01\x01\x12(\n\x1bmax_concurrency_per_replica\x18\x03 \x01(\x05H\x02\x88\x01\x01\x129\n\x0cscale_policy\x18\x04 \x01(\x0e2\x1e.com.clickzetta.rm.ScalePolicyH\x03\x88\x01\x01\x12\x1b\n\x0epreload_tables\x18\x05 \x01(\tH\x04\x88\x01\x01B\x0f\n\r_min_replicasB\x0f\n\r_max_replicasB\x1e\n\x1c_max_concurrency_per_replicaB\x0f\n\r_scale_policyB\x11\n\x0f_preload_tables"h\n\x11GeneralProperties\x12>\n\x10cluster_max_size\x18\x01 \x01(\x0e2\x1f.com.clickzetta.rm.VClusterSizeH\x00\x88\x01\x01B\x13\n\x11_cluster_max_size"Z\n\nVCResource\x12\x13\n\x06memory\x18\x01 \x01(\x03H\x00\x88\x01\x01\x12\x1a\n\rvirtual_cores\x18\x02 \x01(\x05H\x01\x88\x01\x01B\t\n\x07_memoryB\x10\n\x0e_virtual_cores"\xd5\x07\n\x18VirtualClusterProperties\x12\x11\n\x04name\x18\x01 \x01(\tH\x01\x88\x01\x01\x12\x18\n\x0binstance_id\x18\x02 \x01(\x03H\x02\x88\x01\x01\x12\x19\n\x0cworkspace_id\x18\x03 \x01(\x03H\x03\x88\x01\x01\x12:\n\x0ccluster_type\x18\x04 \x01(\x0e2\x1f.com.clickzetta.rm.VClusterTypeH\x04\x88\x01\x01\x12:\n\x0ccluster_size\x18\x05 \x01(\x0e2\x1f.com.clickzetta.rm.VClusterSizeH\x05\x88\x01\x01\x12F\n\x14analytics_properties\x18\x06 \x01(\x0b2&.com.clickzetta.rm.AnalyticsPropertiesH\x00\x12B\n\x12general_properties\x18\x07 \x01(\x0b2$.com.clickzetta.rm.GeneralPropertiesH\x00\x12"\n\x15auto_stop_latency_sec\x18\x08 \x01(\x05H\x06\x88\x01\x01\x12\x1f\n\x12auto_start_enabled\x18\t \x01(\x08H\x07\x88\x01\x01\x12A\n\x03tag\x18\n \x03(\x0b24.com.clickzetta.rm.VirtualClusterProperties.TagEntry\x12\x14\n\x07comment\x18\x0b \x01(\tH\x08\x88\x01\x01\x12)\n\x1cquery_process_time_limit_sec\x18\r \x01(\x05H\t\x88\x01\x01\x12\x1b\n\x0ecreate_time_ms\x18\x0e \x01(\x03H\n\x88\x01\x01\x12 \n\x13last_modify_time_ms\x18\x0f \x01(\x03H\x0b\x88\x01\x01\x12\x1c\n\x0fcreator_user_id\x18\x10 \x01(\x03H\x0c\x88\x01\x01\x12\x14\n\x07version\x18\x11 \x01(\tH\r\x88\x01\x01\x1a*\n\x08TagEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01B\x10\n\x0eresource_oneofB\x07\n\x05_nameB\x0e\n\x0c_instance_idB\x0f\n\r_workspace_idB\x0f\n\r_cluster_typeB\x0f\n\r_cluster_sizeB\x18\n\x16_auto_stop_latency_secB\x15\n\x13_auto_start_enabledB\n\n\x08_commentB\x1f\n\x1d_query_process_time_limit_secB\x11\n\x0f_create_time_msB\x16\n\x14_last_modify_time_msB\x12\n\x10_creator_user_idB\n\n\x08_version"e\n\x0bRequestInfo\x12\x17\n\nrequest_id\x18\x01 \x01(\tH\x00\x88\x01\x01\x12\x1b\n\x0eoperator_token\x18\x02 \x01(\x0cH\x01\x88\x01\x01B\r\n\x0b_request_idB\x11\n\x0f_operator_token"\xbf\x01\n\x0cResponseInfo\x12\x17\n\nrequest_id\x18\x01 \x01(\tH\x00\x88\x01\x01\x12.\n\x06status\x18\x02 \x01(\x0e2\x19.com.clickzetta.rm.StatusH\x01\x88\x01\x01\x12\x17\n\nerror_code\x18\x03 \x01(\tH\x02\x88\x01\x01\x12\x16\n\terror_msg\x18\x04 \x01(\tH\x03\x88\x01\x01B\r\n\x0b_request_idB\t\n\x07_statusB\r\n\x0b_error_codeB\x0c\n\n_error_msg"\x86\x01\n\x12VClusterIdentifier\x12\x18\n\x0binstance_id\x18\x01 \x01(\x03H\x00\x88\x01\x01\x12\x19\n\x0cworkspace_id\x18\x02 \x01(\x03H\x01\x88\x01\x01\x12\x11\n\x04name\x18\x03 \x01(\tH\x02\x88\x01\x01B\x0e\n\x0c_instance_idB\x0f\n\r_workspace_idB\x07\n\x05_name*\xd0\x01\n\x0cVClusterSize\x12\n\n\x06XSMALL\x10\x00\x12\t\n\x05SMALL\x10\x01\x12\n\n\x06MEDIUM\x10\x02\x12\t\n\x05LARGE\x10\x03\x12\n\n\x06XLARGE\x10\x04\x12\x0b\n\x07X2LARGE\x10\x05\x12\x0b\n\x07X3LARGE\x10\x06\x12\x0b\n\x07X4LARGE\x10\x07\x12\x0b\n\x07X5LARGE\x10\x08\x12\x0b\n\x07X6LARGE\x10\t\x12\x0f\n\x0bCUSTOMIZED3\x10e\x12\x10\n\x0cCUSTOMIZED52\x10f\x12\x10\n\x0cCUSTOMIZED48\x10g\x12\x10\n\x0cCUSTOMIZED12\x10h**\n\x0cVClusterType\x12\x0b\n\x07GENERAL\x10\x00\x12\r\n\tANALYTICS\x10\x01*\x1b\n\x0bScalePolicy\x12\x0c\n\x08STANDARD\x10\x00*\xc4\x01\n\x13VirtualClusterState\x12\r\n\tSUSPENDED\x10\x00\x12\x0b\n\x07RUNNING\x10\x01\x12\x0c\n\x08STARTING\x10\x02\x12\x0e\n\nSCALING_UP\x10\x03\x12\x10\n\x0cSCALING_DOWN\x10\x04\x12\x0e\n\nSUSPENDING\x10\x05\x12\x0c\n\x08DROPPING\x10\x06\x12\t\n\x05ERROR\x10\x07\x12\x0b\n\x07DELETED\x10\x08\x12\x0c\n\x08RESUMING\x10\t\x12\x0e\n\nCANCELLING\x10\n\x12\r\n\tUPGRADING\x10\x0b*#\n\x06Status\x12\r\n\tSUCCEEDED\x10\x00\x12\n\n\x06FAILED\x10\x01B/\n\x17com.clickzetta.rm.protoB\x14VirtualClusterProtosb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'virtual_cluster_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x17com.clickzetta.rm.protoB\x14VirtualClusterProtos'
    _globals['_VIRTUALCLUSTERPROPERTIES_TAGENTRY']._loaded_options = None
    _globals['_VIRTUALCLUSTERPROPERTIES_TAGENTRY']._serialized_options = b'8\x01'
    _globals['_VCLUSTERSIZE']._serialized_start = 1971
    _globals['_VCLUSTERSIZE']._serialized_end = 2179
    _globals['_VCLUSTERTYPE']._serialized_start = 2181
    _globals['_VCLUSTERTYPE']._serialized_end = 2223
    _globals['_SCALEPOLICY']._serialized_start = 2225
    _globals['_SCALEPOLICY']._serialized_end = 2252
    _globals['_VIRTUALCLUSTERSTATE']._serialized_start = 2255
    _globals['_VIRTUALCLUSTERSTATE']._serialized_end = 2451
    _globals['_STATUS']._serialized_start = 2453
    _globals['_STATUS']._serialized_end = 2488
    _globals['_ANALYTICSPROPERTIES']._serialized_start = 45
    _globals['_ANALYTICSPROPERTIES']._serialized_end = 352
    _globals['_GENERALPROPERTIES']._serialized_start = 354
    _globals['_GENERALPROPERTIES']._serialized_end = 458
    _globals['_VCRESOURCE']._serialized_start = 460
    _globals['_VCRESOURCE']._serialized_end = 550
    _globals['_VIRTUALCLUSTERPROPERTIES']._serialized_start = 553
    _globals['_VIRTUALCLUSTERPROPERTIES']._serialized_end = 1534
    _globals['_VIRTUALCLUSTERPROPERTIES_TAGENTRY']._serialized_start = 1229
    _globals['_VIRTUALCLUSTERPROPERTIES_TAGENTRY']._serialized_end = 1271
    _globals['_REQUESTINFO']._serialized_start = 1536
    _globals['_REQUESTINFO']._serialized_end = 1637
    _globals['_RESPONSEINFO']._serialized_start = 1640
    _globals['_RESPONSEINFO']._serialized_end = 1831
    _globals['_VCLUSTERIDENTIFIER']._serialized_start = 1834
    _globals['_VCLUSTERIDENTIFIER']._serialized_end = 1968