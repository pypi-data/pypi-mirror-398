from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class TransactionRecord(_message.Message):
    __slots__ = ('state',)
    STATE_FIELD_NUMBER: _ClassVar[int]
    state: int

    def __init__(self, state: _Optional[int]=...) -> None:
        ...

class XidWithState(_message.Message):
    __slots__ = ('xid', 'state')
    XID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    xid: int
    state: int

    def __init__(self, xid: _Optional[int]=..., state: _Optional[int]=...) -> None:
        ...

class CompactedStates(_message.Message):
    __slots__ = ('offset', 'committed', 'aborted')
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    COMMITTED_FIELD_NUMBER: _ClassVar[int]
    ABORTED_FIELD_NUMBER: _ClassVar[int]
    offset: int
    committed: _containers.RepeatedScalarFieldContainer[int]
    aborted: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, offset: _Optional[int]=..., committed: _Optional[_Iterable[int]]=..., aborted: _Optional[_Iterable[int]]=...) -> None:
        ...

class CommittedTable(_message.Message):
    __slots__ = ('table_id', 'last_committed_xid')
    TABLE_ID_FIELD_NUMBER: _ClassVar[int]
    LAST_COMMITTED_XID_FIELD_NUMBER: _ClassVar[int]
    table_id: int
    last_committed_xid: int

    def __init__(self, table_id: _Optional[int]=..., last_committed_xid: _Optional[int]=...) -> None:
        ...

class DistributedTxnSnapshot(_message.Message):
    __slots__ = ('xid', 'incremental_xid', 'xmin', 'xmax', 'compacted_states', 'tables')
    XID_FIELD_NUMBER: _ClassVar[int]
    INCREMENTAL_XID_FIELD_NUMBER: _ClassVar[int]
    XMIN_FIELD_NUMBER: _ClassVar[int]
    XMAX_FIELD_NUMBER: _ClassVar[int]
    COMPACTED_STATES_FIELD_NUMBER: _ClassVar[int]
    TABLES_FIELD_NUMBER: _ClassVar[int]
    xid: int
    incremental_xid: int
    xmin: int
    xmax: int
    compacted_states: CompactedStates
    tables: _containers.RepeatedCompositeFieldContainer[CommittedTable]

    def __init__(self, xid: _Optional[int]=..., incremental_xid: _Optional[int]=..., xmin: _Optional[int]=..., xmax: _Optional[int]=..., compacted_states: _Optional[_Union[CompactedStates, _Mapping]]=..., tables: _Optional[_Iterable[_Union[CommittedTable, _Mapping]]]=...) -> None:
        ...

class LeaderLease(_message.Message):
    __slots__ = ('elected_time', 'last_refresh_time', 'refresh_interval_ms', 'expired_interval_ms', 'status')

    class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Ready: _ClassVar[LeaderLease.Status]
        Wait: _ClassVar[LeaderLease.Status]
        Yield: _ClassVar[LeaderLease.Status]
    Ready: LeaderLease.Status
    Wait: LeaderLease.Status
    Yield: LeaderLease.Status
    ELECTED_TIME_FIELD_NUMBER: _ClassVar[int]
    LAST_REFRESH_TIME_FIELD_NUMBER: _ClassVar[int]
    REFRESH_INTERVAL_MS_FIELD_NUMBER: _ClassVar[int]
    EXPIRED_INTERVAL_MS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    elected_time: int
    last_refresh_time: int
    refresh_interval_ms: int
    expired_interval_ms: int
    status: LeaderLease.Status

    def __init__(self, elected_time: _Optional[int]=..., last_refresh_time: _Optional[int]=..., refresh_interval_ms: _Optional[int]=..., expired_interval_ms: _Optional[int]=..., status: _Optional[_Union[LeaderLease.Status, str]]=...) -> None:
        ...

class LeaderInfo(_message.Message):
    __slots__ = ('address', 'lease', 'prev_leader_address', 'prev_leader_lease')
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    LEASE_FIELD_NUMBER: _ClassVar[int]
    PREV_LEADER_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    PREV_LEADER_LEASE_FIELD_NUMBER: _ClassVar[int]
    address: str
    lease: LeaderLease
    prev_leader_address: str
    prev_leader_lease: LeaderLease

    def __init__(self, address: _Optional[str]=..., lease: _Optional[_Union[LeaderLease, _Mapping]]=..., prev_leader_address: _Optional[str]=..., prev_leader_lease: _Optional[_Union[LeaderLease, _Mapping]]=...) -> None:
        ...