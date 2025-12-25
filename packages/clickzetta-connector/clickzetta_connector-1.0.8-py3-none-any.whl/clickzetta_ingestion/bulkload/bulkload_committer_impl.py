from __future__ import annotations
import threading
import time
import uuid
import re
from typing import List, Collection, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor

from clickzetta_ingestion.bulkload.abstract_bulkload_committer import AbstractBulkLoadCommitter
from clickzetta_ingestion.bulkload.bulkload_committer import CommitRequest, CommitResult, CommitState, \
    CommitRequestHolder, CommitResultHolder
from clickzetta_ingestion.bulkload.bulkload_context import BulkLoadContext
from clickzetta_ingestion.bulkload.bulkload_conf import BulkLoadConf
from clickzetta_ingestion.bulkload.bulkload_handler import AbstractBulkLoadHandler
from clickzetta_ingestion.bulkload.committable import Committable


class PlaceholderCommitResultHolder(CommitResultHolder):
    """Placeholder for commit result holder to delegate calls."""

    def __init__(self, actual_holder: CommitResultHolder, transaction_id: str):
        super().__init__(transaction_id)
        self._actual_holder = actual_holder

    def __getattr__(self, name):
        return getattr(self._actual_holder, name)


class BulkLoadCommitterImpl(AbstractBulkLoadCommitter[Committable]):
    """
    Final implementation of BulkLoadCommitter using handler pattern.
    """

    def __init__(self, context: BulkLoadContext, conf: BulkLoadConf, handler: AbstractBulkLoadHandler):
        super().__init__(context, conf)
        if handler is None:
            raise ValueError("bulkLoad handler cannot be None.")
        self._handler = handler
        self._transaction_map: Dict[str, str] = {}  # transactionId -> jobId
        self._id_counter = 0
        self._id_lock = threading.Lock()
        self._committables: List[Committable] = []
        self._lock = threading.Lock()

    def add_committable(self, committable: Committable):
        """Add a committable to the committer."""
        with self._lock:
            self._committables.append(committable)

    def get_next_transaction_id(self, stream_id: str) -> str:
        """
        Generate next transaction ID.
        """
        with self._id_lock:
            self._id_counter += 1
            uuid_str = str(uuid.uuid4()).replace('-', '')
            return f"{stream_id}_{uuid_str}_{int(time.time() * 1000)}_{self._id_counter}"

    def compare_transaction_id(self, last: str, now: str) -> int:
        """
        Compare transaction IDs for ordering.
        0 if equal, negative if last < now, positive if last > now.
        """
        try:
            # Split transaction ID: streamId_uuid_timestamp_counter
            s1 = last.split("_")
            s2 = now.split("_")

            # Compare timestamp (second to last element)
            time1 = int(s1[-2])
            time2 = int(s2[-2])

            if time1 == time2:
                # Compare counter (last element)
                id1 = int(s1[-1])
                id2 = int(s2[-1])
                return id1 - id2

            return time1 - time2

        except (ValueError, IndexError):
            # Fallback to string comparison
            return -1 if last < now else (1 if last > now else 0)

    def do_prepare_commit(self, commit_request_holder: CommitRequestHolder[Committable],
                          commit_result_holder: CommitResultHolder):
        """
        Do prepare commit using handler.
        """
        self._handler.prepare_commit(commit_request_holder, commit_result_holder)

    def do_commit(self, commit_request_holder: CommitRequestHolder[Committable],
                  commit_result_holder: CommitResultHolder) -> str:
        """
        Do commit using handler with transaction mapping.
        """
        try:
            tid = commit_request_holder.get_transaction_id()
            placeholder = PlaceholderCommitResultHolder(commit_result_holder,
                                                        transaction_id=tid)
            job_id = self._handler.commit(commit_request_holder, placeholder)

            with self._lock:
                self._transaction_map[tid] = job_id

            return job_id
        except Exception as e:
            # Ensure the error is propagated to the result holder
            if commit_result_holder is not None:
                commit_result_holder.set_error(e)
            raise e

    def do_listen(self, transaction_id: str, commit_result_holder: CommitResultHolder):
        """
        Do listen using handler with transaction mapping.
        """
        with self._lock:
            if transaction_id in self._transaction_map:
                try:
                    self._handler.listen(self._transaction_map[transaction_id], commit_result_holder)
                except Exception:
                    # If catch some listener exception
                    self._transaction_map.pop(transaction_id, None)
                    raise
                finally:
                    if commit_result_holder.is_finished():
                        self._transaction_map.pop(transaction_id, None)
            else:
                raise RuntimeError(f"not contains transactionId: {transaction_id}")

    def do_abort_commit(self, transaction_id: str, commit_request_holder: CommitRequestHolder[Committable],
                        commit_result_holder: CommitResultHolder):
        """
        Do abort commit using handler with cleanup.
        """
        try:
            with self._lock:
                if transaction_id in self._transaction_map:
                    self._handler.abort(self._transaction_map[transaction_id], commit_request_holder)
        finally:
            with self._lock:
                self._transaction_map.pop(transaction_id, None)
                try:
                    self._handler.abort(transaction_id, commit_request_holder)
                except Exception:
                    # Ignore cleanup errors
                    pass

    def get_committables(self) -> List[Committable]:
        """Get all committables."""
        with self._lock:
            return self._committables.copy()

    def clear_committables(self):
        """Clear all committables."""
        with self._lock:
            self._committables.clear()

    def get_transaction_mapping(self) -> Dict[str, str]:
        """Get transaction mapping (for debugging/testing)."""
        with self._lock:
            return self._transaction_map.copy()
