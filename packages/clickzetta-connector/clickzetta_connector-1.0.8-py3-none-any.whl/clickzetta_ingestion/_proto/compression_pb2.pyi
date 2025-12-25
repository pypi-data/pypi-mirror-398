from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar
DESCRIPTOR: _descriptor.FileDescriptor

class CompressionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN_COMPRESSION: _ClassVar[CompressionType]
    DEFAULT_COMPRESSION: _ClassVar[CompressionType]
    NO_COMPRESSION: _ClassVar[CompressionType]
    SNAPPY: _ClassVar[CompressionType]
    LZ4: _ClassVar[CompressionType]
    ZLIB: _ClassVar[CompressionType]
UNKNOWN_COMPRESSION: CompressionType
DEFAULT_COMPRESSION: CompressionType
NO_COMPRESSION: CompressionType
SNAPPY: CompressionType
LZ4: CompressionType
ZLIB: CompressionType