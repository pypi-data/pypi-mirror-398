import csv
from typing import Dict, Any, List, Callable

from clickzetta_ingestion.bulkload.storage.file_options import FormatInterface, FormatOptions
from clickzetta_ingestion.bulkload.storage.storage_writer import StorageWriter


class CsvRow:
    def __init__(self, column_names: List[str], data: Dict[str, Any] = None):
        self.column_names = column_names
        self.data = data or {}

    def set(self, column_name: str, value: Any):
        self.data[column_name] = value

    def get(self, column_name: str) -> Any:
        return self.data.get(column_name)

    def to_list(self) -> List[Any]:
        return [self.data.get(col, None) for col in self.column_names]


class CsvStorageWriter(StorageWriter[CsvRow]):
    def get_pos(self) -> int:
        pass

    def flush(self):
        pass

    def __init__(self, path: str, column_names: List[str]):
        super().__init__()
        self._path = path
        self._column_names = column_names
        self._file = open(path, "w", encoding="utf-8", newline='')
        self._writer = csv.writer(self._file)
        self._bytes_written = 0

        # Write header
        header_row = ','.join(self._column_names) + '\n'
        self._file.write(header_row)
        self._bytes_written += len(header_row.encode('utf-8'))

    def write(self, record: CsvRow):
        row_data = record.to_list()
        self._writer.writerow(row_data)
        self._bytes_written += len(','.join(str(v) if v is not None else '' for v in row_data).encode('utf-8')) + 1

    def close(self, wait_time_ms: int = 0):
        if self._file:
            self._file.close()
            self._file = None

    def get_bytes_written(self) -> int:
        return self._bytes_written

    def get_path(self) -> str:
        return self._path


class CsvStorageWriterFactory(StorageWriter.Factory):
    def __init__(self, column_names: List[str]):
        self.column_names = column_names

    def create(self, path: str, output_stream: Any = None) -> StorageWriter[CsvRow]:
        return CsvStorageWriter(path, self.column_names)


class CsvFormat(FormatInterface[CsvRow]):
    def __init__(self, table_format):
        self._table_format = table_format
        # Extract column names from table format (simplified)
        self.column_names = getattr(table_format, 'column_names', [])
        self._callable_func = None

    def get_storage_writer_factory_function(self) -> Callable[[FormatOptions], StorageWriter.Factory]:
        def factory_function(format_options: FormatOptions) -> StorageWriter.Factory:
            return CsvStorageWriterFactory(self.column_names)

        return factory_function

    def init_input_t_format(self, callable_func: Callable[[CsvRow], CsvRow]) -> 'FormatInterface[CsvRow]':
        self._callable_func = callable_func
        return self

    def init_input_format(self, callable_func: Callable[[CsvRow], CsvRow]) -> 'FormatInterface[CsvRow]':
        """Initialize input format with transformation function."""
        return self.init_input_t_format(callable_func)

    def get_target_row(self) -> CsvRow:
        row = CsvRow(self.column_names)
        if self._callable_func:
            return self._callable_func(row)
        return row
