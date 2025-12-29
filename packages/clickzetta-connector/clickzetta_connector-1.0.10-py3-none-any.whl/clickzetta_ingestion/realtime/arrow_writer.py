from __future__ import annotations

import decimal
import logging
from typing import List, Optional, Tuple

import numpy as np
import pyarrow as pa
from clickzetta.connector.v0.exceptions import CZException

from clickzetta_ingestion._proto import ingestion_pb2
from clickzetta_ingestion.realtime.arrow_row import ArrowRow
from clickzetta_ingestion.rpc.arrow_utils import get_default_value_by_type

log = logging.getLogger(__name__)


class ArrowFieldWriter:
    """Base class for field writers"""

    def __init__(self, vector: pa.Array, field: pa.Field):
        self.vector = vector
        self.values = []
        self.name = field.name
        self.nullable = field.nullable
        self.count = 0

    def set_null(self):
        """Set null value"""
        self.values.append(None)

    def set_default_value(self):
        """Set default value when not nullable"""
        try:
            default_value = get_default_value_by_type(self.vector.type)
            self.values.append(default_value)
        except ValueError as e:
            log.error(f"Failed to set default value for {self.name}: {e}")
            raise

    def set_value(self, row: ArrowRow, ordinal: int):
        """Set actual value"""
        value = row.columns.get(ordinal)
        self.values.append(value)

    def write(self, row: ArrowRow, ordinal: int, is_set: bool):
        """Write value using common logic"""
        try:
            if is_set:
                # Check nullable constraint. maybe set null or not null.
                if not self.nullable and row.is_null_at(ordinal):
                    raise ValueError(f"[ArrowFieldWriter.write] Column {self.name} is not nullable but got null value")

                if row.is_null_at(ordinal):
                    self.set_null()
                else:
                    self.set_value(row, ordinal)
            else:
                # Partial update
                if self.nullable:
                    self.set_null()
                else:
                    self.set_default_value()
            self.count += 1
        except Exception as e:
            log.error(f"Failed to write row {row} at ordinal {ordinal}: {e}")
            raise

    def finish(self):
        """Finish writing and validate"""
        self.vector = pa.array(self.values, type=self.vector.type)
        # Check count matches vector length
        if self.count != len(self.vector):
            raise ValueError(f"Count mismatch: wrote {self.count} rows but vector has {len(self.vector)}")

    def reset(self):
        """Reset writer state"""
        self.values.clear()
        self.count = 0


class StructWriter(ArrowFieldWriter):
    """Writer for struct type"""

    def __init__(self, vector: pa.StructArray, children: List[ArrowFieldWriter], field: pa.Field):
        super().__init__(vector, field)
        self.children = children
        self.field_names = [field.name for field in field.type] # like ["name", "age"]

    def set_null(self):
        """Set null for all children"""
        for child in self.children:
            child.set_null()
            child.count += 1

    def set_default_value(self):
        """Set default values for all children"""
        for child in self.children:
            child.set_default_value()
            child.count += 1

    def set_value(self, row: ArrowRow, ordinal: int):
        """Set struct value"""
        value = row.columns.get(ordinal)

        # Convert list/tuple to map if it matches field count
        if isinstance(value, (list, tuple)) and len(value) == len(self.field_names):
            value = dict(zip(self.field_names, value))

        # Write each child field
        for i, (field_name, child_writer) in enumerate(zip(self.field_names, self.children)):
            try:
                # Check if it's a namedtuple type
                if hasattr(value, '_fields') and isinstance(value._fields, tuple) and field_name in value._fields:
                    field_value = getattr(value, field_name)
                elif hasattr(value, 'get') and callable(value.get):
                    # Handle dictionary type
                    field_value = value.get(field_name)
                else:
                    raise ValueError(f"Cannot get field '{field_name}' from struct value of type {type(value)}")

                temp_row = ArrowRow(
                    arrow_table=row.arrow_table,
                    operation_type=row.operation_type,
                    complex_type_recheck=row.complex_type_recheck
                )
                temp_row.columns[0] = field_value
                temp_row.columns_bitset.add(0)
                child_writer.write(temp_row, 0, True)
            except Exception as e:
                log.error(f"Failed to write struct field {field_name}: {e}")
                raise

    def finish(self):
        """Finish writing struct"""
        for child in self.children:
            child.finish()

        # Create struct array using existing arrays without copying
        child_arrays = [child.vector for child in self.children]
        self.vector = pa.StructArray.from_arrays(child_arrays, self.field_names)

    def reset(self):
        """Reset struct writer"""
        super().reset()
        for child in self.children:
            child.reset()


class ListWriter(ArrowFieldWriter):
    """Writer for list type"""

    def __init__(self, vector: pa.ListArray, element_writer: ArrowFieldWriter, field: pa.Field):
        super().__init__(vector, field)
        self.element_writer = element_writer

    def set_null(self):
        """Set null list"""
        self.values.append(None)

    def set_default_value(self):
        """Set empty list"""
        self.values.append([])

    def set_value(self, row: ArrowRow, ordinal: int):
        """Set list value"""
        value = row.columns.get(ordinal)
        self.values.append(value)

    def finish(self):
        """Finish writing list"""
        self.element_writer.finish()
        self.vector = pa.array(self.values, type=pa.list_(self.element_writer.vector.type))

    def reset(self):
        """Reset list writer"""
        super().reset()
        self.element_writer.reset()


class MapWriter(ArrowFieldWriter):
    """Writer for map type"""

    def __init__(self, vector: pa.MapArray, key_writer: ArrowFieldWriter, value_writer: ArrowFieldWriter, field: pa.Field):
        super().__init__(vector, field)
        self.key_writer = key_writer
        self.value_writer = value_writer
        self.maps = []
        self.keys = []
        self.values = []

    def set_null(self):
        """Set null map"""
        self.maps.append(None)

    def set_default_value(self):
        """Set empty map"""
        self.maps.append({})

    def set_value(self, row: ArrowRow, ordinal: int):
        """Set map value"""
        value = row.columns.get(ordinal)
        self.maps.append(value)
        for k, v in value.items():
            self.keys.append(k)
            self.values.append(v)

    def finish(self):
        """Finish writing map"""
        self.key_writer.finish()
        self.value_writer.finish()

        offsets = []
        current_offset = 0
        for map_value in self.maps:
            if map_value is None:
                offsets.append(None)
            else:
                offsets.append(current_offset)
                current_offset += 1
        offsets.append(current_offset)

        self.vector = pa.MapArray.from_arrays(offsets, self.keys, self.values)

    def reset(self):
        """Reset map writer"""
        super().reset()
        self.maps.clear()
        self.keys.clear()
        self.values.clear()


class DecimalWriter(ArrowFieldWriter):
    """Writer for Decimal type data
    
    Handles conversion between Python Decimal and Arrow Decimal128 types
    with proper precision and scale handling.
    """

    def __init__(self, vector: pa.Decimal128Array, field: pa.Field):
        super().__init__(vector, field)
        self.precision = vector.type.precision
        self.scale = vector.type.scale
        self.empty_decimal = decimal.Decimal(0).quantize(
            decimal.Decimal('0.' + '0' * self.scale),
            rounding=decimal.ROUND_HALF_UP
        )

    def set_null(self):
        """Set null value"""
        self.values.append(None)

    def set_default_value(self):
        """Set default (zero) value with proper scale"""
        self.values.append(self.empty_decimal)

    def set_value(self, row: ArrowRow, ordinal: int):
        """Write a decimal value with proper precision and scale handling"""
        value = row.columns.get(ordinal)

        if value is None:
            self.set_null()
            return

        if not isinstance(value, decimal.Decimal):
            try:
                if isinstance(value, float):
                    value = decimal.Decimal(str(value))
                else:
                    value = decimal.Decimal(value)
            except (decimal.InvalidOperation, TypeError) as e:
                log.error(f"Failed to convert {value} to Decimal: {e}")
                raise ValueError(f"Cannot convert {type(value)} to Decimal: {value}")

        try:
            changed, adjusted_value = self._change_precision(value, self.precision, self.scale)
            if changed:
                self.values.append(adjusted_value)
            else:
                log.warning(f"Decimal value {value} exceeds precision {self.precision}. Using default value.")
                self.set_default_value()
        except Exception as e:
            log.error(f"Error adjusting decimal precision: {e}")
            raise

    def _change_precision(self, value: decimal.Decimal, precision: int, scale: int) \
            -> Tuple[bool, Optional[decimal.Decimal]]:
        """Change decimal precision and scale
        
        Args:
            value: The decimal value to adjust
            precision: Target precision
            scale: Target scale
            
        Returns:
            Tuple of (success, adjusted_value)
        """
        try:
            # Adjust the number of decimal places
            adjusted = value.quantize(
                decimal.Decimal('0.' + '0' * scale),
                rounding=decimal.ROUND_HALF_UP
            )

            # Check if the adjusted value exceeds the precision
            if adjusted.as_tuple().digits.__len__() > precision:
                log.warning(
                    f"Data precision {len(adjusted.as_tuple().digits)} > DecimalType precision {precision}. Cast Overflow.")
                return False, None

            return True, adjusted
        except decimal.InvalidOperation as e:
            log.error(f"Invalid operation when adjusting decimal: {e}")
            return False, None


class FixedSizeBinaryWriter(ArrowFieldWriter):
    """Writer for fixed size binary (vector) data"""

    def __init__(self, vector: pa.Array, field: pa.Field):
        super().__init__(vector, field)
        self.byte_width = vector.type.byte_width if "fixed_size_binary" in str(vector.type) else None
        self._empty_binary = None if self.byte_width is None else b'\0' * self.byte_width

    def set_null(self):
        """Set null value"""
        self.values.append(None)

    def set_default_value(self):
        """Set default (empty) value"""
        if self._empty_binary is None:
            raise RuntimeError("Byte width not initialized")
        self.values.append(self._empty_binary)

    def set_value(self, row: ArrowRow, ordinal: int):
        """Write a value to the array"""
        value = row.columns.get(ordinal)
        if value is None:
            self.set_null()
            return

        if isinstance(value, (list, tuple, np.ndarray)):
            value = np.array(value).tobytes()
        elif isinstance(value, bytes):
            value = value
        elif hasattr(value, "__str__"):
            value = str(value).encode('utf-8')
        else:
            raise ValueError(f"Unsupported value type for fixed size binary: {type(value)}")

        # Validate length
        if len(value) != self.byte_width:
            raise ValueError(
                f"Fixed size binary expected length {self.byte_width} but got {len(value)}"
            )

        self.values.append(value)

    def finish(self):
        """Finish writing and create array"""
        self.vector = pa.array(self.values, type=pa.binary(self.byte_width))


class ArrowRecordBatchWriter:
    """Writer for Arrow record batches"""

    def __init__(self, arrow_table, pooled=False, target_row_size: int = -1):
        from clickzetta_ingestion.realtime.arrow_table import ArrowTable
        from clickzetta_ingestion.realtime.arrow_schema import ArrowSchema
        self.arrow_table: ArrowTable = arrow_table
        self.arrow_schema: ArrowSchema = arrow_table.arrow_schema
        self.is_set_bit_maps = []  # BitSet list for each row
        self.operation_types = []
        self.count = 0
        self.pooled = pooled

        # Arrow schema and writers
        self.field_writers: List[ArrowFieldWriter] = []
        self._init_field_writers(target_row_size)

        # Compression options
        self.compression_type = None
        self.compression_level = None

    def _init_field_writers(self, initial_row_size: int):
        """Initialize field writers for each column"""
        try:
            self.field_writers = []
            for i in range(self.arrow_schema.get_column_count()):
                field: pa.Field = self.arrow_schema.get_column_by_index(i)
                empty_vector = self._create_empty_array(field.type)
                if initial_row_size != -1:
                    # TODO: implement pre-allocation if needed
                    pass
                self.field_writers.append(self._create_field_writer(empty_vector, field))
        except Exception as e:
            log.error(f"Failed to initialize field writers: {e}")
            self.close()
            raise e

    @staticmethod
    def _create_empty_array(field_type: pa.DataType) -> pa.Array:
        """Create empty array for field type"""
        return pa.array([], type=field_type)

    @classmethod
    def _create_field_writer(cls, vector, field: pa.Field) -> ArrowFieldWriter:
        """Create appropriate field writer based on type"""
        if isinstance(vector.type, pa.StructType):
            child_writers = [
                cls._create_field_writer(
                    pa.array([], type=t.type), field
                )
                for t in vector.type
            ]
            return StructWriter(vector, child_writers, field)
        elif isinstance(vector.type, pa.ListType):
            element_writer = cls._create_field_writer(
                pa.array([], type=vector.type.value_type), field
            )
            return ListWriter(vector, element_writer, field)
        elif isinstance(vector.type, pa.MapType):
            key_writer = cls._create_field_writer(
                pa.array([], type=vector.type.key_type), field
            )
            value_writer = cls._create_field_writer(
                pa.array([], type=vector.type.item_type), field
            )
            return MapWriter(vector, key_writer, value_writer, field)
        elif isinstance(vector.type, pa.Decimal128Type):
            return DecimalWriter(vector, field)
        elif "fixed_size_binary" in str(vector.type):
            # The Decimal is instance of pa.FixedSizeBinaryType too, so we need to check the string type
            vector = pa.array([], type=vector.type)
            return FixedSizeBinaryWriter(vector, field)
        else:
            return ArrowFieldWriter(vector, field)

    def set_compression(self, compression_type: Optional[str], compression_level: Optional[int]):
        """Set compression options"""
        self.compression_type = compression_type
        self.compression_level = compression_level

    def write(self, row: ArrowRow):
        """Write a row"""
        # Track operation type
        if self.arrow_table.igs_table_type != ingestion_pb2.IGSTableType.ACID:
            if not self.operation_types or self.operation_types[-1] != row.operation_type:
                self.operation_types.append(row.operation_type)
        else:
            self.operation_types.append(row.operation_type)

        # if some not key columns is not nullable. delete Op can not only encode with key row.
        # so all Ops will encode all columns.
        self.is_set_bit_maps.append(row.columns_bitset)

        # Write values
        for i, writer in enumerate(self.field_writers):
            # Check key columns
            if (i in self.arrow_schema.get_key_columns_index() and
                    i not in row.columns_bitset):
                raise ValueError(
                    f"primary|sort|cluster|partition key [{self.arrow_schema.get_column_by_index(i).name}"
                    "] must set value in row."
                )
            writer.write(row, i, i in row.columns_bitset)

        self.count += 1

    def finish(self):
        """Finish writing"""
        for writer in self.field_writers:
            writer.finish()

    def reset(self):
        """Reset writer state"""
        self.field_writers.clear()
        self.is_set_bit_maps.clear()
        self.operation_types.clear()
        self.count = 0

    def encode_is_set_bit_maps(self) -> bytes:
        """Encode is_set bitmaps as bytes"""
        num_columns = self.arrow_schema.get_column_count()
        bytes_per_row = (num_columns + 7) // 8
        result = bytearray(bytes_per_row * len(self.is_set_bit_maps))

        for row_index, bitset in enumerate(self.is_set_bit_maps):
            for col_index in bitset:
                byte_index = row_index * bytes_per_row + (col_index // 8)
                bit_index = col_index % 8
                result[byte_index] |= (1 << bit_index)

        return bytes(result)

    def encode_arrow_row(self) -> bytes:
        """Encode rows as Arrow format"""
        try:
            arrays = [writer.vector for writer in self.field_writers]
            batch = pa.RecordBatch.from_arrays(arrays, schema=self.arrow_schema.schema)

            # Configure compression
            options = {}
            if self.compression_type:
                options["compression"] = self.compression_type
                if self.compression_level is not None:
                    options["compression_level"] = self.compression_level

            # Write to buffer
            with pa.BufferOutputStream() as sink:
                with pa.RecordBatchStreamWriter(sink, self.arrow_schema.schema, options=options) as writer:
                    writer.write_batch(batch)
                return sink.getvalue().to_pybytes()
        except Exception as e:
            log.error(f"Failed to encode arrow row: {e}")
            raise CZException(f"Failed to encode arrow row: {e}")

    def get_row_count(self) -> int:
        """Get number of rows written"""
        return self.count

    def close(self):
        """Clean up resources"""
        pass
