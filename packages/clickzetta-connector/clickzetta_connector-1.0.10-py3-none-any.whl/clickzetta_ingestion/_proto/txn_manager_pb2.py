"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'txn_manager.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11txn_manager.proto\x12\x0bcz.proto.tp""\n\x11TransactionRecord\x12\r\n\x05state\x18\x01 \x01(\x05"*\n\x0cXidWithState\x12\x0b\n\x03xid\x18\x01 \x01(\x03\x12\r\n\x05state\x18\x02 \x01(\x05"E\n\x0fCompactedStates\x12\x0e\n\x06offset\x18\x01 \x01(\x03\x12\x11\n\tcommitted\x18\x02 \x03(\x03\x12\x0f\n\x07aborted\x18\x03 \x03(\x03">\n\x0eCommittedTable\x12\x10\n\x08table_id\x18\x01 \x01(\x03\x12\x1a\n\x12last_committed_xid\x18\x02 \x01(\x03"\xbf\x01\n\x16DistributedTxnSnapshot\x12\x0b\n\x03xid\x18\x02 \x01(\x03\x12\x17\n\x0fincremental_xid\x18\x03 \x01(\x03\x12\x0c\n\x04xmin\x18\x04 \x01(\x03\x12\x0c\n\x04xmax\x18\x05 \x01(\x03\x126\n\x10compacted_states\x18\x06 \x01(\x0b2\x1c.cz.proto.tp.CompactedStates\x12+\n\x06tables\x18\x07 \x03(\x0b2\x1b.cz.proto.tp.CommittedTable"\xd3\x01\n\x0bLeaderLease\x12\x14\n\x0celected_time\x18\x01 \x01(\x04\x12\x19\n\x11last_refresh_time\x18\x02 \x01(\x04\x12\x1b\n\x13refresh_interval_ms\x18\x03 \x01(\x04\x12\x1b\n\x13expired_interval_ms\x18\x04 \x01(\x04\x12/\n\x06status\x18\x05 \x01(\x0e2\x1f.cz.proto.tp.LeaderLease.Status"(\n\x06Status\x12\t\n\x05Ready\x10\x00\x12\x08\n\x04Wait\x10\x01\x12\t\n\x05Yield\x10\x02"\xd0\x01\n\nLeaderInfo\x12\x0f\n\x07address\x18\x01 \x01(\t\x12\'\n\x05lease\x18\x02 \x01(\x0b2\x18.cz.proto.tp.LeaderLease\x12 \n\x13prev_leader_address\x18\x03 \x01(\tH\x00\x88\x01\x01\x128\n\x11prev_leader_lease\x18\x04 \x01(\x0b2\x18.cz.proto.tp.LeaderLeaseH\x01\x88\x01\x01B\x16\n\x14_prev_leader_addressB\x14\n\x12_prev_leader_leaseb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'txn_manager_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_TRANSACTIONRECORD']._serialized_start = 34
    _globals['_TRANSACTIONRECORD']._serialized_end = 68
    _globals['_XIDWITHSTATE']._serialized_start = 70
    _globals['_XIDWITHSTATE']._serialized_end = 112
    _globals['_COMPACTEDSTATES']._serialized_start = 114
    _globals['_COMPACTEDSTATES']._serialized_end = 183
    _globals['_COMMITTEDTABLE']._serialized_start = 185
    _globals['_COMMITTEDTABLE']._serialized_end = 247
    _globals['_DISTRIBUTEDTXNSNAPSHOT']._serialized_start = 250
    _globals['_DISTRIBUTEDTXNSNAPSHOT']._serialized_end = 441
    _globals['_LEADERLEASE']._serialized_start = 444
    _globals['_LEADERLEASE']._serialized_end = 655
    _globals['_LEADERLEASE_STATUS']._serialized_start = 615
    _globals['_LEADERLEASE_STATUS']._serialized_end = 655
    _globals['_LEADERINFO']._serialized_start = 658
    _globals['_LEADERINFO']._serialized_end = 866