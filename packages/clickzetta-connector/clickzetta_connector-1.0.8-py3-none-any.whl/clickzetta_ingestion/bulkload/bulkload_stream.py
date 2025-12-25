import logging
import threading
from abc import ABC, abstractmethod
from typing import List, Sequence, Dict
from typing import TypeVar, Generic, Optional

from clickzetta_ingestion.bulkload.bulkload_committer import BulkLoadCommitter, CommitRequest, CommitRequestImpl
from clickzetta_ingestion.bulkload.bulkload_conf import BulkLoadConf, BulkLoadOptions
from clickzetta_ingestion.bulkload.bulkload_context import BulkLoadContext
from clickzetta_ingestion.bulkload.bulkload_writer import BulkLoadWriter

logger = logging.getLogger(__name__)

T = TypeVar('T')
C = TypeVar('C')


class BulkLoadStream(ABC, Generic[T, C]):
    DEFAULT_STREAM_ID = "default-stream-id"

    @abstractmethod
    def open(self, conf: BulkLoadConf, stream_id: Optional[str] = DEFAULT_STREAM_ID):
        pass

    def open_writer(self, partition_id: int) -> BulkLoadWriter[T, C]:
        writer = self.create_writer(partition_id)
        writer.open()
        return writer

    def open_committer(self) -> BulkLoadCommitter[C]:
        committer = self.create_committer()
        committer.open()
        return committer

    @abstractmethod
    def get_stream_id(self) -> str:
        pass

    @abstractmethod
    def get_operation(self) -> str:
        pass

    @abstractmethod
    def get_partition_specs(self) -> Optional[List[str]]:
        pass

    @abstractmethod
    def get_record_keys(self) -> Optional[List[str]]:
        pass

    @abstractmethod
    def close(self, wait_time_ms: int = 0):
        pass

    @abstractmethod
    def create_writer(self, partition_id: int) -> BulkLoadWriter[T, C]:
        pass

    @abstractmethod
    def create_committer(self) -> BulkLoadCommitter[C]:
        pass

    def set_bulk_load_handler(self, handler):
        pass

    def get_commit_requests(self, *writer_groups: Sequence[BulkLoadWriter[T, C]]) -> Sequence[
        CommitRequest[T]]:
        pass

    @classmethod
    def create_stream(cls, client, schema_name: str, table_name: str, options):
        pass

    @classmethod
    def get_stream(cls, client, schema_name: str, table_name: str, stream_id: str, options):
        pass


# bulk load info hold by current stream.
# no need to do extra operator like call rpc.
# all operators which you want need to init in writer or committer.
class AbstractBulkLoadStream(BulkLoadStream[T, C], ABC):
    """
    Abstract base class for BulkLoad streams thread-safe implementation.
    """

    @classmethod
    def create_stream(cls, client, schema_name: Optional[str], table_name: str,
                      options: Optional[BulkLoadOptions] = None, stream_id: Optional[str] = None) -> \
            BulkLoadStream[T, C]:
        """
        Create a new BulkLoadStream

        Args:
            client: Clickzetta Client instance
            schema_name: Target schema name
            table_name: Target table name
            options: BulkLoadOptions instance
            stream_id: Target stream id

        Returns:
            BulkLoadStream instance
        """
        options = options or BulkLoadOptions.new_builder().build()

        options.get_configure().get_properties().update({
            BulkLoadConf.CONNECTION_WORKSPACE: client.workspace,
            BulkLoadConf.CONNECTION_VC: client.vcluster,
        })

        if not schema_name:
            schema_name = client.schema

        try:
            stream = cls(schema_name, table_name)

            conf = BulkLoadConf(options)

            from clickzetta_ingestion.bulkload.default_bulkload_handler import BulkLoadHandler
            handler = BulkLoadHandler(connection_url=client.uri, properties=conf.get_properties())

            stream.set_bulk_load_handler(handler)

            stream.open(conf, stream_id)
            return stream
        except ImportError as e:
            logger.error(f"Failed to import BulkLoadStream: {e}")
            raise

    @classmethod
    def get_stream(cls, client, schema_name: str, table_name: str, stream_id: str, options) -> \
            BulkLoadStream[T, C]:
        """
        Get an existing BulkLoadStream

        Args:
            client: Clickzetta Client instance
            schema_name: Target schema name
            table_name: Target table name
            stream_id: Existing stream ID
            options: BulkLoadOptions instance

        Returns:
            BulkLoadStream instance
        """
        try:
            from clickzetta_ingestion.bulkload.bulkload_conf import BulkLoadOptions, BulkLoadOperation

            if options is None:
                options = BulkLoadOptions.new_builder() \
                    .with_operation(BulkLoadOperation.APPEND) \
                    .with_properties_dict().build()

            options.get_configure().get_properties().update({
                BulkLoadConf.CONNECTION_WORKSPACE: client.workspace,
                BulkLoadConf.CONNECTION_VC: client.vcluster,
            })

            # Create stream instance with existing stream ID
            stream = cls(schema_name, table_name)
            conf = BulkLoadConf(options)

            from clickzetta_ingestion.bulkload.default_bulkload_handler import BulkLoadHandler
            handler = BulkLoadHandler(connection_url=client.uri, properties=conf.get_properties())
            stream.set_bulk_load_handler(handler)

            # Open the stream
            stream.open(conf, stream_id=stream_id)
            return stream
        except ImportError as e:
            logger.error(f"Failed to import BulkLoadStream: {e}")
            raise

    def __init__(self, schema_name: str, table_name: str):
        self._schema_name = schema_name
        self._table_name = table_name
        self._stream_id: Optional[str] = None
        self._initialized = False
        self._conf: Optional[BulkLoadConf] = None

        # Thread safety components
        self._lock = threading.RLock()
        # Use dict to map partition_id to writer instead of single writer
        self._current_writers: Dict[int, BulkLoadWriter] = {}
        self._current_committer: Optional[BulkLoadCommitter] = None

    def get_stream_id(self) -> str:
        """Return the stream id of the current BulkLoadStream."""
        return self._stream_id

    def get_operation(self) -> str:
        """Return the operation of the current BulkLoadStream."""
        if self._conf:
            return self._conf.get_bulk_load_options().get_operation()
        return "APPEND"

    def get_partition_specs(self) -> Optional[List[str]]:
        """Get partition specs when the BulkLoadStream is created."""
        if self._conf:
            partition_specs = self._conf.get_partition_specs()
            if partition_specs:
                return [partition_specs]
        return None

    def get_record_keys(self) -> Optional[List[str]]:
        """Get record keys when the BulkLoadStream is created."""
        if self._conf:
            return self._conf.get_bulk_load_options().get_record_keys()
        return None

    def open(self, conf: BulkLoadConf, stream_id: Optional[str] = None):
        """Open the bulkload stream with configuration."""
        # Thread-safe initialization using synchronized block
        with self._lock:
            if self._initialized:
                return
            if stream_id is None:
                stream_id = BulkLoadStream.DEFAULT_STREAM_ID
            self._stream_id = stream_id
            self._conf = conf
            self._initialized = True

        logger.info(f"BulkLoadStream {stream_id} {self._schema_name} {self._table_name} open success.")

    def close(self, wait_time_ms: int = 0):
        """Close a stream with max wait times."""
        # Default implementation - subclasses can override
        pass

    def _check_opened(self):
        """Check if the stream is opened."""
        if not self._initialized:
            raise RuntimeError(f"BulkLoadStream {self._stream_id} not initialized or has already closed.")

    def _try_lock(self, func):
        """Execute function under lock."""
        with self._lock:
            return func()

    def create_writer(self, partition_id: int) -> BulkLoadWriter[T, C]:
        """Create a BulkLoadWriter with a unique partition id (thread-safe with per-partition caching)."""
        self._check_opened()

        context = BulkLoadContext(
            schema_name=self._schema_name,
            table_name=self._table_name,
            stream_id=self._stream_id,
            partition_id=partition_id
        )

        def create_writer_func():
            # Check if we have an existing initialized writer for this partition
            if partition_id in self._current_writers:
                existing_writer = self._current_writers[partition_id]
                # Only reuse if it's still initialized (not closed)
                if (existing_writer is not None and
                        existing_writer.get_stream_id() == self._stream_id and
                        existing_writer.get_partition_id() == partition_id and
                        getattr(existing_writer, '_initialized', False)):
                    return existing_writer

            # Create new writer for this partition
            writer_helper = self.internal_build_writer(context, self._conf)
            self._current_writers[partition_id] = writer_helper
            return writer_helper

        writer = self._try_lock(create_writer_func)
        logger.info(f"BulkLoadStream {self._stream_id} {self._schema_name} {self._table_name} "
                    f"createWriter with partitionId {partition_id} success.")
        return writer

    def create_committer(self) -> BulkLoadCommitter[C]:
        """Create a BulkLoadCommitter to commit all files written by one stream or other streams (thread-safe with reuse)."""
        self._check_opened()

        context = BulkLoadContext(
            schema_name=self._schema_name,
            table_name=self._table_name,
            stream_id=self._stream_id
        )

        # Thread-safe committer creation with reuse logic
        def create_committer_internal():
            committer_helper = None
            # Check if we can reuse existing committer
            if self._current_committer is not None and self._current_committer.get_stream_id() == self._stream_id:
                # Shared same committer to do commit
                committer_helper = self._current_committer

            if committer_helper is None:
                committer_helper = self.internal_build_committer(context, self._conf)
                # Do not open the committer after creation
                # committer.open()
                self._current_committer = committer_helper

            return committer_helper

        committer = self._try_lock(create_committer_internal)
        logger.info(f"BulkLoadStream {self._stream_id} {self._schema_name} {self._table_name} "
                    f"createCommitter success.")
        return committer

    def get_commit_requests(self, *writer_groups: Sequence[BulkLoadWriter[T, C]]) -> Sequence[
        CommitRequest[C]]:
        """Get commit requests from all writers."""
        commit_requests = []

        writers = [writer for group in writer_groups for writer in group]

        for w in writers:
            if w is None:
                continue
            if w.get_stream_id() != self._stream_id:
                raise ValueError(
                    f"Writer stream ID {w.get_stream_id()} does not match current stream ID {self._stream_id}.")
            w.close()

            commit_request = CommitRequestImpl(
                stream_id=self._stream_id,
                partition_id=w.get_partition_id(),
                committables=w.get_committables()
            )
            commit_requests.append(commit_request)

        return commit_requests

    def internal_build_writer(self, context: BulkLoadContext, conf: BulkLoadConf) -> BulkLoadWriter[T, C]:
        """Internal method to build writer."""
        raise NotImplementedError("Subclasses must implement internal_build_writer")

    def internal_build_committer(self, context: BulkLoadContext, conf: BulkLoadConf) -> BulkLoadCommitter[C]:
        """Internal method to build committer."""
        raise NotImplementedError("Subclasses must implement internal_build_committer")
