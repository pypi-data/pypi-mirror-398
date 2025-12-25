import bucket_info_pb2 as _bucket_info_pb2
import ddl_pb2 as _ddl_pb2
import data_type_pb2 as _data_type_pb2
import file_format_type_pb2 as _file_format_type_pb2
import txn_manager_pb2 as _txn_manager_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class Code(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SUCCESS: _ClassVar[Code]
    FAILED: _ClassVar[Code]
    THROTTLED: _ClassVar[Code]
    INTERNAL_ERROR: _ClassVar[Code]
    PRECHECK_FAILED: _ClassVar[Code]
    PARTIALLY_SUCCESS: _ClassVar[Code]
    STREAM_UNAVAILABLE: _ClassVar[Code]
    NEED_REDIRECT: _ClassVar[Code]

class BulkLoadStreamState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BL_CREATED: _ClassVar[BulkLoadStreamState]
    BL_SEALED: _ClassVar[BulkLoadStreamState]
    BL_COMMIT_SUBMITTED: _ClassVar[BulkLoadStreamState]
    BL_COMMIT_SUCCESS: _ClassVar[BulkLoadStreamState]
    BL_COMMIT_FAILED: _ClassVar[BulkLoadStreamState]
    BL_CANCELLED: _ClassVar[BulkLoadStreamState]

class BulkLoadStreamOperation(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BL_APPEND: _ClassVar[BulkLoadStreamOperation]
    BL_OVERWRITE: _ClassVar[BulkLoadStreamOperation]
    BL_UPSERT: _ClassVar[BulkLoadStreamOperation]

class ConnectMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DIRECT: _ClassVar[ConnectMode]
    GATEWAY: _ClassVar[ConnectMode]
    GATEWAY_INTERNAL: _ClassVar[ConnectMode]
    GATEWAY_DIRECT: _ClassVar[ConnectMode]
    GATEWAY_DIRECT_ALL: _ClassVar[ConnectMode]

class MaintainTabletOperation(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RELOAD_TABLET: _ClassVar[MaintainTabletOperation]
    FLUSH_TABLET: _ClassVar[MaintainTabletOperation]

class OperationType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN: _ClassVar[OperationType]
    INSERT: _ClassVar[OperationType]
    UPDATE: _ClassVar[OperationType]
    DELETE: _ClassVar[OperationType]
    UPSERT: _ClassVar[OperationType]
    INSERT_IGNORE: _ClassVar[OperationType]
    UPDATE_IGNORE: _ClassVar[OperationType]
    DELETE_IGNORE: _ClassVar[OperationType]
SUCCESS: Code
FAILED: Code
THROTTLED: Code
INTERNAL_ERROR: Code
PRECHECK_FAILED: Code
PARTIALLY_SUCCESS: Code
STREAM_UNAVAILABLE: Code
NEED_REDIRECT: Code
BL_CREATED: BulkLoadStreamState
BL_SEALED: BulkLoadStreamState
BL_COMMIT_SUBMITTED: BulkLoadStreamState
BL_COMMIT_SUCCESS: BulkLoadStreamState
BL_COMMIT_FAILED: BulkLoadStreamState
BL_CANCELLED: BulkLoadStreamState
BL_APPEND: BulkLoadStreamOperation
BL_OVERWRITE: BulkLoadStreamOperation
BL_UPSERT: BulkLoadStreamOperation
DIRECT: ConnectMode
GATEWAY: ConnectMode
GATEWAY_INTERNAL: ConnectMode
GATEWAY_DIRECT: ConnectMode
GATEWAY_DIRECT_ALL: ConnectMode
RELOAD_TABLET: MaintainTabletOperation
FLUSH_TABLET: MaintainTabletOperation
UNKNOWN: OperationType
INSERT: OperationType
UPDATE: OperationType
DELETE: OperationType
UPSERT: OperationType
INSERT_IGNORE: OperationType
UPDATE_IGNORE: OperationType
DELETE_IGNORE: OperationType

class UserIdentifier(_message.Message):
    __slots__ = ('instance_id', 'workspace', 'user_name', 'user_id')
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    USER_NAME_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    instance_id: int
    workspace: str
    user_name: str
    user_id: int

    def __init__(self, instance_id: _Optional[int]=..., workspace: _Optional[str]=..., user_name: _Optional[str]=..., user_id: _Optional[int]=...) -> None:
        ...

class Account(_message.Message):
    __slots__ = ('user_ident', 'token')
    USER_IDENT_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    user_ident: UserIdentifier
    token: str

    def __init__(self, user_ident: _Optional[_Union[UserIdentifier, _Mapping]]=..., token: _Optional[str]=...) -> None:
        ...

class TableIdentifier(_message.Message):
    __slots__ = ('instance_id', 'workspace', 'schema_name', 'table_name')
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_NAME_FIELD_NUMBER: _ClassVar[int]
    TABLE_NAME_FIELD_NUMBER: _ClassVar[int]
    instance_id: int
    workspace: str
    schema_name: str
    table_name: str

    def __init__(self, instance_id: _Optional[int]=..., workspace: _Optional[str]=..., schema_name: _Optional[str]=..., table_name: _Optional[str]=...) -> None:
        ...

class ResponseStatus(_message.Message):
    __slots__ = ('code', 'error_message', 'request_id')
    CODE_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    code: Code
    error_message: str
    request_id: str

    def __init__(self, code: _Optional[_Union[Code, str]]=..., error_message: _Optional[str]=..., request_id: _Optional[str]=...) -> None:
        ...

class DataField(_message.Message):
    __slots__ = ('name', 'type')
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    name: str
    type: _data_type_pb2.DataType

    def __init__(self, name: _Optional[str]=..., type: _Optional[_Union[_data_type_pb2.DataType, _Mapping]]=...) -> None:
        ...

class DistributionSpec(_message.Message):
    __slots__ = ('field_ids', 'hash_functions', 'num_buckets')
    FIELD_IDS_FIELD_NUMBER: _ClassVar[int]
    HASH_FUNCTIONS_FIELD_NUMBER: _ClassVar[int]
    NUM_BUCKETS_FIELD_NUMBER: _ClassVar[int]
    field_ids: _containers.RepeatedScalarFieldContainer[int]
    hash_functions: _containers.RepeatedScalarFieldContainer[str]
    num_buckets: int

    def __init__(self, field_ids: _Optional[_Iterable[int]]=..., hash_functions: _Optional[_Iterable[str]]=..., num_buckets: _Optional[int]=...) -> None:
        ...

class PrimaryKeySpec(_message.Message):
    __slots__ = ('field_ids',)
    FIELD_IDS_FIELD_NUMBER: _ClassVar[int]
    field_ids: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, field_ids: _Optional[_Iterable[int]]=...) -> None:
        ...

class PartitionSpec(_message.Message):
    __slots__ = ('src_field_ids',)
    SRC_FIELD_IDS_FIELD_NUMBER: _ClassVar[int]
    src_field_ids: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, src_field_ids: _Optional[_Iterable[int]]=...) -> None:
        ...

class StreamSchema(_message.Message):
    __slots__ = ('data_fields', 'dist_spec', 'primary_key_spec', 'partition_spec')
    DATA_FIELDS_FIELD_NUMBER: _ClassVar[int]
    DIST_SPEC_FIELD_NUMBER: _ClassVar[int]
    PRIMARY_KEY_SPEC_FIELD_NUMBER: _ClassVar[int]
    PARTITION_SPEC_FIELD_NUMBER: _ClassVar[int]
    data_fields: _containers.RepeatedCompositeFieldContainer[DataField]
    dist_spec: DistributionSpec
    primary_key_spec: PrimaryKeySpec
    partition_spec: PartitionSpec

    def __init__(self, data_fields: _Optional[_Iterable[_Union[DataField, _Mapping]]]=..., dist_spec: _Optional[_Union[DistributionSpec, _Mapping]]=..., primary_key_spec: _Optional[_Union[PrimaryKeySpec, _Mapping]]=..., partition_spec: _Optional[_Union[PartitionSpec, _Mapping]]=...) -> None:
        ...

class CreateOrGetStreamRequest(_message.Message):
    __slots__ = ('account', 'table_ident', 'num_tablets')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    TABLE_IDENT_FIELD_NUMBER: _ClassVar[int]
    NUM_TABLETS_FIELD_NUMBER: _ClassVar[int]
    account: Account
    table_ident: TableIdentifier
    num_tablets: int

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., table_ident: _Optional[_Union[TableIdentifier, _Mapping]]=..., num_tablets: _Optional[int]=...) -> None:
        ...

class CreateOrGetStreamResponse(_message.Message):
    __slots__ = ('table_ident', 'data_schema', 'already_exists', 'status', 'require_commit')
    TABLE_IDENT_FIELD_NUMBER: _ClassVar[int]
    DATA_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    ALREADY_EXISTS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    REQUIRE_COMMIT_FIELD_NUMBER: _ClassVar[int]
    table_ident: TableIdentifier
    data_schema: StreamSchema
    already_exists: bool
    status: ResponseStatus
    require_commit: bool

    def __init__(self, table_ident: _Optional[_Union[TableIdentifier, _Mapping]]=..., data_schema: _Optional[_Union[StreamSchema, _Mapping]]=..., already_exists: bool=..., status: _Optional[_Union[ResponseStatus, _Mapping]]=..., require_commit: bool=...) -> None:
        ...

class CloseStreamRequest(_message.Message):
    __slots__ = ('account', 'table_ident')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    TABLE_IDENT_FIELD_NUMBER: _ClassVar[int]
    account: Account
    table_ident: TableIdentifier

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., table_ident: _Optional[_Union[TableIdentifier, _Mapping]]=...) -> None:
        ...

class CloseStreamResponse(_message.Message):
    __slots__ = ('status',)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=...) -> None:
        ...

class OssStagingPathInfo(_message.Message):
    __slots__ = ('path', 'sts_ak_id', 'sts_ak_secret', 'sts_token', 'oss_endpoint', 'oss_internal_endpoint', 'oss_expire_time')
    PATH_FIELD_NUMBER: _ClassVar[int]
    STS_AK_ID_FIELD_NUMBER: _ClassVar[int]
    STS_AK_SECRET_FIELD_NUMBER: _ClassVar[int]
    STS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    OSS_ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    OSS_INTERNAL_ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    OSS_EXPIRE_TIME_FIELD_NUMBER: _ClassVar[int]
    path: str
    sts_ak_id: str
    sts_ak_secret: str
    sts_token: str
    oss_endpoint: str
    oss_internal_endpoint: str
    oss_expire_time: int

    def __init__(self, path: _Optional[str]=..., sts_ak_id: _Optional[str]=..., sts_ak_secret: _Optional[str]=..., sts_token: _Optional[str]=..., oss_endpoint: _Optional[str]=..., oss_internal_endpoint: _Optional[str]=..., oss_expire_time: _Optional[int]=...) -> None:
        ...

class CosStagingPathInfo(_message.Message):
    __slots__ = ('path', 'sts_ak_id', 'sts_ak_secret', 'sts_token', 'cos_region', 'cos_expire_time')
    PATH_FIELD_NUMBER: _ClassVar[int]
    STS_AK_ID_FIELD_NUMBER: _ClassVar[int]
    STS_AK_SECRET_FIELD_NUMBER: _ClassVar[int]
    STS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    COS_REGION_FIELD_NUMBER: _ClassVar[int]
    COS_EXPIRE_TIME_FIELD_NUMBER: _ClassVar[int]
    path: str
    sts_ak_id: str
    sts_ak_secret: str
    sts_token: str
    cos_region: str
    cos_expire_time: int

    def __init__(self, path: _Optional[str]=..., sts_ak_id: _Optional[str]=..., sts_ak_secret: _Optional[str]=..., sts_token: _Optional[str]=..., cos_region: _Optional[str]=..., cos_expire_time: _Optional[int]=...) -> None:
        ...

class S3StagingPathInfo(_message.Message):
    __slots__ = ('path', 'sts_ak_id', 'sts_ak_secret', 'sts_token', 's3_region', 's3_expire_time')
    PATH_FIELD_NUMBER: _ClassVar[int]
    STS_AK_ID_FIELD_NUMBER: _ClassVar[int]
    STS_AK_SECRET_FIELD_NUMBER: _ClassVar[int]
    STS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    S3_REGION_FIELD_NUMBER: _ClassVar[int]
    S3_EXPIRE_TIME_FIELD_NUMBER: _ClassVar[int]
    path: str
    sts_ak_id: str
    sts_ak_secret: str
    sts_token: str
    s3_region: str
    s3_expire_time: int

    def __init__(self, path: _Optional[str]=..., sts_ak_id: _Optional[str]=..., sts_ak_secret: _Optional[str]=..., sts_token: _Optional[str]=..., s3_region: _Optional[str]=..., s3_expire_time: _Optional[int]=...) -> None:
        ...

class GcsStagingPathInfo(_message.Message):
    __slots__ = ('path', 'sts_ak_id', 'sts_ak_secret', 'sts_token', 'gcs_region', 'gcs_expire_time')
    PATH_FIELD_NUMBER: _ClassVar[int]
    STS_AK_ID_FIELD_NUMBER: _ClassVar[int]
    STS_AK_SECRET_FIELD_NUMBER: _ClassVar[int]
    STS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    GCS_REGION_FIELD_NUMBER: _ClassVar[int]
    GCS_EXPIRE_TIME_FIELD_NUMBER: _ClassVar[int]
    path: str
    sts_ak_id: str
    sts_ak_secret: str
    sts_token: str
    gcs_region: str
    gcs_expire_time: int

    def __init__(self, path: _Optional[str]=..., sts_ak_id: _Optional[str]=..., sts_ak_secret: _Optional[str]=..., sts_token: _Optional[str]=..., gcs_region: _Optional[str]=..., gcs_expire_time: _Optional[int]=...) -> None:
        ...

class ObsStagingPathInfo(_message.Message):
    __slots__ = ('path', 'sts_ak_id', 'sts_ak_secret', 'sts_token', 'obs_endpoint', 'obs_expire_time')
    PATH_FIELD_NUMBER: _ClassVar[int]
    STS_AK_ID_FIELD_NUMBER: _ClassVar[int]
    STS_AK_SECRET_FIELD_NUMBER: _ClassVar[int]
    STS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    OBS_ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    OBS_EXPIRE_TIME_FIELD_NUMBER: _ClassVar[int]
    path: str
    sts_ak_id: str
    sts_ak_secret: str
    sts_token: str
    obs_endpoint: str
    obs_expire_time: int

    def __init__(self, path: _Optional[str]=..., sts_ak_id: _Optional[str]=..., sts_ak_secret: _Optional[str]=..., sts_token: _Optional[str]=..., obs_endpoint: _Optional[str]=..., obs_expire_time: _Optional[int]=...) -> None:
        ...

class TosStagingPathInfo(_message.Message):
    __slots__ = ('path', 'sts_ak_id', 'sts_ak_secret', 'sts_token', 'tos_region', 'tos_expire_time')
    PATH_FIELD_NUMBER: _ClassVar[int]
    STS_AK_ID_FIELD_NUMBER: _ClassVar[int]
    STS_AK_SECRET_FIELD_NUMBER: _ClassVar[int]
    STS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TOS_REGION_FIELD_NUMBER: _ClassVar[int]
    TOS_EXPIRE_TIME_FIELD_NUMBER: _ClassVar[int]
    path: str
    sts_ak_id: str
    sts_ak_secret: str
    sts_token: str
    tos_region: str
    tos_expire_time: int

    def __init__(self, path: _Optional[str]=..., sts_ak_id: _Optional[str]=..., sts_ak_secret: _Optional[str]=..., sts_token: _Optional[str]=..., tos_region: _Optional[str]=..., tos_expire_time: _Optional[int]=...) -> None:
        ...

class LocalStagingPathInfo(_message.Message):
    __slots__ = ('path',)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: str

    def __init__(self, path: _Optional[str]=...) -> None:
        ...

class StagingPathInfo(_message.Message):
    __slots__ = ('oss_path', 'cos_path', 'local_path', 's3_path', 'gcs_path', 'obs_path', 'tos_path')
    OSS_PATH_FIELD_NUMBER: _ClassVar[int]
    COS_PATH_FIELD_NUMBER: _ClassVar[int]
    LOCAL_PATH_FIELD_NUMBER: _ClassVar[int]
    S3_PATH_FIELD_NUMBER: _ClassVar[int]
    GCS_PATH_FIELD_NUMBER: _ClassVar[int]
    OBS_PATH_FIELD_NUMBER: _ClassVar[int]
    TOS_PATH_FIELD_NUMBER: _ClassVar[int]
    oss_path: OssStagingPathInfo
    cos_path: CosStagingPathInfo
    local_path: LocalStagingPathInfo
    s3_path: S3StagingPathInfo
    gcs_path: GcsStagingPathInfo
    obs_path: ObsStagingPathInfo
    tos_path: TosStagingPathInfo

    def __init__(self, oss_path: _Optional[_Union[OssStagingPathInfo, _Mapping]]=..., cos_path: _Optional[_Union[CosStagingPathInfo, _Mapping]]=..., local_path: _Optional[_Union[LocalStagingPathInfo, _Mapping]]=..., s3_path: _Optional[_Union[S3StagingPathInfo, _Mapping]]=..., gcs_path: _Optional[_Union[GcsStagingPathInfo, _Mapping]]=..., obs_path: _Optional[_Union[ObsStagingPathInfo, _Mapping]]=..., tos_path: _Optional[_Union[TosStagingPathInfo, _Mapping]]=...) -> None:
        ...

class BulkLoadStreamInfo(_message.Message):
    __slots__ = ('stream_id', 'stream_state', 'sql_job_id', 'identifier', 'operation', 'partition_spec', 'record_keys', 'stream_schema', 'sql_error_msg', 'prefer_internal_endpoint', 'encryption_options')

    class EncryptionOptionsEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    STREAM_STATE_FIELD_NUMBER: _ClassVar[int]
    SQL_JOB_ID_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    PARTITION_SPEC_FIELD_NUMBER: _ClassVar[int]
    RECORD_KEYS_FIELD_NUMBER: _ClassVar[int]
    STREAM_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    SQL_ERROR_MSG_FIELD_NUMBER: _ClassVar[int]
    PREFER_INTERNAL_ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    stream_id: str
    stream_state: BulkLoadStreamState
    sql_job_id: str
    identifier: TableIdentifier
    operation: BulkLoadStreamOperation
    partition_spec: str
    record_keys: _containers.RepeatedScalarFieldContainer[str]
    stream_schema: StreamSchema
    sql_error_msg: str
    prefer_internal_endpoint: bool
    encryption_options: _containers.ScalarMap[str, str]

    def __init__(self, stream_id: _Optional[str]=..., stream_state: _Optional[_Union[BulkLoadStreamState, str]]=..., sql_job_id: _Optional[str]=..., identifier: _Optional[_Union[TableIdentifier, _Mapping]]=..., operation: _Optional[_Union[BulkLoadStreamOperation, str]]=..., partition_spec: _Optional[str]=..., record_keys: _Optional[_Iterable[str]]=..., stream_schema: _Optional[_Union[StreamSchema, _Mapping]]=..., sql_error_msg: _Optional[str]=..., prefer_internal_endpoint: bool=..., encryption_options: _Optional[_Mapping[str, str]]=...) -> None:
        ...

class BulkLoadStreamWriterConfig(_message.Message):
    __slots__ = ('staging_path', 'file_format', 'max_num_rows_per_file', 'max_size_in_bytes_per_file', 'max_string_bytes', 'max_binary_bytes', 'max_json_bytes')
    STAGING_PATH_FIELD_NUMBER: _ClassVar[int]
    FILE_FORMAT_FIELD_NUMBER: _ClassVar[int]
    MAX_NUM_ROWS_PER_FILE_FIELD_NUMBER: _ClassVar[int]
    MAX_SIZE_IN_BYTES_PER_FILE_FIELD_NUMBER: _ClassVar[int]
    MAX_STRING_BYTES_FIELD_NUMBER: _ClassVar[int]
    MAX_BINARY_BYTES_FIELD_NUMBER: _ClassVar[int]
    MAX_JSON_BYTES_FIELD_NUMBER: _ClassVar[int]
    staging_path: StagingPathInfo
    file_format: _file_format_type_pb2.FileFormatType
    max_num_rows_per_file: int
    max_size_in_bytes_per_file: int
    max_string_bytes: int
    max_binary_bytes: int
    max_json_bytes: int

    def __init__(self, staging_path: _Optional[_Union[StagingPathInfo, _Mapping]]=..., file_format: _Optional[_Union[_file_format_type_pb2.FileFormatType, str]]=..., max_num_rows_per_file: _Optional[int]=..., max_size_in_bytes_per_file: _Optional[int]=..., max_string_bytes: _Optional[int]=..., max_binary_bytes: _Optional[int]=..., max_json_bytes: _Optional[int]=...) -> None:
        ...

class CreateBulkLoadStreamRequest(_message.Message):
    __slots__ = ('account', 'identifier', 'operation', 'partition_spec', 'record_keys', 'prefer_internal_endpoint')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    PARTITION_SPEC_FIELD_NUMBER: _ClassVar[int]
    RECORD_KEYS_FIELD_NUMBER: _ClassVar[int]
    PREFER_INTERNAL_ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    account: Account
    identifier: TableIdentifier
    operation: BulkLoadStreamOperation
    partition_spec: str
    record_keys: _containers.RepeatedScalarFieldContainer[str]
    prefer_internal_endpoint: bool

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., identifier: _Optional[_Union[TableIdentifier, _Mapping]]=..., operation: _Optional[_Union[BulkLoadStreamOperation, str]]=..., partition_spec: _Optional[str]=..., record_keys: _Optional[_Iterable[str]]=..., prefer_internal_endpoint: bool=...) -> None:
        ...

class CreateBulkLoadStreamResponse(_message.Message):
    __slots__ = ('status', 'info')
    STATUS_FIELD_NUMBER: _ClassVar[int]
    INFO_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus
    info: BulkLoadStreamInfo

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=..., info: _Optional[_Union[BulkLoadStreamInfo, _Mapping]]=...) -> None:
        ...

class GetBulkLoadStreamRequest(_message.Message):
    __slots__ = ('account', 'identifier', 'stream_id', 'need_table_meta')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    NEED_TABLE_META_FIELD_NUMBER: _ClassVar[int]
    account: Account
    identifier: TableIdentifier
    stream_id: str
    need_table_meta: bool

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., identifier: _Optional[_Union[TableIdentifier, _Mapping]]=..., stream_id: _Optional[str]=..., need_table_meta: bool=...) -> None:
        ...

class GetBulkLoadStreamResponse(_message.Message):
    __slots__ = ('status', 'info')
    STATUS_FIELD_NUMBER: _ClassVar[int]
    INFO_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus
    info: BulkLoadStreamInfo

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=..., info: _Optional[_Union[BulkLoadStreamInfo, _Mapping]]=...) -> None:
        ...

class CommitBulkLoadStreamRequest(_message.Message):
    __slots__ = ('account', 'identifier', 'stream_id', 'execute_workspace', 'execute_vc_name', 'commit_mode', 'spec_partition_ids')

    class CommitMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        COMMIT_STREAM: _ClassVar[CommitBulkLoadStreamRequest.CommitMode]
        ABORT_STREAM: _ClassVar[CommitBulkLoadStreamRequest.CommitMode]
    COMMIT_STREAM: CommitBulkLoadStreamRequest.CommitMode
    ABORT_STREAM: CommitBulkLoadStreamRequest.CommitMode
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    EXECUTE_WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    EXECUTE_VC_NAME_FIELD_NUMBER: _ClassVar[int]
    COMMIT_MODE_FIELD_NUMBER: _ClassVar[int]
    SPEC_PARTITION_IDS_FIELD_NUMBER: _ClassVar[int]
    account: Account
    identifier: TableIdentifier
    stream_id: str
    execute_workspace: str
    execute_vc_name: str
    commit_mode: CommitBulkLoadStreamRequest.CommitMode
    spec_partition_ids: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., identifier: _Optional[_Union[TableIdentifier, _Mapping]]=..., stream_id: _Optional[str]=..., execute_workspace: _Optional[str]=..., execute_vc_name: _Optional[str]=..., commit_mode: _Optional[_Union[CommitBulkLoadStreamRequest.CommitMode, str]]=..., spec_partition_ids: _Optional[_Iterable[int]]=...) -> None:
        ...

class CommitBulkLoadStreamResponse(_message.Message):
    __slots__ = ('status', 'info')
    STATUS_FIELD_NUMBER: _ClassVar[int]
    INFO_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus
    info: BulkLoadStreamInfo

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=..., info: _Optional[_Union[BulkLoadStreamInfo, _Mapping]]=...) -> None:
        ...

class GetBulkLoadStreamStsTokenRequest(_message.Message):
    __slots__ = ('account', 'identifier', 'stream_id')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    account: Account
    identifier: TableIdentifier
    stream_id: str

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., identifier: _Optional[_Union[TableIdentifier, _Mapping]]=..., stream_id: _Optional[str]=...) -> None:
        ...

class GetBulkLoadStreamStsTokenResponse(_message.Message):
    __slots__ = ('status', 'staging_path')
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STAGING_PATH_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus
    staging_path: StagingPathInfo

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=..., staging_path: _Optional[_Union[StagingPathInfo, _Mapping]]=...) -> None:
        ...

class OpenBulkLoadStreamWriterRequest(_message.Message):
    __slots__ = ('account', 'identifier', 'stream_id', 'partition_id')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    account: Account
    identifier: TableIdentifier
    stream_id: str
    partition_id: int

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., identifier: _Optional[_Union[TableIdentifier, _Mapping]]=..., stream_id: _Optional[str]=..., partition_id: _Optional[int]=...) -> None:
        ...

class OpenBulkLoadStreamWriterResponse(_message.Message):
    __slots__ = ('status', 'config')
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus
    config: BulkLoadStreamWriterConfig

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=..., config: _Optional[_Union[BulkLoadStreamWriterConfig, _Mapping]]=...) -> None:
        ...

class FinishBulkLoadStreamWriterRequest(_message.Message):
    __slots__ = ('account', 'identifier', 'stream_id', 'partition_id', 'written_files', 'written_lengths')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    WRITTEN_FILES_FIELD_NUMBER: _ClassVar[int]
    WRITTEN_LENGTHS_FIELD_NUMBER: _ClassVar[int]
    account: Account
    identifier: TableIdentifier
    stream_id: str
    partition_id: int
    written_files: _containers.RepeatedScalarFieldContainer[str]
    written_lengths: _containers.RepeatedScalarFieldContainer[int]

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., identifier: _Optional[_Union[TableIdentifier, _Mapping]]=..., stream_id: _Optional[str]=..., partition_id: _Optional[int]=..., written_files: _Optional[_Iterable[str]]=..., written_lengths: _Optional[_Iterable[int]]=...) -> None:
        ...

class FinishBulkLoadStreamWriterResponse(_message.Message):
    __slots__ = ('status',)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=...) -> None:
        ...

class GetRouteWorkersRequest(_message.Message):
    __slots__ = ('table_ident', 'connect_mode', 'tablet_id', 'need_bucket_ids')
    TABLE_IDENT_FIELD_NUMBER: _ClassVar[int]
    CONNECT_MODE_FIELD_NUMBER: _ClassVar[int]
    TABLET_ID_FIELD_NUMBER: _ClassVar[int]
    NEED_BUCKET_IDS_FIELD_NUMBER: _ClassVar[int]
    table_ident: TableIdentifier
    connect_mode: ConnectMode
    tablet_id: _containers.RepeatedScalarFieldContainer[int]
    need_bucket_ids: bool

    def __init__(self, table_ident: _Optional[_Union[TableIdentifier, _Mapping]]=..., connect_mode: _Optional[_Union[ConnectMode, str]]=..., tablet_id: _Optional[_Iterable[int]]=..., need_bucket_ids: bool=...) -> None:
        ...

class HostPortTuple(_message.Message):
    __slots__ = ('host', 'port')
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    host: str
    port: int

    def __init__(self, host: _Optional[str]=..., port: _Optional[int]=...) -> None:
        ...

class GetRouteWorkersResponse(_message.Message):
    __slots__ = ('tuple', 'tablet_id', 'status', 'bucket_ids')
    TUPLE_FIELD_NUMBER: _ClassVar[int]
    TABLET_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    BUCKET_IDS_FIELD_NUMBER: _ClassVar[int]
    tuple: _containers.RepeatedCompositeFieldContainer[HostPortTuple]
    tablet_id: _containers.RepeatedScalarFieldContainer[int]
    status: ResponseStatus
    bucket_ids: _containers.RepeatedCompositeFieldContainer[_bucket_info_pb2.BucketIds]

    def __init__(self, tuple: _Optional[_Iterable[_Union[HostPortTuple, _Mapping]]]=..., tablet_id: _Optional[_Iterable[int]]=..., status: _Optional[_Union[ResponseStatus, _Mapping]]=..., bucket_ids: _Optional[_Iterable[_Union[_bucket_info_pb2.BucketIds, _Mapping]]]=...) -> None:
        ...

class ServerTokenMap(_message.Message):
    __slots__ = ('server_tokens',)

    class ServerTokensEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: str

        def __init__(self, key: _Optional[int]=..., value: _Optional[str]=...) -> None:
            ...
    SERVER_TOKENS_FIELD_NUMBER: _ClassVar[int]
    server_tokens: _containers.ScalarMap[int, str]

    def __init__(self, server_tokens: _Optional[_Mapping[int, str]]=...) -> None:
        ...

class ServerTokenList(_message.Message):
    __slots__ = ('server_token', 'server_token_map')
    SERVER_TOKEN_FIELD_NUMBER: _ClassVar[int]
    SERVER_TOKEN_MAP_FIELD_NUMBER: _ClassVar[int]
    server_token: _containers.RepeatedScalarFieldContainer[str]
    server_token_map: _containers.RepeatedCompositeFieldContainer[ServerTokenMap]

    def __init__(self, server_token: _Optional[_Iterable[str]]=..., server_token_map: _Optional[_Iterable[_Union[ServerTokenMap, _Mapping]]]=...) -> None:
        ...

class CommitRequest(_message.Message):
    __slots__ = ('account', 'table_ident', 'server_token_list')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    TABLE_IDENT_FIELD_NUMBER: _ClassVar[int]
    SERVER_TOKEN_LIST_FIELD_NUMBER: _ClassVar[int]
    account: Account
    table_ident: _containers.RepeatedCompositeFieldContainer[TableIdentifier]
    server_token_list: ServerTokenList

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., table_ident: _Optional[_Iterable[_Union[TableIdentifier, _Mapping]]]=..., server_token_list: _Optional[_Union[ServerTokenList, _Mapping]]=...) -> None:
        ...

class CommitResponse(_message.Message):
    __slots__ = ('status', 'commit_id')
    STATUS_FIELD_NUMBER: _ClassVar[int]
    COMMIT_ID_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus
    commit_id: int

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=..., commit_id: _Optional[int]=...) -> None:
        ...

class CheckCommitResultRequest(_message.Message):
    __slots__ = ('account', 'commit_id', 'table_ident')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    COMMIT_ID_FIELD_NUMBER: _ClassVar[int]
    TABLE_IDENT_FIELD_NUMBER: _ClassVar[int]
    account: Account
    commit_id: int
    table_ident: TableIdentifier

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., commit_id: _Optional[int]=..., table_ident: _Optional[_Union[TableIdentifier, _Mapping]]=...) -> None:
        ...

class CheckCommitResultResponse(_message.Message):
    __slots__ = ('status', 'finished')
    STATUS_FIELD_NUMBER: _ClassVar[int]
    FINISHED_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus
    finished: bool

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=..., finished: bool=...) -> None:
        ...

class RouteRule(_message.Message):
    __slots__ = ('resource_id', 'resource_type', 'service_tag')
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    SERVICE_TAG_FIELD_NUMBER: _ClassVar[int]
    resource_id: str
    resource_type: int
    service_tag: str

    def __init__(self, resource_id: _Optional[str]=..., resource_type: _Optional[int]=..., service_tag: _Optional[str]=...) -> None:
        ...

class UpdateRouteRuleBroadcastRequest(_message.Message):
    __slots__ = ('rule',)
    RULE_FIELD_NUMBER: _ClassVar[int]
    rule: RouteRule

    def __init__(self, rule: _Optional[_Union[RouteRule, _Mapping]]=...) -> None:
        ...

class UpdateRouteRuleBroadcastResponse(_message.Message):
    __slots__ = ('status',)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=...) -> None:
        ...

class MaintainTabletRequest(_message.Message):
    __slots__ = ('account', 'table_ident', 'operation')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    TABLE_IDENT_FIELD_NUMBER: _ClassVar[int]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    account: Account
    table_ident: TableIdentifier
    operation: MaintainTabletOperation

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., table_ident: _Optional[_Union[TableIdentifier, _Mapping]]=..., operation: _Optional[_Union[MaintainTabletOperation, str]]=...) -> None:
        ...

class MaintainTabletResponse(_message.Message):
    __slots__ = ('status',)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=...) -> None:
        ...

class OperationTypeList(_message.Message):
    __slots__ = ('op_types',)
    OP_TYPES_FIELD_NUMBER: _ClassVar[int]
    op_types: _containers.RepeatedScalarFieldContainer[OperationType]

    def __init__(self, op_types: _Optional[_Iterable[_Union[OperationType, str]]]=...) -> None:
        ...

class DataBlock(_message.Message):
    __slots__ = ('arrow_payload', 'is_set_bitmaps_payload', 'row_op_type_list', 'block_op_type', 'num_rows')
    ARROW_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    IS_SET_BITMAPS_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    ROW_OP_TYPE_LIST_FIELD_NUMBER: _ClassVar[int]
    BLOCK_OP_TYPE_FIELD_NUMBER: _ClassVar[int]
    NUM_ROWS_FIELD_NUMBER: _ClassVar[int]
    arrow_payload: bytes
    is_set_bitmaps_payload: bytes
    row_op_type_list: OperationTypeList
    block_op_type: OperationType
    num_rows: int

    def __init__(self, arrow_payload: _Optional[bytes]=..., is_set_bitmaps_payload: _Optional[bytes]=..., row_op_type_list: _Optional[_Union[OperationTypeList, _Mapping]]=..., block_op_type: _Optional[_Union[OperationType, str]]=..., num_rows: _Optional[int]=...) -> None:
        ...

class MutateRowStatus(_message.Message):
    __slots__ = ('code', 'error_message', 'row_index')
    CODE_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ROW_INDEX_FIELD_NUMBER: _ClassVar[int]
    code: Code
    error_message: str
    row_index: int

    def __init__(self, code: _Optional[_Union[Code, str]]=..., error_message: _Optional[str]=..., row_index: _Optional[int]=...) -> None:
        ...

class MutateRequest(_message.Message):
    __slots__ = ('account', 'table_ident', 'batch_id', 'write_timestamp', 'data_fields', 'data_block', 'server_token', 'server_tokens', 'txn_snapshot')

    class ServerTokensEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: str

        def __init__(self, key: _Optional[int]=..., value: _Optional[str]=...) -> None:
            ...
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    TABLE_IDENT_FIELD_NUMBER: _ClassVar[int]
    BATCH_ID_FIELD_NUMBER: _ClassVar[int]
    WRITE_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELDS_FIELD_NUMBER: _ClassVar[int]
    DATA_BLOCK_FIELD_NUMBER: _ClassVar[int]
    SERVER_TOKEN_FIELD_NUMBER: _ClassVar[int]
    SERVER_TOKENS_FIELD_NUMBER: _ClassVar[int]
    TXN_SNAPSHOT_FIELD_NUMBER: _ClassVar[int]
    account: Account
    table_ident: TableIdentifier
    batch_id: int
    write_timestamp: int
    data_fields: _containers.RepeatedCompositeFieldContainer[DataField]
    data_block: DataBlock
    server_token: str
    server_tokens: _containers.ScalarMap[int, str]
    txn_snapshot: _txn_manager_pb2.DistributedTxnSnapshot

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., table_ident: _Optional[_Union[TableIdentifier, _Mapping]]=..., batch_id: _Optional[int]=..., write_timestamp: _Optional[int]=..., data_fields: _Optional[_Iterable[_Union[DataField, _Mapping]]]=..., data_block: _Optional[_Union[DataBlock, _Mapping]]=..., server_token: _Optional[str]=..., server_tokens: _Optional[_Mapping[int, str]]=..., txn_snapshot: _Optional[_Union[_txn_manager_pb2.DistributedTxnSnapshot, _Mapping]]=...) -> None:
        ...

class MutateResponse(_message.Message):
    __slots__ = ('batch_id', 'num_rows', 'status', 'row_status_list', 'server_token', 'server_tokens')

    class ServerTokensEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: str

        def __init__(self, key: _Optional[int]=..., value: _Optional[str]=...) -> None:
            ...
    BATCH_ID_FIELD_NUMBER: _ClassVar[int]
    NUM_ROWS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ROW_STATUS_LIST_FIELD_NUMBER: _ClassVar[int]
    SERVER_TOKEN_FIELD_NUMBER: _ClassVar[int]
    SERVER_TOKENS_FIELD_NUMBER: _ClassVar[int]
    batch_id: int
    num_rows: int
    status: ResponseStatus
    row_status_list: _containers.RepeatedCompositeFieldContainer[MutateRowStatus]
    server_token: str
    server_tokens: _containers.ScalarMap[int, str]

    def __init__(self, batch_id: _Optional[int]=..., num_rows: _Optional[int]=..., status: _Optional[_Union[ResponseStatus, _Mapping]]=..., row_status_list: _Optional[_Iterable[_Union[MutateRowStatus, _Mapping]]]=..., server_token: _Optional[str]=..., server_tokens: _Optional[_Mapping[int, str]]=...) -> None:
        ...

class MultiMutateRequest(_message.Message):
    __slots__ = ('batch_id', 'write_timestamp', 'mutate_requests')
    BATCH_ID_FIELD_NUMBER: _ClassVar[int]
    WRITE_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    MUTATE_REQUESTS_FIELD_NUMBER: _ClassVar[int]
    batch_id: int
    write_timestamp: int
    mutate_requests: _containers.RepeatedCompositeFieldContainer[MutateRequest]

    def __init__(self, batch_id: _Optional[int]=..., write_timestamp: _Optional[int]=..., mutate_requests: _Optional[_Iterable[_Union[MutateRequest, _Mapping]]]=...) -> None:
        ...

class MultiMutateResponse(_message.Message):
    __slots__ = ('batch_id', 'num_rows', 'status', 'mutate_responses')
    BATCH_ID_FIELD_NUMBER: _ClassVar[int]
    NUM_ROWS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MUTATE_RESPONSES_FIELD_NUMBER: _ClassVar[int]
    batch_id: int
    num_rows: int
    status: ResponseStatus
    mutate_responses: _containers.RepeatedCompositeFieldContainer[MutateResponse]

    def __init__(self, batch_id: _Optional[int]=..., num_rows: _Optional[int]=..., status: _Optional[_Union[ResponseStatus, _Mapping]]=..., mutate_responses: _Optional[_Iterable[_Union[MutateResponse, _Mapping]]]=...) -> None:
        ...

class SchemaChangeRequest(_message.Message):
    __slots__ = ('account', 'table_ident', 'updates', 'ddlSql', 'server_token')
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    TABLE_IDENT_FIELD_NUMBER: _ClassVar[int]
    UPDATES_FIELD_NUMBER: _ClassVar[int]
    DDLSQL_FIELD_NUMBER: _ClassVar[int]
    SERVER_TOKEN_FIELD_NUMBER: _ClassVar[int]
    account: Account
    table_ident: TableIdentifier
    updates: _containers.RepeatedCompositeFieldContainer[_ddl_pb2.TableChange]
    ddlSql: _containers.RepeatedScalarFieldContainer[str]
    server_token: str

    def __init__(self, account: _Optional[_Union[Account, _Mapping]]=..., table_ident: _Optional[_Union[TableIdentifier, _Mapping]]=..., updates: _Optional[_Iterable[_Union[_ddl_pb2.TableChange, _Mapping]]]=..., ddlSql: _Optional[_Iterable[str]]=..., server_token: _Optional[str]=...) -> None:
        ...

class SchemaChangeResponse(_message.Message):
    __slots__ = ('status',)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=...) -> None:
        ...

class GetControllerAddressRequest(_message.Message):
    __slots__ = ('instance_id', 'workspace', 'schema', 'table')
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    instance_id: int
    workspace: str
    schema: str
    table: str

    def __init__(self, instance_id: _Optional[int]=..., workspace: _Optional[str]=..., schema: _Optional[str]=..., table: _Optional[str]=...) -> None:
        ...

class GetControllerAddressResponse(_message.Message):
    __slots__ = ('status', 'service_address')
    STATUS_FIELD_NUMBER: _ClassVar[int]
    SERVICE_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus
    service_address: str

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=..., service_address: _Optional[str]=...) -> None:
        ...

class UpdateRouteRuleRequest(_message.Message):
    __slots__ = ('rule',)
    RULE_FIELD_NUMBER: _ClassVar[int]
    rule: RouteRule

    def __init__(self, rule: _Optional[_Union[RouteRule, _Mapping]]=...) -> None:
        ...

class UpdateRouteRuleResponse(_message.Message):
    __slots__ = ('status',)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=...) -> None:
        ...

class RemoveRouteRuleRequest(_message.Message):
    __slots__ = ('resource_id', 'resource_type')
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    resource_id: str
    resource_type: int

    def __init__(self, resource_id: _Optional[str]=..., resource_type: _Optional[int]=...) -> None:
        ...

class RemoveRouteRuleResponse(_message.Message):
    __slots__ = ('status',)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=...) -> None:
        ...

class ClearRouteRuleRequest(_message.Message):
    __slots__ = ()

    def __init__(self) -> None:
        ...

class ClearRouteRuleResponse(_message.Message):
    __slots__ = ('status',)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=...) -> None:
        ...

class ChangeDefaultServiceRequest(_message.Message):
    __slots__ = ('service_tag',)
    SERVICE_TAG_FIELD_NUMBER: _ClassVar[int]
    service_tag: str

    def __init__(self, service_tag: _Optional[str]=...) -> None:
        ...

class ChangeDefaultServiceResponse(_message.Message):
    __slots__ = ('status',)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=...) -> None:
        ...

class ControllerServiceInfo(_message.Message):
    __slots__ = ('service_tag', 'service_address', 'default_service', 'build_info')
    SERVICE_TAG_FIELD_NUMBER: _ClassVar[int]
    SERVICE_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_SERVICE_FIELD_NUMBER: _ClassVar[int]
    BUILD_INFO_FIELD_NUMBER: _ClassVar[int]
    service_tag: str
    service_address: str
    default_service: bool
    build_info: str

    def __init__(self, service_tag: _Optional[str]=..., service_address: _Optional[str]=..., default_service: bool=..., build_info: _Optional[str]=...) -> None:
        ...

class RegisterNewServiceRequest(_message.Message):
    __slots__ = ('service',)
    SERVICE_FIELD_NUMBER: _ClassVar[int]
    service: ControllerServiceInfo

    def __init__(self, service: _Optional[_Union[ControllerServiceInfo, _Mapping]]=...) -> None:
        ...

class RegisterNewServiceResponse(_message.Message):
    __slots__ = ('status',)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: ResponseStatus

    def __init__(self, status: _Optional[_Union[ResponseStatus, _Mapping]]=...) -> None:
        ...