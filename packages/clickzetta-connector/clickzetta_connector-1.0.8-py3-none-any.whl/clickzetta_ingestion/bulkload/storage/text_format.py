from typing import Any, Callable, Union

from clickzetta_ingestion.bulkload.storage import FormatOptions
from clickzetta_ingestion.bulkload.storage.file_options import FormatInterface
from clickzetta_ingestion.bulkload.storage.storage_writer import StorageWriter
from clickzetta_ingestion.common.row import Row


class TextRow(Row):
    """Represents a text row for bulk loading."""

    def set_value(self, column_name_or_index: Union[str, int], value: Any) -> None:
        if isinstance(value, str):
            self.data = value
        else:
            raise TypeError("TextRow only supports string values.")

    def __init__(self, data: str = ""):
        self.data = data

    def set_text(self, text: str):
        """Set the text content."""
        self.data = text

    def get_text(self) -> str:
        """Get the text content."""
        return self.data

    def to_string(self) -> str:
        """Convert to string representation."""
        return self.data


class TextStorageWriter(StorageWriter[TextRow]):
    """Storage writer for text format."""

    def get_pos(self) -> int:
        pass

    def flush(self):
        pass

    def __init__(self, path: str):
        super().__init__()
        self._path = path
        self._file = open(path, "w", encoding="utf-8")
        self._bytes_written = 0

    def get_path(self) -> str:
        return self._path

    def write(self, record: TextRow):
        """Write a text record."""
        line = record.to_string() + "\n"
        self._file.write(line)
        self._bytes_written += len(line.encode('utf-8'))

    def close(self, wait_time_ms: int = 0):
        """Close the writer."""
        if self._file:
            self._file.close()

    def get_bytes_written(self) -> int:
        """Get total bytes written."""
        return self._bytes_written


class TextStorageWriterFactory(StorageWriter.Factory):
    """Factory for creating text storage writers."""

    def create(self, path: str) -> StorageWriter[TextRow]:
        """Create a text storage writer."""
        return TextStorageWriter(path)


class TextFormat(FormatInterface[TextRow]):
    """Text format implementation."""

    def __init__(self, table_format):
        self._table_format = table_format
        self._callable_func = None

    def get_storage_writer_factory_function(self) -> Callable[[FormatOptions], StorageWriter.Factory]:
        """Get storage writer factory function."""
        return lambda options: TextStorageWriterFactory()

    def init_input_format(self, callable_func: Callable[[TextRow], TextRow]) -> 'FormatInterface[TextRow]':
        """Initialize input format with transformation function."""
        self._callable_func = callable_func
        return self

    def get_target_row(self) -> TextRow:
        """Get target row instance."""
        return TextRow()
