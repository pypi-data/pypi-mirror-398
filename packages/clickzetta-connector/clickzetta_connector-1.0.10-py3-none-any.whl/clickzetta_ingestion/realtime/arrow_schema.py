import threading
from typing import List, Dict, Set, Optional
import pyarrow as pa

from clickzetta_ingestion._proto import data_type_pb2


class ArrowSchema:

    def __init__(self, original_types: List[data_type_pb2.DataType],
                 fields: List[pa.Field], key_fields_index: Set[int]):
        """Initialize ArrowSchema
        
        Args:
            original_types: Original protobuf DataType list
            fields: PyArrow field list
            key_fields_index: Set of indices for key fields (primary/sort/cluster/partition keys)
        """
        if len(original_types) != len(fields):
            raise ValueError("Original types and fields must have same length")

        # Key columns (primary/sort/cluster/partition keys)
        self.key_columns_index: Set[int] = set(key_fields_index)
        self._lock = threading.Lock()

        # Column mappings
        self.columns_by_index: List[pa.Field] = []
        self.columns_by_name: Dict[str, int] = {}
        self.columns_by_name_case: Dict[str, int] = {}  # Case-insensitive lookup
        self.column_types_by_index: Dict[int, pa.DataType] = {}

        # Original protobuf types
        self.column_original_types_by_index: Dict[int, data_type_pb2.DataType] = {}

        # Store original types
        for idx, data_type in enumerate(original_types):
            self.column_original_types_by_index[idx] = data_type

        # Process fields
        for idx, field in enumerate(fields):
            self.columns_by_index.append(field)

            # Check for duplicate names
            if field.name in self.columns_by_name:
                raise ValueError(f"Column names must be unique: {field.name}")

            self.columns_by_name[field.name] = idx
            self.columns_by_name_case[field.name.lower()] = idx
            self.columns_by_name_case[field.name.upper()] = idx
            self.column_types_by_index[idx] = field.type

        self.schema = pa.schema(fields)
        self.row_size = len(self.schema.serialize())

    def apply_new_arrow_schema(self, new_arrow_schema: 'ArrowSchema'):
        """Apply a new schema, replacing current one"""
        with self._lock:
            self.key_columns_index = new_arrow_schema.key_columns_index
            self.columns_by_index = new_arrow_schema.columns_by_index
            self.columns_by_name = new_arrow_schema.columns_by_name
            self.column_types_by_index = new_arrow_schema.column_types_by_index
            self.columns_by_name_case = new_arrow_schema.columns_by_name_case
            self.schema = new_arrow_schema.schema
            self.row_size = new_arrow_schema.row_size
            self.column_original_types_by_index = new_arrow_schema.column_original_types_by_index

    def get_schema(self) -> pa.Schema:
        """Get PyArrow schema"""
        return self.schema

    def get_row_size(self) -> int:
        """Get serialized schema size"""
        return self.row_size

    def get_columns(self) -> List[pa.Field]:
        """Get list of all columns"""
        return list(self.columns_by_index)

    def has_column(self, column_name: str) -> bool:
        """Check if column exists"""
        return column_name in self.columns_by_name

    def get_column_index(self, column_name: str) -> int:
        """Get column index by name (case-insensitive)"""
        index = self.columns_by_name.get(column_name)
        if index is None:
            # Try case-insensitive lookup
            index = (self.columns_by_name_case.get(column_name.lower()) or
                     self.columns_by_name_case.get(column_name.upper()))

        if index is None:
            raise ValueError(f"Unknown column: {column_name}")

        return index

    def get_column_by_index(self, idx: int) -> Optional[pa.Field]:
        """Get column field by index"""
        return self.columns_by_index[idx]

    def get_column_original_type_by_index(self, idx: int) -> Optional[data_type_pb2.DataType]:
        """Get original protobuf DataType by index"""
        return self.column_original_types_by_index.get(idx)

    def get_column(self, column_name: str) -> pa.Field:
        """Get column field by name"""
        return self.columns_by_index[self.get_column_index(column_name)]

    def get_column_count(self) -> int:
        """Get total number of columns"""
        return len(self.columns_by_index)

    def get_column_types_by_index(self, idx: int) -> pa.DataType:
        """Get mapping of column index to type"""
        return self.column_types_by_index[idx]

    def get_key_columns_index(self) -> Set[int]:
        """Get indices of key columns"""
        return self.key_columns_index

    def __str__(self) -> str:
        return (f"ArrowSchema("
                f"key_columns_index={self.key_columns_index}, "
                f"columns_by_index={self.columns_by_index}, "
                f"columns_by_name={self.columns_by_name}, "
                f"column_types_by_index={self.column_types_by_index}, "
                f"columns_by_name_case={self.columns_by_name_case}, "
                f"schema={self.schema}, "
                f"row_size={self.row_size}, "
                f"column_original_types_by_index={self.column_original_types_by_index})")
