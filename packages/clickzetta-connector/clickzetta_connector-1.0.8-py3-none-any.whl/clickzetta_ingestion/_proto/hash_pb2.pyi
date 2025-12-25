from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar
DESCRIPTOR: _descriptor.FileDescriptor

class HashAlgorithm(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN_HASH: _ClassVar[HashAlgorithm]
    MURMUR_HASH_2: _ClassVar[HashAlgorithm]
    CITY_HASH: _ClassVar[HashAlgorithm]
    FAST_HASH: _ClassVar[HashAlgorithm]
UNKNOWN_HASH: HashAlgorithm
MURMUR_HASH_2: HashAlgorithm
CITY_HASH: HashAlgorithm
FAST_HASH: HashAlgorithm