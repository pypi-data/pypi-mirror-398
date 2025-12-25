from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class RMAppState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RM_APP_RUNNING: _ClassVar[RMAppState]
    RM_APP_SUCCESS: _ClassVar[RMAppState]
    RM_APP_FAILED: _ClassVar[RMAppState]
RM_APP_RUNNING: RMAppState
RM_APP_SUCCESS: RMAppState
RM_APP_FAILED: RMAppState

class RMAppMeta(_message.Message):
    __slots__ = ('app_id', 'app_name', 'priority', 'vc_id', 'app_state', 'submit_time', 'finish_time')
    APP_ID_FIELD_NUMBER: _ClassVar[int]
    APP_NAME_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    VC_ID_FIELD_NUMBER: _ClassVar[int]
    APP_STATE_FIELD_NUMBER: _ClassVar[int]
    SUBMIT_TIME_FIELD_NUMBER: _ClassVar[int]
    FINISH_TIME_FIELD_NUMBER: _ClassVar[int]
    app_id: str
    app_name: str
    priority: int
    vc_id: int
    app_state: RMAppState
    submit_time: int
    finish_time: int

    def __init__(self, app_id: _Optional[str]=..., app_name: _Optional[str]=..., priority: _Optional[int]=..., vc_id: _Optional[int]=..., app_state: _Optional[_Union[RMAppState, str]]=..., submit_time: _Optional[int]=..., finish_time: _Optional[int]=...) -> None:
        ...