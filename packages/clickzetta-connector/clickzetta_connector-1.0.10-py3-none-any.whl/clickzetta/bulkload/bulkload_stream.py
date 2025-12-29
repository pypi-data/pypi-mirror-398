import threading
from logging import getLogger
from typing import Optional, List, Dict

from clickzetta.bulkload.bulkload_enums import BulkLoadMetaData, BulkLoadCommitOptions, BulkLoadState, StreamSchema
from clickzetta.bulkload.bulkload_writer import BulkLoadWriter as BulkLoadWriterV1
from clickzetta.bulkload.cz_table import CZTable
from clickzetta.connector.v0._dbapi import Field
from clickzetta.connector.v0.client import Client
from clickzetta_ingestion.bulkload.bulkload_conf import BulkLoadConf, BulkLoadOptions as V2BulkLoadOptions, \
    BulkLoadOperation as V2BulkLoadOperation
from clickzetta_ingestion.bulkload.bulkload_context import FieldSchema
from clickzetta_ingestion.bulkload.v2 import BulkLoadStreamV2

_log = getLogger(__name__)


class BulkLoadStream:
    """
    V1 BulkLoad Stream API with V2 implementation.
    
    This class maintains a single V1 writer reference and delegates commit operations
    to the writer. The writer manages V2 writers internally and handles auto-prepare-commit.
    """

    # Default max rows threshold for auto prepareCommit
    DEFAULT_MAX_ROWS_THRESHOLD = 1000000

    # Default scheduler interval in seconds
    DEFAULT_SCHEDULER_INTERVAL_SECONDS = 15

    def __init__(self, meta_data: BulkLoadMetaData, client: Client,
                 commit_options: BulkLoadCommitOptions = None,
                 max_rows_threshold: int = DEFAULT_MAX_ROWS_THRESHOLD,
                 auto_prepare_interval_seconds: int = DEFAULT_SCHEDULER_INTERVAL_SECONDS):
        self.meta_data = meta_data
        self.client = client
        self.schema = client.schema
        self.commit_options = commit_options
        self.closed = False

        # V2 internal implementation
        self._v2_stream: Optional[BulkLoadStreamV2] = None
        # Use dict to map partition_id to writer instead of single writer
        self._v1_writers: Dict[int, BulkLoadWriterV1] = {}
        self._writer_lock = threading.Lock()
        self._initialized = False

        self._max_rows_threshold = max_rows_threshold
        self._auto_prepare_interval_seconds = auto_prepare_interval_seconds

        self.table: Optional[CZTable] = None
        self._ensure_v2_initialized()

    def _check_writer_exception(self):
        """Check and propagate any exception from writer's scheduler thread.

        Raises:
            IOError: If writer's scheduler thread encountered an exception
        """
        # Check all writers for exceptions
        for writer in self._v1_writers.values():
            if writer is not None:
                writer.check_exception()

    def _ensure_v2_initialized(self):
        """Lazy initialize V2 stream on first use."""
        if self._initialized:
            return

        with self._writer_lock:
            if self._initialized:
                return

            # Convert V1 metadata to V2 options
            v2_options = self._convert_v1_to_v2_options()

            # Create V2 stream
            self._v2_stream = BulkLoadStreamV2(
                self.meta_data.get_schema_name(),
                self.meta_data.get_table_name()
            )

            # Create configuration
            conf = BulkLoadConf(v2_options)

            # Open V2 stream
            self._v2_stream.open(conf, self.meta_data.get_stream_id())

            self._initialized = True
            self.meta_data.bulkload_stream = self

    def _convert_v1_to_v2_options(self) -> V2BulkLoadOptions:
        """Convert V1 metadata and options to V2 BulkLoadOptions."""
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

        builder.with_properties(BulkLoadConf.LOAD_URI, f"file://{self.meta_data.load_uri}")

        return builder.build()

    def get_v2_stream(self) -> BulkLoadStreamV2:
        return self._v2_stream

    def get_stream_id(self):
        """Get stream ID."""
        return self._v2_stream.get_stream_id() if self._v2_stream else None

    def get_operation(self):
        """Get operation type."""
        return self._v2_stream.get_operation() if self._v2_stream else None

    def get_partition_specs(self):
        """Get partition specs."""
        return self._v2_stream.get_partition_specs() if self._v2_stream else None

    def get_record_keys(self):
        """Get record keys."""
        return self._v2_stream.get_record_keys() if self._v2_stream else None

    # V1 compatibility methods (deprecated but kept for compatibility)
    def get_stream_state(self):
        """Get stream state - V1 compatibility method."""
        return BulkLoadState.CREATED if not self.closed else BulkLoadState.SEALED

    def get_sql_error(self):
        """Get SQL error - V1 compatibility method."""
        return None

    def get_schema(self):
        """Get schema name - V1 compatibility method."""
        return self.schema

    def get_table(self):
        """Get table - V1 compatibility method."""
        if not self._initialized:
            _log.error("Cannot get bulkload stream. Should have been created")
            return None
        if not self._v1_writers:
            return self.meta_data.get_table()
        else:
            v2_table = self._v1_writers[0].get_table()
            field_schemas: List[FieldSchema] = v2_table.get_table_schema()
            data_fields = [Field(name=schema.name, field_type=schema.type, nullable=schema.nullable) for schema in
                           field_schemas]
            table_meta = StreamSchema(data_fields)
            self.table = CZTable(table_meta, self.meta_data.get_schema_name(), self.meta_data.get_table_name())
        return self.table

    def open_writer(self, partition_id: int) -> 'BulkLoadWriterV1':
        """Open a writer for the specified partition.

        Args:
            partition_id: Partition ID

        Returns:
            BulkLoadWriter instance for the given partition_id
        """
        with self._writer_lock:
            # Return existing writer if already created for this partition
            if partition_id in self._v1_writers:
                return self._v1_writers[partition_id]

            # Create V1 writer with V2 stream reference
            from clickzetta.bulkload.bulkload_enums import BulkLoadConfig
            config = BulkLoadConfig()  # Default config

            writer = BulkLoadWriterV1(
                self.client,
                self.meta_data,
                config,
                partition_id,
                self._v2_stream,
                self._max_rows_threshold,
                self._auto_prepare_interval_seconds
            )

            # Store in mapping
            self._v1_writers[partition_id] = writer
            return writer

    def commit(self, options: BulkLoadCommitOptions = None):
        """Commit the stream using V2 two-phase commit.

        Args:
            options: Commit options (workspace and vcluster)
        """
        self._check_writer_exception()

        stream_info = self.meta_data.info

        if self.closed:
            stream_info.stream_state = BulkLoadState.ABORTED
            return

        _log.info("Committing BulkLoadStream: %s", self.meta_data.get_stream_id())

        if options is None:
            options = self.commit_options
            if options is None:
                raise ValueError('No commit option specified')

        self._ensure_v2_initialized()

        try:
            # Step 1: Prepare all writers (stops schedulers, prepares local data)
            all_transaction_ids = []
            all_commit_requests = []
            shared_committer = None

            _log.info("Starting unified commit for %d partitions", len(self._v1_writers))

            with self._writer_lock:
                for partition_id, writer in self._v1_writers.items():
                    if writer is not None:
                        _log.info("Preparing partition %d", partition_id)
                        writer.prepare_all()

                        all_transaction_ids.extend(writer.prepared_transaction_ids)
                        all_commit_requests.extend(writer.prepared_commit_requests)

                        # Use the first writer's committer (or create shared one later)
                        if shared_committer is None and writer.committer is not None:
                            shared_committer = writer.committer

            # Step 2: Execute unified commit for all partitions
            if all_transaction_ids and all_commit_requests:
                if shared_committer is None:
                    shared_committer = self._v2_stream.create_committer()
                    shared_committer.open()

                _log.info("Executing unified commit for %d transactions across %d partitions",
                         len(all_transaction_ids), len(self._v1_writers))

                commit_result = shared_committer.commit(
                    all_transaction_ids,
                    all_commit_requests
                )

                # Wait for commit to complete
                future = commit_result.get_future()
                result = future.result()
                _log.info("Unified commit completed successfully: %s", result)

            # Step 3: Close all committers
            with self._writer_lock:
                for writer in self._v1_writers.values():
                    if writer is not None:
                        writer.close_committer()

            stream_info.stream_state = BulkLoadState.COMMIT_SUCCESS
            _log.info("Commit completed successfully")
            self.closed = True

        except Exception as e:
            _log.error("Commit failed: %s", str(e))
            stream_info.stream_state = BulkLoadState.COMMIT_FAILED

            # Try to abort on failure
            try:
                self.abort_commit_all()
            except Exception as abort_error:
                _log.error("Abort failed: %s", str(abort_error))

            raise IOError(f"BulkLoadStream commit failed: {str(e)}") from e

    def abort_commit_all(self):
        """Abort all prepared transactions across all partitions.

        This method coordinates aborting commits for all writers in this stream.
        It should be called when a commit fails and needs to be rolled back.
        """
        _log.info("Aborting all commits for BulkLoadStream: %s", self.meta_data.get_stream_id())

        with self._writer_lock:
            for partition_id, writer in self._v1_writers.items():
                if writer is not None:
                    try:
                        _log.info("Aborting partition %d", partition_id)
                        writer.abort_commit_all()
                        writer.close_committer()
                    except Exception as e:
                        _log.warning("Failed to abort writer for partition %d: %s", partition_id, str(e))

    def abort(self):
        """Abort the stream and cleanup resources."""
        # Check for writer exception first
        self._check_writer_exception()

        _log.info("Aborting BulkLoadStream: %s", self.meta_data.get_stream_id())

        # Abort all prepared commits
        self.abort_commit_all()

        # Clear writers
        with self._writer_lock:
            self._v1_writers.clear()

        # Close V2 stream
        if self._v2_stream:
            try:
                self._v2_stream.close()
            except Exception as e:
                _log.warning("Failed to close V2 stream: %s", str(e))

        self.closed = True

    def close(self):
        """Close the stream. If not committed, will auto-commit."""
        # Check for writer exception first
        self._check_writer_exception()

        if self.closed:
            return
        else:
            self.commit()
