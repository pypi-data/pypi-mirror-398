from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class EncryptionConfig(_message.Message):
    __slots__ = ('encryption_type', 'encryption_algorithm', 'encryption_key_id', 'byok_config')

    class EncryptionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        NONE_ENCRYPTION: _ClassVar[EncryptionConfig.EncryptionType]
        DISABLE: _ClassVar[EncryptionConfig.EncryptionType]
        FULL_MANAGED: _ClassVar[EncryptionConfig.EncryptionType]
        BYOK_ALIYUN_KMS: _ClassVar[EncryptionConfig.EncryptionType]
        BYOK_AES128_KEY: _ClassVar[EncryptionConfig.EncryptionType]
    NONE_ENCRYPTION: EncryptionConfig.EncryptionType
    DISABLE: EncryptionConfig.EncryptionType
    FULL_MANAGED: EncryptionConfig.EncryptionType
    BYOK_ALIYUN_KMS: EncryptionConfig.EncryptionType
    BYOK_AES128_KEY: EncryptionConfig.EncryptionType

    class EncryptionAlgorithm(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        NONE_ALGORITHM: _ClassVar[EncryptionConfig.EncryptionAlgorithm]
        AES256: _ClassVar[EncryptionConfig.EncryptionAlgorithm]
        AES128: _ClassVar[EncryptionConfig.EncryptionAlgorithm]
    NONE_ALGORITHM: EncryptionConfig.EncryptionAlgorithm
    AES256: EncryptionConfig.EncryptionAlgorithm
    AES128: EncryptionConfig.EncryptionAlgorithm
    ENCRYPTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTION_ALGORITHM_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTION_KEY_ID_FIELD_NUMBER: _ClassVar[int]
    BYOK_CONFIG_FIELD_NUMBER: _ClassVar[int]
    encryption_type: EncryptionConfig.EncryptionType
    encryption_algorithm: EncryptionConfig.EncryptionAlgorithm
    encryption_key_id: str
    byok_config: str

    def __init__(self, encryption_type: _Optional[_Union[EncryptionConfig.EncryptionType, str]]=..., encryption_algorithm: _Optional[_Union[EncryptionConfig.EncryptionAlgorithm, str]]=..., encryption_key_id: _Optional[str]=..., byok_config: _Optional[str]=...) -> None:
        ...