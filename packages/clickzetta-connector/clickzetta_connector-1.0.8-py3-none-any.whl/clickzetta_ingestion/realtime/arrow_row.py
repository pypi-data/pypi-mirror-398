from dataclasses import field, dataclass
from datetime import timedelta
from typing import Any, Union, Optional, List

from clickzetta_ingestion._proto import ingestion_pb2, ingestion_v2_pb2, data_type_pb2
from clickzetta_ingestion.realtime.row_pool import RowPool
import numpy as np


@dataclass
class DataField:
    name: str
    type: data_type_pb2.DataType
    nullable: bool = True


@dataclass
class DistributionSpec:
    field_ids: List[int]
    hash_functions: List[str]
    num_buckets: int


class ArrowRow:
    """
        <p>The mappings from SQL data types to the internal data structures are listed in the following
    table:
    <pre>
    +--------------------------------+-----------------------------------------+
    | SQL Data Types                 | Internal Data Structures                |
    +--------------------------------+-----------------------------------------+
    | BOOLEAN                        | bool                                    |
    +--------------------------------+-----------------------------------------+
    | STRING / JSON                  | str                                     |
    +--------------------------------+-----------------------------------------+
    | CHAR(n) / VARCHAR(n)           | str(超限写入将截断)                       |
    +--------------------------------+-----------------------------------------+
    | BINARY                         | bytes                                   |
    +--------------------------------+-----------------------------------------+
    | DECIMAL                        | Decimal                                 |
    +--------------------------------+-----------------------------------------+
    | INT8                           | int                                     |
    +--------------------------------+-----------------------------------------+
    | INT16                          | int                                     |
    +--------------------------------+-----------------------------------------+
    | INT32                          | int                                     |
    +--------------------------------+-----------------------------------------+
    | INT64                          | int                                     |
    +--------------------------------+-----------------------------------------+
    | FLOAT                          | float                                   |
    +--------------------------------+-----------------------------------------+
    | DOUBLE                         | float                                   |
    +--------------------------------+-----------------------------------------+
    | DATE                           | date                                    |
    +--------------------------------+-----------------------------------------+
    | TIMESTAMP_LTZ                  | datetime(tz=timezone_info)              |
    +--------------------------------+-----------------------------------------+
    | TIMESTAMP_NTZ                  | datetime                                |
    +--------------------------------+-----------------------------------------+
    | INTERVAL_DAY_TIME              | interval_day_time                       |
    +--------------------------------+-----------------------------------------+
    | INTERVAL_YEAR_MONTH            | -                                       |
    +--------------------------------+-----------------------------------------+
    | ARRAY                          | list                                    |
    +--------------------------------+-----------------------------------------+
    | MAP                            | map                                     |
    +--------------------------------+-----------------------------------------+
    | STRUCT                         | json and collections.namedtuple         |
    +--------------------------------+-----------------------------------------+
    </pre>
    <p>Nullability is always handled by the container data structure.
    """

    def __init__(self, arrow_table, operation_type, complex_type_recheck=True):
        if (arrow_table.igs_table_type != ingestion_pb2.IGSTableType.ACID and
                operation_type not in (ingestion_v2_pb2.OperationType.INSERT,
                                       ingestion_v2_pb2.OperationType.INSERT_IGNORE)):
            raise ValueError("Append Only stream only support the INSERT operation")
        from clickzetta_ingestion.realtime.arrow_table import ArrowTable  # To avoid circular import
        from clickzetta_ingestion.realtime.arrow_schema import ArrowSchema
        self.arrow_table: ArrowTable = arrow_table
        self.arrow_schema: ArrowSchema = arrow_table.arrow_schema
        self.operation_type: Optional[ingestion_v2_pb2.OperationType] = operation_type
        self.complex_type_recheck = complex_type_recheck
        self.columns = {}  # The array to store the actual internal format values.
        self.columns_bitset = set()  # Store column index that has been set
        self.row_size = 0 # Memory size of data row
        self.offset_size = 0 # Memory size of complex type offset
        self.pooled = False
        self._pool = None

    # TODO should we merge with clickzetta_ingestion.bulkload.storage.iceberg_row.IcebergRow._cast_row_value_to_input?
    def cast_row_value_to_input(self, column_name: str, data_type: data_type_pb2.DataType, value: Any) -> Any:
        """Cast value to expected type based on schema"""
        if value is None:
            if not data_type.nullable:
                raise ValueError(f"Column {column_name} is not nullable but got None value")
            return None

        try:
            category = data_type.category
            if category == data_type_pb2.DataTypeCategory.BOOLEAN:
                self.row_size += 1
                return bool(value)

            elif category == data_type_pb2.DataTypeCategory.INT8:
                self.row_size += 1
                return int(value)

            elif category == data_type_pb2.DataTypeCategory.INT16:
                self.row_size += 2
                return int(value)

            elif category == data_type_pb2.DataTypeCategory.INT32:
                self.row_size += 4
                return int(value)

            elif category == data_type_pb2.DataTypeCategory.INT64:
                self.row_size += 8
                return int(value)

            elif category == data_type_pb2.DataTypeCategory.FLOAT32:
                self.row_size += 4
                return float(value)

            elif category == data_type_pb2.DataTypeCategory.FLOAT64:
                self.row_size += 8
                return float(value)

            elif category == data_type_pb2.DataTypeCategory.DECIMAL:
                self.row_size += 16
                if data_type.HasField('decimalTypeInfo'):
                    from decimal import Decimal
                    return Decimal(str(value))
                else:
                    raise ValueError("Decimal type missing decimalTypeInfo")

            elif category in (data_type_pb2.DataTypeCategory.VARCHAR,
                              data_type_pb2.DataTypeCategory.CHAR):
                # Get length limit for CHAR/VARCHAR
                length = (int(data_type.charTypeInfo.length)
                          if category == data_type_pb2.DataTypeCategory.CHAR
                          else int(data_type.varCharTypeInfo.length))

                if not isinstance(value, str):
                    value = str(value)

                # Truncate if exceeds length
                if length < len(value):
                    value = value[:length]

                self.row_size += len(value.encode('utf-8'))
                self.offset_size += 8
                return value

            elif category in (data_type_pb2.DataTypeCategory.STRING,
                              data_type_pb2.DataTypeCategory.JSON):
                if isinstance(value, str):
                    self.row_size += len(value.encode('utf-8'))
                    self.offset_size += 8
                    return value
                elif isinstance(value, bytes):
                    self.row_size += len(value)
                    self.offset_size += 8
                    return value
                else:
                    raise ValueError(f"String/JSON type only supports str or bytes, got {type(value)}")

            elif category == data_type_pb2.DataTypeCategory.BINARY:
                if isinstance(value, str):
                    value = value.encode('utf-8')
                elif not isinstance(value, bytes):
                    value = bytes(str(value), 'utf-8')
                self.row_size += len(value)
                self.offset_size += 8
                return value

            elif category == data_type_pb2.DataTypeCategory.DATE:
                self.row_size += 4
                from datetime import date
                if isinstance(value, int):
                    # Check date range
                    if not (0 <= value <= 2932896):
                        raise ValueError(f"Date value {value} out of valid range [0, 2932896]")
                    return value
                elif isinstance(value, date):
                    # Convert to days since epoch
                    epoch = date(1970, 1, 1)
                    return (value - epoch).days
                else:
                    raise ValueError(f"Date type only supports int or date, got {type(value)}")

            elif category in (data_type_pb2.DataTypeCategory.TIMESTAMP_LTZ,
                              data_type_pb2.DataTypeCategory.TIMESTAMP_NTZ):
                self.row_size += 8
                from datetime import datetime
                if isinstance(value,
                              int) and data_type.timestamp_info.tsUnit == data_type_pb2.TimestampUnit.MICROSECONDS:
                    return value
                elif isinstance(value, datetime):
                    return int(value.timestamp() * 1_000_000)  # Convert to microseconds
                else:
                    raise ValueError(f"Timestamp type only supports int or datetime, got {type(value)}")

            elif category == data_type_pb2.DataTypeCategory.ARRAY:
                # Convert list/tuple to list
                if not isinstance(value, (list, tuple)):
                    raise ValueError(f"Expected list/tuple for array type, got {type(value)}")

                element_type = data_type.arrayTypeInfo.elementType
                if self.complex_type_recheck:
                    result = [
                        self.cast_row_value_to_input(column_name, element_type, item)
                        for item in value
                    ]
                else:
                    result = list(value)

                # Update memory tracking
                self.offset_size += 8  # Array header
                return result

            elif category == data_type_pb2.DataTypeCategory.MAP:
                # Convert dict to map
                if not isinstance(value, dict):
                    raise ValueError(f"Expected dict for map type, got {type(value)}")

                key_type = data_type.mapTypeInfo.keyType
                value_type = data_type.mapTypeInfo.valueType

                if self.complex_type_recheck:
                    result = {
                        self.cast_row_value_to_input(column_name, key_type, k):
                            self.cast_row_value_to_input(column_name, value_type, v)
                        for k, v in value.items()
                    }
                else:
                    result = dict(value)

                # Update memory tracking
                self.offset_size += 8  # Map header
                return result

            elif category == data_type_pb2.DataTypeCategory.STRUCT:
                # Handle struct type
                if isinstance(value, (list, tuple)):
                    if len(value) != len(data_type.structTypeInfo.fields):
                        raise ValueError(
                            f"Struct value length mismatch: expected {len(data_type.structTypeInfo.fields)}, got {len(value)}")

                    if self.complex_type_recheck:
                        result = [
                            self.cast_row_value_to_input(f.name, f.type, val)
                            for f, val in zip(data_type.structTypeInfo.fields, value)
                        ]
                    else:
                        result = list(value)

                elif isinstance(value, dict):
                    if self.complex_type_recheck:
                        result = {}
                        for data_field in data_type.structTypeInfo.fields:
                            if data_field.name not in value:
                                raise ValueError(f"Missing field {data_field.name} in struct value")
                            result[data_field.name] = self.cast_row_value_to_input(
                                data_field.name, data_field.type, value[data_field.name]
                            )
                    else:
                        result = dict(value)
                else:
                    raise ValueError(f"Expected list/tuple/dict for struct type, got {type(value)}")

                # Update memory tracking
                self.offset_size += 8  # Struct header
                return result

            elif category == data_type_pb2.DataTypeCategory.INTERVAL_DAY_TIME:
                # Convert to milliseconds
                self.row_size += 8
                if isinstance(value, timedelta):
                    return int(value.total_seconds() * 1000)
                elif isinstance(value, (int, float)):
                    return int(value)
                else:
                    raise ValueError(f"Expected timedelta or number for interval day time, got {type(value)}")

            elif category == data_type_pb2.DataTypeCategory.INTERVAL_YEAR_MONTH:
                # Convert to milliseconds
                if isinstance(value, timedelta):
                    return int(value.total_seconds() * 1000)
                elif isinstance(value, (int, float)):
                    return int(value)
                else:
                    raise ValueError(f"Expected timedelta or number for interval day time, got {type(value)}")

            elif category == data_type_pb2.DataTypeCategory.VECTOR_TYPE:
                # Compute vector size
                vector_size = VectorTypeUtil.compute_vector_size(data_type)
                self.row_size += vector_size
                self.offset_size += 8
                
                try:
                    binary_value = VectorTypeUtil.convert_vector(data_type, value)
                    
                    # Validate length
                    if len(binary_value) != vector_size:
                        raise ValueError(
                            f"Vector value length mismatch. Expected {vector_size} bytes, got {len(binary_value)}"
                        )
                        
                    return binary_value
                    
                except Exception as e:
                    raise ValueError(f"Failed to convert vector value: {str(e)}")

            else:
                raise ValueError(f"Unsupported data type category: {category}")

        except Exception as e:
            raise ValueError(f"Failed to cast value for column {column_name}: {str(e)}")

    def set_value(self, column_name_or_index: Union[str, int], value: Any):
        """Sets value for a column by name or index"""
        if isinstance(column_name_or_index, str):
            column_index = self.arrow_table.get_column_index(column_name_or_index)
            if column_index is None:
                raise ValueError(f"Column {column_name_or_index} not found in table schema")
        else:
            column_index = column_name_or_index

        current_field = self.arrow_table.get_column_by_index(column_index)
        if not current_field:
            raise ValueError(f"Column index {column_index} not found in table schema")

        # Cast value and track memory (memory tracking is done inside cast_row_value_to_input)
        converted_value = self.cast_row_value_to_input(current_field.name, current_field.type, value)
        self.columns[column_index] = converted_value
        self.columns_bitset.add(column_index)

    def validate(self):
        if self.operation_type in (ingestion_v2_pb2.OperationType.INSERT,
                                   ingestion_v2_pb2.OperationType.INSERT_IGNORE,
                                   ingestion_v2_pb2.OperationType.UPSERT):
            if len(self.columns_bitset) != len(self.arrow_table.get_column_names()):
                raise ValueError("Insert/Upsert row must set all columns")

    def get_memory_size(self) -> int:
        return self.row_size + self.offset_size

    def reset_row_meta(self, arrow_table, operation_type) -> 'ArrowRow':
        """Reset row metadata for reuse"""
        # Check operation type
        if (arrow_table.igs_table_type != ingestion_pb2.IGSTableType.ACID and
                operation_type not in (ingestion_v2_pb2.OperationType.INSERT,
                                       ingestion_v2_pb2.OperationType.INSERT_IGNORE)):
            raise ValueError("Common or Cluster Table only support Insert Operation")

        self.operation_type = operation_type

        # Check if table or schema changed
        schema_changed = (
                self.arrow_table is None or
                self.arrow_table != arrow_table or
                self.arrow_table.arrow_schema != arrow_table.arrow_schema
        )

        if schema_changed:
            self.arrow_table = arrow_table
            self.arrow_schema = arrow_table.arrow_schema

        # Reset state
        self.columns.clear()
        self.columns_bitset.clear()
        self.row_size = 0
        self.offset_size = 0

        return self

    def set_pool(self, pool: 'RowPool'):
        """Set the pool this row belongs to"""
        self._pool = pool
        self.pooled = True

    def release(self):
        """Release row back to pool if pooled"""
        if self._pool and self.pooled:
            self._pool.release_row(self)

    def clean(self):
        """Clean up resources"""
        self.arrow_table = None
        self.operation_type = None
        self.columns.clear()
        self.columns_bitset.clear()
        self.row_size = 0
        self.offset_size = 0
        self._pool = None
        self.pooled = False

    def is_null_at(self, ordinal):
        return ordinal not in self.columns_bitset


@dataclass
class ArrowIGSTableMeta:
    """
    wrap for TableMeta & IGSTableType
    <p>
    IGSTableType:
    CLUSTER,
    ACID,
    NORMAL
    """

    instance_id: int
    schema_name: str
    table_name: str
    table_meta: ingestion_v2_pb2.StreamSchema
    require_commit: bool = False
    data_fields: List[DataField] = field(default_factory=list)
    dist_spec = None

    def __post_init__(self):
        self.data_fields = [
            DataField(
                name=f.name,
                type=f.type,
                # From the proto definition -> data_type.proto DataField.DataType.nullable
                nullable=f.type.nullable
            ) for f in self.table_meta.data_fields
        ]

        if self.table_meta.dist_spec:
            self.dist_spec = DistributionSpec(
                field_ids=list(self.table_meta.dist_spec.field_ids),
                hash_functions=list(self.table_meta.dist_spec.hash_functions),
                num_buckets=self.table_meta.dist_spec.num_buckets
            )

        self.table_type = (
            ingestion_pb2.IGSTableType.ACID if self.table_meta.HasField("primary_key_spec")
            else ingestion_pb2.IGSTableType.CLUSTER if self.table_meta.HasField("dist_spec")
            else ingestion_pb2.IGSTableType.NORMAL
        )

    def __str__(self):
        return (
            f"ArrowIGSTableMeta(instance_id={self.instance_id}, schema_name='{self.schema_name}', "
            f"table_name='{self.table_name}', table_meta={self.table_meta}, data_fields={self.data_fields}, "
            f"dist_spec={self.dist_spec}, table_type={self.table_type}, require_commit={self.require_commit})"
        )

    def __repr__(self):
        return self.__str__()


class VectorTypeUtil:
    """Utility class for handling vector type data"""
    
    @staticmethod
    def compute_vector_size(vector_type: data_type_pb2.DataType) -> int:
        """Compute size in bytes for vector type"""
        vector_info = vector_type.vector_info
        dimension = vector_info.dimension
        
        if vector_info.numberType == data_type_pb2.VectorNumberType.I8:
            return dimension
        elif vector_info.numberType in (data_type_pb2.VectorNumberType.I16,
                                      data_type_pb2.VectorNumberType.F16):
            return dimension * 2
        elif vector_info.numberType in (data_type_pb2.VectorNumberType.I32,
                                      data_type_pb2.VectorNumberType.F32):
            return dimension * 4
        elif vector_info.numberType in (data_type_pb2.VectorNumberType.I64,
                                      data_type_pb2.VectorNumberType.F64,
                                      data_type_pb2.VectorNumberType.BF64):
            return dimension * 8
        else:
            raise ValueError(f"Invalid vector type: {vector_type}")
            
    @staticmethod
    def check_dimension(array_length: int, dimension: int):
        """Check if array length matches expected dimension"""
        if array_length != dimension:
            raise ValueError(
                f"Vector lengths do not match, input:{array_length}, dimension:{dimension}"
            )
            
    @staticmethod
    def convert_vector(vector_type: data_type_pb2.DataType, value: Any) -> bytes:
        """Convert vector value to bytes"""
        vector_info = vector_type.vector_info
        dim = vector_info.dimension
        vector = None
        
        if vector_info.numberType == data_type_pb2.VectorNumberType.I8:
            if isinstance(value, (bytes, bytearray)):
                vector = value
                VectorTypeUtil.check_dimension(len(vector), dim)
            elif isinstance(value, (list, tuple, np.ndarray)):
                arr = np.array(value, dtype=np.int8)
                VectorTypeUtil.check_dimension(len(arr), dim)
                vector = arr.tobytes()
                
        elif vector_info.numberType == data_type_pb2.VectorNumberType.I32:
            if isinstance(value, (list, tuple, np.ndarray)):
                arr = np.array(value, dtype=np.int32)
                VectorTypeUtil.check_dimension(len(arr), dim)
                vector = arr.tobytes()
                
        elif vector_info.numberType == data_type_pb2.VectorNumberType.F32:
            if isinstance(value, (list, tuple, np.ndarray)):
                arr = np.array(value, dtype=np.float32)
                VectorTypeUtil.check_dimension(len(arr), dim)
                vector = arr.tobytes()
                
        if vector is None:
            raise ValueError(f"Invalid vector input: {value}")
            
        return vector
        
    @staticmethod
    def write_int8_bits_to_array(array: bytearray, offset: int, bits: int):
        """Write 8-bit integer to byte array"""
        array[offset] = bits & 0xFF
        
    @staticmethod
    def write_int32_bits_to_array(array: bytearray, offset: int, bits: int):
        """Write 32-bit integer to byte array"""
        array[offset] = bits & 0xFF
        array[offset + 1] = (bits >> 8) & 0xFF
        array[offset + 2] = (bits >> 16) & 0xFF
        array[offset + 3] = (bits >> 24) & 0xFF
