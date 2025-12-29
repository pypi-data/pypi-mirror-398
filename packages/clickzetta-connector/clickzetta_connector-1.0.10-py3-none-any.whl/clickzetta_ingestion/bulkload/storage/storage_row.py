from __future__ import annotations

import logging
import struct
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List

import pyarrow as pa

try:
    import pyroaring

    HAS_PYROARING = True
except ImportError:
    HAS_PYROARING = False

from clickzetta_ingestion.bulkload.storage.iceberg_schema import IcebergSchema
from clickzetta_ingestion.common.row import Row

logger = logging.getLogger(__name__)


class IcebergRow(Row):
    """
    Implements both Row and Record interfaces for Iceberg data handling.
    """

    def __init__(self, iceberg_schema: IcebergSchema, complex_type_pre_check: bool = False,
                 is_cz_bitmap_type: bool = False):
        """
        Initialize IcebergRow.
        
        Args:
            iceberg_schema: Schema for the row
            complex_type_pre_check: Whether to perform complex type validation
            is_cz_bitmap_type: Whether to support ClickZetta bitmap types
        """
        super().__init__()
        self._iceberg_schema = iceberg_schema
        self._complex_type_pre_check = complex_type_pre_check
        # The bulkload bitmap no need to add 0xFF byte in the header. Igs must add it.
        self._is_cz_bitmap_type = False

        # Initialize record data
        self._record_data: Dict[int, Any] = {}

    def set_value(self, column_name: str, value: Any):
        """
        Set value by column name.
        
        Args:
            column_name: Name of the column
            value: Value to set
        """
        column_index = self._iceberg_schema.get_column_index(column_name)
        self.set_value_by_index(column_index, value)

    def set_value_by_index(self, column_index: int, value: Any):
        """
        Set value by column index.
        
        Args:
            column_index: Index of the column
            value: Value to set
        """
        field: pa.Field = self._iceberg_schema.get_column_by_index(column_index)
        data_type = self._iceberg_schema.get_column_original_type_by_index(column_index)

        self._check_column_exists(field)

        # Nullable check
        if value is None and not field.nullable:
            raise ValueError(f"Not nullable field [{field.name}] set with null value.")

        # Cast and validate value
        casted_value = self.cast_row_value_to_input(field.name, data_type, value, field.type)

        self._record_data[column_index] = casted_value

    def get_value(self, column_name: str) -> Any:
        """Get value by column name."""
        column_index = self._iceberg_schema.get_column_index(column_name)
        return self._record_data.get(column_index)

    def get_value_by_index(self, column_index: int) -> Any:
        """Get value by column index."""
        return self._record_data.get(column_index)

    def _check_column_exists(self, field: Optional[pa.Field]):
        """Check if column exists in schema."""
        if field is None:
            raise ValueError("Column name isn't present in the table's schema")
        col = self._iceberg_schema.get_column(field.name)
        if col is None:
            raise ValueError(f"Column {field.name} isn't present in the table's schema")

    def cast_row_value_to_input(self, column_name: str, data_type: str, value: Any, output_type: Any) -> Any:
        """
        Cast row value to appropriate input type.
        
        Args:
            column_name: Name of the column
            data_type: Original data type
            value: Input value
            output_type: Target PyArrow type
            
        Returns:
            Casted value
        """
        # Handle null values
        if value is None:
            return None

        # Get data type category string for matching
        data_type_str = data_type.upper() if data_type else str(output_type).upper()

        try:
            # Handle complex types first (they contain keywords that might match basic types)
            if 'ARRAY' in data_type_str and data_type_str.startswith('ARRAY'):
                return self._handle_array_value(column_name, data_type, value, output_type)

            elif 'MAP' in data_type_str and data_type_str.startswith('MAP'):
                return self._handle_map_value(column_name, data_type, value, output_type)

            elif 'STRUCT' in data_type_str and data_type_str.startswith('STRUCT'):
                return self._handle_struct_value(column_name, data_type, value, output_type)

            elif 'VECTOR' in data_type_str and data_type_str.startswith('VECTOR'):
                return self._handle_vector_value(data_type, value)

            # Handle basic data type categories
            elif 'BOOLEAN' in data_type_str or 'BOOL' in data_type_str:
                return bool(value)

            elif 'INT8' in data_type_str or 'TINYINT' in data_type_str or 'INT16' in data_type_str or 'SMALLINT' in data_type_str or 'INT32' in data_type_str or 'INT' in data_type_str or 'INTEGER' in data_type_str:
                return int(value)

            elif 'INT64' in data_type_str or 'BIGINT' in data_type_str or 'LONG' in data_type_str:
                return int(value)

            elif 'FLOAT32' in data_type_str or 'FLOAT' in data_type_str:
                return float(value)

            elif 'FLOAT64' in data_type_str or 'DOUBLE' in data_type_str:
                return float(value)

            elif 'DECIMAL' in data_type_str:
                decimal_val = Decimal(str(value))
                # TODO: Handle precision and scale validation
                return decimal_val

            elif 'VARCHAR' in data_type_str or 'CHAR' in data_type_str:
                # Handle VARCHAR/CHAR with length constraints
                if isinstance(value, str):
                    # TODO: Extract length from data_type and truncate if needed
                    return value
                elif isinstance(value, bytes):
                    return value.decode('utf-8')
                else:
                    return str(value)

            elif 'STRING' in data_type_str or 'TEXT' in data_type_str or 'JSON' in data_type_str:
                if isinstance(value, str):
                    return value
                elif isinstance(value, bytes):
                    return value.decode('utf-8')
                else:
                    return str(value)

            elif 'BINARY' in data_type_str:
                if isinstance(value, bytes):
                    return value
                elif isinstance(value, str):
                    return value.encode('utf-8')
                else:
                    return str(value).encode('utf-8')

            elif 'BITMAP' in data_type_str:
                return self._handle_bitmap_value(column_name, value)

            elif 'DATE' in data_type_str:
                return self._handle_date_value(value)

            elif 'TIMESTAMP' in data_type_str:
                return self._handle_timestamp_value(value, data_type_str)

            elif 'INTERVAL_DAY_TIME' in data_type_str:
                if isinstance(value, timedelta):
                    return int(value.total_seconds() * 1000)  # Convert to milliseconds
                return int(value)

            elif 'INTERVAL_YEAR_MONTH' in data_type_str:
                # Handle year-month intervals
                return int(value)

            else:
                # Default: convert to string
                return str(value)

        except Exception as e:
            raise ValueError(
                f"Value type does not match column type {data_type_str} for column {column_name} with target value {value}: {e}")

    def _handle_bitmap_value(self, column_name: str, value: Any) -> bytes:
        """Handle bitmap values"""
        if not HAS_PYROARING:
            raise ImportError("pyroaring is required for bitmap support. Install with: pip install pyroaring")

        # Create bitmap based on input type
        if isinstance(value, bytes):
            # If already bytes, convert to string first
            value = value.decode('utf-8')

        if isinstance(value, str):
            bitmap_str = value.strip()

            # Handle empty or null bitmap strings
            if bitmap_str.startswith("{") and bitmap_str.endswith("}"):
                bitmap_str = bitmap_str[1:-1]

            if not bitmap_str or bitmap_str.lower() == "null":
                bitmap = pyroaring.BitMap64()
            else:
                # Parse comma-separated values
                try:
                    bitmap_values = [int(x.strip()) for x in bitmap_str.split(",") if x.strip()]
                    bitmap = pyroaring.BitMap64(bitmap_values)
                except ValueError as e:
                    raise ValueError(f"Invalid bitmap string format for column {column_name}: {bitmap_str}") from e

        elif isinstance(value, (list, tuple)):
            # Handle list/tuple of integers
            bitmap_values = [int(x) for x in value]
            bitmap = pyroaring.BitMap64(bitmap_values)

        elif isinstance(value, pyroaring.BitMap64):
            bitmap = value

        else:
            raise ValueError(f"Unsupported bitmap value type for column {column_name}: {type(value)}")

        # Serialize bitmap to bytes
        bitmap_bytes = bitmap.serialize()

        # Add ClickZetta bitmap type marker if needed
        if self._is_cz_bitmap_type:
            # Prepend 0xFF byte 
            return b'\xFF' + bitmap_bytes
        else:
            return bitmap_bytes

    @staticmethod
    def _handle_date_value(value: Any) -> date:
        """Handle date values."""
        if isinstance(value, date):
            return value
        elif isinstance(value, datetime):
            return value.date()
        elif isinstance(value, str):
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y']:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse date string: {value}")
        elif isinstance(value, int):
            # Days since epoch (1970-01-01)
            epoch_date = date(1970, 1, 1)
            return epoch_date + timedelta(days=value)
        else:
            raise ValueError(f"Unsupported date value type: {type(value)}")

    @staticmethod
    def _handle_timestamp_value(value: Any, data_type_str: str) -> datetime:
        """Handle timestamp values."""
        if isinstance(value, datetime):
            # Handle timezone based on timestamp type
            if 'LTZ' in data_type_str:
                # Local timezone timestamp
                if value.tzinfo is None:
                    # Assume local timezone
                    return value.replace(tzinfo=timezone.utc)
                return value
            else:
                # NTZ (no timezone) - return as naive datetime
                return value.replace(tzinfo=None)

        elif isinstance(value, str):
            # Parse ISO format timestamp
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                if 'NTZ' in data_type_str:
                    return dt.replace(tzinfo=None)
                return dt
            except ValueError:
                raise ValueError(f"Unable to parse timestamp string: {value}")

        elif isinstance(value, int):
            # Microseconds since epoch
            dt = datetime.fromtimestamp(value / 1_000_000, tz=timezone.utc)
            if 'NTZ' in data_type_str:
                return dt.replace(tzinfo=None)
            return dt

        else:
            raise ValueError(f"Unsupported timestamp value type: {type(value)}")

    @staticmethod
    def _handle_array_value(column_name: str, data_type: str, value: Any, output_type: Any) -> List[Any]:
        """Handle array values with element type validation."""
        if isinstance(value, (list, tuple)):
            array_list = list(value)
        else:
            # Single value becomes single-element array
            array_list = [value]

        # since data_type is just a string. Return the list as-is.
        return array_list

    @staticmethod
    def _handle_map_value(column_name: str, data_type: str, value: Any, output_type: Any) -> Dict[Any, Any]:
        """Handle map values with key/value type validation."""
        if not isinstance(value, dict):
            raise ValueError(f"Map value must be a dictionary for column {column_name}")

        # For Python implementation, return the dict as-is since data_type is just a string
        return dict(value)

    @staticmethod
    def _handle_struct_value(column_name: str, data_type: str, value: Any, output_type: Any) -> Dict[str, Any]:
        """Handle struct values."""
        if isinstance(value, dict):
            return dict(value)
        elif isinstance(value, (list, tuple)):
            # Convert array/list to struct
            struct_dict = {}
            for i, field_value in enumerate(value):
                struct_dict[f"field_{i}"] = field_value
            return struct_dict
        else:
            raise ValueError(f"Struct value must be a dictionary or array for column {column_name}")

    @staticmethod
    def _handle_vector_value(data_type: str, value: Any) -> bytes:
        """Handle vector values."""
        # For Python implementation, since data_type is a string, we'll do basic conversion
        if isinstance(value, (list, tuple)):
            # Convert list to bytes - assume float32 for now
            return struct.pack(f'<{len(value)}f', *[float(x) for x in value])
        elif isinstance(value, bytes):
            return value
        else:
            raise ValueError(f"Unsupported vector value type: {type(value)}")

    def copy(self) -> IcebergRow:
        """Create a copy of this row."""
        new_row = IcebergRow(self._iceberg_schema, self._complex_type_pre_check, self._is_cz_bitmap_type)
        new_row._record_data = self._record_data.copy()
        return new_row

    def size(self) -> int:
        """Get the number of fields in the row."""
        return self._iceberg_schema.get_column_count()

    def to_dict(self) -> Dict[str, Any]:
        """Convert row to dictionary with column names as keys."""
        result = {}
        for index, value in self._record_data.items():
            field = self._iceberg_schema.get_column_by_index(index)
            result[field.name] = value
        return result

    def get_schema(self) -> IcebergSchema:
        """Get the schema for this row."""
        return self._iceberg_schema

    def __repr__(self) -> str:
        """String representation."""
        return f"IcebergRow({self.to_dict()})"
