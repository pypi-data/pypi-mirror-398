"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 28, 1, '', 'encryption.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10encryption.proto\x12\x08cz.proto"\x87\x03\n\x10EncryptionConfig\x12B\n\x0fencryption_type\x18\x01 \x01(\x0e2).cz.proto.EncryptionConfig.EncryptionType\x12L\n\x14encryption_algorithm\x18\x02 \x01(\x0e2..cz.proto.EncryptionConfig.EncryptionAlgorithm\x12\x19\n\x11encryption_key_id\x18\x03 \x01(\t\x12\x13\n\x0bbyok_config\x18\x04 \x01(\t"n\n\x0eEncryptionType\x12\x13\n\x0fNONE_ENCRYPTION\x10\x00\x12\x0b\n\x07DISABLE\x10\x01\x12\x10\n\x0cFULL_MANAGED\x10\x02\x12\x13\n\x0fBYOK_ALIYUN_KMS\x10\x03\x12\x13\n\x0fBYOK_AES128_KEY\x10\x04"A\n\x13EncryptionAlgorithm\x12\x12\n\x0eNONE_ALGORITHM\x10\x00\x12\n\n\x06AES256\x10\x01\x12\n\n\x06AES128\x10\x02b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'encryption_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_ENCRYPTIONCONFIG']._serialized_start = 31
    _globals['_ENCRYPTIONCONFIG']._serialized_end = 422
    _globals['_ENCRYPTIONCONFIG_ENCRYPTIONTYPE']._serialized_start = 245
    _globals['_ENCRYPTIONCONFIG_ENCRYPTIONTYPE']._serialized_end = 355
    _globals['_ENCRYPTIONCONFIG_ENCRYPTIONALGORITHM']._serialized_start = 357
    _globals['_ENCRYPTIONCONFIG_ENCRYPTIONALGORITHM']._serialized_end = 422