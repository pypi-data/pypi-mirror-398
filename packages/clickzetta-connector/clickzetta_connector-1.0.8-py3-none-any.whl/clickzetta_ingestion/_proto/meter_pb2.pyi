from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class Meter(_message.Message):
    __slots__ = ('account_id', 'instance_id', 'sku_code', 'resource_id', 'resource_name', 'measurement_start', 'measurement_end', 'measurements', 'resource_properties', 'idempotent', 'is_obj_dropped')

    class ResourcePropertiesEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    ACCOUNT_ID_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    SKU_CODE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    MEASUREMENT_START_FIELD_NUMBER: _ClassVar[int]
    MEASUREMENT_END_FIELD_NUMBER: _ClassVar[int]
    MEASUREMENTS_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENT_FIELD_NUMBER: _ClassVar[int]
    IS_OBJ_DROPPED_FIELD_NUMBER: _ClassVar[int]
    account_id: int
    instance_id: int
    sku_code: str
    resource_id: int
    resource_name: str
    measurement_start: int
    measurement_end: int
    measurements: _containers.RepeatedCompositeFieldContainer[Measurement]
    resource_properties: _containers.ScalarMap[str, str]
    idempotent: str
    is_obj_dropped: bool

    def __init__(self, account_id: _Optional[int]=..., instance_id: _Optional[int]=..., sku_code: _Optional[str]=..., resource_id: _Optional[int]=..., resource_name: _Optional[str]=..., measurement_start: _Optional[int]=..., measurement_end: _Optional[int]=..., measurements: _Optional[_Iterable[_Union[Measurement, _Mapping]]]=..., resource_properties: _Optional[_Mapping[str, str]]=..., idempotent: _Optional[str]=..., is_obj_dropped: bool=...) -> None:
        ...

class Measurement(_message.Message):
    __slots__ = ('key', 'unit', 'value')
    KEY_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    unit: str
    value: str

    def __init__(self, key: _Optional[str]=..., unit: _Optional[str]=..., value: _Optional[str]=...) -> None:
        ...

class MeterEvent(_message.Message):
    __slots__ = ('account_id', 'instance_id', 'sku_code', 'resource_id', 'resource_name', 'event_timestamp_ms', 'event_type', 'resource_properties', 'idempotent', 'is_obj_dropped')

    class ResourcePropertiesEntry(_message.Message):
        __slots__ = ('key', 'value')
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str

        def __init__(self, key: _Optional[str]=..., value: _Optional[str]=...) -> None:
            ...
    ACCOUNT_ID_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    SKU_CODE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    EVENT_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENT_FIELD_NUMBER: _ClassVar[int]
    IS_OBJ_DROPPED_FIELD_NUMBER: _ClassVar[int]
    account_id: int
    instance_id: int
    sku_code: str
    resource_id: int
    resource_name: str
    event_timestamp_ms: int
    event_type: int
    resource_properties: _containers.ScalarMap[str, str]
    idempotent: str
    is_obj_dropped: bool

    def __init__(self, account_id: _Optional[int]=..., instance_id: _Optional[int]=..., sku_code: _Optional[str]=..., resource_id: _Optional[int]=..., resource_name: _Optional[str]=..., event_timestamp_ms: _Optional[int]=..., event_type: _Optional[int]=..., resource_properties: _Optional[_Mapping[str, str]]=..., idempotent: _Optional[str]=..., is_obj_dropped: bool=...) -> None:
        ...