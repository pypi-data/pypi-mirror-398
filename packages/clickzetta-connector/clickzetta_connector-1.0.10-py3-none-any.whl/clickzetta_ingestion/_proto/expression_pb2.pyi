import data_type_pb2 as _data_type_pb2
import property_pb2 as _property_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class ReferenceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LOGICAL_FIELD: _ClassVar[ReferenceType]
    REF_LOCAL: _ClassVar[ReferenceType]
    PHYSICAL_FIELD: _ClassVar[ReferenceType]
    REF_VARIABLE: _ClassVar[ReferenceType]
LOGICAL_FIELD: ReferenceType
REF_LOCAL: ReferenceType
PHYSICAL_FIELD: ReferenceType
REF_VARIABLE: ReferenceType

class ParseTreeInfo(_message.Message):
    __slots__ = ('start', 'end')

    class LocationInfo(_message.Message):
        __slots__ = ('line', 'col', 'pos')
        LINE_FIELD_NUMBER: _ClassVar[int]
        COL_FIELD_NUMBER: _ClassVar[int]
        POS_FIELD_NUMBER: _ClassVar[int]
        line: int
        col: int
        pos: int

        def __init__(self, line: _Optional[int]=..., col: _Optional[int]=..., pos: _Optional[int]=...) -> None:
            ...
    START_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    start: ParseTreeInfo.LocationInfo
    end: ParseTreeInfo.LocationInfo

    def __init__(self, start: _Optional[_Union[ParseTreeInfo.LocationInfo, _Mapping]]=..., end: _Optional[_Union[ParseTreeInfo.LocationInfo, _Mapping]]=...) -> None:
        ...

class IntervalDayTime(_message.Message):
    __slots__ = ('seconds', 'nanos')
    SECONDS_FIELD_NUMBER: _ClassVar[int]
    NANOS_FIELD_NUMBER: _ClassVar[int]
    seconds: int
    nanos: int

    def __init__(self, seconds: _Optional[int]=..., nanos: _Optional[int]=...) -> None:
        ...

class ArrayValue(_message.Message):
    __slots__ = ('elements',)
    ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    elements: _containers.RepeatedCompositeFieldContainer[Constant]

    def __init__(self, elements: _Optional[_Iterable[_Union[Constant, _Mapping]]]=...) -> None:
        ...

class MapValue(_message.Message):
    __slots__ = ('keys', 'values')
    KEYS_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    keys: _containers.RepeatedCompositeFieldContainer[Constant]
    values: _containers.RepeatedCompositeFieldContainer[Constant]

    def __init__(self, keys: _Optional[_Iterable[_Union[Constant, _Mapping]]]=..., values: _Optional[_Iterable[_Union[Constant, _Mapping]]]=...) -> None:
        ...

class StructValue(_message.Message):
    __slots__ = ('fields',)
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[Constant]

    def __init__(self, fields: _Optional[_Iterable[_Union[Constant, _Mapping]]]=...) -> None:
        ...

class BitmapValue(_message.Message):
    __slots__ = ('value',)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: bytes

    def __init__(self, value: _Optional[bytes]=...) -> None:
        ...

class Constant(_message.Message):
    __slots__ = ('null', 'tinyint', 'smallInt', 'int', 'bigint', 'float', 'double', 'decimal', 'boolean', 'char', 'varchar', 'string', 'binary', 'date', 'timestamp', 'IntervalYearMonth', 'IntervalDayTime', 'array', 'map', 'struct', 'bitmap')
    NULL_FIELD_NUMBER: _ClassVar[int]
    TINYINT_FIELD_NUMBER: _ClassVar[int]
    SMALLINT_FIELD_NUMBER: _ClassVar[int]
    INT_FIELD_NUMBER: _ClassVar[int]
    BIGINT_FIELD_NUMBER: _ClassVar[int]
    FLOAT_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_FIELD_NUMBER: _ClassVar[int]
    DECIMAL_FIELD_NUMBER: _ClassVar[int]
    BOOLEAN_FIELD_NUMBER: _ClassVar[int]
    CHAR_FIELD_NUMBER: _ClassVar[int]
    VARCHAR_FIELD_NUMBER: _ClassVar[int]
    STRING_FIELD_NUMBER: _ClassVar[int]
    BINARY_FIELD_NUMBER: _ClassVar[int]
    DATE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    INTERVALYEARMONTH_FIELD_NUMBER: _ClassVar[int]
    INTERVALDAYTIME_FIELD_NUMBER: _ClassVar[int]
    ARRAY_FIELD_NUMBER: _ClassVar[int]
    MAP_FIELD_NUMBER: _ClassVar[int]
    STRUCT_FIELD_NUMBER: _ClassVar[int]
    BITMAP_FIELD_NUMBER: _ClassVar[int]
    null: bool
    tinyint: int
    smallInt: int
    int: int
    bigint: int
    float: float
    double: float
    decimal: str
    boolean: bool
    char: str
    varchar: str
    string: str
    binary: bytes
    date: int
    timestamp: int
    IntervalYearMonth: int
    IntervalDayTime: IntervalDayTime
    array: ArrayValue
    map: MapValue
    struct: StructValue
    bitmap: BitmapValue

    def __init__(self, null: bool=..., tinyint: _Optional[int]=..., smallInt: _Optional[int]=..., int: _Optional[int]=..., bigint: _Optional[int]=..., float: _Optional[float]=..., double: _Optional[float]=..., decimal: _Optional[str]=..., boolean: bool=..., char: _Optional[str]=..., varchar: _Optional[str]=..., string: _Optional[str]=..., binary: _Optional[bytes]=..., date: _Optional[int]=..., timestamp: _Optional[int]=..., IntervalYearMonth: _Optional[int]=..., IntervalDayTime: _Optional[_Union[IntervalDayTime, _Mapping]]=..., array: _Optional[_Union[ArrayValue, _Mapping]]=..., map: _Optional[_Union[MapValue, _Mapping]]=..., struct: _Optional[_Union[StructValue, _Mapping]]=..., bitmap: _Optional[_Union[BitmapValue, _Mapping]]=...) -> None:
        ...

class SubFieldPruning(_message.Message):
    __slots__ = ('id', 'subfields')
    ID_FIELD_NUMBER: _ClassVar[int]
    SUBFIELDS_FIELD_NUMBER: _ClassVar[int]
    id: Constant
    subfields: SubFieldsPruning

    def __init__(self, id: _Optional[_Union[Constant, _Mapping]]=..., subfields: _Optional[_Union[SubFieldsPruning, _Mapping]]=...) -> None:
        ...

class SubFieldsPruning(_message.Message):
    __slots__ = ('fields', 'reserve_size')
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    RESERVE_SIZE_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[SubFieldPruning]
    reserve_size: bool

    def __init__(self, fields: _Optional[_Iterable[_Union[SubFieldPruning, _Mapping]]]=..., reserve_size: bool=...) -> None:
        ...

class Reference(_message.Message):
    __slots__ = ('id', 'local', 'name', 'ref_type')
    ID_FIELD_NUMBER: _ClassVar[int]
    LOCAL_FIELD_NUMBER: _ClassVar[int]
    FROM_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    REF_TYPE_FIELD_NUMBER: _ClassVar[int]
    id: int
    local: bool
    name: str
    ref_type: ReferenceType

    def __init__(self, id: _Optional[int]=..., local: bool=..., name: _Optional[str]=..., ref_type: _Optional[_Union[ReferenceType, str]]=..., **kwargs) -> None:
        ...

class Udf(_message.Message):
    __slots__ = ('instanceId', 'path', 'creator')
    INSTANCEID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    CREATOR_FIELD_NUMBER: _ClassVar[int]
    instanceId: int
    path: _containers.RepeatedScalarFieldContainer[str]
    creator: int

    def __init__(self, instanceId: _Optional[int]=..., path: _Optional[_Iterable[str]]=..., creator: _Optional[int]=...) -> None:
        ...

class ScalarFunction(_message.Message):
    __slots__ = ('name', 'builtIn', 'arguments', 'properties', 'execDesc', 'functionProperties', 'udf')
    FROM_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    BUILTIN_FIELD_NUMBER: _ClassVar[int]
    ARGUMENTS_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    EXECDESC_FIELD_NUMBER: _ClassVar[int]
    FUNCTIONPROPERTIES_FIELD_NUMBER: _ClassVar[int]
    UDF_FIELD_NUMBER: _ClassVar[int]
    name: str
    builtIn: bool
    arguments: _containers.RepeatedCompositeFieldContainer[ScalarExpression]
    properties: _property_pb2.Properties
    execDesc: str
    functionProperties: _property_pb2.Properties
    udf: Udf

    def __init__(self, name: _Optional[str]=..., builtIn: bool=..., arguments: _Optional[_Iterable[_Union[ScalarExpression, _Mapping]]]=..., properties: _Optional[_Union[_property_pb2.Properties, _Mapping]]=..., execDesc: _Optional[str]=..., functionProperties: _Optional[_Union[_property_pb2.Properties, _Mapping]]=..., udf: _Optional[_Union[Udf, _Mapping]]=..., **kwargs) -> None:
        ...

class VariableDef(_message.Message):
    __slots__ = ('type', 'id')
    TYPE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    type: _data_type_pb2.DataType
    id: int

    def __init__(self, type: _Optional[_Union[_data_type_pb2.DataType, _Mapping]]=..., id: _Optional[int]=...) -> None:
        ...

class LambdaFunction(_message.Message):
    __slots__ = ('params', 'impl')
    PARAMS_FIELD_NUMBER: _ClassVar[int]
    IMPL_FIELD_NUMBER: _ClassVar[int]
    params: _containers.RepeatedCompositeFieldContainer[VariableDef]
    impl: ScalarExpression

    def __init__(self, params: _Optional[_Iterable[_Union[VariableDef, _Mapping]]]=..., impl: _Optional[_Union[ScalarExpression, _Mapping]]=...) -> None:
        ...

class ScalarExpression(_message.Message):
    __slots__ = ('type', 'constant', 'reference', 'function', 'pt')
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CONSTANT_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_FIELD_NUMBER: _ClassVar[int]
    LAMBDA_FIELD_NUMBER: _ClassVar[int]
    PT_FIELD_NUMBER: _ClassVar[int]
    type: _data_type_pb2.DataType
    constant: Constant
    reference: Reference
    function: ScalarFunction
    pt: ParseTreeInfo

    def __init__(self, type: _Optional[_Union[_data_type_pb2.DataType, _Mapping]]=..., constant: _Optional[_Union[Constant, _Mapping]]=..., reference: _Optional[_Union[Reference, _Mapping]]=..., function: _Optional[_Union[ScalarFunction, _Mapping]]=..., pt: _Optional[_Union[ParseTreeInfo, _Mapping]]=..., **kwargs) -> None:
        ...