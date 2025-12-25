import json
from typing import Dict, Any, Callable, Union

from clickzetta_ingestion.bulkload.storage.file_options import FormatInterface, FormatOptions
from clickzetta_ingestion.bulkload.storage.storage_writer import StorageWriter
from clickzetta_ingestion.common.row import Row

class JsonRow(Row):
    def set_value(self, column_name_or_index: Union[str, int], value: Any) -> None:
        if isinstance(column_name_or_index, str):
            self.data[column_name_or_index] = value
        elif isinstance(column_name_or_index, int):
            raise NotImplementedError("Setting value by index is not supported in JsonRow.")
        else:
            raise TypeError("column_name_or_index must be a string or an integer.")

    def __init__(self, data: Dict[str, Any] = None):
        self.data = data or {}
    
    def set(self, key: str, value: Any):
        self.data[key] = value
    
    def get(self, key: str) -> Any:
        return self.data.get(key)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.data


class JsonStorageWriter(StorageWriter[JsonRow]):
    def get_pos(self) -> int:
        pass

    def flush(self):
        pass

    def __init__(self, path: str):
        super().__init__()
        self._path = path
        self._file = open(path, "w", encoding="utf-8")
        self._bytes_written = 0

    def write(self, record: JsonRow):
        line = json.dumps(record.to_dict(), ensure_ascii=False) + "\n"
        self._file.write(line)
        self._bytes_written += len(line.encode('utf-8'))

    def close(self, wait_time_ms: int = 0):
        if self._file:
            self._file.close()
            self._file = None

    def get_bytes_written(self) -> int:
        return self._bytes_written

    def get_path(self) -> str:
        return self._path


class JsonStorageWriterFactory(StorageWriter.Factory):
    def create(self, path: str) -> StorageWriter[JsonRow]:
        return JsonStorageWriter(path)


class JsonFormat(FormatInterface[JsonRow]):
    def __init__(self, table_format):
        self._table_format = table_format
        self._callable_func = None

    def get_storage_writer_factory_function(self) -> Callable[[FormatOptions], StorageWriter.Factory]:
        def factory_function(format_options: FormatOptions) -> StorageWriter.Factory:
            return JsonStorageWriterFactory()
        return factory_function
    
    def init_input_t_format(self, callable_func: Callable[[JsonRow], JsonRow]) -> 'FormatInterface[JsonRow]':
        """Initialize input format with transformation function."""
        self._callable_func = callable_func
        return self
    
    def init_input_format(self, callable_func: Callable[[JsonRow], JsonRow]) -> 'FormatInterface[JsonRow]':
        """Initialize input format with transformation function."""
        return self.init_input_t_format(callable_func)

    def get_target_row(self) -> JsonRow:
        row = JsonRow()
        if self._callable_func:
            return self._callable_func(row)
        return row
