"""
Storage writer interfaces for BulkLoad V2.
"""
from abc import ABC, abstractmethod
from typing import Any
from typing import TypeVar, Generic

T = TypeVar('T')


class StorageWriter(ABC, Generic[T]):
    """
    Abstract base class for storage writers.
    """

    @abstractmethod
    def write(self, element: Any):
        """
        Write an element to storage.
        
        Args:
            element: Element to write
        """
        pass

    @abstractmethod
    def close(self, wait_time_ms: int = 0):
        """
        Close the writer.
        
        Args:
            wait_time_ms: Wait time in milliseconds
        """
        pass

    @abstractmethod
    def flush(self) -> int:
        """Flush any buffered data."""
        pass

    @abstractmethod
    def get_pos(self) -> int:
        """Get current position in the output."""
        pass

    class Factory(ABC):
        """
        Factory interface for creating storage writers.
        """

        @abstractmethod
        def create(self, path: str) -> 'StorageWriter':
            """
            Create a storage writer.
            
            Args:
                path: Output file path
                out: Position output stream
                
            Returns:
                StorageWriter instance
            """
            pass
