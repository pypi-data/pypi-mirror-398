"""
File options for BulkLoad V2 storage operations.
"""
import threading
from abc import ABC, abstractmethod
import os
from enum import Enum
from typing import TypeVar, Generic, Callable, Any

from clickzetta_ingestion.bulkload.storage.load_options import LoadOptions
from clickzetta_ingestion.common.configure import Configure

T = TypeVar('T')
OutputT = TypeVar('OutputT')


class Format(Enum):
    """Supported file formats."""
    PARQUET = "PARQUET"
    JSON = "JSON"
    TEXT = "TEXT"
    CSV = "CSV"


class Location(Enum):
    """Enumeration of storage locations."""

    LOCAL = ("file://", "local.")
    OBJECT_STORE = ("objectstore://", "objectstore.")
    OBJECT_STORE_LOCAL = ("objectstore_local://", "objectstore_local.")

    def __init__(self, prefix: str, conf_prefix: str):
        """
        Initialize location.

        Args:
            prefix: URL prefix for this location type
            conf_prefix: Configuration prefix for this location type
        """
        self._prefix = prefix
        self._conf_prefix = conf_prefix

    @property
    def prefix(self) -> str:
        """Get the URL prefix."""
        return self._prefix

    @property
    def conf_prefix(self) -> str:
        """Get the configuration prefix."""
        return self._conf_prefix

    @classmethod
    def from_uri(cls, uri: str) -> 'Location':
        """
        Determine location type from URI.

        Args:
            uri: URI string

        Returns:
            Location enum value
        """
        uri_lower = uri.lower()
        for location in cls:
            if uri_lower.startswith(location.prefix.lower()):
                return location
        # Default to LOCAL if no prefix matches
        return cls.LOCAL


class FormatInterface(ABC, Generic[T]):
    """Base format interface for storage operations."""

    @abstractmethod
    def get_storage_writer_factory_function(self) -> Callable[[Any], Any]:
        """Get the storage writer factory function."""
        pass

    @abstractmethod
    def init_input_format(self, callable_func: Callable[[T], OutputT]) -> 'FormatInterface[OutputT]':
        """Initialize input format with a callable function."""
        pass

    @abstractmethod
    def get_target_row(self) -> T:
        """Get the target row for this format."""
        pass


class FormatOptions(ABC):
    """Abstract base class for format options."""

    @abstractmethod
    def format(self) -> Format:
        """Get the format type."""
        pass

    @abstractmethod
    def format_configure(self) -> Configure:
        """Get format-specific configuration."""
        pass

    @abstractmethod
    def file_options(self) -> "FileOptionsInterface":
        """Get file-specific options."""
        pass

    @staticmethod
    def build(partition_id: int, load_options: LoadOptions) -> 'FormatOptions':
        """
        Build appropriate FormatOptions based on format type.

        Args:
            partition_id: Partition identifier
            load_options: Load configuration options

        Returns:
            FormatOptions instance
        """
        format_str = load_options.get_format().name
        format_type = Format[format_str]

        if format_type == Format.PARQUET:
            return ParquetFormatOptions(partition_id, load_options)
        elif format_type == Format.JSON or format_type == Format.TEXT:
            return TextFormatOptions(partition_id, load_options)
        elif format_type == Format.CSV:
            return CsvFormatOptions(partition_id, load_options)
        else:
            raise ValueError(f"Unsupported format: {format_type}")


class FileOptionsInterface(ABC):
    """Abstract base class for file options."""

    @abstractmethod
    def uri(self) -> str:
        """Get the URI."""
        pass

    @abstractmethod
    def location(self) -> Location:
        """Get the storage location type."""
        pass

    @abstractmethod
    def base_path(self) -> str:
        """Get the base path for file operations."""
        pass

    @abstractmethod
    def partition_id(self) -> int:
        """Get the partition ID."""
        pass

    @abstractmethod
    def file_name_prefix(self) -> str:
        """Get the file name prefix."""
        pass

    @abstractmethod
    def max_file_size(self) -> int:
        """Get maximum file size in bytes."""
        pass

    @abstractmethod
    def max_row_count(self) -> int:
        """Get maximum row count per file."""
        pass

    @abstractmethod
    def file_configure(self) -> Configure:
        """Get file-specific configuration."""
        pass

    @abstractmethod
    def format_options(self) -> 'FormatOptions':
        """Get the associated format options."""
        pass

    @staticmethod
    def build(partition_id: int, load_options: LoadOptions, format_options: 'FormatOptions') -> 'FileOptionsInterface':
        """
        Build appropriate FileOptions based on location.
        
        Args:
            partition_id: Partition identifier
            load_options: Load configuration options
            format_options: Format options
            
        Returns:
            FileOptions instance
        """
        uri = load_options.get_uri()
        location = Location.from_uri(uri)

        if location == Location.LOCAL:
            return LocalFileOptions(partition_id, load_options, format_options)
        elif location == Location.OBJECT_STORE_LOCAL:
            return ObjectStoreLocalFileOptions(partition_id, load_options, format_options)
        elif location == Location.OBJECT_STORE:
            return ObjectStoreFileOptions(partition_id, load_options, format_options)
        else:
            raise ValueError(f"Unsupported location: {location}")


class AbstractFileOptions(FileOptionsInterface):
    """Abstract base implementation of FileOptions."""

    def location(self) -> Location:
        pass

    def base_path(self) -> str:
        pass

    # Default values
    DEFAULT_FILE_NAME_PREFIX = "part"
    DEFAULT_MAX_FILE_SIZE = 128 * 1024 * 1024  # 128MB
    DEFAULT_MAX_ROW_COUNT = 100000

    def __init__(self, partition_id: int, load_options: LoadOptions, format_options: 'FormatOptions'):
        """
        Initialize abstract file options.
        
        Args:
            partition_id: Partition identifier
            load_options: Load configuration options
            format_options: Format options
        """
        self._partition_id = partition_id
        self._load_options = load_options
        self._format_options = format_options
        self._file_configure = None
        self._lock = threading.RLock()

    def uri(self) -> str:
        """Get the URI."""
        return self._load_options.get_uri()

    def partition_id(self) -> int:
        """Get the partition ID."""
        return self._partition_id

    def file_name_prefix(self) -> str:
        """Get the file name prefix."""
        return self._load_options.get_file_name_prefix()

    def max_file_size(self) -> int:
        """Get maximum file size in bytes."""
        return int(self._load_options.get_max_file_size())

    def max_row_count(self) -> int:
        """Get maximum row count per file."""
        return int(self._load_options.get_max_row_count())

    def file_configure(self) -> Configure:
        """Get file-specific configuration."""
        # default file conf.
        if self._file_configure is None:
            with self._lock:
                if self._file_configure is None:
                    # Extract file-specific properties
                    prefix = self.location().conf_prefix
                    file_properties = {}

                    for key, value in self._load_options.get_properties().items():
                        if key.startswith(prefix):
                            file_properties[key] = value

                    self._file_configure = Configure(file_properties)

        return self._file_configure

    def format_options(self) -> 'FormatOptions':
        """Get the associated format options."""
        return self._format_options


class LocalFileOptions(AbstractFileOptions):
    """File options for local file system storage."""

    def location(self) -> Location:
        """Get the storage location type."""
        return Location.LOCAL

    def base_path(self) -> str:
        """Get the base path for file operations."""
        base_path = self.uri()
        prefix = Location.LOCAL.prefix.lower()

        if base_path.lower().startswith(prefix):
            base_path = base_path[len(prefix):]

        # Ensure path exists
        if base_path and not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)

        return base_path


class ObjectStoreFileOptions(AbstractFileOptions):
    """File options for object store storage."""

    def location(self) -> Location:
        """Get the storage location type."""
        return Location.OBJECT_STORE

    def base_path(self) -> str:
        """Get the base path for file operations."""
        base_path = self.uri()
        prefix = Location.OBJECT_STORE.prefix.lower()

        if base_path.lower().startswith(prefix):
            base_path = base_path[len(prefix):]

        return base_path


class ObjectStoreLocalFileOptions(AbstractFileOptions):
    """Object store File options for local object store storage."""

    def location(self) -> Location:
        """Get the storage location type."""
        return Location.OBJECT_STORE_LOCAL

    def base_path(self) -> str:
        """Get the base path for file operations."""
        base_path = self.uri()
        prefix = Location.OBJECT_STORE_LOCAL.prefix.lower()

        if base_path.lower().startswith(prefix):
            base_path = base_path[len(prefix):]

        # Ensure path exists for local object store
        if base_path and not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)

        return base_path


class AbstractFormatOptions(FormatOptions):
    """Abstract base implementation of FormatOptions."""

    def __init__(self, partition_id: int, load_options: LoadOptions):
        """
        Initialize abstract format options.

        Args:
            partition_id: Partition identifier
            load_options: Load configuration options
        """
        self._partition_id = partition_id
        self._load_options = load_options
        self._uri = load_options.get_uri()
        self._properties = load_options.get_properties()
        self._format_configure = None
        self._file_options = None

    def format(self) -> Format:
        """Get the format type."""
        return self._load_options.get_format()

    def format_configure(self) -> Configure:
        """Get format-specific configuration."""
        if self._format_configure is None:
            # Extract format-specific properties
            format_prefix = f"{self.format().name.lower()}."
            format_properties = {}

            for key, value in self._properties.items():
                if key.startswith(format_prefix):
                    new_key = key[len(format_prefix):]
                    format_properties[new_key] = value

            self._format_configure = Configure(format_properties)

        return self._format_configure

    def file_options(self) -> "FileOptionsInterface":
        """Get file-specific options."""
        if self._file_options is None:
            self._file_options = FileOptionsInterface.build(self._partition_id, self._load_options, self)
        return self._file_options


class ParquetFormatOptions(AbstractFormatOptions):
    """Parquet format specific options."""

    COMPRESSION = "compression"
    COMPRESSION_LEVEL = "compression_level"
    ROW_GROUP_SIZE = "row_group_size"

    def get_compression(self) -> str:
        """Get compression algorithm."""
        return self._properties.get(f"parquet.{self.COMPRESSION}", "zstd")

    def get_compression_level(self) -> int:
        """Get compression level."""
        return int(self._properties.get(f"parquet.{self.COMPRESSION_LEVEL}", 1))

    def get_row_group_size(self) -> int:
        """Get row group size in bytes."""
        return int(self._properties.get(f"parquet.{self.ROW_GROUP_SIZE}", 128 * 1024 * 1024))


class CsvFormatOptions(AbstractFormatOptions):
    """CSV format specific options."""

    FIELD_DELIMITER = "field.delimiter"
    QUOTE_CHARACTER = "quote.character"
    ESCAPE_CHARACTER = "escape.character"
    NULL_LITERAL = "null.literal"
    CHARSET = "charset"

    def get_field_delimiter(self) -> str:
        """Get field delimiter."""
        return self._properties.get(f"csv.{self.FIELD_DELIMITER}", ",")

    def get_quote_character(self) -> str:
        """Get quote character."""
        return self._properties.get(f"csv.{self.QUOTE_CHARACTER}", '"')

    def get_escape_character(self) -> str:
        """Get escape character."""
        return self._properties.get(f"csv.{self.ESCAPE_CHARACTER}", "\\")

    def get_null_literal(self) -> str:
        """Get null literal."""
        return self._properties.get(f"csv.{self.NULL_LITERAL}", "")

    def get_charset(self) -> str:
        """Get charset."""
        return self._properties.get(f"csv.{self.CHARSET}", "UTF-8")


class JsonFormatOptions(AbstractFormatOptions):
    """JSON format specific options."""

    CHARSET = "charset"
    PRETTY_PRINT = "pretty_print"

    def get_charset(self) -> str:
        """Get charset."""
        return self._properties.get(f"json.{self.CHARSET}", "UTF-8")

    def is_pretty_print(self) -> bool:
        """Check if pretty print is enabled."""
        return bool(self._properties.get(f"json.{self.PRETTY_PRINT}", False))


class TextFormatOptions(AbstractFormatOptions):
    """Text format specific options."""

    CHARSET = "charset"
    LINE_DELIMITER = "line.delimiter"

    def get_charset(self) -> str:
        """Get charset."""
        return self._properties.get(f"text.{self.CHARSET}", "UTF-8")

    def get_line_delimiter(self) -> str:
        """Get line delimiter."""
        return self._properties.get(f"text.{self.LINE_DELIMITER}", "\n")
