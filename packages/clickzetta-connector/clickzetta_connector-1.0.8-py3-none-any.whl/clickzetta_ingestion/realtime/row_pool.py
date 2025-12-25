from __future__ import annotations
from __future__ import absolute_import
from __future__ import division
import queue
from queue import Queue
import threading
import logging
from abc import ABC, abstractmethod
from typing import Callable, TypeVar, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from clickzetta_ingestion.realtime.arrow_row import ArrowRow

T = TypeVar('T')
log = logging.getLogger(__name__)


class RowPool(ABC):
    """Base class for row pools"""

    def __init__(self, pool_size: int, row_loader: Callable[[], T]):
        self.pool_size = pool_size
        self.row_loader = row_loader
        self.queue = Queue(maxsize=pool_size)
        self.pool_lock = threading.Lock()
        self.pool_support = True

    @property
    def pool_support(self) -> bool:
        return self._pool_support

    @pool_support.setter
    def pool_support(self, value: bool):
        self._pool_support = value

    @abstractmethod
    def acquire_row(self) -> Optional[T]:
        """Get a row from pool or create new one"""
        pass

    @abstractmethod
    def release_row(self, row: T):
        """Return a row to pool"""
        pass

    def close(self):
        pass


class RowQueuePool(RowPool):
    def __init__(self, pool_size: int, row_loader: Callable[[], "ArrowRow"]):
        super().__init__(pool_size, row_loader)
        self.current_size = 0
        self.queue = queue.Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        raise NotImplementedError("RowQueuePool is not implemented yet")

    def acquire_row(self) -> "ArrowRow":
        """Get a row from the pool or create new if pool not full"""
        if not self.pool_support:
            return self.row_loader()

        with self._lock:
            if self.queue.empty() and self.current_size < self.pool_size:
                # Pool not full, create new row
                self.current_size += 1
                row = self.row_loader()
                row.pooled = True
                return row

        # Pool full or has available rows, block until one is available
        try:
            row = self.queue.get(timeout=1.0)
            if row:
                return row
        except queue.Empty:
            pass

        log.warning("Failed to get row from pool, creating temporary row")
        row = self.row_loader()
        row.pooled = False
        return row

    def release_row(self, row: "ArrowRow"):
        """Return a row to pool if pooled"""
        if not self.pool_support or not row.pooled:
            return

        try:
            self.queue.put(row, timeout=1.0)
        except queue.Full:
            log.warning("Row pool is full, discarding row")
            self.current_size -= 1

    def close(self):
        """Clean up pool resources"""
        try:
            while not self.queue.empty():
                try:
                    row = self.queue.get_nowait()
                    if row:
                        row.clean()
                except queue.Empty:
                    break
        finally:
            self.current_size = 0
            self.pool_support = False
