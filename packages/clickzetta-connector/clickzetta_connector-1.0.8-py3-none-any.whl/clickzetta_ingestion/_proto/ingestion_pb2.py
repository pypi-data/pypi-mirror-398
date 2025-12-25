"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'ingestion.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0fingestion.proto\x12\x12cz.proto.ingestion"]\n\x0eResponseStatus\x12&\n\x04code\x18\x01 \x01(\x0e2\x18.cz.proto.ingestion.Code\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x12\n\nrequest_id\x18\x03 \x01(\t",\n\x0bVersionInfo\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0f\n\x07version\x18\x02 \x01(\x05"\x94\x01\n\x0eGatewayRequest\x12\x17\n\x0fmethodEnumValue\x18\x01 \x01(\x05\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x12\n\ninstanceId\x18\x03 \x01(\x03\x12\x0e\n\x06userId\x18\x04 \x01(\x03\x124\n\x0bversionInfo\x18\x05 \x01(\x0b2\x1f.cz.proto.ingestion.VersionInfo"V\n\x0fGatewayResponse\x122\n\x06status\x18\x01 \x01(\x0b2".cz.proto.ingestion.ResponseStatus\x12\x0f\n\x07message\x18\x02 \x01(\t*>\n\x0cIGSTableType\x12\n\n\x06NORMAL\x10\x00\x12\x0b\n\x07CLUSTER\x10\x01\x12\x08\n\x04ACID\x10\x02\x12\x0b\n\x07UNKNOWN\x10\x03*\x9f\x01\n\x04Code\x12\x0b\n\x07SUCCESS\x10\x00\x12\n\n\x06FAILED\x10\x01\x12\x17\n\x13IGS_WORKER_REGISTED\x10\x02\x12\r\n\tTHROTTLED\x10\x03\x12\r\n\tNOT_FOUND\x10\x04\x12\x13\n\x0fALREADY_PRESENT\x10\x05\x12\x0f\n\x0bTABLE_EXIST\x10\x06\x12\x11\n\rTABLE_DROPPED\x10\x07\x12\x0e\n\nCORRUPTION\x10\x08*\xdd\x05\n\nMethodEnum\x12\x14\n\x10GATEWAY_RPC_CALL\x10\x00\x12\x12\n\x0eGET_TABLE_META\x10\x01\x12\x11\n\rCREATE_TABLET\x10\x02\x12\x15\n\x11GET_MUTATE_WORKER\x10\x03\x12\x11\n\rCOMMIT_TABLET\x10\x04\x12\x0f\n\x0bDROP_TABLET\x10\x05\x12\x16\n\x12CHECK_TABLE_EXISTS\x10\x06\x12\x1b\n\x17CREATE_BULK_LOAD_STREAM\x10\x0b\x12\x18\n\x14GET_BULK_LOAD_STREAM\x10\x0c\x12\x1b\n\x17COMMIT_BULK_LOAD_STREAM\x10\r\x12 \n\x1cOPEN_BULK_LOAD_STREAM_WRITER\x10\x0e\x12"\n\x1eFINISH_BULK_LOAD_STREAM_WRITER\x10\x0f\x12\x1b\n\x17CREATE_OR_GET_STREAM_V2\x10\x10\x12\x13\n\x0fCLOSE_STREAM_V2\x10\x11\x12\x17\n\x13GET_ROUTE_WORKER_V2\x10\x12\x12\x1e\n\x1aCREATE_BULK_LOAD_STREAM_V2\x10\x13\x12\x1b\n\x17GET_BULK_LOAD_STREAM_V2\x10\x14\x12\x1e\n\x1aCOMMIT_BULK_LOAD_STREAM_V2\x10\x15\x12#\n\x1fOPEN_BULK_LOAD_STREAM_WRITER_V2\x10\x16\x12%\n!FINISH_BULK_LOAD_STREAM_WRITER_V2\x10\x17\x12%\n!GET_BULK_LOAD_STREAM_STS_TOKEN_V2\x10\x18\x12\r\n\tCOMMIT_V2\x10\x19\x12\x13\n\x0fASYNC_COMMIT_V2\x10\x1a\x12\x1a\n\x16CHECK_COMMIT_RESULT_V2\x10\x1b\x12!\n\x1dGET_ROUTER_CONTROLLER_ADDRESS\x10\x1c\x12\x11\n\rSCHEMA_CHANGE\x10\x1d\x12\x14\n\x10MAINTAIN_TABLETS\x10\x1e2q\n\x14IGSControllerService\x12Y\n\x0eGatewayRpcCall\x12".cz.proto.ingestion.GatewayRequest\x1a#.cz.proto.ingestion.GatewayResponseB\x14\n\x12cz.proto.ingestionb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'ingestion_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'\n\x12cz.proto.ingestion'
    _globals['_IGSTABLETYPE']._serialized_start = 419
    _globals['_IGSTABLETYPE']._serialized_end = 481
    _globals['_CODE']._serialized_start = 484
    _globals['_CODE']._serialized_end = 643
    _globals['_METHODENUM']._serialized_start = 646
    _globals['_METHODENUM']._serialized_end = 1379
    _globals['_RESPONSESTATUS']._serialized_start = 39
    _globals['_RESPONSESTATUS']._serialized_end = 132
    _globals['_VERSIONINFO']._serialized_start = 134
    _globals['_VERSIONINFO']._serialized_end = 178
    _globals['_GATEWAYREQUEST']._serialized_start = 181
    _globals['_GATEWAYREQUEST']._serialized_end = 329
    _globals['_GATEWAYRESPONSE']._serialized_start = 331
    _globals['_GATEWAYRESPONSE']._serialized_end = 417
    _globals['_IGSCONTROLLERSERVICE']._serialized_start = 1381
    _globals['_IGSCONTROLLERSERVICE']._serialized_end = 1494