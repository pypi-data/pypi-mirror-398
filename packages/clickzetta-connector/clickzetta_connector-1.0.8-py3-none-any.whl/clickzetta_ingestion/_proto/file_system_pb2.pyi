from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar
DESCRIPTOR: _descriptor.FileDescriptor

class FileSystemType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LOCAL: _ClassVar[FileSystemType]
    OSS: _ClassVar[FileSystemType]
    CACHE: _ClassVar[FileSystemType]
    RPC: _ClassVar[FileSystemType]
    COS: _ClassVar[FileSystemType]
    HDFS: _ClassVar[FileSystemType]
    S3: _ClassVar[FileSystemType]
    GCS: _ClassVar[FileSystemType]
    OBS: _ClassVar[FileSystemType]
    TOS: _ClassVar[FileSystemType]
LOCAL: FileSystemType
OSS: FileSystemType
CACHE: FileSystemType
RPC: FileSystemType
COS: FileSystemType
HDFS: FileSystemType
S3: FileSystemType
GCS: FileSystemType
OBS: FileSystemType
TOS: FileSystemType