"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'streaming_pipe_service.proto')
_sym_db = _symbol_database.Default()
from . import service_common_pb2 as service__common__pb2
from . import object_identifier_pb2 as object__identifier__pb2
from . import coordinator_service_pb2 as coordinator__service__pb2
from . import file_system_pb2 as file__system__pb2
from . import file_format_type_pb2 as file__format__type__pb2
from . import table_common_pb2 as table__common__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1cstreaming_pipe_service.proto\x12\x13cz.proto.common_api\x1a\x14service_common.proto\x1a\x17object_identifier.proto\x1a\x19coordinator_service.proto\x1a\x11file_system.proto\x1a\x16file_format_type.proto\x1a\x12table_common.proto"5\n\x0cStreamSchema\x12%\n\x06fields\x18\x01 \x03(\x0b2\x15.cz.proto.FieldSchema"\xdc\x01\n\x0bChannelMeta\x12\x12\n\nchannel_id\x18\x01 \x01(\x03\x12\x16\n\x0erecycle_offset\x18\x02 \x01(\x03\x12\x19\n\x11compaction_offset\x18\x03 \x01(\x03\x12\x16\n\x0ecurrent_offset\x18\x04 \x01(\x03\x12\x13\n\x0bcreate_time\x18\x05 \x01(\x03\x12\x18\n\x10last_modify_time\x18\x06 \x01(\x03\x12\x10\n\x08location\x18\x07 \x01(\t\x12-\n\x0bfile_format\x18\x08 \x01(\x0e2\x18.cz.proto.FileFormatType"\xa3\x01\n\x0fChannelFileMeta\x12\x0c\n\x04path\x18\x01 \x01(\t\x12\x14\n\x0cstart_row_id\x18\x02 \x01(\t\x12\x12\n\nend_row_id\x18\r \x01(\t\x12\x12\n\nchannel_id\x18\x04 \x01(\x03\x12\x0e\n\x06offset\x18\x05 \x01(\x03\x12\x13\n\x0bcommit_time\x18\x06 \x01(\x03\x12\x0c\n\x04size\x18\x07 \x01(\x03\x12\x11\n\trow_count\x18\x08 \x01(\x03"\xd0\x01\n\x13ChannelTempDirToken\x12\x10\n\x08location\x18\x01 \x01(\t\x12-\n\x0bfile_system\x18\x02 \x01(\x0e2\x18.cz.proto.FileSystemType\x12\x11\n\tsts_ak_id\x18\x03 \x01(\t\x12\x15\n\rsts_ak_secret\x18\x04 \x01(\t\x12\x11\n\tsts_token\x18\x05 \x01(\t\x12\x10\n\x08endpoint\x18\x06 \x01(\t\x12\x19\n\x11internal_endpoint\x18\x07 \x01(\t\x12\x0e\n\x06region\x18\x08 \x01(\t"\x88\x01\n\x14CreateChannelRequest\x12,\n\x08table_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x122\n\x0bfile_format\x18\x02 \x01(\x0e2\x18.cz.proto.FileFormatTypeH\x00\x88\x01\x01B\x0e\n\x0c_file_format"\xf3\x01\n\x15CreateChannelResponse\x12-\n\x0bresp_status\x18\x01 \x01(\x0b2\x18.cz.proto.ResponseStatus\x126\n\x0cchannel_meta\x18\x02 \x01(\x0b2 .cz.proto.common_api.ChannelMeta\x12@\n\x0etemp_dir_token\x18\x03 \x01(\x0b2(.cz.proto.common_api.ChannelTempDirToken\x121\n\x06schema\x18\x04 \x01(\x0b2!.cz.proto.common_api.StreamSchema"B\n\x12ListChannelRequest\x12,\n\x08table_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier"|\n\x13ListChannelResponse\x12-\n\x0bresp_status\x18\x01 \x01(\x0b2\x18.cz.proto.ResponseStatus\x126\n\x0cchannel_meta\x18\x02 \x03(\x0b2 .cz.proto.common_api.ChannelMeta"U\n\x11GetChannelRequest\x12,\n\x08table_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12\x12\n\nchannel_id\x18\x02 \x01(\x03"\xf0\x01\n\x12GetChannelResponse\x12-\n\x0bresp_status\x18\x01 \x01(\x0b2\x18.cz.proto.ResponseStatus\x126\n\x0cchannel_meta\x18\x02 \x01(\x0b2 .cz.proto.common_api.ChannelMeta\x12@\n\x0etemp_dir_token\x18\x03 \x01(\x0b2(.cz.proto.common_api.ChannelTempDirToken\x121\n\x06schema\x18\x04 \x01(\x0b2!.cz.proto.common_api.StreamSchema"l\n\x14DeleteChannelRequest\x12,\n\x08table_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12\x12\n\nchannel_id\x18\x02 \x01(\x03\x12\x12\n\ndelete_all\x18\x03 \x01(\x08"F\n\x15DeleteChannelResponse\x12-\n\x0bresp_status\x18\x01 \x01(\x0b2\x18.cz.proto.ResponseStatus"\x93\x01\n\x11CommitFileRequest\x12,\n\x08table_id\x18\x01 \x01(\x0b2\x1a.cz.proto.ObjectIdentifier\x12\x12\n\nchannel_id\x18\x02 \x01(\x03\x12<\n\x0efile_meta_list\x18\x03 \x03(\x0b2$.cz.proto.common_api.ChannelFileMeta"C\n\x12CommitFileResponse\x12-\n\x0bresp_status\x18\x01 \x01(\x0b2\x18.cz.proto.ResponseStatus"\xeb\x03\n\x14StreamingPipeRequest\x12.\n\x07account\x18\x01 \x01(\x0b2\x1d.cz.proto.coordinator.Account\x12\x12\n\nrequest_id\x18\x02 \x01(\t\x12\x13\n\x0binstance_id\x18\x03 \x01(\x03\x12K\n\x16create_channel_request\x18\n \x01(\x0b2).cz.proto.common_api.CreateChannelRequestH\x00\x12G\n\x14list_channel_request\x18\x0b \x01(\x0b2\'.cz.proto.common_api.ListChannelRequestH\x00\x12E\n\x13get_channel_request\x18\x0c \x01(\x0b2&.cz.proto.common_api.GetChannelRequestH\x00\x12K\n\x16delete_channel_request\x18\r \x01(\x0b2).cz.proto.common_api.DeleteChannelRequestH\x00\x12E\n\x13commit_file_request\x18\x0e \x01(\x0b2&.cz.proto.common_api.CommitFileRequestH\x00B\t\n\x07request"\x9e\x03\n\x15StreamingPipeResponse\x12M\n\x17create_channel_response\x18\x01 \x01(\x0b2*.cz.proto.common_api.CreateChannelResponseH\x00\x12I\n\x15list_channel_response\x18\x02 \x01(\x0b2(.cz.proto.common_api.ListChannelResponseH\x00\x12G\n\x14get_channel_response\x18\x03 \x01(\x0b2\'.cz.proto.common_api.GetChannelResponseH\x00\x12M\n\x17delete_channel_response\x18\x04 \x01(\x0b2*.cz.proto.common_api.DeleteChannelResponseH\x00\x12G\n\x14commit_file_response\x18\x05 \x01(\x0b2\'.cz.proto.common_api.CommitFileResponseH\x00B\n\n\x08response2\xee\x04\n\x14StreamingPipeService\x12f\n\rStreamingPipe\x12).cz.proto.common_api.StreamingPipeRequest\x1a*.cz.proto.common_api.StreamingPipeResponse\x12f\n\rCreateChannel\x12).cz.proto.common_api.CreateChannelRequest\x1a*.cz.proto.common_api.CreateChannelResponse\x12`\n\x0bListChannel\x12\'.cz.proto.common_api.ListChannelRequest\x1a(.cz.proto.common_api.ListChannelResponse\x12]\n\nGetChannel\x12&.cz.proto.common_api.GetChannelRequest\x1a\'.cz.proto.common_api.GetChannelResponse\x12f\n\rDeleteChannel\x12).cz.proto.common_api.DeleteChannelRequest\x1a*.cz.proto.common_api.DeleteChannelResponse\x12]\n\nCommitFile\x12&.cz.proto.common_api.CommitFileRequest\x1a\'.cz.proto.common_api.CommitFileResponseb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'streaming_pipe_service_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_STREAMSCHEMA']._serialized_start = 190
    _globals['_STREAMSCHEMA']._serialized_end = 243
    _globals['_CHANNELMETA']._serialized_start = 246
    _globals['_CHANNELMETA']._serialized_end = 466
    _globals['_CHANNELFILEMETA']._serialized_start = 469
    _globals['_CHANNELFILEMETA']._serialized_end = 632
    _globals['_CHANNELTEMPDIRTOKEN']._serialized_start = 635
    _globals['_CHANNELTEMPDIRTOKEN']._serialized_end = 843
    _globals['_CREATECHANNELREQUEST']._serialized_start = 846
    _globals['_CREATECHANNELREQUEST']._serialized_end = 982
    _globals['_CREATECHANNELRESPONSE']._serialized_start = 985
    _globals['_CREATECHANNELRESPONSE']._serialized_end = 1228
    _globals['_LISTCHANNELREQUEST']._serialized_start = 1230
    _globals['_LISTCHANNELREQUEST']._serialized_end = 1296
    _globals['_LISTCHANNELRESPONSE']._serialized_start = 1298
    _globals['_LISTCHANNELRESPONSE']._serialized_end = 1422
    _globals['_GETCHANNELREQUEST']._serialized_start = 1424
    _globals['_GETCHANNELREQUEST']._serialized_end = 1509
    _globals['_GETCHANNELRESPONSE']._serialized_start = 1512
    _globals['_GETCHANNELRESPONSE']._serialized_end = 1752
    _globals['_DELETECHANNELREQUEST']._serialized_start = 1754
    _globals['_DELETECHANNELREQUEST']._serialized_end = 1862
    _globals['_DELETECHANNELRESPONSE']._serialized_start = 1864
    _globals['_DELETECHANNELRESPONSE']._serialized_end = 1934
    _globals['_COMMITFILEREQUEST']._serialized_start = 1937
    _globals['_COMMITFILEREQUEST']._serialized_end = 2084
    _globals['_COMMITFILERESPONSE']._serialized_start = 2086
    _globals['_COMMITFILERESPONSE']._serialized_end = 2153
    _globals['_STREAMINGPIPEREQUEST']._serialized_start = 2156
    _globals['_STREAMINGPIPEREQUEST']._serialized_end = 2647
    _globals['_STREAMINGPIPERESPONSE']._serialized_start = 2650
    _globals['_STREAMINGPIPERESPONSE']._serialized_end = 3064
    _globals['_STREAMINGPIPESERVICE']._serialized_start = 3067
    _globals['_STREAMINGPIPESERVICE']._serialized_end = 3689