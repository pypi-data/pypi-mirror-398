from __future__ import annotations

import logging
import os
import threading
from typing import Callable, Dict, Any
from typing import List, Union

import pyarrow as pa
import pyarrow.parquet as pq

from clickzetta_ingestion.bulkload.bulkload_context import FieldSchema
from clickzetta_ingestion.bulkload.storage.file_options import FormatInterface
from clickzetta_ingestion.bulkload.storage.file_options import FormatOptions
from clickzetta_ingestion.bulkload.storage.iceberg_schema import IcebergSchema, ParquetSchemaConverter
from clickzetta_ingestion.bulkload.storage.storage_row import IcebergRow
from clickzetta_ingestion.bulkload.storage.storage_writer import StorageWriter
from clickzetta_ingestion.bulkload.table_parser import BulkLoadTable

logger = logging.getLogger(__name__)


class IcebergParquetFormat(FormatInterface[IcebergRow]):
    """
    Implements StorageHandler.Format for Iceberg Parquet data.
    """

    def __init__(self, table_format: 'BulkLoadTable', complex_type_pre_check: bool = True,
                 cz_bitmap_type_check: bool = True):
        """
        Initialize IcebergParquetFormat.

        Args:
            table_format: Table format information (BulkLoadTable)
            complex_type_pre_check: Whether to perform complex type validation
            cz_bitmap_type_check: Whether to support ClickZetta bitmap types
        """
        # Convert table schema to Iceberg schema
        self._original_field_schemas: List[FieldSchema] = table_format.get_table_schema()
        self._iceberg_schema: IcebergSchema = ParquetSchemaConverter.convert_to_iceberg_schema(
            self._original_field_schemas
        )
        self._table_format: BulkLoadTable = table_format  # Store for static partition handling
        self._complex_type_pre_check = complex_type_pre_check
        self._is_cz_bitmap_type = cz_bitmap_type_check

        # Default callable (identity function)
        self._callable: Callable[[IcebergRow], IcebergRow] = lambda record: record

    def init_input_format(self, callable_func: Callable[[IcebergRow], IcebergRow]):
        """
        Initialize input format with transformation function.

        Args:
            callable_func: Transformation function for records

        Returns:
            Self for method chaining
        """
        if callable_func is None:
            raise ValueError("Callable function cannot be None")
        self._callable = callable_func
        return self

    def get_storage_writer_factory_function(self) -> Callable[[FormatOptions], ParquetWriterFactory]:
        """
        Get storage writer factory function.

        Returns:
            Function that takes FormatOptions and returns StorageWriter.Factory
        """

        def create_parquet_factory(format_options) -> ParquetWriterFactory:
            """
            Create Parquet factory function.
            """

            def parquet_builder_func(output_file_path: str, format_properties):
                """
                Create Parquet file appender with Iceberg configuration.
                """
                # Create IcebergParquetFileAppender with file path
                return IcebergParquetFileAppender(
                    output_file=output_file_path,
                    schema=self._iceberg_schema.get_schema(),
                    compression=format_properties.get('compression', 'zstd'),
                    compression_level=int(format_properties.get('compression_level', 1)),
                    properties=format_properties,
                    iceberg_schema=self._iceberg_schema
                )

            # Create ParquetBuilder with the builder function
            parquet_builder = ParquetBuilder(parquet_builder_func)

            return ParquetWriterFactory(format_options, parquet_builder)

        return create_parquet_factory

    def get_target_row(self) -> IcebergRow:
        """
        Get target row instance.

        Returns:
            IcebergRow instance with applied transformations
        """
        record = IcebergRow(self._iceberg_schema, self._complex_type_pre_check, self._is_cz_bitmap_type)
        return self._callable(record)

    def get_iceberg_schema(self) -> IcebergSchema:
        """Get the Iceberg schema."""
        return self._iceberg_schema

    def is_complex_type_pre_check_enabled(self) -> bool:
        """Check if complex type pre-check is enabled."""
        return self._complex_type_pre_check

    def is_cz_bitmap_type_enabled(self) -> bool:
        """Check if ClickZetta bitmap type support is enabled."""
        return self._is_cz_bitmap_type


class IcebergParquetFileAppender:
    """
    File appender for Iceberg Parquet format that writes directly to file path.
    """

    def __init__(self, output_file: str, schema: pa.Schema, compression: str = 'zstd',
                 compression_level: int = 1, properties: Dict[str, Any] = None,
                 iceberg_schema: IcebergSchema = None):
        """
        Initialize file appender.

        Args:
            output_file: Path to output file
            schema: PyArrow schema
            compression: Compression algorithm
            compression_level: Compression level
            properties: Additional properties
            iceberg_schema: IcebergSchema instance
        """
        self.output_file = output_file
        self.schema = schema
        self.compression = compression
        self.compression_level = compression_level
        self.properties = properties or {}
        self.iceberg_schema = iceberg_schema
        self._closed = False
        self._records_written = 0
        self._bytes_written = 0  # Track total bytes written
        self._parquet_writer = None

        # PyArrow components
        self._record_batch_buffer = {}
        self._current_batch_rows = 0
        self._batch_size = 1000  # Records per batch

        # Thread safety: protect ParquetWriter access (PyArrow is not thread-safe)
        self._writer_lock = threading.RLock()

        # Create PyArrow schema from Iceberg schema
        self._pyarrow_schema = self._create_pyarrow_schema()
        # Create directory if needed
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        logger.info("Initializing PyArrow Parquet writer for {} with compression={}".format(
            self.output_file, self.compression))

    def _create_pyarrow_schema(self) -> pa.Schema:
        """
        Create PyArrow schema from Iceberg schema.
        """
        try:
            if self.iceberg_schema:
                # Use IcebergSchema to get PyArrow schema directly
                return self.iceberg_schema.get_schema()
            elif isinstance(self.schema, pa.Schema):
                # Use schema directly if it's already a PyArrow schema
                return self.schema
            elif isinstance(self.schema, dict) and 'fields' in self.schema:
                # Fallback: create schema from dict if available
                fields = []
                for field_info in self.schema['fields']:
                    field_name = field_info.get('name')
                    field_type = field_info.get('type', pa.string())
                    nullable = field_info.get('nullable', True)
                    fields.append(pa.field(field_name, field_type, nullable))
                return pa.schema(fields)
            else:
                raise ValueError("No valid schema available to create PyArrow schema")

        except Exception as e:
            logger.error("Error creating PyArrow schema: {}".format(e))
            raise

    def add(self, record: Union[IcebergRow | Dict[str, Any]]):
        """
        Add a record to the Parquet file.

        Args:
            record: IcebergRow or Record to write
        """
        with self._writer_lock:
            if self._closed:
                raise RuntimeError("File appender is closed")

            try:
                # Initialize record batch if needed
                if not self._record_batch_buffer:
                    self._construct_new_record_batch()

                # Convert IcebergRow to batch format
                row_data = record.to_dict() if hasattr(record, 'to_dict') else record

                # Add to batch buffer
                for column_name, value in row_data.items():
                    if column_name in self._record_batch_buffer:
                        self._record_batch_buffer[column_name].append(value)

                # Fill missing columns with None
                for column_name in self._record_batch_buffer:
                    if column_name not in row_data:
                        self._record_batch_buffer[column_name].append(None)

                self._current_batch_rows += 1
                self._records_written += 1

                # Flush batch if it's full
                # Note: _flush_record_batch also acquires the lock, but RLock allows reentrant locking
                if self._current_batch_rows >= self._batch_size:
                    self._flush_record_batch()

            except Exception as e:
                logger.error("Error adding record to Parquet file: {}".format(e))
                raise

    def _construct_new_record_batch(self):
        """
        Construct new record batch buffer with empty value.
        """
        self._record_batch_buffer.clear()

        if self.iceberg_schema:
            # Use Iceberg schema
            for i in range(self.iceberg_schema.get_column_count()):
                field = self.iceberg_schema.get_column_by_index(i)
                self._record_batch_buffer[field.name] = []
        elif self._pyarrow_schema:
            # Use PyArrow schema
            for field in self._pyarrow_schema:
                self._record_batch_buffer[field.name] = []
        else:
            raise ValueError("No schema available to construct record batch")

        self._current_batch_rows = 0

    def _flush_record_batch(self) -> int:
        """
        Flush record batch to Parquet file.
        """
        with self._writer_lock:
            if self._current_batch_rows == 0:
                return 0

            try:
                # Convert batch data to PyArrow format
                batch_data = []
                for column_name in self._record_batch_buffer:
                    column_data = self._record_batch_buffer[column_name]
                    # Convert data using PyArrow's type casting
                    arrow_type = None
                    if self._pyarrow_schema:
                        for field in self._pyarrow_schema:
                            if field.name == column_name:
                                arrow_type = field.type
                                break

                    if arrow_type:
                        try:
                            # Special handling for bitmap/binary columns with BitMap64 data
                            if arrow_type == pa.binary() and column_data:
                                converted_data = []
                                for item in column_data:
                                    if item is None:
                                        converted_data.append(None)
                                    elif hasattr(item, 'serialize'):  # pyroaring.BitMap64
                                        converted_data.append(item.serialize())
                                    elif isinstance(item, bytes):
                                        converted_data.append(item)
                                    else:
                                        converted_data.append(str(item).encode('utf-8'))
                                batch_data.append(pa.array(converted_data, type=arrow_type))
                            # Special handling for MAP types - convert dict to list of (key, value) pairs
                            elif hasattr(pa.lib, 'MapType') and isinstance(arrow_type, pa.lib.MapType) and column_data:
                                converted_data = []
                                for item in column_data:
                                    if item is None:
                                        converted_data.append(None)
                                    elif isinstance(item, dict):
                                        converted_data.append(list(item.items()))
                                    else:
                                        converted_data.append(item)
                                batch_data.append(pa.array(converted_data, type=arrow_type))
                            else:
                                # Use PyArrow's compute.cast for other types
                                import pyarrow.compute as pc
                                batch_data.append(pc.cast(column_data, arrow_type))
                        except Exception as e:
                            logger.error(f"Failed to cast column {column_name} to type {arrow_type}: {e}")
                            raise ValueError(
                                f"Failed to cast column {column_name} to type {arrow_type} when flushing record batch")
                    else:
                        batch_data.append(pa.array(column_data))

                # Create record batch
                if self._pyarrow_schema:
                    batch = pa.record_batch(batch_data, schema=self._pyarrow_schema)
                else:
                    # Create schema on the fly
                    field_names = list(self._record_batch_buffer.keys())
                    batch = pa.record_batch(batch_data, names=field_names)

                # Write to Parquet file
                if self._parquet_writer is None:
                    # Create ParquetWriter lazily
                    self._parquet_writer = pq.ParquetWriter(
                        self.output_file,
                        self._pyarrow_schema or batch.schema,
                        compression=self.compression
                    )

                self._parquet_writer.write_batch(batch)

                # Clear batch
                self._current_batch_rows = 0
                self._record_batch_buffer.clear()

                # Update bytes written
                bytes_written = batch.get_total_buffer_size()
                self._bytes_written += bytes_written
                return bytes_written
            except Exception as e:
                logger.error("Error flushing record batch: {}".format(e))
                raise

    def close(self):
        """
        Close the file appender.
        """
        with self._writer_lock:
            if self._closed:
                return

            error = None
            try:
                # Flush any remaining records
                # Note: flush() calls _flush_record_batch which also acquires the lock
                # RLock allows reentrant locking
                if self._current_batch_rows > 0:
                    self.flush()
            except Exception as e:
                logger.error("Error closing Parquet file appender: {}".format(e))
                error = e

            try:
                # Close PyArrow ParquetWriter
                if self._parquet_writer:
                    self._parquet_writer.close()
                    self._parquet_writer = None
                logger.info("Closed Parquet writer for {}, total records written: {}".format(
                    self.output_file, self._records_written))
            except Exception as e:
                logger.error("Error closing Parquet writer: {}".format(e))
                error = e

            self._closed = True

            if error:
                raise error

    def flush(self) -> int:
        """Flush any pending data."""
        if self._current_batch_rows > 0:
            return self._flush_record_batch()
        return 0

    def get_records_written(self) -> int:
        """Get the number of records written."""
        return self._records_written
    
    def get_pos(self) -> int:
        """
        Get current position (total bytes written so far).
        
        Returns:
            Total bytes written to the file
        """
        return self._bytes_written


class ParquetBuilder:
    """
    Builder interface for creating Parquet file writers.
    """

    def __init__(self, create_writer_func: Callable):
        """
        Initialize ParquetBuilder.

        Args:
            create_writer_func: Function to create writer
        """
        self._create_writer_func = create_writer_func

    def create_writer(self, output_file_path: str, format_properties: Dict[str, Any]) -> Any:
        """
        Create a writer for the given output file path.

        Args:
            output_file_path: Path to output file
            format_properties: Format-specific properties

        Returns:
            File appender instance
        """
        return self._create_writer_func(output_file_path, format_properties)


class ParquetWriterFactory(StorageWriter.Factory):
    """
    Factory for creating Parquet storage writers.
    """

    def __init__(self, format_options: FormatOptions, writer_builder: ParquetBuilder):
        """
        Initialize ParquetWriterFactory.

        Args:
            format_options: Format options for the writer
            writer_builder: Builder for creating Parquet writers
        """
        self._format_options = format_options
        self._writer_builder = writer_builder

    def create(self, path: str) -> StorageWriter[IcebergRow]:
        """
        Create a storage writer.

        Args:
            path: Output file path
            out: Unused parameter (kept for compatibility)

        Returns:
            StorageWriter instance
        """
        try:
            # Get format properties from options
            format_properties = {}
            if self._format_options:
                configure = self._format_options.format_configure()
                format_properties = configure.get_properties()

            file_appender = self._writer_builder.create_writer(path, format_properties)

            return ParquetStorageWriter(file_appender, path)

        except Exception as e:
            logger.error(f"Error creating Parquet storage writer for path {path}: {e}")
            raise


class ParquetStorageWriter(StorageWriter):
    """
    Storage writer implementation for Parquet format.
    """

    def __init__(self, file_appender: Any, file_path: str):
        """
        Initialize Parquet storage writer.

        Args:
            file_appender: File appender for writing
            file_path: Path to the output file
        """
        if file_appender is None:
            raise ValueError("file_appender cannot be None")

        self._file_appender = file_appender
        self._file_path = file_path
        self._closed = False

    def write(self, element: Any):
        """
        Write an element to the Parquet file.

        Args:
            element: Element to write
        """
        if self._closed:
            raise RuntimeError("Writer is closed")

        # Add element to file appender
        if hasattr(self._file_appender, "add"):
            self._file_appender.add(element)
        else:
            raise RuntimeError(f"Current file appender {self._file_appender} does not support 'add' method")

    def close(self, wait_time_ms: int = 0):
        """
        Close the writer.

        Args:
            wait_time_ms: Wait time in milliseconds (for compatibility)
        """
        if self._closed:
            return

        try:
            self._file_appender.close()
        except Exception as e:
            logger.error(f"Error closing file appender: {e}")
            raise
        finally:
            self._closed = True

    def flush(self) -> int:
        """Flush the writer."""
        return self._file_appender.flush()

    def get_pos(self) -> int:
        """Get current position (total bytes written)."""
        return self._file_appender.get_pos()

    @property
    def is_closed(self) -> bool:
        """Check if writer is closed."""
        return self._closed
