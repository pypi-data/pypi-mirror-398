import threading
from logging import getLogger
from typing import Optional, List, Dict, Any

from clickzetta.bulkload.bulkload_enums import BulkLoadMetaData, BulkLoadConfig
from clickzetta.connector.v0.client import Client
from clickzetta_ingestion.bulkload.bulkload_committer import BulkLoadCommitter, CommitRequest
from clickzetta_ingestion.bulkload.bulkload_conf import BulkLoadConf, BulkLoadOptions as V2BulkLoadOptions, \
    BulkLoadOperation as V2BulkLoadOperation
from clickzetta_ingestion.bulkload.bulkload_writer import BulkLoadWriter as V2BulkLoadWriter
from clickzetta_ingestion.bulkload.committable import Committable
from clickzetta_ingestion.bulkload.v2 import BulkLoadStreamV2

_log = getLogger(__name__)


class Row:
    """V1 Row API for backward compatibility.

    This class wraps a dictionary to provide the V1 Row API.
    """

    def __init__(self, full_fields: dict, table_name: str):
        self.field_name_values = {}
        self.full_fields = full_fields
        self.table_name = table_name

    def set_value(self, field_name: str, field_value):
        """Set a field value in the row.

        Args:
            field_name: Name of the field
            field_value: Value to set
        """
        if field_name in self.full_fields:
            self.field_name_values[field_name] = field_value
        else:
            raise RuntimeError(f'Field name:{field_name} is not in table:{self.table_name}')


class BulkLoadWriter:
    """V1 BulkLoadWriter API with V2 implementation internally.
    """

    # Default max rows threshold for auto prepareCommit
    DEFAULT_MAX_ROWS_THRESHOLD = 1000000

    # Default scheduler interval in seconds
    DEFAULT_SCHEDULER_INTERVAL_SECONDS = 15

    def __init__(self, client: Client, meta_data: BulkLoadMetaData, config: BulkLoadConfig, partition_id: int,
                 v2_stream: Optional[BulkLoadStreamV2] = None,
                 max_rows_threshold: int = DEFAULT_MAX_ROWS_THRESHOLD,
                 auto_prepare_interval_seconds: int = DEFAULT_SCHEDULER_INTERVAL_SECONDS):
        """Initialize BulkLoadWriter with original V1 API signature.Only uses local V2 stream.
        It will store multiple commit requests to support auto prepareCommit.

        Args:
            client: ClickZetta client
            meta_data: Bulkload metadata
            config: Bulkload configuration
            partition_id: Partition ID
            v2_stream: V2 BulkLoadStream instance
            max_rows_threshold: Max rows threshold for auto prepareCommit
            auto_prepare_interval_seconds: Auto prepare commit interval in seconds
        """
        self.client = client
        self.meta_data = meta_data
        self.config = config
        self.partition_id = partition_id
        self._closed = False
        self._table_schema = None

        # V2 stream reference
        if v2_stream is None:
            raise RuntimeError('v2_stream is required')
        self._v2_stream: BulkLoadStreamV2 = v2_stream

        # Current active V2 writer for write operations
        self._current_v2_writer: Optional[V2BulkLoadWriter[dict, Committable]] = None

        # Lock for swapping writers (write vs prepare-commit)
        self._writer_swap_lock = threading.Lock()

        # Lock for prepare operations
        self._prepare_lock = threading.Lock()

        # Auto prepareCommit configuration
        self._max_rows_threshold = max_rows_threshold
        self._auto_prepare_interval_seconds = auto_prepare_interval_seconds

        # Prepared commit state
        self._prepared_transaction_ids: List[str] = []
        self._prepared_commit_requests: List[CommitRequest[Committable]] = []
        self._committer: Optional[BulkLoadCommitter[Committable]] = None

        # Periodic scheduler for auto prepareCommit
        self._scheduler_thread: Optional[threading.Thread] = None
        self._scheduler_stop_event = threading.Event()

        # Exception from scheduler thread for propagation to main thread
        self._scheduler_exception: Optional[Exception] = None
        self._exception_lock = threading.RLock()

        # Initialize first V2 writer
        self._initialized = False
        self._init_writer()

    @property
    def prepared_transaction_ids(self) -> List[str]:
        """Get the list of prepared transaction IDs."""
        return self._prepared_transaction_ids

    @property
    def prepared_commit_requests(self) -> List[CommitRequest[Committable]]:
        """Get the list of prepared commit requests."""
        return self._prepared_commit_requests

    @property
    def committer(self) -> Optional[BulkLoadCommitter[Committable]]:
        """Get the committer instance."""
        return self._committer

    def _set_exception(self, exception: Exception):
        """Store exception from scheduler thread for later propagation."""
        with self._exception_lock:
            if self._scheduler_exception is None:
                self._scheduler_exception = exception
                _log.error("Scheduler exception stored for partition %d: %s",
                           self.partition_id, str(exception), exc_info=True)

    def check_exception(self):
        """Check and raise any stored exception from scheduler thread.
        
        Raises:
            IOError: If scheduler thread encountered an exception
        """
        with self._exception_lock:
            if self._scheduler_exception is not None:
                exception = self._scheduler_exception
                raise IOError(f"BulkLoadWriter failed due to scheduler exception: {str(exception)}") from exception

    def _init_writer(self):
        """Initialize the first V2 writer and start scheduler."""
        with self._writer_swap_lock:
            self._current_v2_writer = self._v2_stream.open_writer(self.partition_id)
        self._initialized = True
        self._start_scheduler()

    def _create_new_v2_writer(self) -> V2BulkLoadWriter[dict, Committable]:
        """Create a new V2 writer for the same partition."""
        return self._v2_stream.open_writer(self.partition_id)

    def _start_scheduler(self):
        """Start the periodic scheduler thread for auto prepareCommit."""
        if self._scheduler_thread is not None:
            return

        def scheduler_loop():
            """Scheduler loop that runs periodically to check and trigger auto prepareCommit."""
            _log.info("Auto prepareCommit scheduler started for partition %d with interval: %d seconds",
                      self.partition_id, self._auto_prepare_interval_seconds)

            # Initial delay before first check
            if not self._scheduler_stop_event.wait(self._auto_prepare_interval_seconds):
                while not self._scheduler_stop_event.is_set():
                    try:
                        # Check if should auto prepare commit
                        if self._should_auto_prepare_commit():
                            # Run prepareCommit synchronously guarded by prepare lock
                            if self._prepare_lock.acquire(blocking=False):
                                try:
                                    self._auto_prepare_commit()
                                finally:
                                    self._prepare_lock.release()
                            else:
                                _log.debug("Auto prepareCommit already in progress for partition %d, skipping...",
                                           self.partition_id)
                    except Exception as e:
                        _log.error("Error in scheduler loop for partition %d: %s",
                                   self.partition_id, str(e), exc_info=True)
                        # Store exception for propagation to main thread
                        self._set_exception(e)
                        # Stop scheduler on exception
                        break

                    # Wait for next interval or stop event
                    if self._scheduler_stop_event.wait(self._auto_prepare_interval_seconds):
                        break

            _log.info("Auto prepareCommit scheduler stopped for partition %d", self.partition_id)

        self._scheduler_thread = threading.Thread(
            target=scheduler_loop,
            name=f"auto-prepare-commit-scheduler-{self.partition_id}",
            daemon=True
        )
        self._scheduler_thread.start()

    def stop_scheduler(self):
        """Stop the periodic scheduler thread."""
        # Check exception first
        self.check_exception()

        if self._scheduler_thread is None:
            return

        _log.info("Stopping auto prepareCommit scheduler for partition %d...", self.partition_id)
        self._scheduler_stop_event.set()

        # Wait for scheduler thread to finish (with timeout)
        if self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=5.0)
            if self._scheduler_thread.is_alive():
                _log.warning("Scheduler thread for partition %d did not stop within timeout", self.partition_id)

        self._scheduler_thread = None

        # Check exception again after stopping
        self.check_exception()

    def _should_auto_prepare_commit(self) -> bool:
        """Check if should auto execute prepareCommit based on row count threshold.

        Returns:
            True if total rows written exceeds threshold, False otherwise
        """
        if self._current_v2_writer is None:
            return False

        try:
            with self._writer_swap_lock:
                if self._current_v2_writer is None:
                    return False
                stats = self._current_v2_writer.stats()
                total_rows = stats.get_rows_written()
            return total_rows > self._max_rows_threshold
        except Exception as e:
            _log.warning("Failed to get stats from writer for partition %d: %s",
                         self.partition_id, str(e))
            return False

    def _auto_prepare_commit(self):
        """Auto execute prepareCommit in background thread.

        This method:
        1. Swaps out current writer with a new one
        2. Closes old writer and collects committables
        3. Executes prepareCommit
        4. Saves transaction ID and commit requests for later commit
        """
        # Swap writer under lock
        old_writer = None
        with self._writer_swap_lock:
            if self._current_v2_writer is None or self._closed:
                _log.debug("No writer to prepare commit for partition %d, skipping...", self.partition_id)
                return

            # Swap current writer with a new one
            old_writer = self._current_v2_writer
            if old_writer is not None:
                # Execute prepareCommit outside of swap lock (allows writes to continue)
                old_writer.flush()
                old_writer.close()
            self._current_v2_writer = self._create_new_v2_writer()
            _log.info("Swapped V2 writer for partition %d during auto prepareCommit", self.partition_id)
            if old_writer is None:
                return

        committables = old_writer.get_committables()

        if not committables:
            _log.debug("No committables from old writer for partition %d", self.partition_id)
            return

        commit_request = CommitRequest.Builder().build(
            old_writer.get_stream_id(),
            self.partition_id,
            committables
        )

        if self._committer is None:
            self._committer = self._v2_stream.create_committer()
            self._committer.open()

        transaction_id = self._committer.prepare_commit([commit_request])
        _log.info("Auto prepareCommit completed for partition %d with transaction_id: %s",
                  self.partition_id, transaction_id)

        self._prepared_commit_requests.append(commit_request)
        self._prepared_transaction_ids.append(transaction_id)

    def _convert_v1_to_v2_options(self) -> V2BulkLoadOptions:
        """Convert V1 config to V2 BulkLoadOptions."""
        from clickzetta.bulkload.bulkload_enums import BulkLoadOperation as V1Operation

        # Map V1 operation to V2
        v1_op = self.meta_data.get_operation()
        if v1_op == V1Operation.APPEND:
            operation = V2BulkLoadOperation.APPEND
        elif v1_op == V1Operation.OVERWRITE:
            operation = V2BulkLoadOperation.OVERWRITE
        elif v1_op == V1Operation.UPSERT:
            operation = V2BulkLoadOperation.UPSERT
        else:
            operation = V2BulkLoadOperation.APPEND

        # Build V2 options
        builder = V2BulkLoadOptions.new_builder()
        builder.with_operation(operation)

        # Set partition specs
        partition_specs = self.meta_data.get_partition_specs()
        if partition_specs:
            builder.with_partition_specs(partition_specs)

        # Set record keys
        record_keys = self.meta_data.get_record_keys()
        if record_keys:
            builder.with_record_keys(record_keys)

        # Set prefer internal endpoint
        builder.with_prefer_internal_endpoint(self.meta_data.get_prefer_internal_endpoint())

        # Set connection URL from client
        connection_url = self.client.get_connection_url()
        builder.with_properties(BulkLoadConf.CONNECTION_URL, connection_url)

        # Set staging location from config
        staging_config = self.config.get_staging_config(self.meta_data.get_prefer_internal_endpoint())
        if staging_config and hasattr(staging_config, 'get_location'):
            builder.with_properties(BulkLoadConf.LOAD_URI, staging_config.get_location())
        else:
            # Set default local storage path
            import tempfile
            import os
            default_path = os.path.join(tempfile.gettempdir(), "clickzetta_bulkload")
            builder.with_properties(BulkLoadConf.LOAD_URI, f"file://{default_path}")

        return builder.build()

    def _get_table_schema(self) -> dict:
        """Get table schema from V2 writer."""
        return self.meta_data.get_table().schema

    def get_v2_stream(self) -> BulkLoadStreamV2:
        """Get the underlying V2 stream for internal use."""
        return self._v2_stream

    def get_stream_id(self):
        """Get the stream ID."""
        return self._current_v2_writer.get_stream_id() if self._current_v2_writer else None

    def get_operation(self):
        """Get the operation type."""
        return self.meta_data.get_operation()

    def get_schema(self):
        """Get the table schema."""
        return self._get_table_schema()

    def get_table(self):
        """Get the table."""
        self.check_exception()
        return self._current_v2_writer.get_table() if self._current_v2_writer else None

    def get_partition_id(self):
        """Get the partition ID."""
        return self.partition_id

    def create_row(self):
        """Create a new row for writing.

        Returns:
            Row object with V1 API
        """
        schema = self._get_table_schema()
        row = Row(schema, self.meta_data.get_table_name())
        with self._writer_swap_lock:
            full_fields: Dict[str, Any] = self._current_v2_writer.create_row()
            # Initialize row with full fields if available
            if full_fields:
                row.field_name_values = full_fields
        return row

    def write(self, row: Row):
        """Write a row to the stream.

        Args:
            row: Row object to write
        """
        # Check for scheduler exception before write
        self.check_exception()

        if self._closed:
            raise RuntimeError('BulkLoadWriter is already closed.')

        # Thread-safe write with swap lock
        with self._writer_swap_lock:
            if self._current_v2_writer is None:
                raise RuntimeError('BulkLoadWriter V2 writer is not initialized.')
            self._current_v2_writer.write(row.field_name_values)

    def finish(self):
        """Finish writing and flush all data."""
        # Check for scheduler exception
        self.check_exception()

        if self._closed:
            _log.warning('BulkLoadWriter is already closed.')
            return

        _log.info("Finishing BulkLoadWriter for stream: %s, partition: %d",
                  self.get_stream_id(), self.get_partition_id())

        # Stop scheduler first
        self.stop_scheduler()

        # Flush and close current V2 writer
        with self._writer_swap_lock:
            if self._current_v2_writer:
                self._current_v2_writer.flush()
                self._current_v2_writer.close()

    def abort(self):
        """Abort writing and cleanup resources."""
        # Check for scheduler exception
        self.check_exception()

        if not self._initialized:
            # Nothing to abort if not initialized
            self._closed = True
            return

        _log.info("Aborting BulkLoadWriter for stream: %s, partition: %d",
                  self.get_stream_id(), self.get_partition_id())

        # Stop scheduler
        self.stop_scheduler()

        try:
            with self._writer_swap_lock:
                if self._current_v2_writer:
                    self._current_v2_writer.close()
        except Exception as e:
            _log.warning("Failed to close V2 writer during abort: %s", str(e))

        self._closed = True

    def prepare_all(self):
        """Prepare all remaining data for commit (without actually committing).
        """
        self.check_exception()

        self.stop_scheduler()

        # Wait for in-flight auto prepareCommit to complete
        try:
            if self._prepare_lock.acquire(timeout=300):
                self._prepare_lock.release()
        except Exception as e:
            _log.error("Waiting for auto prepareCommit lock failed for partition %d: %s",
                       self.partition_id, str(e), exc_info=True)

        self.check_exception()

        # Process remaining data in current writer
        with self._writer_swap_lock:
            if self._current_v2_writer and not self._closed:
                _log.info("Preparing remaining data in current writer for partition %d", self.partition_id)
                try:
                    # Flush and close current writer
                    self._current_v2_writer.flush()
                    self._current_v2_writer.close()

                    committables = self._current_v2_writer.get_committables()

                    if committables:
                        request_builder = CommitRequest.Builder()
                        commit_request = request_builder.build(
                            self._current_v2_writer.get_stream_id(),
                            self.partition_id,
                            committables
                        )

                        if self._committer is None:
                            self._committer = self._v2_stream.create_committer()
                            self._committer.open()

                        # Prepare commit for remaining data
                        transaction_id = self._committer.prepare_commit([commit_request])
                        _log.info("Prepared remaining data for partition %d with transaction_id: %s",
                                  self.partition_id, transaction_id)

                        self._prepared_commit_requests.append(commit_request)
                        self._prepared_transaction_ids.append(transaction_id)

                except Exception as e:
                    _log.error("Failed to prepare remaining data for partition %d: %s",
                               self.partition_id, str(e), exc_info=True)
                    raise

                self._current_v2_writer = None

        _log.info("Partition %d prepared with %d transactions",
                  self.partition_id, len(self._prepared_transaction_ids))

    def abort_commit_all(self):
        """Abort all prepared data and close all writers."""
        # Check for scheduler exception
        self.check_exception()

        try:
            # Stop scheduler
            self.stop_scheduler()

            # Abort all prepared transactions
            if self._prepared_transaction_ids and self._prepared_commit_requests:
                _log.info("Aborting %d prepared transactions for partition %d",
                          len(self._prepared_transaction_ids), self.partition_id)
                if self._committer:
                    self._committer.abort_commit(
                        self._prepared_transaction_ids,
                        self._prepared_commit_requests
                    )
                self._prepared_transaction_ids.clear()
                self._prepared_commit_requests.clear()

            # Close current writer
            with self._writer_swap_lock:
                if self._current_v2_writer and not self._closed:
                    try:
                        self._current_v2_writer.close()
                    except Exception as e:
                        _log.warning("Failed to close current writer for partition %d: %s",
                                     self.partition_id, str(e))
                self._current_v2_writer = None

        except Exception as e:
            _log.error("Error during abort for partition %d: %s",
                       self.partition_id, str(e), exc_info=True)

    def close_committer(self):
        """Close the committer if exists."""
        # Check for scheduler exception
        self.check_exception()

        if self._committer:
            try:
                self._committer.close()
            except Exception as e:
                _log.warning("Failed to close committer for partition %d: %s",
                             self.partition_id, str(e))

    def is_closed(self):
        return self._closed

    def close(self):
        """Close the writer. Calls finish() if not already closed."""
        # Check for scheduler exception
        self.check_exception()

        if self._closed:
            return
        self.finish()
