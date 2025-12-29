from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Collection
from .bulkload_stats import BulkLoadStats

InputT = TypeVar('InputT')
CommT = TypeVar('CommT')
TableT = TypeVar('TableT')


class BulkLoadWriter(ABC, Generic[InputT, CommT]):
    """
    Abstract base class for bulk load writers.

    This interface defines the contract for bulk loading data into ClickZetta tables.
    It supports generic input types and committable types for flexibility.
    """

    @abstractmethod
    def open(self) -> None:
        """
        Open the bulk load writer.

        Raises:
            IOError: If an I/O error occurs during opening
        """
        pass

    @abstractmethod
    def get_stream_id(self) -> str:
        """
        Get the stream identifier for this writer.

        Returns:
            str: The stream ID
        """
        pass

    @abstractmethod
    def get_partition_id(self) -> int:
        """
        Get the partition identifier for this writer.

        Returns:
            int: The partition ID
        """
        pass

    @abstractmethod
    def get_table(self) -> TableT:
        """
        Get the table associated with this writer.

        Returns:
            TableT: The table instance
        """
        pass

    @abstractmethod
    def create_input(self) -> InputT:
        """
        Create a new input object for writing.

        Returns:
            InputT: A new input object
        """
        pass

    def create_row(self) -> InputT:
        """
        Alias for create_input to maintain compatibility.

        Returns:
            InputT: A new input object
        """
        return self.create_input()

    @abstractmethod
    def write(self, obj: InputT) -> None:
        """
        Write an input object to the bulk load stream.

        Args:
            obj: The input object to write

        Raises:
            IOError: If an I/O error occurs during writing
        """
        pass

    @abstractmethod
    def flush(self) -> None:
        """
        Flush any buffered data to the underlying storage.

        Raises:
            IOError: If an I/O error occurs during flushing
        """
        pass

    @abstractmethod
    def stats(self) -> BulkLoadStats:
        """
        Get statistics about the bulk load operation.

        Returns:
            BulkLoadStats: Statistics about records written, bytes written, etc.
        """
        pass

    @abstractmethod
    def get_committables(self) -> Collection[CommT]:
        """
        Get the committable objects that can be used to commit the bulk load.

        Returns:
            Collection[CommT]: A collection of committable objects
        """
        pass

    @abstractmethod
    def close(self, wait_time_ms: int = 0) -> None:
        """
        Close the bulk load writer and release any resources.

        This method should be called when the bulk load operation is complete.
        """
        pass

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
