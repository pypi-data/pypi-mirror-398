from __future__ import annotations

import logging
import threading
from typing import Optional, List, Sequence, TypeVar

from clickzetta.connector.v0.utils import try_with_finally
from clickzetta_ingestion.bulkload.bulkload_committer import BulkLoadCommitter, CommitRequest
from clickzetta_ingestion.bulkload.bulkload_conf import BulkLoadConf
from clickzetta_ingestion.bulkload.bulkload_factory import BulkLoadFactoryImpl
from clickzetta_ingestion.bulkload.bulkload_handler import AbstractBulkLoadHandler
from clickzetta_ingestion.bulkload.bulkload_stream import AbstractBulkLoadStream, BulkLoadStream
from clickzetta_ingestion.bulkload.bulkload_stream_impl import BulkLoadStreamImpl
from clickzetta_ingestion.bulkload.bulkload_writer import BulkLoadWriter
from clickzetta_ingestion.bulkload.committable import Committable
from clickzetta_ingestion.bulkload.default_bulkload_handler import BulkLoadHandler

logger = logging.getLogger(__name__)

InputT = TypeVar('InputT')
CommT = TypeVar('CommT')


class BulkLoadStreamV2(AbstractBulkLoadStream[dict, Committable]):
    """BulkLoad Stream V2 implementation."""

    def __init__(self, schema_name: str, table_name: str):
        super().__init__(schema_name, table_name)
        self._schema_name = schema_name
        self._table_name = table_name
        self._stream_id: Optional[str] = None
        self._conf: Optional[BulkLoadConf] = None
        self._initialized = False
        self._handler_proxy: Optional[AbstractBulkLoadHandler] = None
        self._stream_proxy: Optional[AbstractBulkLoadStream] = None
        self._lock = threading.Lock()

    def set_bulk_load_handler(self, handler: AbstractBulkLoadHandler):
        """Set bulkload handler for testing purposes."""
        self._handler_proxy = handler

    def open(self, conf: BulkLoadConf, stream_id: Optional[str] = None):
        """Open the bulkload stream with configuration."""
        with self._lock:
            if self._initialized:
                return

            if stream_id is None:
                self._stream_id = BulkLoadStream.DEFAULT_STREAM_ID
            else:
                self._stream_id = stream_id
            self._conf = conf

            # hack reset bulkLoad handler for ut test
            if self._handler_proxy is None:
                self._handler_proxy = BulkLoadHandler(conf.get_connection_url(), conf.get_properties())

            self._handler_proxy.open(conf)
            bulk_load_factory = BulkLoadFactoryImpl(self._handler_proxy)

            # Open bulkLoad stream v2
            self._stream_proxy = BulkLoadStreamImpl(self._schema_name, self._table_name, bulk_load_factory)
            self._stream_proxy.open(conf, self._stream_id)
            self._initialized = True

    def get_stream_id(self) -> str:
        """Return the stream id of the current BulkLoadStream."""
        return self._stream_id

    def get_operation(self) -> str:
        """Operation of the current BulkLoadStream."""
        return self._conf.get_operation() if self._conf else "APPEND"

    def get_partition_specs(self) -> Optional[str]:
        """Get partition specs when the BulkLoadStream is created."""
        return self._conf.get_partition_specs() if self._conf else None

    def get_record_keys(self) -> Optional[List[str]]:
        """Get record keys when the BulkLoadStream is created."""
        return self._conf.get_record_keys() if self._conf else None

    def close(self, wait_time_ms: int = 0):
        """Close a stream with max wait times."""
        with self._lock:
            if not self._initialized:
                return
            self._initialized = False

        # Use try_with_finally to ensure proper cleanup
        try_with_finally(
            lambda: self._close_stream_proxy(wait_time_ms),
            lambda: self._close_handler_proxy()
        )

    def _close_stream_proxy(self, wait_time_ms: int):
        """Close stream proxy."""
        try:
            if self._stream_proxy is not None:
                self._stream_proxy.close(wait_time_ms)
        finally:
            self._stream_proxy = None

    def _close_handler_proxy(self):
        """Close handler proxy."""
        try:
            if self._handler_proxy is not None:
                self._handler_proxy.close()
        finally:
            self._handler_proxy = None

    def create_writer(self, partition_id: int) -> BulkLoadWriter[dict, Committable]:
        """Create a BulkLoadWriter with a unique partition id."""
        return self._stream_proxy.create_writer(partition_id)

    def create_committer(self) -> BulkLoadCommitter[Committable]:
        """Commit a unique commit to commit all files write by one stream or other streams."""
        return self._stream_proxy.create_committer()

    def get_commit_requests(self, *writer_groups: Sequence[BulkLoadWriter[InputT, CommT]]) -> Sequence[
        CommitRequest[Committable]]:
        """Get commit requests from all writers."""
        # Flatten the writer groups into a single sequence
        return self._stream_proxy.get_commit_requests(*writer_groups)
