"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'job_meta.proto')
_sym_db = _symbol_database.Default()
from . import virtual_cluster_pb2 as virtual__cluster__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0ejob_meta.proto\x12\x08cz.proto\x1a\x15virtual_cluster.proto"D\n\x07JobCost\x12\x0b\n\x03cpu\x18\x01 \x01(\r\x12\x0e\n\x06memory\x18\x02 \x01(\r\x12\x1c\n\x14runtime_wall_time_ns\x18\x03 \x01(\x04"s\n\nJobHistory\x12\x18\n\x10coordinator_host\x18\x01 \x01(\t\x12\x1b\n\x13coordinator_version\x18\x02 \x01(\x04\x12\x15\n\rstart_time_ms\x18\x03 \x01(\x04\x12\x17\n\x0frelease_version\x18\x04 \x01(\t"\xaf\x01\n\x0cSQLJobConfig\x12\x0f\n\x07timeout\x18\x01 \x01(\x05\x12\x18\n\x10adhoc_size_limit\x18\x02 \x01(\x03\x12\x17\n\x0fadhoc_row_limit\x18\x03 \x01(\x03\x12.\n\x04hint\x18\x04 \x03(\x0b2 .cz.proto.SQLJobConfig.HintEntry\x1a+\n\tHintEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"\xa4\x01\n\x06SQLJob\x12\r\n\x05query\x18\x01 \x03(\t\x12\x19\n\x11default_namespace\x18\x02 \x03(\t\x12*\n\nsql_config\x18\x03 \x01(\x0b2\x16.cz.proto.SQLJobConfig\x12\x1b\n\x13default_instance_id\x18\x04 \x01(\x03\x12\'\n\nquery_type\x18\x05 \x01(\x0e2\x13.cz.proto.QueryType"\xf5\x02\n\x12JobSummaryLocation\x12\x18\n\x10summary_location\x18\x01 \x01(\t\x12\x15\n\rplan_location\x18\x02 \x01(\t\x12\x16\n\x0estats_location\x18\x03 \x01(\t\x12\x19\n\x11progress_location\x18\x04 \x01(\t\x12\x17\n\x0fresult_location\x18\x05 \x01(\t\x12\x15\n\rbase_location\x18\n \x01(\t\x12\x1f\n\x17job_properties_location\x18\x0b \x01(\t\x12\x1c\n\x14table_stats_location\x18\x0c \x01(\t\x12 \n\x18preprocess_plan_location\x18\r \x01(\t\x12\x1b\n\x13job_status_location\x18\x0e \x01(\t\x12\x1b\n\x13debug_plan_location\x18\x0f \x01(\t\x12\x19\n\x11job_desc_location\x18\x10 \x01(\t\x12\x15\n\rjob_meta_dump\x18\x11 \x01(\t"t\n\x0cJobProfiling\x12:\n\tprofiling\x18\x01 \x03(\x0b2\'.cz.proto.JobProfiling.JobProfilingItem\x1a(\n\x10JobProfilingItem\x12\t\n\x01e\x18\x01 \x01(\x05\x12\t\n\x01t\x18\x02 \x01(\x03"\x85\r\n\x07JobMeta\x12\x10\n\x08job_name\x18\x02 \x01(\t\x12\x17\n\x0fvirtual_cluster\x18\x03 \x01(\x03\x12#\n\x06status\x18\x04 \x01(\x0e2\x13.cz.proto.JobStatus\x12\x1f\n\x04type\x18\x05 \x01(\x0e2\x11.cz.proto.JobType\x12\x12\n\nstart_time\x18\x06 \x01(\x04\x12\x10\n\x08end_time\x18\x07 \x01(\x04\x12\x10\n\x08priority\x18\t \x01(\r\x12\x11\n\tsignature\x18\n \x01(\t\x12\x1f\n\x04cost\x18\x0b \x01(\x0b2\x11.cz.proto.JobCost\x120\n\thistories\x18\x0c \x01(\x0b2\x1d.cz.proto.JobMeta.HistoryList\x12\x0e\n\x06result\x18\r \x01(\t\x121\n\x0bjob_summary\x18\x0e \x01(\x0b2\x1c.cz.proto.JobSummaryLocation\x121\n\x0cinput_tables\x18\x0f \x01(\x0b2\x1b.cz.proto.JobMeta.TableList\x122\n\routput_tables\x18\x10 \x01(\x0b2\x1b.cz.proto.JobMeta.TableList\x12*\n\x07content\x18\x11 \x01(\x0b2\x19.cz.proto.JobMeta.Content\x12\x12\n\nerror_code\x18\x12 \x01(\t\x12\x15\n\rerror_message\x18\x13 \x01(\t\x12)\n\tprofiling\x18\x14 \x01(\x0b2\x16.cz.proto.JobProfiling\x12\x11\n\tquery_tag\x18\x15 \x01(\t\x12#\n\x04lite\x18\x16 \x01(\x0b2\x15.cz.proto.JobMetaLite\x12\x10\n\x08job_uuid\x18\x17 \x01(\x03\x12\'\n\njob_source\x18\x18 \x01(\x0e2\x13.cz.proto.JobSource\x12*\n\x0cjob_sub_type\x18\x19 \x01(\x0e2\x14.cz.proto.JobSubType\x1a4\n\x0bHistoryList\x12%\n\x07history\x18\x01 \x03(\x0b2\x14.cz.proto.JobHistory\x1a,\n\tPartition\x12\x10\n\x08field_id\x18\x01 \x03(\r\x12\r\n\x05value\x18\x02 \x03(\t\x1a\x92\x02\n\x05Table\x12\x11\n\tnamespace\x18\x01 \x03(\t\x12\x11\n\ttableName\x18\x02 \x01(\t\x12\x0c\n\x04size\x18\x03 \x01(\x04\x12\x0e\n\x06record\x18\x04 \x01(\x04\x12\x12\n\ncache_size\x18\x05 \x01(\x04\x12/\n\npartitions\x18\x06 \x03(\x0b2\x1b.cz.proto.JobMeta.Partition\x12\x13\n\x0binstance_id\x18\x07 \x01(\x03\x12\x12\n\ndelta_size\x18\x08 \x01(\x04\x12\x12\n\nfile_count\x18\t \x01(\x04\x12\x18\n\x10delta_file_count\x18\n \x01(\x04\x12\x0c\n\x04type\x18\x0b \x01(\t\x12\n\n\x02id\x18\x0c \x01(\x04\x12\x0f\n\x07version\x18\r \x01(\x04\x1a3\n\tTableList\x12&\n\x05table\x18\x01 \x03(\x0b2\x17.cz.proto.JobMeta.Table\x1a\xf1\x03\n\x07Content\x12<\n\njob_config\x18\x01 \x03(\x0b2(.cz.proto.JobMeta.Content.JobConfigEntry\x12#\n\x07sql_job\x18\x02 \x01(\x0b2\x10.cz.proto.SQLJobH\x00\x12\x17\n\x0frelease_version\x18\x03 \x01(\t\x12\x1c\n\x14virtual_cluster_name\x18\x04 \x01(\t\x12\x12\n\njob_client\x18\x05 \x01(\t\x12\x0e\n\x06schema\x18\x06 \x01(\t\x12\x11\n\tschema_id\x18\x07 \x01(\x04\x12\x1f\n\x17external_scheduled_info\x18\x08 \x01(\t\x12=\n\x14virtual_cluster_type\x18\t \x01(\x0e2\x1f.com.clickzetta.rm.VClusterType\x12\x18\n\x10disable_failover\x18\n \x01(\x08\x12\x19\n\x11is_continuous_job\x18\x0b \x01(\x08\x12\x11\n\tquery_md5\x18\x0c \x01(\t\x12\x19\n\x11coordinator_label\x18\r \x01(\t\x12\x19\n\x11job_desc_location\x18\x14 \x01(\t\x1a0\n\x0eJobConfigEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01B\x05\n\x03job"\xf0\x05\n\x0bJobMetaLite\x12\x13\n\x0binput_bytes\x18\x01 \x01(\x04\x12\x15\n\rrows_produced\x18\x02 \x01(\x04\x123\n\nquery_lite\x18\x03 \x01(\x0b2\x1f.cz.proto.JobMetaLite.QueryLite\x12=\n\x11job_meta_strategy\x18\x04 \x01(\x0e2".cz.proto.JobMetaOperationStrategy\x12\x12\n\nis_mv_used\x18\x05 \x01(\x08\x12\x16\n\x0eis_automv_used\x18\x06 \x01(\x08\x12%\n\x1ddisable_dump_stats_in_persist\x18\x07 \x01(\x08\x12L\n\x14incremental_property\x18\x08 \x01(\x0b2).cz.proto.JobMetaLite.IncrementalPropertyH\x00\x88\x01\x01\x12\x1b\n\x13is_hit_result_cache\x18\t \x01(\x08\x12\x1b\n\x13result_cache_job_id\x18\n \x01(\t\x12\'\n\x1fresult_cache_not_support_reason\x18\x0b \x01(\t\x12#\n\x1bresult_cache_not_hit_reason\x18\x0c \x01(\t\x12\x1a\n\x12read_metadata_only\x18\r \x01(\x08\x1a5\n\tQueryLite\x12\x11\n\tstatement\x18\x01 \x03(\t\x12\x15\n\rstatement_cut\x18\x02 \x01(\x08\x1a\xab\x01\n\x13IncrementalProperty\x12\x1b\n\x13is_incremental_plan\x18\x01 \x01(\t\x12\x16\n\tsubmitter\x18\x02 \x01(\tH\x00\x88\x01\x01\x12\x13\n\x0bis_dt_or_mv\x18\x03 \x01(\t\x12\x16\n\x0emv_instance_id\x18\x04 \x01(\t\x12\x13\n\x0bmv_table_id\x18\x05 \x01(\t\x12\x0f\n\x07mv_name\x18\x06 \x01(\tB\x0c\n\n_submitterB\x17\n\x15_incremental_property*\x7f\n\tJobStatus\x12\t\n\x05SETUP\x10\x00\x12\x0c\n\x08QUEUEING\x10\x01\x12\x0b\n\x07RUNNING\x10\x02\x12\x0b\n\x07SUCCEED\x10\x03\x12\x0e\n\nCANCELLING\x10\x04\x12\r\n\tCANCELLED\x10\x05\x12\n\n\x06FAILED\x10\x06\x12\x14\n\x10RESUMING_CLUSTER\x10\x07*\xbf\x01\n\tQueryType\x12\x0b\n\x07QT_NONE\x10\x00\x12\r\n\tQT_SELECT\x10\x01\x12\r\n\tQT_INSERT\x10\x02\x12\x0c\n\x08QT_MERGE\x10\x03\x12\r\n\tQT_UPDATE\x10\x04\x12\r\n\tQT_DELETE\x10\x05\x12\x10\n\x0cQT_OTHER_DML\x10\x06\x12\n\n\x06QT_DDL\x10\x07\x12\x16\n\x12QT_CREATE_TABLE_AS\x10\x08\x12\x10\n\x0cQT_CREATE_MV\x10\t\x12\x13\n\x0fQT_SHOW_OR_LIST\x10\n*A\n\x07JobType\x12\x0b\n\x07SQL_JOB\x10\x00\x12\x12\n\x0eCOMPACTION_JOB\x10\x01\x12\x15\n\x11SQL_TRANSLATE_JOB\x10\x02*c\n\x18JobMetaOperationStrategy\x12\x16\n\x12CREATE_WITH_STAGED\x10\x00\x12\x19\n\x15CREATE_WITHOUT_STAGED\x10\x01\x12\x14\n\x10CREATE_ON_FINISH\x10\x02*9\n\tJobSource\x12\x16\n\x12DEFAULT_JOB_SOURCE\x10\x00\x12\x14\n\x10MAINTAIN_SERVICE\x10\x01*h\n\nJobSubType\x12\x18\n\x14DEFAULT_JOB_SUB_TYPE\x10\x00\x12\x1d\n\x19DYNAMIC_TABLE_REFRESH_JOB\x10\x01\x12!\n\x1dMATERIALIZED_VIEW_REFRESH_JOB\x10\x02B\x02P\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'job_meta_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'P\x01'
    _globals['_SQLJOBCONFIG_HINTENTRY']._loaded_options = None
    _globals['_SQLJOBCONFIG_HINTENTRY']._serialized_options = b'8\x01'
    _globals['_JOBMETA_CONTENT_JOBCONFIGENTRY']._loaded_options = None
    _globals['_JOBMETA_CONTENT_JOBCONFIGENTRY']._serialized_options = b'8\x01'
    _globals['_JOBSTATUS']._serialized_start = 3504
    _globals['_JOBSTATUS']._serialized_end = 3631
    _globals['_QUERYTYPE']._serialized_start = 3634
    _globals['_QUERYTYPE']._serialized_end = 3825
    _globals['_JOBTYPE']._serialized_start = 3827
    _globals['_JOBTYPE']._serialized_end = 3892
    _globals['_JOBMETAOPERATIONSTRATEGY']._serialized_start = 3894
    _globals['_JOBMETAOPERATIONSTRATEGY']._serialized_end = 3993
    _globals['_JOBSOURCE']._serialized_start = 3995
    _globals['_JOBSOURCE']._serialized_end = 4052
    _globals['_JOBSUBTYPE']._serialized_start = 4054
    _globals['_JOBSUBTYPE']._serialized_end = 4158
    _globals['_JOBCOST']._serialized_start = 51
    _globals['_JOBCOST']._serialized_end = 119
    _globals['_JOBHISTORY']._serialized_start = 121
    _globals['_JOBHISTORY']._serialized_end = 236
    _globals['_SQLJOBCONFIG']._serialized_start = 239
    _globals['_SQLJOBCONFIG']._serialized_end = 414
    _globals['_SQLJOBCONFIG_HINTENTRY']._serialized_start = 371
    _globals['_SQLJOBCONFIG_HINTENTRY']._serialized_end = 414
    _globals['_SQLJOB']._serialized_start = 417
    _globals['_SQLJOB']._serialized_end = 581
    _globals['_JOBSUMMARYLOCATION']._serialized_start = 584
    _globals['_JOBSUMMARYLOCATION']._serialized_end = 957
    _globals['_JOBPROFILING']._serialized_start = 959
    _globals['_JOBPROFILING']._serialized_end = 1075
    _globals['_JOBPROFILING_JOBPROFILINGITEM']._serialized_start = 1035
    _globals['_JOBPROFILING_JOBPROFILINGITEM']._serialized_end = 1075
    _globals['_JOBMETA']._serialized_start = 1078
    _globals['_JOBMETA']._serialized_end = 2747
    _globals['_JOBMETA_HISTORYLIST']._serialized_start = 1819
    _globals['_JOBMETA_HISTORYLIST']._serialized_end = 1871
    _globals['_JOBMETA_PARTITION']._serialized_start = 1873
    _globals['_JOBMETA_PARTITION']._serialized_end = 1917
    _globals['_JOBMETA_TABLE']._serialized_start = 1920
    _globals['_JOBMETA_TABLE']._serialized_end = 2194
    _globals['_JOBMETA_TABLELIST']._serialized_start = 2196
    _globals['_JOBMETA_TABLELIST']._serialized_end = 2247
    _globals['_JOBMETA_CONTENT']._serialized_start = 2250
    _globals['_JOBMETA_CONTENT']._serialized_end = 2747
    _globals['_JOBMETA_CONTENT_JOBCONFIGENTRY']._serialized_start = 2692
    _globals['_JOBMETA_CONTENT_JOBCONFIGENTRY']._serialized_end = 2740
    _globals['_JOBMETALITE']._serialized_start = 2750
    _globals['_JOBMETALITE']._serialized_end = 3502
    _globals['_JOBMETALITE_QUERYLITE']._serialized_start = 3250
    _globals['_JOBMETALITE_QUERYLITE']._serialized_end = 3303
    _globals['_JOBMETALITE_INCREMENTALPROPERTY']._serialized_start = 3306
    _globals['_JOBMETALITE_INCREMENTALPROPERTY']._serialized_end = 3477