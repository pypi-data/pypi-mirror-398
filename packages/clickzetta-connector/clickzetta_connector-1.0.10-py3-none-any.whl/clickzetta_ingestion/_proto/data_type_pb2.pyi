from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class DataTypeCategory(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NONE: _ClassVar[DataTypeCategory]
    INT8: _ClassVar[DataTypeCategory]
    INT16: _ClassVar[DataTypeCategory]
    INT32: _ClassVar[DataTypeCategory]
    INT64: _ClassVar[DataTypeCategory]
    FLOAT32: _ClassVar[DataTypeCategory]
    FLOAT64: _ClassVar[DataTypeCategory]
    DECIMAL: _ClassVar[DataTypeCategory]
    BOOLEAN: _ClassVar[DataTypeCategory]
    CHAR: _ClassVar[DataTypeCategory]
    VARCHAR: _ClassVar[DataTypeCategory]
    STRING: _ClassVar[DataTypeCategory]
    BINARY: _ClassVar[DataTypeCategory]
    DATE: _ClassVar[DataTypeCategory]
    TIMESTAMP_LTZ: _ClassVar[DataTypeCategory]
    INTERVAL_YEAR_MONTH: _ClassVar[DataTypeCategory]
    INTERVAL_DAY_TIME: _ClassVar[DataTypeCategory]
    TIMESTAMP_NTZ: _ClassVar[DataTypeCategory]
    BITMAP: _ClassVar[DataTypeCategory]
    ARRAY: _ClassVar[DataTypeCategory]
    MAP: _ClassVar[DataTypeCategory]
    STRUCT: _ClassVar[DataTypeCategory]
    FUNCTION_TYPE: _ClassVar[DataTypeCategory]
    JSON: _ClassVar[DataTypeCategory]
    VECTOR_TYPE: _ClassVar[DataTypeCategory]
    VOID: _ClassVar[DataTypeCategory]

class IntervalUnit(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NONE_INTERVAL_UNIT: _ClassVar[IntervalUnit]
    YEAR: _ClassVar[IntervalUnit]
    MONTH: _ClassVar[IntervalUnit]
    DAY: _ClassVar[IntervalUnit]
    HOUR: _ClassVar[IntervalUnit]
    MINUTE: _ClassVar[IntervalUnit]
    SECOND: _ClassVar[IntervalUnit]

class TimestampUnit(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SECONDS: _ClassVar[TimestampUnit]
    MILLISECONDS: _ClassVar[TimestampUnit]
    MICROSECONDS: _ClassVar[TimestampUnit]
    NANOSECONDS: _ClassVar[TimestampUnit]

class VectorNumberType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    I8: _ClassVar[VectorNumberType]
    I16: _ClassVar[VectorNumberType]
    I32: _ClassVar[VectorNumberType]
    I64: _ClassVar[VectorNumberType]
    F16: _ClassVar[VectorNumberType]
    F32: _ClassVar[VectorNumberType]
    F64: _ClassVar[VectorNumberType]
    BF64: _ClassVar[VectorNumberType]
NONE: DataTypeCategory
INT8: DataTypeCategory
INT16: DataTypeCategory
INT32: DataTypeCategory
INT64: DataTypeCategory
FLOAT32: DataTypeCategory
FLOAT64: DataTypeCategory
DECIMAL: DataTypeCategory
BOOLEAN: DataTypeCategory
CHAR: DataTypeCategory
VARCHAR: DataTypeCategory
STRING: DataTypeCategory
BINARY: DataTypeCategory
DATE: DataTypeCategory
TIMESTAMP_LTZ: DataTypeCategory
INTERVAL_YEAR_MONTH: DataTypeCategory
INTERVAL_DAY_TIME: DataTypeCategory
TIMESTAMP_NTZ: DataTypeCategory
BITMAP: DataTypeCategory
ARRAY: DataTypeCategory
MAP: DataTypeCategory
STRUCT: DataTypeCategory
FUNCTION_TYPE: DataTypeCategory
JSON: DataTypeCategory
VECTOR_TYPE: DataTypeCategory
VOID: DataTypeCategory
NONE_INTERVAL_UNIT: IntervalUnit
YEAR: IntervalUnit
MONTH: IntervalUnit
DAY: IntervalUnit
HOUR: IntervalUnit
MINUTE: IntervalUnit
SECOND: IntervalUnit
SECONDS: TimestampUnit
MILLISECONDS: TimestampUnit
MICROSECONDS: TimestampUnit
NANOSECONDS: TimestampUnit
I8: VectorNumberType
I16: VectorNumberType
I32: VectorNumberType
I64: VectorNumberType
F16: VectorNumberType
F32: VectorNumberType
F64: VectorNumberType
BF64: VectorNumberType

class CharTypeInfo(_message.Message):
    __slots__ = ('length',)
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    length: int

    def __init__(self, length: _Optional[int]=...) -> None:
        ...

class VarCharTypeInfo(_message.Message):
    __slots__ = ('length',)
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    length: int

    def __init__(self, length: _Optional[int]=...) -> None:
        ...

class DecimalTypeInfo(_message.Message):
    __slots__ = ('precision', 'scale')
    PRECISION_FIELD_NUMBER: _ClassVar[int]
    SCALE_FIELD_NUMBER: _ClassVar[int]
    precision: int
    scale: int

    def __init__(self, precision: _Optional[int]=..., scale: _Optional[int]=...) -> None:
        ...

class IntervalDayTimeInfo(_message.Message):
    __slots__ = ('to', 'precision')
    FROM_FIELD_NUMBER: _ClassVar[int]
    TO_FIELD_NUMBER: _ClassVar[int]
    PRECISION_FIELD_NUMBER: _ClassVar[int]
    to: IntervalUnit
    precision: TimestampUnit

    def __init__(self, to: _Optional[_Union[IntervalUnit, str]]=..., precision: _Optional[_Union[TimestampUnit, str]]=..., **kwargs) -> None:
        ...

class IntervalYearMonthInfo(_message.Message):
    __slots__ = ('to',)
    FROM_FIELD_NUMBER: _ClassVar[int]
    TO_FIELD_NUMBER: _ClassVar[int]
    to: IntervalUnit

    def __init__(self, to: _Optional[_Union[IntervalUnit, str]]=..., **kwargs) -> None:
        ...

class VectorTypeInfo(_message.Message):
    __slots__ = ('numberType', 'dimension')
    NUMBERTYPE_FIELD_NUMBER: _ClassVar[int]
    DIMENSION_FIELD_NUMBER: _ClassVar[int]
    numberType: VectorNumberType
    dimension: int

    def __init__(self, numberType: _Optional[_Union[VectorNumberType, str]]=..., dimension: _Optional[int]=...) -> None:
        ...

class ArrayTypeInfo(_message.Message):
    __slots__ = ('elementType',)
    ELEMENTTYPE_FIELD_NUMBER: _ClassVar[int]
    elementType: DataType

    def __init__(self, elementType: _Optional[_Union[DataType, _Mapping]]=...) -> None:
        ...

class MapTypeInfo(_message.Message):
    __slots__ = ('keyType', 'valueType')
    KEYTYPE_FIELD_NUMBER: _ClassVar[int]
    VALUETYPE_FIELD_NUMBER: _ClassVar[int]
    keyType: DataType
    valueType: DataType

    def __init__(self, keyType: _Optional[_Union[DataType, _Mapping]]=..., valueType: _Optional[_Union[DataType, _Mapping]]=...) -> None:
        ...

class StructTypeInfo(_message.Message):
    __slots__ = ('fields',)

    class Field(_message.Message):
        __slots__ = ('name', 'type', 'type_reference')
        NAME_FIELD_NUMBER: _ClassVar[int]
        TYPE_FIELD_NUMBER: _ClassVar[int]
        TYPE_REFERENCE_FIELD_NUMBER: _ClassVar[int]
        name: str
        type: DataType
        type_reference: int

        def __init__(self, name: _Optional[str]=..., type: _Optional[_Union[DataType, _Mapping]]=..., type_reference: _Optional[int]=...) -> None:
            ...
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[StructTypeInfo.Field]

    def __init__(self, fields: _Optional[_Iterable[_Union[StructTypeInfo.Field, _Mapping]]]=...) -> None:
        ...

class FunctionTypeInfo(_message.Message):
    __slots__ = ('args', 'return_type')
    ARGS_FIELD_NUMBER: _ClassVar[int]
    RETURN_TYPE_FIELD_NUMBER: _ClassVar[int]
    args: _containers.RepeatedCompositeFieldContainer[DataType]
    return_type: DataType

    def __init__(self, args: _Optional[_Iterable[_Union[DataType, _Mapping]]]=..., return_type: _Optional[_Union[DataType, _Mapping]]=...) -> None:
        ...

class TimestampInfo(_message.Message):
    __slots__ = ('tsUnit',)
    TSUNIT_FIELD_NUMBER: _ClassVar[int]
    tsUnit: TimestampUnit

    def __init__(self, tsUnit: _Optional[_Union[TimestampUnit, str]]=...) -> None:
        ...

class DataType(_message.Message):
    __slots__ = ('category', 'nullable', 'field_id', 'charTypeInfo', 'varCharTypeInfo', 'decimalTypeInfo', 'arrayTypeInfo', 'mapTypeInfo', 'structTypeInfo', 'interval_day_time_info', 'interval_year_month_info', 'timestamp_info', 'function_info', 'vector_info')
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    NULLABLE_FIELD_NUMBER: _ClassVar[int]
    FIELD_ID_FIELD_NUMBER: _ClassVar[int]
    CHARTYPEINFO_FIELD_NUMBER: _ClassVar[int]
    VARCHARTYPEINFO_FIELD_NUMBER: _ClassVar[int]
    DECIMALTYPEINFO_FIELD_NUMBER: _ClassVar[int]
    ARRAYTYPEINFO_FIELD_NUMBER: _ClassVar[int]
    MAPTYPEINFO_FIELD_NUMBER: _ClassVar[int]
    STRUCTTYPEINFO_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_DAY_TIME_INFO_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_YEAR_MONTH_INFO_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_INFO_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_INFO_FIELD_NUMBER: _ClassVar[int]
    VECTOR_INFO_FIELD_NUMBER: _ClassVar[int]
    category: DataTypeCategory
    nullable: bool
    field_id: int
    charTypeInfo: CharTypeInfo
    varCharTypeInfo: VarCharTypeInfo
    decimalTypeInfo: DecimalTypeInfo
    arrayTypeInfo: ArrayTypeInfo
    mapTypeInfo: MapTypeInfo
    structTypeInfo: StructTypeInfo
    interval_day_time_info: IntervalDayTimeInfo
    interval_year_month_info: IntervalYearMonthInfo
    timestamp_info: TimestampInfo
    function_info: FunctionTypeInfo
    vector_info: VectorTypeInfo

    def __init__(self, category: _Optional[_Union[DataTypeCategory, str]]=..., nullable: bool=..., field_id: _Optional[int]=..., charTypeInfo: _Optional[_Union[CharTypeInfo, _Mapping]]=..., varCharTypeInfo: _Optional[_Union[VarCharTypeInfo, _Mapping]]=..., decimalTypeInfo: _Optional[_Union[DecimalTypeInfo, _Mapping]]=..., arrayTypeInfo: _Optional[_Union[ArrayTypeInfo, _Mapping]]=..., mapTypeInfo: _Optional[_Union[MapTypeInfo, _Mapping]]=..., structTypeInfo: _Optional[_Union[StructTypeInfo, _Mapping]]=..., interval_day_time_info: _Optional[_Union[IntervalDayTimeInfo, _Mapping]]=..., interval_year_month_info: _Optional[_Union[IntervalYearMonthInfo, _Mapping]]=..., timestamp_info: _Optional[_Union[TimestampInfo, _Mapping]]=..., function_info: _Optional[_Union[FunctionTypeInfo, _Mapping]]=..., vector_info: _Optional[_Union[VectorTypeInfo, _Mapping]]=...) -> None:
        ...