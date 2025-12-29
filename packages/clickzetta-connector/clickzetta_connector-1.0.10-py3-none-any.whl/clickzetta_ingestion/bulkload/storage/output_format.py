"""
Output format interfaces and implementations for BulkLoad V2.
"""
import logging
import os
import threading
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Dict, Any, Optional, Callable

from clickzetta_ingestion.bulkload.storage.file_options import FormatOptions
from clickzetta_ingestion.bulkload.storage.load_options import LoadOptions
from clickzetta_ingestion.bulkload.storage.storage_writer import StorageWriter

logger = logging.getLogger(__name__)

InputT = TypeVar('InputT')
CommT = TypeVar('CommT')


class Stats:
    """Statistics for output format."""

    def __init__(self):
        self._total_count = 0
        self._total_size = 0

    def total_count(self) -> int:
        """Get total record count."""
        return self._total_count

    def total_size(self) -> int:
        """Get total size in bytes."""
        return self._total_size

    def update(self, count: int = 0, size: int = 0):
        """Update statistics."""
        self._total_count += count
        self._total_size += size

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'rows_written': self._total_count,
            'bytes_written': self._total_size,
            'files_written': 0  # Will be tracked separately
        }


class FileConf:
    """File configuration interfaces."""

    class Request:
        """Request for next file configuration."""

        def __init__(self, partition: int, uri: str, base_path: str,
                     prefix: str, format_name: str):
            self._partition = partition
            self._uri = uri
            self._base_path = base_path
            self._prefix = prefix
            self._format = format_name

        def partition(self) -> int:
            return self._partition

        def uri(self) -> str:
            return self._uri

        def base_path(self) -> str:
            return self._base_path

        def prefix(self) -> str:
            return self._prefix

        def format(self) -> str:
            return self._format

    class Response(Generic[CommT]):
        """Response with file configuration."""

        def __init__(self, path: str, file_properties: Dict[str, Any],
                     committable_obj: Optional[CommT] = None):
            self._path = path
            self._file_properties = file_properties or {}
            self._committable = committable_obj

        def path(self) -> str:
            return self._path

        def file_properties(self) -> Dict[str, Any]:
            return self._file_properties

        def committable(self) -> Optional[CommT]:
            return self._committable


class OutputFormat(ABC, Generic[InputT]):
    """Abstract base class for output formats."""

    @abstractmethod
    def open(self):
        """Open the output format."""
        pass

    @abstractmethod
    def write(self, obj: InputT):
        """Write an object."""
        pass

    @abstractmethod
    def flush(self):
        """Flush pending writes."""
        pass

    @abstractmethod
    def stats(self) -> Stats:
        """Get statistics."""
        pass

    @abstractmethod
    def close(self):
        """Close the output format."""
        pass


class Splittable(ABC):
    """Interface for splittable output formats."""

    @abstractmethod
    def should_split(self) -> bool:
        """Check if should split to new file."""
        pass

    @abstractmethod
    def split_to_new_file(self):
        """Split to a new file."""
        pass


class SplitOutputFormat(OutputFormat[InputT], Splittable, Generic[InputT]):
    """
    Output format that supports splitting into multiple files.
    """

    def __init__(self, partition_id: int, load_options: LoadOptions,
                 storage_writer_factory_function: Callable[[FormatOptions], StorageWriter.Factory]):
        """
        Initialize split output format.
        
        Args:
            partition_id: Partition identifier
            load_options: Load configuration options
            storage_writer_factory_function: Function to create storage writer factory
        """
        self.partition_id = partition_id
        self.load_options = load_options
        self.storage_writer_factory_function = storage_writer_factory_function

        # Format options and factories
        self.format_options: Optional[FormatOptions] = None
        self.storage_writer_factory: Optional[StorageWriter.Factory] = None

        # Current writer and file path
        self.storage_writer: Optional[StorageWriter] = None
        self.current_file_path: Optional[str] = None

        # Current file statistics
        self.current_lines = 0
        self.current_size = 0

        # Total statistics
        self._stats = Stats()
        self.total_lines = 0
        self.last_total_size = 0
        self.total_size = 0

        # Control flags
        self.mark_next_to_new_file = True

        # Thread safety
        self.lock = threading.RLock()

    def open(self):
        """Open the output format."""
        # Build format options
        self.format_options = FormatOptions.build(self.partition_id, self.load_options)

        # Create storage writer factory
        self.storage_writer_factory = self.storage_writer_factory_function(self.format_options)

        # Mark first write to open a new file
        self.mark_next_to_new_file = True

        logger.info(f"SplitOutputFormat opened for partition {self.partition_id}")

    def options(self) -> FormatOptions:
        """Get format options."""
        return self.format_options

    def should_split(self) -> bool:
        """Check if should split to new file."""
        if not self.format_options:
            return False

        file_options = self.format_options.file_options()
        max_rows = file_options.max_row_count()
        max_size = file_options.max_file_size()

        actual_file_size = self.current_size
        if self.current_size >= max_size and self.current_lines < max_rows:
            # Use actual file size for split decision (most accurate)
            actual_file_size = self._get_actual_file_size()

        should_split = (self.current_lines >= max_rows or actual_file_size >= max_size)

        if should_split:
            logger.debug(
                f"Should split: lines={self.current_lines}>={max_rows} or actual_size={actual_file_size}>={max_size}")

        return should_split

    def write(self, obj: InputT):
        """Write an object."""
        # Check if you need to open new file
        if self.mark_next_to_new_file:
            self.split_to_new_file()
            self.mark_next_to_new_file = False
            self.current_size = 0
            self.current_lines = 0

        self.storage_writer.write(obj)

        self.current_size = self.storage_writer.get_pos()
        self.current_lines += 1

        # Update total statistics
        self.total_lines += 1
        size_delta = self.current_size - self.last_total_size
        self.total_size += size_delta
        self.last_total_size = self.current_size

        # Update Stats object
        self._stats.update(count=1, size=size_delta)

        # Check if should split after writing
        if self.should_split():
            self.mark_next_to_new_file = True

    def stats(self) -> Stats:
        """Get statistics."""
        return self._stats

    def flush(self):
        """Flush pending writes and update size statistics."""
        # Flush the writer first
        if not self.storage_writer:
            return
        self.storage_writer.flush()

    def split_to_new_file(self):
        """Split to a new file."""
        with self.lock:
            # Close current file
            self._close_current_file()

            # Open next new file
            request = FileConf.Request(
                partition=self.partition_id,
                uri=self.format_options.file_options().uri(),
                base_path=self.format_options.file_options().base_path(),
                prefix=self.format_options.file_options().file_name_prefix(),
                format_name=self.format_options.format().name.lower()
            )

            # Get next file configuration
            next_file_conf = self.get_next_file_conf(request)
            self.current_file_path = next_file_conf.path()

            # Create storage writer directly with file path
            self.storage_writer = self.storage_writer_factory.create(self.current_file_path)

            logger.info(f"OutputFormat partition {self.partition_id} opened new file: {self.current_file_path}")

    def _close_current_file(self):
        """Close current file and clean up resources."""
        exceptions = []

        try:
            # Close storage writer
            if self.storage_writer:
                try:
                    # Flush and update size statistics
                    self.flush()

                    # Close the writer
                    self.storage_writer.close()
                except Exception as e:
                    exceptions.append(e)

        finally:
            # Reset references
            self.storage_writer = None
            self.current_file_path = None

        # Raise first exception if any
        if exceptions:
            raise exceptions[0]

    def _get_actual_file_size(self) -> int:
        """Get current file size."""
        try:
            if self.current_file_path and os.path.exists(self.current_file_path):
                return os.path.getsize(self.current_file_path) # Byte
        except Exception:
            pass
        return 0

    def close(self):
        """Close the output format."""
        with self.lock:
            self._close_current_file()

    @abstractmethod
    def get_next_file_conf(self, request: FileConf.Request) -> FileConf.Response[CommT]:
        """
        Get next file configuration.
        
        Args:
            request: File configuration request
            
        Returns:
            File configuration response
        """
        pass


class FileSplitOutputFormat(SplitOutputFormat[InputT], Generic[InputT]):
    """
    File-based split output format with configurable file generation.
    """

    def __init__(self, partition_id: int, load_options: LoadOptions,
                 storage_writer_factory_function: Callable[[FormatOptions], StorageWriter.Factory],
                 next_file_caller: Callable[[FileConf.Request], FileConf.Response]):
        """
        Initialize file split output format.
        
        Args:
            partition_id: Partition identifier
            load_options: Load configuration options
            storage_writer_factory_function: Function to create storage writer factory
            next_file_caller: Callable to get next file configuration
        """
        super().__init__(partition_id, load_options, storage_writer_factory_function)

        if next_file_caller is None:
            raise ValueError("next_file_caller cannot be None")

        self.next_file_caller = next_file_caller

    def get_next_file_conf(self, request: FileConf.Request) -> FileConf.Response:
        """
        Get next file configuration using the provided caller.
        
        Args:
            request: File configuration request
            
        Returns:
            File configuration response
        """
        return self.next_file_caller(request)
