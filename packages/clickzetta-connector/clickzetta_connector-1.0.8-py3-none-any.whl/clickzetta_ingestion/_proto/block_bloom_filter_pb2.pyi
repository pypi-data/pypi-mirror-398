import hash_pb2 as _hash_pb2
import pb_util_pb2 as _pb_util_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class BlockBloomFilterPB(_message.Message):
    __slots__ = ('log_space_bytes', 'bloom_data', 'always_false', 'hash_algorithm', 'hash_seed')
    LOG_SPACE_BYTES_FIELD_NUMBER: _ClassVar[int]
    BLOOM_DATA_FIELD_NUMBER: _ClassVar[int]
    ALWAYS_FALSE_FIELD_NUMBER: _ClassVar[int]
    HASH_ALGORITHM_FIELD_NUMBER: _ClassVar[int]
    HASH_SEED_FIELD_NUMBER: _ClassVar[int]
    log_space_bytes: int
    bloom_data: bytes
    always_false: bool
    hash_algorithm: _hash_pb2.HashAlgorithm
    hash_seed: int

    def __init__(self, log_space_bytes: _Optional[int]=..., bloom_data: _Optional[bytes]=..., always_false: bool=..., hash_algorithm: _Optional[_Union[_hash_pb2.HashAlgorithm, str]]=..., hash_seed: _Optional[int]=...) -> None:
        ...