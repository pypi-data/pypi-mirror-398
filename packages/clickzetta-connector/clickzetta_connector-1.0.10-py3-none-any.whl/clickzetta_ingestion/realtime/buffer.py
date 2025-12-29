import logging
from abc import ABC, abstractmethod
from typing import List

from clickzetta_ingestion.realtime.size_manager import ArrowStrictSizeManager, ArrowSizeManager, WriteOperation

log = logging.getLogger(__name__)

class Buffer(ABC):
    """Abstract base class for buffers"""

    @abstractmethod
    def add_operation(self, operation: WriteOperation):
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        pass

    @abstractmethod
    def is_full(self, byte_size: int, pre_check: bool) -> bool:
        pass

    @abstractmethod
    def get_operations(self) -> List[WriteOperation]:
        pass

    @abstractmethod
    def get_current_lines(self) -> int:
        pass

    @abstractmethod
    def get_current_bytes(self) -> int:
        pass

    @abstractmethod
    def get_memory_usage(self) -> int:
        pass

    @abstractmethod
    def get_pooled_operation_index(self) -> List[int]:
        pass

    @abstractmethod
    def reset(self):
        pass


class DefaultBuffer(Buffer):
    """Default implementation of Buffer"""

    def __init__(self, line_capacity: int, byte_capacity: int, strict_mode: bool = True):
        self.line_capacity = line_capacity
        self.byte_capacity = byte_capacity
        self.strict_mode = strict_mode
        self.operations: List[WriteOperation] = []
        self.pooled_index: List[int] = []
        self.size_manager = ArrowStrictSizeManager() if strict_mode else ArrowSizeManager()

    def add_operation(self, operation: WriteOperation):
        """Add a write operation to buffer"""
        if operation.get_pooled_status():
            self.pooled_index.append(len(self.operations))

        self.operations.append(operation)
        self.size_manager.add_operation(operation)

    def is_empty(self) -> bool:
        return len(self.operations) == 0

    def is_full(self, byte_size: int, pre_check: bool = False) -> bool:
        """Check if buffer is full"""
        if pre_check:
            return self.size_manager.get_current_bytes() + byte_size >= self.byte_capacity
        else:
            return (self.size_manager.get_current_lines() + 1 >= self.line_capacity or
                    self.size_manager.get_current_bytes() + byte_size >= self.byte_capacity)

    def get_operations(self) -> List[WriteOperation]:
        return self.operations

    def get_current_lines(self) -> int:
        return self.size_manager.get_current_lines()

    def get_current_bytes(self) -> int:
        return self.size_manager.get_current_bytes()

    def get_memory_usage(self) -> int:
        return self.size_manager.get_current_bytes()

    def get_pooled_operation_index(self) -> List[int]:
        return self.pooled_index

    def reset(self):
        """Reset buffer state"""
        for op in self.operations:
            op.clean()

        self.operations.clear()
        self.pooled_index.clear()
        self.size_manager.reset()