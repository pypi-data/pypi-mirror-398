from __future__ import annotations

import logging
import threading
from typing import Dict, Any, Optional

from clickzetta_ingestion.bulkload.abstract_bulkload_writer import AbstractBulkLoadWriter
from clickzetta_ingestion.bulkload.bulkload_conf import BulkLoadConf, BulkLoadFileConf
from clickzetta_ingestion.bulkload.bulkload_context import BulkLoadContext
from clickzetta_ingestion.bulkload.bulkload_handler import AbstractBulkLoadHandler
from clickzetta_ingestion.bulkload.committable import Committable
from clickzetta_ingestion.bulkload.storage.file_options import FormatInterface
from clickzetta_ingestion.common.row import Row as ArrowRow

logger = logging.getLogger(__name__)


class BulkLoadWriterImpl(AbstractBulkLoadWriter[Dict[str, Any], Committable]):
    """
    Final implementation of BulkLoadWriter using handler pattern.
    """

    def __init__(self, context: BulkLoadContext, conf: BulkLoadConf, handler: AbstractBulkLoadHandler, table=None):
        """
        Initialize BulkLoadWriterImpl.
        
        Args:
            context: BulkLoad context containing stream/table information
            conf: BulkLoad configuration
            handler: BulkLoad handler for operations
            table: Optional table instance (will be fetched if None)
        """
        super().__init__(context, conf, table)
        if handler is None:
            raise ValueError("bulkLoad handler cannot be None.")
        self._handler = handler
        
        # Thread-safe format initialization
        self._format_lock = threading.Lock()
        self._bulk_load_format: Optional[FormatInterface[ArrowRow]] = None

    def _lazy_init_target_format(self):
        """Lazy initialize target format (thread-safe)."""
        if self._bulk_load_format is None:
            with self._format_lock:
                if self._bulk_load_format is None:
                    self._bulk_load_format = self._handler.get_target_format(self.table)

    def get_storage_writer_factory_function(self):
        """
        Get storage writer factory function.
        """
        self._lazy_init_target_format()
        return self._bulk_load_format.get_storage_writer_factory_function()

    def generate_next_committable(self, request: BulkLoadFileConf.Request) -> BulkLoadFileConf.Response[Committable]:
        """Generate next committable."""
        return self._handler.generate_next_committable(request)

    def get_target_table(self):
        """Get target table."""
        return self._handler.get_target_table(self.context.schema_name, self.context.table_name)

    def create_input_with_table(self, table) -> Dict[str, Any]:
        """Create input with table."""
        self._lazy_init_target_format()
        return self._bulk_load_format.get_target_row().to_dict()

    def get_stream_id(self) -> str:
        """Get stream ID from context."""
        return self.context.stream_id

    def get_partition_id(self) -> int:
        """Get partition ID from context."""
        return self.context.partition_id

    def get_schema_name(self) -> str:
        """Get schema name from context."""
        return self.context.schema_name

    def get_table_name(self) -> str:
        """Get table name from context."""
        return self.context.table_name

    def get_handler(self) -> AbstractBulkLoadHandler:
        """Get the bulk load handler."""
        return self._handler

    def get_format(self):
        """Get the bulk load format (lazy initialized)."""
        self._lazy_init_target_format()
        return self._bulk_load_format