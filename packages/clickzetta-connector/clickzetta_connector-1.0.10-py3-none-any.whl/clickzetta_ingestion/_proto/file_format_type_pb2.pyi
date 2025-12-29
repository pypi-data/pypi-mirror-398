from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar
DESCRIPTOR: _descriptor.FileDescriptor

class FileFormatType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TEXT: _ClassVar[FileFormatType]
    PARQUET: _ClassVar[FileFormatType]
    ORC: _ClassVar[FileFormatType]
    AVRO: _ClassVar[FileFormatType]
    CSV: _ClassVar[FileFormatType]
    ARROW: _ClassVar[FileFormatType]
    HIVE_RESULT: _ClassVar[FileFormatType]
    DUMMY: _ClassVar[FileFormatType]
    MEMORY: _ClassVar[FileFormatType]
    ICEBERG: _ClassVar[FileFormatType]
TEXT: FileFormatType
PARQUET: FileFormatType
ORC: FileFormatType
AVRO: FileFormatType
CSV: FileFormatType
ARROW: FileFormatType
HIVE_RESULT: FileFormatType
DUMMY: FileFormatType
MEMORY: FileFormatType
ICEBERG: FileFormatType