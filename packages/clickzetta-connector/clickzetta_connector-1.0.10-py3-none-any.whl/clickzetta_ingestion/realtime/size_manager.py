from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from clickzetta_ingestion.realtime.arrow_writer import ArrowRecordBatchWriter


@dataclass
class WriteOperation:
    """Represents a write operation with a row"""
    row: Any = None
    pooled: bool = False

    def get_memory_size(self) -> int:
        return self.row.get_memory_size() if self.row else 0

    def clean(self):
        if self.row:
            self.row.clean()

    def get_pooled_status(self) -> bool:
        return self.pooled


class SizeManager(ABC):
    """Abstract base class for size managers"""

    @abstractmethod
    def add_operation(self, operation: WriteOperation):
        """Add operation and update size tracking"""
        pass

    @abstractmethod
    def get_current_lines(self) -> int:
        """Get current number of lines"""
        pass

    @abstractmethod
    def get_current_bytes(self) -> int:
        """Get current size in bytes"""
        pass

    @abstractmethod
    def reset(self):
        """Reset size tracking"""
        pass


class ArrowSizeManager(SizeManager):
    """Size manager that uses fixed size estimation"""

    def __init__(self):
        self.current_lines = 0
        self.current_bytes = 0

        # Arrow row memory tracking
        self.column_size = 0
        self.remain_set = False
        self.remained_size = 0
        self.valid_set_size = 0
        self.metadata_size = 0

    def add_operation(self, operation: WriteOperation):
        """Add operation and update size estimation"""
        if not self.remain_set:
            self.remained_size = operation.row.get_memory_size()
            self.column_size = operation.row.arrow_table.arrow_schema.get_column_count()
            self.remain_set = True

        self.current_lines += 1
        self.current_bytes += operation.get_memory_size()

        # Update valid set and metadata sizes
        self.valid_set_size = ((self.current_lines + 7) // 8) * self.column_size
        self.metadata_size = (self.column_size * (8 + 8) +
                              (2 * self.column_size + 1) * (8 + 8))

    def get_current_lines(self) -> int:
        return self.current_lines

    def get_current_bytes(self) -> int:
        """Get total size including header overhead"""
        return (self.current_bytes + self.remained_size +
                self.valid_set_size + self.metadata_size)

    def reset(self):
        """Reset all counters"""
        self.current_lines = 0
        self.current_bytes = 0
        self.remained_size = 0
        self.column_size = 0
        self.valid_set_size = 0
        self.metadata_size = 0
        self.remain_set = False


class ArrowStrictSizeManager(SizeManager):
    """Size manager that uses actual Arrow header size calculation"""

    def __init__(self):
        self.current_lines = 0
        self.current_bytes = 0

        # Arrow header tracking
        self.remain_set = False
        self.remained_size = 0

    def add_operation(self, operation: WriteOperation):
        """Add operation and calculate actual sizes"""
        if not self.remain_set:
            # Initialize remained_size by getting empty Arrow batch size
            arrow_table = operation.row.arrow_table
            writer = ArrowRecordBatchWriter(arrow_table, pooled=False, target_row_size=0)
            try:
                writer.finish()
                arrow_payload = writer.encode_arrow_row()
                self.remained_size = len(arrow_payload)
            except Exception as e:
                raise RuntimeError(f"Failed to calculate Arrow header size: {e}")
            finally:
                writer.close()
            self.remain_set = True

        self.current_lines += 1
        self.current_bytes += operation.get_memory_size()

    def get_current_lines(self) -> int:
        return self.current_lines

    def get_current_bytes(self) -> int:
        """Get total size including actual header size"""
        return self.remained_size + self.current_bytes

    def reset(self):
        """Reset counters"""
        self.current_lines = 0
        self.current_bytes = 0
        self.remained_size = 0
        self.remain_set = False
