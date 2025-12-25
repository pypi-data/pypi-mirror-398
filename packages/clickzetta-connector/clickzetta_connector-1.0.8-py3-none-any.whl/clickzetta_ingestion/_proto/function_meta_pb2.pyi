import object_identifier_pb2 as _object_identifier_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class FunctionResource(_message.Message):
    __slots__ = ('type', 'uri', 'content')
    TYPE_FIELD_NUMBER: _ClassVar[int]
    URI_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    type: str
    uri: str
    content: str

    def __init__(self, type: _Optional[str]=..., uri: _Optional[str]=..., content: _Optional[str]=...) -> None:
        ...

class FunctionResourceList(_message.Message):
    __slots__ = ('resources',)
    RESOURCES_FIELD_NUMBER: _ClassVar[int]
    resources: _containers.RepeatedCompositeFieldContainer[FunctionResource]

    def __init__(self, resources: _Optional[_Iterable[_Union[FunctionResource, _Mapping]]]=...) -> None:
        ...

class RemoteEntrypoint(_message.Message):
    __slots__ = ('internal_url', 'external_url', 'protocol', 'vendor_type', 'vendor_info')

    class VendorInfo(_message.Message):
        __slots__ = ('service', 'function')
        SERVICE_FIELD_NUMBER: _ClassVar[int]
        FUNCTION_FIELD_NUMBER: _ClassVar[int]
        service: str
        function: str

        def __init__(self, service: _Optional[str]=..., function: _Optional[str]=...) -> None:
            ...
    INTERNAL_URL_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_URL_FIELD_NUMBER: _ClassVar[int]
    PROTOCOL_FIELD_NUMBER: _ClassVar[int]
    VENDOR_TYPE_FIELD_NUMBER: _ClassVar[int]
    VENDOR_INFO_FIELD_NUMBER: _ClassVar[int]
    internal_url: str
    external_url: str
    protocol: str
    vendor_type: str
    vendor_info: RemoteEntrypoint.VendorInfo

    def __init__(self, internal_url: _Optional[str]=..., external_url: _Optional[str]=..., protocol: _Optional[str]=..., vendor_type: _Optional[str]=..., vendor_info: _Optional[_Union[RemoteEntrypoint.VendorInfo, _Mapping]]=...) -> None:
        ...

class Function(_message.Message):
    __slots__ = ('category', 'exec_type', 'signature', 'handler', 'connection', 'resources', 'remote_entrypoint')
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    EXEC_TYPE_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    HANDLER_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_FIELD_NUMBER: _ClassVar[int]
    RESOURCES_FIELD_NUMBER: _ClassVar[int]
    REMOTE_ENTRYPOINT_FIELD_NUMBER: _ClassVar[int]
    category: str
    exec_type: str
    signature: str
    handler: str
    connection: _object_identifier_pb2.ObjectIdentifier
    resources: FunctionResourceList
    remote_entrypoint: RemoteEntrypoint

    def __init__(self, category: _Optional[str]=..., exec_type: _Optional[str]=..., signature: _Optional[str]=..., handler: _Optional[str]=..., connection: _Optional[_Union[_object_identifier_pb2.ObjectIdentifier, _Mapping]]=..., resources: _Optional[_Union[FunctionResourceList, _Mapping]]=..., remote_entrypoint: _Optional[_Union[RemoteEntrypoint, _Mapping]]=...) -> None:
        ...