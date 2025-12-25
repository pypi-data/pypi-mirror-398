import virtual_cluster_pb2 as _virtual_cluster_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class DisplayVirtualClusterPolicy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DISPLAY_ALL: _ClassVar[DisplayVirtualClusterPolicy]
    DISPLAY_CURRENT_VERSION: _ClassVar[DisplayVirtualClusterPolicy]
    DISPLAY_TARGET_VERSION: _ClassVar[DisplayVirtualClusterPolicy]

class UpgradeVirtualClusterPolicy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UPGRADE_SWITCH: _ClassVar[UpgradeVirtualClusterPolicy]

class UpgradeState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UPGRADE_NONE: _ClassVar[UpgradeState]
    UPGRADE_SWITCHING: _ClassVar[UpgradeState]
    UPGRADE_DRAINING: _ClassVar[UpgradeState]
    UPGRADE_CANCELLING: _ClassVar[UpgradeState]
DISPLAY_ALL: DisplayVirtualClusterPolicy
DISPLAY_CURRENT_VERSION: DisplayVirtualClusterPolicy
DISPLAY_TARGET_VERSION: DisplayVirtualClusterPolicy
UPGRADE_SWITCH: UpgradeVirtualClusterPolicy
UPGRADE_NONE: UpgradeState
UPGRADE_SWITCHING: UpgradeState
UPGRADE_DRAINING: UpgradeState
UPGRADE_CANCELLING: UpgradeState

class CreateVirtualClusterRequest(_message.Message):
    __slots__ = ('properties', 'create_if_not_exists', 'request_info', 'is_suspended')
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    CREATE_IF_NOT_EXISTS_FIELD_NUMBER: _ClassVar[int]
    REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    IS_SUSPENDED_FIELD_NUMBER: _ClassVar[int]
    properties: _virtual_cluster_pb2.VirtualClusterProperties
    create_if_not_exists: bool
    request_info: _virtual_cluster_pb2.RequestInfo
    is_suspended: bool

    def __init__(self, properties: _Optional[_Union[_virtual_cluster_pb2.VirtualClusterProperties, _Mapping]]=..., create_if_not_exists: bool=..., request_info: _Optional[_Union[_virtual_cluster_pb2.RequestInfo, _Mapping]]=..., is_suspended: bool=...) -> None:
        ...

class CreateVirtualClusterResponse(_message.Message):
    __slots__ = ('vc_id', 'response_info')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_INFO_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    response_info: _virtual_cluster_pb2.ResponseInfo

    def __init__(self, vc_id: _Optional[int]=..., response_info: _Optional[_Union[_virtual_cluster_pb2.ResponseInfo, _Mapping]]=...) -> None:
        ...

class AlteredVirtualClusterProperty(_message.Message):
    __slots__ = ('name', 'cluster_size', 'auto_stop_latency_sec', 'auto_start_enabled', 'tags', 'unset_tags', 'comment', 'query_process_time_limit_sec', 'analytics_properties', 'general_properties')

    class TagsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_SIZE_FIELD_NUMBER: _ClassVar[int]
    AUTO_STOP_LATENCY_SEC_FIELD_NUMBER: _ClassVar[int]
    AUTO_START_ENABLED_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    UNSET_TAGS_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    QUERY_PROCESS_TIME_LIMIT_SEC_FIELD_NUMBER: _ClassVar[int]
    ANALYTICS_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    GENERAL_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    name: str
    cluster_size: _virtual_cluster_pb2.VClusterSize
    auto_stop_latency_sec: int
    auto_start_enabled: bool
    tags: _containers.ScalarMap[str, str]
    unset_tags: _containers.RepeatedScalarFieldContainer[str]
    comment: str
    query_process_time_limit_sec: int
    analytics_properties: _virtual_cluster_pb2.AnalyticsProperties
    general_properties: _virtual_cluster_pb2.GeneralProperties

    def __init__(self, name: _Optional[str]=..., cluster_size: _Optional[_Union[_virtual_cluster_pb2.VClusterSize, str]]=..., auto_stop_latency_sec: _Optional[int]=..., auto_start_enabled: bool=..., tags: _Optional[_Mapping[str, str]]=..., unset_tags: _Optional[_Iterable[str]]=..., comment: _Optional[str]=..., query_process_time_limit_sec: _Optional[int]=..., analytics_properties: _Optional[_Union[_virtual_cluster_pb2.AnalyticsProperties, _Mapping]]=..., general_properties: _Optional[_Union[_virtual_cluster_pb2.GeneralProperties, _Mapping]]=...) -> None:
        ...

class UpdateVirtualClustersRequest(_message.Message):
    __slots__ = ('vc_id', 'to_update_properties', 'if_exists', 'request_info')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    TO_UPDATE_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    IF_EXISTS_FIELD_NUMBER: _ClassVar[int]
    REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    to_update_properties: AlteredVirtualClusterProperty
    if_exists: bool
    request_info: _virtual_cluster_pb2.RequestInfo

    def __init__(self, vc_id: _Optional[int]=..., to_update_properties: _Optional[_Union[AlteredVirtualClusterProperty, _Mapping]]=..., if_exists: bool=..., request_info: _Optional[_Union[_virtual_cluster_pb2.RequestInfo, _Mapping]]=...) -> None:
        ...

class UpdateVirtualClusterResponse(_message.Message):
    __slots__ = ('vc_id', 'response_info')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_INFO_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    response_info: _virtual_cluster_pb2.ResponseInfo

    def __init__(self, vc_id: _Optional[int]=..., response_info: _Optional[_Union[_virtual_cluster_pb2.ResponseInfo, _Mapping]]=...) -> None:
        ...

class UpdateVirtualClustersResponse(_message.Message):
    __slots__ = ('responses',)
    RESPONSES_FIELD_NUMBER: _ClassVar[int]
    responses: _containers.RepeatedCompositeFieldContainer[UpdateVirtualClusterResponse]

    def __init__(self, responses: _Optional[_Iterable[_Union[UpdateVirtualClusterResponse, _Mapping]]]=...) -> None:
        ...

class StartVirtualClusterRequest(_message.Message):
    __slots__ = ('vc_id', 'if_exists', 'if_stopped', 'request_info')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    IF_EXISTS_FIELD_NUMBER: _ClassVar[int]
    IF_STOPPED_FIELD_NUMBER: _ClassVar[int]
    REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    if_exists: bool
    if_stopped: bool
    request_info: _virtual_cluster_pb2.RequestInfo

    def __init__(self, vc_id: _Optional[int]=..., if_exists: bool=..., if_stopped: bool=..., request_info: _Optional[_Union[_virtual_cluster_pb2.RequestInfo, _Mapping]]=...) -> None:
        ...

class StartVirtualClusterResponse(_message.Message):
    __slots__ = ('vc_id', 'response_info')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_INFO_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    response_info: _virtual_cluster_pb2.ResponseInfo

    def __init__(self, vc_id: _Optional[int]=..., response_info: _Optional[_Union[_virtual_cluster_pb2.ResponseInfo, _Mapping]]=...) -> None:
        ...

class StopVirtualClusterRequest(_message.Message):
    __slots__ = ('vc_id', 'if_exists', 'force', 'request_info')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    IF_EXISTS_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    if_exists: bool
    force: bool
    request_info: _virtual_cluster_pb2.RequestInfo

    def __init__(self, vc_id: _Optional[int]=..., if_exists: bool=..., force: bool=..., request_info: _Optional[_Union[_virtual_cluster_pb2.RequestInfo, _Mapping]]=...) -> None:
        ...

class StopVirtualClusterResponse(_message.Message):
    __slots__ = ('vc_id', 'response_info')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_INFO_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    response_info: _virtual_cluster_pb2.ResponseInfo

    def __init__(self, vc_id: _Optional[int]=..., response_info: _Optional[_Union[_virtual_cluster_pb2.ResponseInfo, _Mapping]]=...) -> None:
        ...

class ResizeVirtualClusterRequest(_message.Message):
    __slots__ = ('vc_id', 'cluster_size', 'if_exists', 'request_info')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_SIZE_FIELD_NUMBER: _ClassVar[int]
    IF_EXISTS_FIELD_NUMBER: _ClassVar[int]
    REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    cluster_size: _virtual_cluster_pb2.VClusterSize
    if_exists: bool
    request_info: _virtual_cluster_pb2.RequestInfo

    def __init__(self, vc_id: _Optional[int]=..., cluster_size: _Optional[_Union[_virtual_cluster_pb2.VClusterSize, str]]=..., if_exists: bool=..., request_info: _Optional[_Union[_virtual_cluster_pb2.RequestInfo, _Mapping]]=...) -> None:
        ...

class ResizeVirtualClusterResponse(_message.Message):
    __slots__ = ('vc_id', 'response_info')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_INFO_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    response_info: _virtual_cluster_pb2.ResponseInfo

    def __init__(self, vc_id: _Optional[int]=..., response_info: _Optional[_Union[_virtual_cluster_pb2.ResponseInfo, _Mapping]]=...) -> None:
        ...

class VirtualClusterStateInfo(_message.Message):
    __slots__ = ('state', 'pre_state', 'error_msg', 'replica_count', 'state_info')
    STATE_FIELD_NUMBER: _ClassVar[int]
    PRE_STATE_FIELD_NUMBER: _ClassVar[int]
    ERROR_MSG_FIELD_NUMBER: _ClassVar[int]
    REPLICA_COUNT_FIELD_NUMBER: _ClassVar[int]
    STATE_INFO_FIELD_NUMBER: _ClassVar[int]
    state: _virtual_cluster_pb2.VirtualClusterState
    pre_state: _virtual_cluster_pb2.VirtualClusterState
    error_msg: str
    replica_count: int
    state_info: str

    def __init__(self, state: _Optional[_Union[_virtual_cluster_pb2.VirtualClusterState, str]]=..., pre_state: _Optional[_Union[_virtual_cluster_pb2.VirtualClusterState, str]]=..., error_msg: _Optional[str]=..., replica_count: _Optional[int]=..., state_info: _Optional[str]=...) -> None:
        ...

class VirtualClusterJobInfo(_message.Message):
    __slots__ = ('jobs_running', 'jobs_in_queue')
    JOBS_RUNNING_FIELD_NUMBER: _ClassVar[int]
    JOBS_IN_QUEUE_FIELD_NUMBER: _ClassVar[int]
    jobs_running: int
    jobs_in_queue: int

    def __init__(self, jobs_running: _Optional[int]=..., jobs_in_queue: _Optional[int]=...) -> None:
        ...

class VirtualClusterStatus(_message.Message):
    __slots__ = ('vc_id', 'properties', 'job_info', 'state_info')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    JOB_INFO_FIELD_NUMBER: _ClassVar[int]
    STATE_INFO_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    properties: _virtual_cluster_pb2.VirtualClusterProperties
    job_info: VirtualClusterJobInfo
    state_info: VirtualClusterStateInfo

    def __init__(self, vc_id: _Optional[int]=..., properties: _Optional[_Union[_virtual_cluster_pb2.VirtualClusterProperties, _Mapping]]=..., job_info: _Optional[_Union[VirtualClusterJobInfo, _Mapping]]=..., state_info: _Optional[_Union[VirtualClusterStateInfo, _Mapping]]=...) -> None:
        ...

class ListVirtualClusterFilter(_message.Message):
    __slots__ = ('cluster_size', 'cluster_state')
    CLUSTER_SIZE_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_STATE_FIELD_NUMBER: _ClassVar[int]
    cluster_size: _virtual_cluster_pb2.VClusterSize
    cluster_state: _virtual_cluster_pb2.VirtualClusterState

    def __init__(self, cluster_size: _Optional[_Union[_virtual_cluster_pb2.VClusterSize, str]]=..., cluster_state: _Optional[_Union[_virtual_cluster_pb2.VirtualClusterState, str]]=...) -> None:
        ...

class ListVirtualClusterRequest(_message.Message):
    __slots__ = ('instance_id', 'workspace_name', 'pattern', 'where', 'request_info', 'display_policy')
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_NAME_FIELD_NUMBER: _ClassVar[int]
    PATTERN_FIELD_NUMBER: _ClassVar[int]
    WHERE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_POLICY_FIELD_NUMBER: _ClassVar[int]
    instance_id: int
    workspace_name: str
    pattern: str
    where: ListVirtualClusterFilter
    request_info: _virtual_cluster_pb2.RequestInfo
    display_policy: DisplayVirtualClusterPolicy

    def __init__(self, instance_id: _Optional[int]=..., workspace_name: _Optional[str]=..., pattern: _Optional[str]=..., where: _Optional[_Union[ListVirtualClusterFilter, _Mapping]]=..., request_info: _Optional[_Union[_virtual_cluster_pb2.RequestInfo, _Mapping]]=..., display_policy: _Optional[_Union[DisplayVirtualClusterPolicy, str]]=...) -> None:
        ...

class ListVirtualClustersResponse(_message.Message):
    __slots__ = ('statuses', 'response_info')
    STATUSES_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_INFO_FIELD_NUMBER: _ClassVar[int]
    statuses: _containers.RepeatedCompositeFieldContainer[VirtualClusterStatus]
    response_info: _virtual_cluster_pb2.ResponseInfo

    def __init__(self, statuses: _Optional[_Iterable[_Union[VirtualClusterStatus, _Mapping]]]=..., response_info: _Optional[_Union[_virtual_cluster_pb2.ResponseInfo, _Mapping]]=...) -> None:
        ...

class DescribeVirtualClusterRequest(_message.Message):
    __slots__ = ('instance_id', 'workspace_name', 'vc_name', 'request_info', 'display_policy')
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_NAME_FIELD_NUMBER: _ClassVar[int]
    VC_NAME_FIELD_NUMBER: _ClassVar[int]
    REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_POLICY_FIELD_NUMBER: _ClassVar[int]
    instance_id: int
    workspace_name: str
    vc_name: str
    request_info: _virtual_cluster_pb2.RequestInfo
    display_policy: DisplayVirtualClusterPolicy

    def __init__(self, instance_id: _Optional[int]=..., workspace_name: _Optional[str]=..., vc_name: _Optional[str]=..., request_info: _Optional[_Union[_virtual_cluster_pb2.RequestInfo, _Mapping]]=..., display_policy: _Optional[_Union[DisplayVirtualClusterPolicy, str]]=...) -> None:
        ...

class DescribeVirtualClusterResponse(_message.Message):
    __slots__ = ('status', 'response_info')
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_INFO_FIELD_NUMBER: _ClassVar[int]
    status: VirtualClusterStatus
    response_info: _virtual_cluster_pb2.ResponseInfo

    def __init__(self, status: _Optional[_Union[VirtualClusterStatus, _Mapping]]=..., response_info: _Optional[_Union[_virtual_cluster_pb2.ResponseInfo, _Mapping]]=...) -> None:
        ...

class DeleteVirtualClusterRequest(_message.Message):
    __slots__ = ('vc_id', 'if_exists', 'force', 'request_info')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    IF_EXISTS_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    if_exists: bool
    force: bool
    request_info: _virtual_cluster_pb2.RequestInfo

    def __init__(self, vc_id: _Optional[int]=..., if_exists: bool=..., force: bool=..., request_info: _Optional[_Union[_virtual_cluster_pb2.RequestInfo, _Mapping]]=...) -> None:
        ...

class DeleteVirtualClusterResponse(_message.Message):
    __slots__ = ('vc_id', 'response_info')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_INFO_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    response_info: _virtual_cluster_pb2.ResponseInfo

    def __init__(self, vc_id: _Optional[int]=..., response_info: _Optional[_Union[_virtual_cluster_pb2.ResponseInfo, _Mapping]]=...) -> None:
        ...

class CancelAllJobsRequest(_message.Message):
    __slots__ = ('vc_id', 'if_exists', 'request_info')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    IF_EXISTS_FIELD_NUMBER: _ClassVar[int]
    REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    if_exists: bool
    request_info: _virtual_cluster_pb2.RequestInfo

    def __init__(self, vc_id: _Optional[int]=..., if_exists: bool=..., request_info: _Optional[_Union[_virtual_cluster_pb2.RequestInfo, _Mapping]]=...) -> None:
        ...

class CancelAllJobsResponse(_message.Message):
    __slots__ = ('vc_id', 'response_info')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_INFO_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    response_info: _virtual_cluster_pb2.ResponseInfo

    def __init__(self, vc_id: _Optional[int]=..., response_info: _Optional[_Union[_virtual_cluster_pb2.ResponseInfo, _Mapping]]=...) -> None:
        ...

class TerminateVirtualClusterStatusChangeRequest(_message.Message):
    __slots__ = ('vc_id', 'request_info')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    request_info: _virtual_cluster_pb2.RequestInfo

    def __init__(self, vc_id: _Optional[int]=..., request_info: _Optional[_Union[_virtual_cluster_pb2.RequestInfo, _Mapping]]=...) -> None:
        ...

class TerminateVirtualClusterStatusChangeResponse(_message.Message):
    __slots__ = ('vc_id', 'response_info')
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_INFO_FIELD_NUMBER: _ClassVar[int]
    vc_id: int
    response_info: _virtual_cluster_pb2.ResponseInfo

    def __init__(self, vc_id: _Optional[int]=..., response_info: _Optional[_Union[_virtual_cluster_pb2.ResponseInfo, _Mapping]]=...) -> None:
        ...

class UpgradeVirtualClusterRequest(_message.Message):
    __slots__ = ('request_info', 'vc_identifier', 'target_version', 'policy')
    REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    VC_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    TARGET_VERSION_FIELD_NUMBER: _ClassVar[int]
    POLICY_FIELD_NUMBER: _ClassVar[int]
    request_info: _virtual_cluster_pb2.RequestInfo
    vc_identifier: _virtual_cluster_pb2.VClusterIdentifier
    target_version: str
    policy: UpgradeVirtualClusterPolicy

    def __init__(self, request_info: _Optional[_Union[_virtual_cluster_pb2.RequestInfo, _Mapping]]=..., vc_identifier: _Optional[_Union[_virtual_cluster_pb2.VClusterIdentifier, _Mapping]]=..., target_version: _Optional[str]=..., policy: _Optional[_Union[UpgradeVirtualClusterPolicy, str]]=...) -> None:
        ...

class UpgradeVirtualClusterResponse(_message.Message):
    __slots__ = ('response_info',)
    RESPONSE_INFO_FIELD_NUMBER: _ClassVar[int]
    response_info: _virtual_cluster_pb2.ResponseInfo

    def __init__(self, response_info: _Optional[_Union[_virtual_cluster_pb2.ResponseInfo, _Mapping]]=...) -> None:
        ...

class AbortUpgradeVirtualClusterRequest(_message.Message):
    __slots__ = ('request_info', 'vc_identifier')
    REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    VC_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    request_info: _virtual_cluster_pb2.RequestInfo
    vc_identifier: _virtual_cluster_pb2.VClusterIdentifier

    def __init__(self, request_info: _Optional[_Union[_virtual_cluster_pb2.RequestInfo, _Mapping]]=..., vc_identifier: _Optional[_Union[_virtual_cluster_pb2.VClusterIdentifier, _Mapping]]=...) -> None:
        ...

class AbortUpgradeVirtualClusterResponse(_message.Message):
    __slots__ = ('response_info',)
    RESPONSE_INFO_FIELD_NUMBER: _ClassVar[int]
    response_info: _virtual_cluster_pb2.ResponseInfo

    def __init__(self, response_info: _Optional[_Union[_virtual_cluster_pb2.ResponseInfo, _Mapping]]=...) -> None:
        ...

class GetVirtualClusterUpgradeStatusRequest(_message.Message):
    __slots__ = ('request_info', 'vc_identifier')
    REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    VC_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    request_info: _virtual_cluster_pb2.RequestInfo
    vc_identifier: _virtual_cluster_pb2.VClusterIdentifier

    def __init__(self, request_info: _Optional[_Union[_virtual_cluster_pb2.RequestInfo, _Mapping]]=..., vc_identifier: _Optional[_Union[_virtual_cluster_pb2.VClusterIdentifier, _Mapping]]=...) -> None:
        ...

class VirtualClusterUpgradeStatus(_message.Message):
    __slots__ = ('upgrade_state', 'target_version', 'current_version', 'target_vc_id', 'current_vc_id')
    UPGRADE_STATE_FIELD_NUMBER: _ClassVar[int]
    TARGET_VERSION_FIELD_NUMBER: _ClassVar[int]
    CURRENT_VERSION_FIELD_NUMBER: _ClassVar[int]
    TARGET_VC_ID_FIELD_NUMBER: _ClassVar[int]
    CURRENT_VC_ID_FIELD_NUMBER: _ClassVar[int]
    upgrade_state: UpgradeState
    target_version: str
    current_version: str
    target_vc_id: int
    current_vc_id: int

    def __init__(self, upgrade_state: _Optional[_Union[UpgradeState, str]]=..., target_version: _Optional[str]=..., current_version: _Optional[str]=..., target_vc_id: _Optional[int]=..., current_vc_id: _Optional[int]=...) -> None:
        ...

class GetVirtualClusterUpgradeStatusResponse(_message.Message):
    __slots__ = ('response_info', 'upgrade_status')
    RESPONSE_INFO_FIELD_NUMBER: _ClassVar[int]
    UPGRADE_STATUS_FIELD_NUMBER: _ClassVar[int]
    response_info: _virtual_cluster_pb2.ResponseInfo
    upgrade_status: VirtualClusterUpgradeStatus

    def __init__(self, response_info: _Optional[_Union[_virtual_cluster_pb2.ResponseInfo, _Mapping]]=..., upgrade_status: _Optional[_Union[VirtualClusterUpgradeStatus, _Mapping]]=...) -> None:
        ...

class FinishSwitchVirtualClusterRequest(_message.Message):
    __slots__ = ('request_info', 'vc_identifier')
    REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    VC_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    request_info: _virtual_cluster_pb2.RequestInfo
    vc_identifier: _virtual_cluster_pb2.VClusterIdentifier

    def __init__(self, request_info: _Optional[_Union[_virtual_cluster_pb2.RequestInfo, _Mapping]]=..., vc_identifier: _Optional[_Union[_virtual_cluster_pb2.VClusterIdentifier, _Mapping]]=...) -> None:
        ...

class FinishSwitchVirtualClusterResponse(_message.Message):
    __slots__ = ('response_info',)
    RESPONSE_INFO_FIELD_NUMBER: _ClassVar[int]
    response_info: _virtual_cluster_pb2.ResponseInfo

    def __init__(self, response_info: _Optional[_Union[_virtual_cluster_pb2.ResponseInfo, _Mapping]]=...) -> None:
        ...