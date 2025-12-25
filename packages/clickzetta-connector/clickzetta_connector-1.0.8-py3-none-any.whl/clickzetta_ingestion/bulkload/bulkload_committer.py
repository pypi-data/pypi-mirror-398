import threading
from concurrent.futures import Future
from enum import Enum
from typing import TypeVar, Optional, Callable
import concurrent.futures

from clickzetta_ingestion.bulkload.committable import Committable

C = TypeVar('C')


class CommitState(Enum):
    """Commit state enumeration."""
    PRE_SUBMIT = "PRE_SUBMIT"
    SUBMITTED = "SUBMITTED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


from typing import Generic, Sequence, TypeVar, Collection
from abc import ABC, abstractmethod

CommT = TypeVar('CommT')


class CommitRequest(ABC, Generic[CommT]):
    @abstractmethod
    def get_stream_id(self) -> str:
        pass

    @abstractmethod
    def partition_id(self) -> int:
        pass

    @abstractmethod
    def get_committables(self) -> Collection[CommT]:
        pass

    class Builder:
        def build(self, stream_id: str, partition_id: int, committables: Collection[CommT]):
            return CommitRequestImpl(stream_id, partition_id, committables)


class CommitRequestImpl(CommitRequest[Committable]):
    """Concrete implementation of CommitRequest."""

    def __init__(self, stream_id: str, partition_id: int, committables: Collection[Committable]):
        self._stream_id = stream_id
        self._partition_id = partition_id
        self._committables = committables

    def get_stream_id(self) -> str:
        return self._stream_id

    def partition_id(self) -> int:
        return self._partition_id

    def get_committables(self) -> Collection[Committable]:
        return self._committables


class CommitResult:
    """Result of a commit operation."""

    def __init__(self, commit_id: Optional[str] = None, commit_state: CommitState = CommitState.PRE_SUBMIT,
                 error_msg: Optional[str] = None):
        self._commit_id = commit_id
        self._commit_state = commit_state
        self._error_msg = error_msg
        self._future: Future = Future()

    def get_commit_id(self) -> Optional[str]:
        return self._commit_id

    def get_commit_state(self) -> CommitState:
        return self._commit_state

    def get_error_msg(self) -> Optional[str]:
        return self._error_msg

    def get_future(self) -> Future:
        """Get the future for async operations."""
        return self._future

    def set_commit_id(self, commit_id: str):
        self._commit_id = commit_id

    def set_commit_state(self, state: CommitState):
        self._commit_state = state

    def set_error_msg(self, error_msg: str):
        self._error_msg = error_msg


class BulkLoadCommitter(ABC, Generic[C]):
    """Interface for bulkload committer."""

    @abstractmethod
    def add_committable(self, committable: C):
        """Add a committable to the committer."""
        pass

    @abstractmethod
    def open(self):
        """Open the committer."""
        pass

    def prepare_commit(self, commit_requests: Optional[Collection['CommitRequest[C]']] = None,
                       callback: Optional[Callable[['CommitResult'], None]] = None) -> str:
        """
        Prepare commit and return transaction ID.
        
        Args:
            commit_requests: Collection of commit requests (optional)
            callback: Optional callback for commit result
            
        Returns:
            Transaction ID
        """
        if commit_requests is None:
            commit_requests = []
        return self.prepare_commit_with_callback(commit_requests, callback)

    @abstractmethod
    def prepare_commit_with_callback(self, commit_requests: Collection['CommitRequest[C]'],
                                     callback: Optional[Callable[['CommitResult'], None]] = None) -> str:
        """
        Prepare commit with callback and return transaction ID.
        
        Args:
            commit_requests: Collection of commit requests
            callback: Optional callback for commit result
            
        Returns:
            Transaction ID
        """
        pass

    @abstractmethod
    def commit(self, transaction_ids: Sequence[str],
               commit_requests: Sequence['CommitRequest[C]']) -> 'CommitResult':
        """
        Commit with prepared transaction IDs and commit requests.
        
        Args:
            transaction_ids: Sequence of transaction IDs from prepare_commit
            commit_requests: Sequence of commit requests from prepare_commit
            
        Returns:
            CommitResult with commit status
        """
        pass

    @abstractmethod
    def abort_commit(self, transaction_ids: Sequence[str], commit_requests: Sequence['CommitRequest[C]']):
        """
        Abort commit with transaction IDs and commit requests.
        
        Args:
            transaction_ids: Sequence of transaction IDs to abort
            commit_requests: Sequence of commit requests to abort
        """
        pass

    @abstractmethod
    def get_stream_id(self) -> str:
        """Get the stream ID associated with this committer."""
        pass

    @abstractmethod
    def close(self, wait_time_ms: int = 5000):
        """Close the committer."""
        pass

    def __enter__(self) -> 'BulkLoadCommitter':
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class CommitRequestHolder(Generic[C]):
    """Holder for commit request information."""

    def __init__(self, transaction_id: str, stream_id: str, schema_name: str, table_name: str,
                 requests: Sequence[CommitRequest[CommT]]):
        self._transaction_id = transaction_id
        self._stream_id = stream_id
        self._schema_name = schema_name
        self._table_name = table_name
        self._requests = requests
        self._committables: Sequence[C] = [committable for request in requests for committable in
                                           request.get_committables()]

    def get_transaction_id(self) -> str:
        """Get the transaction ID."""
        return self._transaction_id

    def get_stream_id(self) -> str:
        """Get the stream ID."""
        return self._stream_id

    def get_schema_name(self) -> str:
        """Get the schema name."""
        return self._schema_name

    def get_table_name(self) -> str:
        """Get the table name."""
        return self._table_name

    def get_committables(self) -> Sequence[C]:
        """Get the list of committables."""
        return self._committables


class CommitResultHolder(CommitResult):
    """Holder for commit result information."""

    def __init__(self, transaction_id: str):
        super().__init__(transaction_id)
        self._transaction_id = transaction_id
        self._commit_state = CommitState.PRE_SUBMIT
        self._commit_id: Optional[str] = None
        self._error_msg: Optional[str] = None
        self._lock = threading.Lock()
        # Initialize future for async operations
        self._future: Future = concurrent.futures.Future()

    def get_transaction_id(self) -> str:
        """Get the transaction ID."""
        return self._transaction_id

    def set_commit_id(self, commit_id: str):
        """Set the commit ID."""
        self._commit_id = commit_id

    def get_commit_id(self) -> Optional[str]:
        """Get the commit ID."""
        return self._commit_id

    def set_committed(self):
        """Set the commit state to submitted."""
        with self._lock:
            if self._commit_state == CommitState.PRE_SUBMIT:
                self._commit_state = CommitState.SUBMITTED
        return self

    def set_succeed(self):
        """Set the commit state to success."""
        with self._lock:
            if self._commit_state in [CommitState.PRE_SUBMIT, CommitState.SUBMITTED]:
                self._commit_state = CommitState.SUCCESS
                self._future.set_result(None)
        return self

    def set_failed(self, error_msg: str):
        """Set the commit state to failed with error message."""
        with self._lock:
            if self._commit_state in [CommitState.PRE_SUBMIT, CommitState.SUBMITTED]:
                self._commit_state = CommitState.FAILED
                self._error_msg = error_msg
                self._future.set_exception(Exception(error_msg))
        return self

    def set_error(self, error: Exception):
        """Set the commit state to failed with exception."""
        with self._lock:
            if self._commit_state in [CommitState.PRE_SUBMIT, CommitState.SUBMITTED]:
                self._commit_state = CommitState.FAILED
                self._error_msg = str(error)
                self._future.set_exception(error)
        return self

    def set_abort(self):
        """Set the commit state to cancelled."""
        with self._lock:
            if self._commit_state in [CommitState.PRE_SUBMIT, CommitState.SUBMITTED]:
                self._commit_state = CommitState.CANCELLED
                self._future.set_result(None)
        return self

    def is_finished(self) -> bool:
        """Check if the commit is finished."""
        return self._commit_state in [CommitState.FAILED, CommitState.SUCCESS, CommitState.CANCELLED]

    def get_commit_state(self) -> CommitState:
        """Get the current commit state."""
        return self._commit_state

    def get_error_msg(self) -> Optional[str]:
        """Get the error message if failed."""
        return self._error_msg

    def get_error_message(self) -> Optional[str]:
        """Get the error message if failed (alias for get_error_msg)."""
        return self._error_msg

    def is_succeed(self) -> bool:
        """Check if the commit succeeded."""
        return self._commit_state == CommitState.SUCCESS

    def is_failed(self) -> bool:
        """Check if the commit failed."""
        return self._commit_state == CommitState.FAILED

    def is_cancelled(self) -> bool:
        """Check if the commit was cancelled."""
        return self._commit_state == CommitState.CANCELLED

    def get_future(self) -> Future:
        """Get the future for async operations."""
        return self._future
