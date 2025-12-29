from __future__ import annotations

import threading
import re
from logging import getLogger
from typing import Dict, List, Set, Any

import pyarrow as pa

from clickzetta_ingestion.bulkload.bulkload_context import FieldSchema
from clickzetta_ingestion.common.loading_cache import LoadingCache

logger = getLogger(__name__)


def string_type_to_arrow_type(type_str: str) -> pa.DataType:
    """
    Convert string-based data type to PyArrow type.
    
    Args:
        type_str: String representation of the data type
        
    Returns:
        PyArrow DataType
        
    Raises:
        ValueError: If the type string is not supported
    """
    if not type_str:
        raise ValueError("Type string cannot be empty")

    # Normalize to uppercase for case-insensitive matching
    upper_type = type_str.upper().strip()

    # Basic types
    if upper_type in ['INT8', 'TINYINT', 'INT16', 'SMALLINT', 'INT32', 'INT', 'INTEGER']:
        return pa.int32()
    elif upper_type in ['INT64', 'BIGINT', 'LONG']:
        return pa.int64()
    elif upper_type in ['FLOAT32', 'FLOAT']:
        return pa.float32()
    elif upper_type in ['FLOAT64', 'DOUBLE']:
        return pa.float64()
    elif upper_type in ['BOOLEAN', 'BOOL']:
        return pa.bool_()
    elif upper_type in ['STRING', 'TEXT']:
        return pa.string()
    elif upper_type in ['BINARY', 'VARBINARY', "BITMAP"]:
        return pa.binary()
    elif upper_type == 'DATE':
        return pa.date32()
    elif upper_type in ['JSON']:
        return pa.string()  # JSON stored as string in Arrow

    # Handle parameterized types with regex

    # VARCHAR(n) or CHAR(n)
    varchar_match = re.match(r'^(VARCHAR|CHAR|STRING|JSON)\((\d+)\)$', upper_type)
    if varchar_match:
        return pa.string()

    # DECIMAL(precision) or DECIMAL(precision, scale)
    decimal_match = re.match(r'^DECIMAL\((\d+)(?:,\s*(\d+))?\)$', upper_type)
    if decimal_match:
        precision = int(decimal_match.group(1))
        scale = int(decimal_match.group(2)) if decimal_match.group(2) else 0
        return pa.decimal128(precision, scale)

    # TIMESTAMP types
    if upper_type in ['TIMESTAMP', 'TIMESTAMP_LTZ']:
        return pa.timestamp('us', tz='UTC')
    elif upper_type in ['TIMESTAMP_NTZ', 'DATETIME']:
        return pa.timestamp('us', tz=None)

    # Interval types
    elif upper_type in ['INTERVAL_DAY_TIME']:
        return pa.duration('us')
    elif upper_type in ['INTERVAL_YEAR_MONTH']:
        return pa.duration('M')

    # Array types - ARRAY<element_type>
    array_match = re.match(r'^ARRAY<(.+)>$', type_str, re.IGNORECASE)
    if array_match:
        element_type_str = array_match.group(1)
        element_type = string_type_to_arrow_type(element_type_str)
        return pa.list_(element_type)

    # Map types - MAP<key_type, value_type>
    map_match = re.match(r'^MAP<(.+)>$', type_str, re.IGNORECASE)
    if map_match:
        inner_content = map_match.group(1)
        # Parse key and value types properly handling nested types
        key_type_str, value_type_str = _parse_map_types(inner_content)
        key_type = string_type_to_arrow_type(key_type_str)
        value_type = string_type_to_arrow_type(value_type_str)
        return pa.map_(key_type, value_type)

    # Struct types - STRUCT<field1:type1, field2:type2, ...>
    # Use original type_str to preserve field name casing
    struct_match = re.match(r'^STRUCT<(.+)>$', type_str, re.IGNORECASE)
    if struct_match:
        fields_str = struct_match.group(1)
        fields = []

        # Parse struct fields - handle nested types properly
        field_parts = _parse_struct_fields(fields_str)
        for field_part in field_parts:
            field_match = re.match(r'^\s*(\w+)\s*:\s*(.+)\s*$', field_part.strip())
            if field_match:
                field_name = field_match.group(1)  # Preserve original casing
                field_type_str = field_match.group(2).strip()
                field_type = string_type_to_arrow_type(field_type_str)
                fields.append(pa.field(field_name, field_type, True))  # Default nullable

        return pa.struct(fields)

    # Vector types - VECTOR(type, dimension)
    vector_match = re.match(r'^VECTOR\((\w+),\s*(\d+)\)$', upper_type)
    if vector_match:
        number_type = vector_match.group(1).upper()
        dimension = int(vector_match.group(2))

        if number_type in ['INT8', 'TINYINT', 'INT16', 'SMALLINT', 'INT32', 'INT', 'INTEGER']:
            type_width = 1
        elif number_type in ['INT64', 'BIGINT', 'LONG']:
            type_width = 2
        elif number_type in ['FLOAT32', 'FLOAT']:
            type_width = 4
        elif number_type in ['FLOAT64', 'DOUBLE']:
            type_width = 8
        else:
            raise ValueError(f"Unsupported vector number type: {number_type}")

        return pa.binary(dimension * type_width)

    # If no match found, raise error
    raise ValueError(f"Unsupported data type: {type_str}")


def _parse_map_types(content: str) -> tuple[str, str]:
    """
    Parse MAP<key_type, value_type> content, handling nested types properly.
    
    Args:
        content: String containing key and value type definitions
        
    Returns:
        Tuple of (key_type_str, value_type_str)
        
    Raises:
        ValueError: If content cannot be parsed as map types
    """
    bracket_count = 0
    angle_bracket_count = 0
    paren_count = 0
    comma_pos = -1

    for i, char in enumerate(content):
        if char == '<':
            angle_bracket_count += 1
        elif char == '>':
            angle_bracket_count -= 1
        elif char == '(':
            paren_count += 1
        elif char == ')':
            paren_count -= 1
        elif char == '[':
            bracket_count += 1
        elif char == ']':
            bracket_count -= 1
        elif char == ',' and bracket_count == 0 and angle_bracket_count == 0 and paren_count == 0:
            # This comma is at the top level, so it separates key and value types
            comma_pos = i
            break

    if comma_pos == -1:
        raise ValueError(f"Cannot parse MAP types from: {content}")

    key_type_str = content[:comma_pos].strip()
    value_type_str = content[comma_pos + 1:].strip()

    if not key_type_str or not value_type_str:
        raise ValueError(f"Invalid MAP type definition: {content}")

    return key_type_str, value_type_str


def _parse_struct_fields(fields_str: str) -> List[str]:
    """
    Parse struct field definitions, handling nested types properly.
    
    Args:
        fields_str: String containing field definitions
        
    Returns:
        List of field definition strings
    """
    fields = []
    current_field = ""
    bracket_count = 0
    angle_bracket_count = 0

    for char in fields_str:
        if char == '<':
            angle_bracket_count += 1
        elif char == '>':
            angle_bracket_count -= 1
        elif char == '(':
            bracket_count += 1
        elif char == ')':
            bracket_count -= 1
        elif char == ',' and bracket_count == 0 and angle_bracket_count == 0:
            # This comma is at the top level, so it separates fields
            if current_field.strip():
                fields.append(current_field.strip())
            current_field = ""
            continue

        current_field += char

    # Add the last field
    if current_field.strip():
        fields.append(current_field.strip())

    return fields


class IcebergSchema:
    """
    Manages column mappings and schema information for Iceberg tables.
    """

    def __init__(self, original_types: List[str], fields: List[pa.Field], key_fields_index: Set[int]):
        """
        Initialize IcebergSchema.
        
        Args:
            original_types: List of original ClickZetta data types
            fields: List of Iceberg fields
            key_fields_index: Set of key field indices
        """
        if len(original_types) != len(fields):
            raise ValueError("Original types and fields must have same length")

        self._columns_by_index: List[pa.Field] = []
        self._columns_by_name: Dict[str, int] = {}
        self._columns_by_name_with_case: Dict[str, int] = {}
        self._column_types_by_index: Dict[int, str] = {}
        self._column_original_data_types_by_index: Dict[int, str] = {}
        self._key_columns_index: Set[int] = set()
        self._schema = None

        self._key_columns_index.update(key_fields_index)

        # Build original data types mapping
        for index, original_type in enumerate(original_types):
            self._column_original_data_types_by_index[index] = original_type

        # Build field mappings
        for index, field in enumerate(fields):
            self._columns_by_index.append(field)

            if field.name in self._columns_by_name:
                raise ValueError(f"Column names must be unique: {field.name}")

            self._columns_by_name[field.name] = index

            # Only used for case senstive match when use row.setValue.
            self._columns_by_name_with_case[field.name.lower()] = index
            self._columns_by_name_with_case[field.name.upper()] = index

            self._column_types_by_index[index] = field.type

        # Build schema dictionary
        self._schema = pa.schema(fields)

    def get_schema(self) -> pa.Schema:
        """Get the schema dictionary."""
        return self._schema

    def get_column_index(self, column_name: str) -> int:
        """
        Get column index by name (case-insensitive).
        
        Args:
            column_name: Name of the column
            
        Returns:
            Column index
            
        Raises:
            ValueError: If column not found
        """
        # Try exact match first
        index = self._columns_by_name.get(column_name)

        if index is None:
            # Try case-insensitive match
            index = (self._columns_by_name_with_case.get(column_name.lower()) or
                     self._columns_by_name_with_case.get(column_name.upper()))

        if index is None:
            raise ValueError(f"Unknown column: {column_name}")

        return index

    def get_column_by_index(self, idx: int) -> pa.Field:
        """Get column by index."""
        if idx < 0 or idx >= len(self._columns_by_index):
            raise IndexError(f"Column index out of range: {idx}")
        return self._columns_by_index[idx]

    def get_column_original_type_by_index(self, idx: int) -> Any:
        """Get original data type by index."""
        return self._column_original_data_types_by_index.get(idx)

    def get_column(self, column_name: str) -> pa.Field:
        """Get column by name."""
        index = self.get_column_index(column_name)
        return self._columns_by_index[index]

    def get_column_count(self) -> int:
        """Get total column count."""
        return len(self._columns_by_index)

    def get_key_columns_index(self) -> Set[int]:
        """Get key column indices."""
        return self._key_columns_index.copy()

    def __str__(self) -> str:
        """String representation."""
        return (f"IcebergSchema("
                f"key_columns_index={self._key_columns_index}, "
                f"columns_by_index={[f.name for f in self._columns_by_index]}, "
                f"columns_by_name={self._columns_by_name},"
                f"column_types_by_index={self._column_types_by_index},"
                f"columns_by_name_with_case={self._columns_by_name_with_case},"
                f"schema={self._schema},"
                f"column_original_data_types_by_index={self._column_original_data_types_by_index}"
                f")")


class ParquetSchemaConverter:
    """
    Converts ClickZetta schema to Iceberg schema for Parquet format.
    """

    # Store the mapping from cache key to actual schema
    _schema_key_to_schema = {}
    _cache_lock = threading.Lock()

    _schema_cache: LoadingCache = LoadingCache(
        loader=lambda schema_key: ParquetSchemaConverter._load_schema_from_key(schema_key),
        max_size=32,
    )

    @classmethod
    def convert_to_iceberg_schema(cls, table_schema: List[FieldSchema]) -> IcebergSchema:
        """
        Convert table schema to Iceberg schema.
        
        Args:
            table_schema: List of FieldSchema objects
            
        Returns:
            IcebergSchema instance
        """
        # Create a hashable key from the schema list
        schema_key = cls._create_schema_cache_key(table_schema)

        # Store the mapping from key to schema for the loader to use
        with cls._cache_lock:
            cls._schema_key_to_schema[schema_key] = table_schema

        # Use the cache with the hashable key
        return cls._schema_cache.get(schema_key)

    @classmethod
    def _create_schema_cache_key(cls, table_schema: List[FieldSchema]) -> str:
        """
        Create a hashable cache key from table schema.
        
        Args:
            table_schema: List of FieldSchema objects
            
        Returns:
            String representation that can be used as cache key
        """
        key_parts = []
        for field in table_schema:
            # Create a string representation of each field
            field_key = f"{field.name}:{field.type}"
            key_parts.append(field_key)
        return "|".join(key_parts)

    @classmethod
    def _load_schema_from_key(cls, schema_key: str) -> IcebergSchema:
        """
        Load schema from cache key by looking up the stored table_schema.
        
        Args:
            schema_key: Cache key string
            
        Returns:
            IcebergSchema instance
        """
        with cls._cache_lock:
            table_schema = cls._schema_key_to_schema.get(schema_key)
            if table_schema is None:
                raise KeyError(f"No schema found for cache key: {schema_key}")

        return cls._convert_to_iceberg_schema_internal(table_schema)

    @classmethod
    def _convert_to_iceberg_schema_internal(cls, table_schema: List[FieldSchema]) -> IcebergSchema:
        """Internal method to convert schema."""
        original_types = []
        fields = []

        for i, field_schema in enumerate(table_schema):
            column_data_type_str = field_schema.type
            column_name = field_schema.name
            arrow_type = string_type_to_arrow_type(column_data_type_str)

            iceberg_field = pa.field(column_name, arrow_type, field_schema.nullable)
            fields.append(iceberg_field)
            original_types.append(column_data_type_str)

        # Return IcebergSchema with empty key fields set
        return IcebergSchema(original_types, fields, set())
