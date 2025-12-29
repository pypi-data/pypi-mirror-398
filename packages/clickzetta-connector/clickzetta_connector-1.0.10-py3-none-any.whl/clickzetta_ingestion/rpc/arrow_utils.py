from __future__ import annotations

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Optional, Any
from typing import TYPE_CHECKING

import numpy as np
import pyarrow as pa

if TYPE_CHECKING:
    from clickzetta_ingestion.realtime.arrow_row import DataField

from clickzetta_ingestion._proto import data_type_pb2, ingestion_v2_pb2
from clickzetta_ingestion.realtime.arrow_schema import ArrowSchema

log = logging.getLogger(__name__)


def convert_to_external_schema(stream_schema: ingestion_v2_pb2.StreamSchema,
                               data_fields: List["DataField"]) -> "ArrowSchema":
    """Convert StreamSchema to Arrow schema
    
    Args:
        stream_schema: Proto StreamSchema
        data_fields: List of DataField objects
        
    Returns:
        ArrowSchema object
    """
    arrow_fields = []
    key_columns_index = set()
    original_types = []

    for field in data_fields:
        original_types.append(field.type)
        arrow_fields.append(_to_arrow_field(field))

    # Handle key fields
    if stream_schema.primary_key_spec:
        for field_id in stream_schema.primary_key_spec.field_ids:
            key_columns_index.add(_get_field_index(data_fields, field_id))

    if stream_schema.dist_spec:
        for field_id in stream_schema.dist_spec.field_ids:
            key_columns_index.add(_get_field_index(data_fields, field_id))

    if stream_schema.partition_spec:
        for field_id in stream_schema.partition_spec.src_field_ids:
            key_columns_index.add(_get_field_index(data_fields, field_id))

    return ArrowSchema(original_types, arrow_fields, key_columns_index)


def _get_field_index(fields: List, field_id: int) -> int:
    """Get field index by field ID"""
    for idx, field in enumerate(fields):
        if field.type.field_id == field_id:
            return idx
    return -1


def _to_arrow_field(field) -> Optional[pa.Field]:
    """Convert field to Arrow field"""
    try:
        from clickzetta_ingestion.realtime.arrow_row import DataField
        metadata = _extract_field_metadata(field.type)
        data_type = field.type

        if data_type.category == data_type_pb2.DataTypeCategory.ARRAY:
            # Handle array type
            element_field = DataField("element", data_type.arrayTypeInfo.elementType)
            element_field = _to_arrow_field(element_field)
            if not element_field:
                raise ValueError(f"Failed to convert array element type for {field.name}")
            field_type = pa.list_(element_field.type)

        elif data_type.category == data_type_pb2.DataTypeCategory.STRUCT:
            # Handle struct type
            struct_fields = []
            for struct_field in data_type.structTypeInfo.fields:
                data_field = DataField(struct_field.name, struct_field.type)
                arrow_field = _to_arrow_field(data_field)
                if arrow_field:
                    struct_fields.append(arrow_field)
            field_type = pa.struct(struct_fields)

        elif data_type.category == data_type_pb2.DataTypeCategory.MAP:
            # Handle map type
            # Note: Map key cannot be null
            key_type = data_type.mapTypeInfo.keyType
            value_type = data_type.mapTypeInfo.valueType

            # Force key type to be non-nullable
            key_type_copy = data_type_pb2.DataType()
            key_type_copy.CopyFrom(key_type)
            key_type_copy.nullable = False

            # Create the map field type
            field_type = pa.map_(
                key_type=to_arrow_type(key_type_copy),
                item_type=to_arrow_type(value_type),
                keys_sorted=False
            )

        else:
            # Handle basic types
            field_type = to_arrow_type(data_type)

        return pa.field(field.name, field_type, data_type.nullable, metadata=metadata)

    except Exception as e:
        log.error(f"Failed to convert field {field.name} {field.type}: {str(e)}", exc_info=True)
        raise ValueError(
            f"Failed to convert field {field.name}: {str(e)}\n"
            f"Field type: {field.type}\n"
        )


def _extract_field_metadata(data_type: data_type_pb2.DataType) -> Dict[str, str]:
    """Extract metadata from data type"""
    try:
        metadata = {}

        # Add field ID
        if data_type.field_id > 0:
            metadata["PARQUET:field_id"] = str(data_type.field_id)

        # Add type info
        if data_type.category == data_type_pb2.DataTypeCategory.CHAR:
            metadata["CzType"] = f"char({data_type.charTypeInfo.length})"
        elif data_type.category == data_type_pb2.DataTypeCategory.VARCHAR:
            metadata["CzType"] = f"varchar({data_type.varCharTypeInfo.length})"
        elif data_type.category == data_type_pb2.DataTypeCategory.JSON:
            metadata["CzType"] = "json"

        return metadata

    except Exception as e:
        log.error(f"Failed to extract metadata: {e}", exc_info=True)
        raise


def estimate_type_size(data_type: data_type_pb2.DataType) -> int:
    """Estimate size for a data type
    
    Args:
        data_type: Proto DataType
        
    Returns:
        Estimated size in bytes
    """
    category = data_type.category

    if category == data_type_pb2.DataTypeCategory.BOOLEAN:
        return 1
    elif category == data_type_pb2.DataTypeCategory.INT8:
        return 1
    elif category == data_type_pb2.DataTypeCategory.INT16:
        return 2
    elif category == data_type_pb2.DataTypeCategory.INT32:
        return 4
    elif category == data_type_pb2.DataTypeCategory.INT64:
        return 8
    elif category == data_type_pb2.DataTypeCategory.FLOAT32:
        return 4
    elif category == data_type_pb2.DataTypeCategory.FLOAT64:
        return 8
    elif category == data_type_pb2.DataTypeCategory.DECIMAL:
        return 16
    elif category in (data_type_pb2.DataTypeCategory.VARCHAR,
                      data_type_pb2.DataTypeCategory.CHAR,
                      data_type_pb2.DataTypeCategory.STRING,
                      data_type_pb2.DataTypeCategory.JSON):
        # Base size for string/varchar/char/json
        if category == data_type_pb2.DataTypeCategory.CHAR:
            return data_type.charTypeInfo.length
        elif category == data_type_pb2.DataTypeCategory.VARCHAR:
            return data_type.varCharTypeInfo.length
        return 16  # Default string size
    elif category == data_type_pb2.DataTypeCategory.BINARY:
        return 16  # Base size for binary
    elif category == data_type_pb2.DataTypeCategory.DATE:
        return 4  # Int32 for days
    elif category in (data_type_pb2.DataTypeCategory.TIMESTAMP_LTZ,
                      data_type_pb2.DataTypeCategory.TIMESTAMP_NTZ):
        return 8  # Int64 for microseconds
    elif category == data_type_pb2.DataTypeCategory.INTERVAL_DAY_TIME:
        return 8  # Int64 for milliseconds
    elif category == data_type_pb2.DataTypeCategory.INTERVAL_YEAR_MONTH:
        return 4  # Int32 for months
    elif category == data_type_pb2.DataTypeCategory.ARRAY:
        # Base size + element type size
        element_size = estimate_type_size(data_type.arrayTypeInfo.elementType)
        return 8 + element_size  # 8 bytes for offset + element size
    elif category == data_type_pb2.DataTypeCategory.MAP:
        # Base size + key size + value size
        key_size = estimate_type_size(data_type.mapTypeInfo.keyType)
        value_size = estimate_type_size(data_type.mapTypeInfo.valueType)
        return 8 + key_size + value_size  # 8 bytes for offset + key/value sizes
    elif category == data_type_pb2.DataTypeCategory.STRUCT:
        # Sum of field sizes
        total_size = 8  # Base struct size
        for field in data_type.structTypeInfo.fields:
            total_size += estimate_type_size(field.type)
        return total_size
    else:
        return 8  # Default size for unknown types

def convert_to_field_type(field_type: str, partition_value: str) -> object:
    """Convert partition value to appropriate type based on field schema"""
    # Boolean types
    upper_field = field_type.upper()
    if upper_field in ['BOOLEAN', 'BOOL']:
        return partition_value.lower() in ['true', '1', 'yes', 'on']

    # Integer types
    elif upper_field in ['INT8', 'TINYINT']:
        return int(partition_value)
    elif upper_field in ['INT16', 'SMALLINT']:
        return int(partition_value)
    elif upper_field in ['INT32', 'INT', 'INTEGER']:
        return int(partition_value)
    elif upper_field in ['INT64', 'BIGINT', 'LONG']:
        return int(partition_value)

    # Float types
    elif upper_field in ['FLOAT32', 'FLOAT']:
        return float(partition_value)
    elif upper_field in ['FLOAT64', 'DOUBLE']:
        return float(partition_value)

    # String types
    elif upper_field in ['STRING', 'VARCHAR', 'CHAR', 'TEXT']:
        return partition_value

    # Binary types
    elif upper_field in ['BINARY', 'VARBINARY']:
        return partition_value.encode('utf-8')

    # Date/Time types
    elif upper_field in ['DATE']:
        # Simple date parsing - in production, use proper date parsing
        return partition_value  # Return as string for now
    elif upper_field in ['TIMESTAMP', 'TIMESTAMP_LTZ', 'DATETIME']:
        return partition_value  # Return as string for now

    # Decimal types
    elif upper_field in ['DECIMAL', 'NUMERIC']:
        return Decimal(partition_value)

    # Default: return as string
    else:
        return partition_value


def to_arrow_type(data_type: data_type_pb2.DataType) -> pa.DataType:
    """Convert ClickZetta data type to Arrow type"""
    category = data_type.category

    if category == data_type_pb2.DataTypeCategory.INT8:
        return pa.int8()
    elif category == data_type_pb2.DataTypeCategory.INT16:
        return pa.int16()
    elif category == data_type_pb2.DataTypeCategory.INT32:
        return pa.int32()
    elif category == data_type_pb2.DataTypeCategory.INT64:
        return pa.int64()
    elif category == data_type_pb2.DataTypeCategory.FLOAT32:
        return pa.float32()
    elif category == data_type_pb2.DataTypeCategory.FLOAT64:
        return pa.float64()
    elif category == data_type_pb2.DataTypeCategory.DECIMAL:
        if data_type.decimalTypeInfo:
            precision = data_type.decimalTypeInfo.precision
            scale = data_type.decimalTypeInfo.scale
            return pa.decimal128(precision, scale)
        return pa.decimal128(38, 10)  # Default precision and scale
    elif category == data_type_pb2.DataTypeCategory.BOOLEAN:
        return pa.bool_()
    elif category in (data_type_pb2.DataTypeCategory.VARCHAR,
                      data_type_pb2.DataTypeCategory.CHAR,
                      data_type_pb2.DataTypeCategory.STRING,
                      data_type_pb2.DataTypeCategory.JSON):
        return pa.string()
    elif category == data_type_pb2.DataTypeCategory.BINARY:
        return pa.binary()
    elif category == data_type_pb2.DataTypeCategory.DATE:
        return pa.date32()  # Days since Unix epoch
    elif category == data_type_pb2.DataTypeCategory.TIMESTAMP_LTZ:
        unit = _get_timestamp_unit(data_type.timestamp_info)
        return pa.timestamp(unit, tz='UTC')
    elif category == data_type_pb2.DataTypeCategory.TIMESTAMP_NTZ:
        return pa.timestamp('us', tz=None)
    elif category == data_type_pb2.DataTypeCategory.INTERVAL_DAY_TIME:
        return pa.duration('us')
    elif category == data_type_pb2.DataTypeCategory.INTERVAL_YEAR_MONTH:
        return pa.duration('M')
    elif category == data_type_pb2.DataTypeCategory.ARRAY:
        element_type = to_arrow_type(data_type.arrayTypeInfo.elementType)
        return pa.list_(element_type)
    elif category == data_type_pb2.DataTypeCategory.MAP:
        key_type = to_arrow_type(data_type.mapTypeInfo.keyType)
        value_type = to_arrow_type(data_type.mapTypeInfo.valueType)
        return pa.map_(key_type, value_type)
    elif category == data_type_pb2.DataTypeCategory.STRUCT:
        fields = []
        for field in data_type.structTypeInfo.fields:
            field_type = to_arrow_type(field.type)
            fields.append(pa.field(field.name, field_type, field.type.nullable))
        return pa.struct(fields)
    elif category == data_type_pb2.DataTypeCategory.VECTOR_TYPE:
        # Handle vector type as binary array
        vector_info = data_type.vector_info
        type_width = 0

        if vector_info.numberType == data_type_pb2.VectorNumberType.I8:
            type_width = 1  # Byte.BYTES
        elif vector_info.numberType == data_type_pb2.VectorNumberType.I32:
            type_width = 4  # Integer.BYTES
        elif vector_info.numberType == data_type_pb2.VectorNumberType.F32:
            type_width = 4  # Float.BYTES
        else:
            raise ValueError(f"Unsupported vector number type: {vector_info.numberType}")
        # FixedSizeBinaryType
        return pa.binary(vector_info.dimension * type_width)
        # return pa.fixed_size_binary(vector_info.dimension * type_width)
    else:
        raise ValueError(f"Unsupported data type: {category}")


def _get_timestamp_unit(timestamp_info: data_type_pb2.TimestampInfo) -> str:
    """Get Arrow timestamp unit from proto timestamp info"""
    if not timestamp_info:
        return 'us'  # Default to microseconds

    unit = timestamp_info.tsUnit
    if unit == data_type_pb2.TimestampUnit.SECONDS:
        return 's'
    elif unit == data_type_pb2.TimestampUnit.MILLISECONDS:
        return 'ms'
    elif unit == data_type_pb2.TimestampUnit.MICROSECONDS:
        return 'us'
    elif unit == data_type_pb2.TimestampUnit.NANOSECONDS:
        return 'ns'
    return 'us'  # Default


def create_arrow_schema(fields: List[Dict]) -> pa.Schema:
    """Create Arrow schema from field definitions"""
    arrow_fields = []
    for field in fields:
        try:
            arrow_type = to_arrow_type(field['type'])
            arrow_fields.append(pa.field(field['name'], arrow_type, field.get('nullable', True)))
        except Exception as e:
            log.error(f"Failed to convert field {field['name']}: {e}")
            raise ValueError(f"Failed to convert field {field['name']}: {e}")
    return pa.schema(arrow_fields)


def convert_array_value(value: List, element_type: data_type_pb2.DataType) -> pa.Array:
    """Convert array value to Arrow array"""
    if value is None:
        return None

    converted_values = []
    for item in value:
        converted_item = convert_value(item, element_type)
        converted_values.append(converted_item)

    return pa.array(converted_values, type=to_arrow_type(element_type))


def convert_map_value(value: Dict, key_type: data_type_pb2.DataType, value_type: data_type_pb2.DataType) -> pa.Array:
    """Convert map value to Arrow array"""
    if value is None:
        return None

    keys = []
    values = []
    for k, v in value.items():
        keys.append(convert_value(k, key_type))
        values.append(convert_value(v, value_type))

    return pa.MapArray.from_arrays(
        pa.array(keys, type=to_arrow_type(key_type)),
        pa.array(values, type=to_arrow_type(value_type))
    )


def convert_struct_value(value: Dict, fields) -> pa.Array:
    """Convert struct value to Arrow array"""
    if value is None:
        return None

    converted_values = {}
    for field in fields:
        field_value = value.get(field.name)
        converted_value = convert_value(field_value, field.type)
        converted_values[field.name] = converted_value

    return pa.StructArray.from_arrays(
        [pa.array([v]) for v in converted_values.values()],
        list(converted_values.keys())
    )


def convert_value(value: Any, data_type: data_type_pb2.DataType) -> Any:
    """Convert value based on data type"""
    if value is None:
        return None

    category = data_type.category
    try:
        if category == data_type_pb2.DataTypeCategory.INT8:
            return np.int8(value)
        elif category == data_type_pb2.DataTypeCategory.INT16:
            return np.int16(value)
        elif category == data_type_pb2.DataTypeCategory.INT32:
            return np.int32(value)
        elif category == data_type_pb2.DataTypeCategory.INT64:
            return np.int64(value)
        elif category == data_type_pb2.DataTypeCategory.FLOAT32:
            return np.float32(value)
        elif category == data_type_pb2.DataTypeCategory.FLOAT64:
            return np.float64(value)
        elif category == data_type_pb2.DataTypeCategory.DECIMAL:
            if not isinstance(value, Decimal):
                value = Decimal(str(value))
            return value
        elif category == data_type_pb2.DataTypeCategory.STRING:
            return str(value)
        elif category == data_type_pb2.DataTypeCategory.BINARY:
            return bytes(value)
        elif category == data_type_pb2.DataTypeCategory.DATE:
            if isinstance(value, datetime):
                value = value.date()
            if isinstance(value, date):
                return value.toordinal() - date(1970, 1, 1).toordinal()
            return value
        elif category == data_type_pb2.DataTypeCategory.TIMESTAMP_LTZ:
            if isinstance(value, datetime):
                return int(value.timestamp() * 1_000_000)  # Convert to microseconds
            return value
        elif category == data_type_pb2.DataTypeCategory.ARRAY:
            return convert_array_value(value, data_type.arrayTypeInfo.elementType)
        elif category == data_type_pb2.DataTypeCategory.MAP:
            return convert_map_value(value, data_type.mapTypeInfo.keyType, data_type.mapTypeInfo.valueType)
        elif category == data_type_pb2.DataTypeCategory.STRUCT:
            return convert_struct_value(value, data_type.structTypeInfo.fields)
        else:
            raise ValueError(f"Unsupported data type: {category}")
    except Exception as e:
        raise ValueError(f"Failed to convert value {value} to type {category}: {str(e)}")


def generate_pyarrow_schema(schema: dict[str, Any]) -> pa.Schema:
    pyarrow_fields = []
    for field in schema:
        data_type = schema[field]
        if data_type.category == data_type_pb2.DataTypeCategory.INT8:
            pyarrow_fields.append(pa.field(field, pa.int8()))
        elif data_type.category == data_type_pb2.DataTypeCategory.INT16:
            pyarrow_fields.append(pa.field(field, pa.int16()))
        elif data_type.category == data_type_pb2.DataTypeCategory.INT32:
            pyarrow_fields.append(pa.field(field, pa.int32()))
        elif data_type.category == data_type_pb2.DataTypeCategory.INT64:
            pyarrow_fields.append(pa.field(field, pa.int64()))
        elif data_type.category == data_type_pb2.DataTypeCategory.FLOAT32:
            pyarrow_fields.append(pa.field(field, pa.float32()))
        elif data_type.category == data_type_pb2.DataTypeCategory.FLOAT64:
            pyarrow_fields.append(pa.field(field, pa.float64()))
        elif data_type.category == data_type_pb2.DataTypeCategory.DECIMAL:
            precision = data_type.decimalTypeInfo.precision
            scale = data_type.decimalTypeInfo.scale
            pyarrow_fields.append(pa.field(field, pa.decimal128(precision, scale)))
        elif data_type.category == data_type_pb2.DataTypeCategory.BOOLEAN:
            pyarrow_fields.append(pa.field(field, pa.bool_()))
        elif data_type.category == data_type_pb2.DataTypeCategory.CHAR or \
                data_type.category == data_type_pb2.DataTypeCategory.VARCHAR or \
                data_type.category == data_type_pb2.DataTypeCategory.STRING:
            pyarrow_fields.append(pa.field(field, pa.string()))
        elif data_type.category == data_type_pb2.DataTypeCategory.DATE:
            pyarrow_fields.append(pa.field(field, pa.date32()))
        elif data_type.category == data_type_pb2.DataTypeCategory.TIMESTAMP_LTZ:
            timestamp_unit = data_type.timestamp_info.tsUnit
            if timestamp_unit == data_type_pb2.TimestampUnit.SECONDS:
                pyarrow_fields.append(pa.field(field, pa.timestamp('s', tz='UTC')))
            elif timestamp_unit == data_type_pb2.TimestampUnit.MILLISECONDS:
                pyarrow_fields.append(pa.field(field, pa.timestamp('ms', tz='UTC')))
            elif timestamp_unit == data_type_pb2.TimestampUnit.MICROSECONDS:
                pyarrow_fields.append(pa.field(field, pa.timestamp('us', tz='UTC')))
            elif timestamp_unit == data_type_pb2.TimestampUnit.NANOSECONDS:
                pyarrow_fields.append(pa.field(field, pa.timestamp('ns', tz='UTC')))
    return pa.schema(pyarrow_fields)


# Add MapVector constants
class MapVector:
    """Constants for map vector field names"""
    KEY_NAME = "key"
    VALUE_NAME = "value"
    DATA_VECTOR_NAME = "entries"


def get_default_value_by_type(arrow_type: pa.DataType) -> Any:
    """Get default value for Arrow data type
    
    Args:
        arrow_type: PyArrow data type
        
    Returns:
        Default value for the type
    """
    # Boolean type
    if pa.types.is_boolean(arrow_type):
        return False
    
    # Integer types
    elif pa.types.is_int8(arrow_type):
        return np.int8(0)
    elif pa.types.is_int16(arrow_type):
        return np.int16(0)
    elif pa.types.is_int32(arrow_type):
        return np.int32(0)
    elif pa.types.is_int64(arrow_type):
        return np.int64(0)
    elif pa.types.is_uint8(arrow_type):
        return np.uint8(0)
    elif pa.types.is_uint16(arrow_type):
        return np.uint16(0)
    elif pa.types.is_uint32(arrow_type):
        return np.uint32(0)
    elif pa.types.is_uint64(arrow_type):
        return np.uint64(0)
    
    # Floating point types
    elif pa.types.is_float32(arrow_type):
        return np.float32(0.0)
    elif pa.types.is_float64(arrow_type):
        return np.float64(0.0)
    elif pa.types.is_float16(arrow_type):
        return np.float16(0.0)
    
    # String and binary types
    elif pa.types.is_string(arrow_type):
        return ""
    elif pa.types.is_large_string(arrow_type):
        return ""
    elif pa.types.is_binary(arrow_type):
        return b""
    elif pa.types.is_large_binary(arrow_type):
        return b""
    elif pa.types.is_fixed_size_binary(arrow_type):
        return b'\0' * arrow_type.byte_width
    
    # Date and time types
    elif pa.types.is_date32(arrow_type):
        return np.int32(0)  # epoch
    elif pa.types.is_date64(arrow_type):
        return np.int64(0)  # epoch
    elif pa.types.is_timestamp(arrow_type):
        return np.int64(0)  # epoch
    elif pa.types.is_time32(arrow_type):
        return np.int32(0)
    elif pa.types.is_time64(arrow_type):
        return np.int64(0)
    elif pa.types.is_duration(arrow_type):
        return np.int64(0)
    
    # Decimal types
    elif pa.types.is_decimal128(arrow_type):
        return Decimal('0.0')
    elif pa.types.is_decimal256(arrow_type):
        return Decimal('0.0')
    
    # Interval types
    elif pa.types.is_interval(arrow_type):
        return np.int32(0)
    
    # Complex types
    elif pa.types.is_list(arrow_type):
        return []
    elif pa.types.is_large_list(arrow_type):
        return []
    elif pa.types.is_fixed_size_list(arrow_type):
        return []
    elif pa.types.is_map(arrow_type):
        return {}
    elif pa.types.is_struct(arrow_type):
        return {}
    elif pa.types.is_dictionary(arrow_type):
        # Return default value for the dictionary's value type
        return get_default_value_by_type(arrow_type.value_type)
    
    # Null type
    elif pa.types.is_null(arrow_type):
        return None
    
    else:
        raise ValueError(f"Unsupported type for default value: {arrow_type}")
