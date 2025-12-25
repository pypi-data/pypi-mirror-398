from __future__ import annotations

import logging
import queue
import threading
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Optional, Sequence, Callable, TypeVar, Generic

from clickzetta_ingestion.bulkload.bulkload_committer import BulkLoadCommitter, CommitRequest, CommitResult, \
    CommitRequestHolder, CommitResultHolder
from clickzetta_ingestion.bulkload.bulkload_conf import BulkLoadConf
from clickzetta_ingestion.bulkload.bulkload_context import BulkLoadContext
from clickzetta_ingestion.bulkload.committable import Committable

CommT = TypeVar('CommT')

logger = logging.getLogger(__name__)


class AbstractBulkLoadCommitter(BulkLoadCommitter[CommT], ABC, Generic[CommT]):
    """
    Abstract base class for BulkLoad committers.
    """

    def __init__(self, context: BulkLoadContext, conf: BulkLoadConf):
        self.context = context
        self.conf = conf

        # Thread safety components 
        self._to_commit_queue: Optional[queue.Queue] = None
        self._result_map: Dict[str, CommitResult] = {}
        self._result_queue: Optional[queue.Queue] = None
        self._next_loop_lock = threading.Lock()

        # Thread state
        self._thread_service_init = False
        self._thread_service_state = False
        self._commit_executor: Optional[ThreadPoolExecutor] = None
        self._listener_executor: Optional[ThreadPoolExecutor] = None
        self._commit_timer_future: Optional[Future] = None
        self._listener_future: Optional[Future] = None

        # Transaction lock
        self._transaction_lock = threading.RLock()
        self._transaction_condition = threading.Condition(self._transaction_lock)
        self._initialized = False

        self._last_transaction_id: Optional[str] = None
        self._main_lock = threading.Lock()

    def open(self):
        """Open the committer."""
        with self._main_lock:
            if self._initialized:
                return

            self._to_commit_queue = queue.Queue()
            self._result_map = {}
            self._result_queue = queue.Queue()
            # Lazy init executor service
            self._initialized = True

        logger.info(f"BulkLoadCommitter {self.context.stream_id} {self.context.schema_name} "
                    f"{self.context.table_name} open success.")

    def _lazy_init_executor_service(self):
        """Lazy initialize executor services."""
        if not self._thread_service_init:
            with self._main_lock:
                if not self._thread_service_init:
                    if self._commit_executor is None:
                        self._commit_executor = ThreadPoolExecutor(
                            max_workers=1,
                            thread_name_prefix="BulkLoadCommitter"
                        )
                    if self._listener_executor is None:
                        self._listener_executor = ThreadPoolExecutor(
                            max_workers=1,
                            thread_name_prefix="BulkLoadlistener"
                        )

                    # Start executor service runners
                    self._thread_service_state = True
                    self._commit_timer_future = self._commit_executor.submit(self._internal_run_commit)
                    self._listener_future = self._listener_executor.submit(self._internal_run_listener)

                    self._thread_service_init = True

    def get_stream_id(self) -> str:
        """Get stream ID."""
        return self.context.stream_id

    def _check_opened(self):
        """Check if the committer is opened."""
        if not self._initialized:
            raise RuntimeError(f"BulkLoadCommitter {self.context.stream_id} not initial or has already close.")

    def _try_transaction_lock(self, func):
        """Execute function under transaction lock."""
        with self._transaction_lock:
            return func()

    def _check_request_stream_id(self, commit_request: CommitRequest[CommT]):
        """Check if request stream ID matches."""
        if commit_request.get_stream_id() != self.context.stream_id:
            raise RuntimeError(
                f"BulkLoadCommitter {self.context.stream_id} receive other streamId {commit_request.get_stream_id()} commitRequest.")

    def _check_last_transaction_id(self, next_transaction_id: str) -> bool:
        """Check last transaction ID for ordering."""
        if self._last_transaction_id is None or self._last_transaction_id == next_transaction_id:
            return True

        # Compare transaction IDs
        compare_result = self.compare_transaction_id(self._last_transaction_id, next_transaction_id)
        if compare_result > 0:
            raise RuntimeError(f"BulkLoadCommitter {self.context.stream_id} must do transaction with "
                               f"greater id. now is {next_transaction_id} last is {self._last_transaction_id}.")
        return True

    def _get_min_transaction_id(self, transaction_ids: Sequence[str]) -> str:
        """Get minimum transaction ID."""
        if not transaction_ids:
            raise RuntimeError("transaction_ids is empty")

        sorted_transaction_ids = list(transaction_ids)
        if len(sorted_transaction_ids) == 1:
            return sorted_transaction_ids[0]

        # Sort using compare_transaction_id. The default sort is ascending.
        from functools import cmp_to_key
        sorted_transaction_ids.sort(key=cmp_to_key(self.compare_transaction_id))
        return sorted_transaction_ids[0]

    def prepare_commit_with_callback(self, commit_requests: Sequence[CommitRequest[CommT]],
                                     callback: Optional[Callable[[CommitResult], None]] = None) -> str:
        """
        Prepare commit and return transaction ID.
        
        Args:
            commit_requests: Sequence of commit requests
            callback: Optional callback for commit result
            
        Returns:
            Transaction ID
        """
        # Only check & add to commit map to wait for be committed
        self._check_opened()

        # Pre-check Sequence of commitRequests should not be null or empty
        if commit_requests is None or len(commit_requests) == 0:
            raise RuntimeError("commitRequests is null or empty")

        for commit_request in commit_requests:
            # Check each commit request should not be null or empty
            if commit_request is None or commit_request.get_committables() is None or len(
                    commit_request.get_committables()) == 0:
                raise RuntimeError(
                    "committables is null or empty. Maybe no data has been written. commit_request: " + str(
                        commit_request))
            self._check_request_stream_id(commit_request)

        # Generate new transactionId to do current transaction commit
        def prepare_internal():
            tid = self.get_next_transaction_id(self.get_stream_id())
            self._check_last_transaction_id(tid)

            # Construct commit request holder
            holder = CommitRequestHolder(
                transaction_id=tid,
                stream_id=self.get_stream_id(),
                schema_name=self.context.schema_name,
                table_name=self.context.table_name,
                requests=commit_requests
            )

            return tid, holder

        transaction_id, commit_request_holder = self._try_transaction_lock(prepare_internal)

        logger.info(f"BulkLoadCommitter {self.get_stream_id()} prepareCommit transactionId {transaction_id}.")

        commit_result_holder = CommitResultHolder(transaction_id)
        commit_result_holder.set_committed()

        try:
            self.do_prepare_commit(commit_request_holder, commit_result_holder)
            commit_result_holder.set_succeed()
        except Exception as e:
            commit_result_holder.set_error(e)
            if isinstance(e, RuntimeError):
                raise e
            else:
                raise RuntimeError(str(e))
        finally:
            if callback is not None:
                callback(commit_result_holder)

        return transaction_id

    @abstractmethod
    def get_next_transaction_id(self, stream_id: str) -> str:
        """
        Generate next transaction ID - to be implemented by subclasses.
        """
        pass

    @abstractmethod
    def compare_transaction_id(self, last: str, now: str) -> int:
        """
        Compare transaction IDs for ordering - to be implemented by subclasses.
        """
        pass

    @abstractmethod
    def do_prepare_commit(self, commit_request_holder: CommitRequestHolder[CommT],
                          commit_result_holder: CommitResultHolder):
        """Do prepare commit - to be implemented by subclasses."""
        pass

    def commit(self, transaction_ids: Sequence[str],
               commit_requests: Sequence[CommitRequest[CommT]]) -> CommitResult:
        """Commit with prepared transaction IDs and commit requests."""
        self._check_opened()
        self._lazy_init_executor_service()

        min_transaction_id = self._get_min_transaction_id(transaction_ids)
        self._check_last_transaction_id(min_transaction_id)

        def commit_internal():
            # Construct commit request holder
            commit_request_holder = CommitRequestHolder(
                transaction_id=min_transaction_id,
                stream_id=self.get_stream_id(),
                schema_name=self.context.schema_name,
                table_name=self.context.table_name,
                requests=commit_requests
            )

            # Only for tracking commit result
            commit_result = CommitResultHolder(min_transaction_id)
            self._result_map[min_transaction_id] = commit_result
            self._to_commit_queue.put(commit_request_holder)
            self._last_transaction_id = min_transaction_id

            return commit_result

        commit_result_holder = self._try_transaction_lock(commit_internal)
        return commit_result_holder

    @abstractmethod
    def do_commit(self, commit_request_holder: CommitRequestHolder[CommT],
                  commit_result_holder: CommitResultHolder) -> str:
        """Do commit - to be implemented by subclasses."""
        pass

    def _internal_run_commit(self):
        """Internal commit runner (runs in background thread)."""
        thread_name = threading.current_thread().name
        stream_id = self.get_stream_id()
        log_prefix = f"BulkLoadCommitter {stream_id} commit thread [{thread_name}]"
        
        logger.info(f"{log_prefix} started")

        try:
            while self._thread_service_state or not self._to_commit_queue.empty():
                # Try to get next commit request with timeout
                try:
                    request_holder = self._to_commit_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                # Process commit request
                self._process_commit_request(request_holder, stream_id)
                
        except Exception as e:
            logger.error(f"{log_prefix} crashed with unexpected error", exc_info=e)
        finally:
            logger.info(f"{log_prefix} finished and exiting")

    def _process_commit_request(self, request_holder: CommitRequestHolder[CommT], stream_id: str):
        """Process a single commit request."""
        transaction_id = request_holder.get_transaction_id()
        result_holder: Optional[CommitResultHolder] = None

        try:
            result_holder = self._try_transaction_lock(lambda: self._result_map.get(transaction_id))
            
            # Execute commit operation
            commit_id = self.do_commit(request_holder, result_holder)

            # Update result holder with success state
            result_holder.set_committed()
            result_holder.set_commit_id(commit_id)

            # Add to result queue for listening
            self._try_transaction_lock(lambda: self._result_queue.put(result_holder))
            logger.info(f"BulkLoadCommitter {stream_id} committed transactionId {transaction_id}. wait for result.")

        except Exception as e:
            logger.error(
                f"BulkLoadCommitter {stream_id} commit transactionId {transaction_id} failed.",
                exc_info=e)
            if result_holder is not None:
                result_holder.set_error(e)
            self._remove_result_holder(transaction_id)

    def _remove_result_holder(self, transaction_id: str):
        """Remove result holder from map and queue."""
        try:
            def remove_internal():
                # Remove from result queue if present
                temp_queue = queue.Queue()
                while not self._result_queue.empty():
                    try:
                        result = self._result_queue.get_nowait()
                        if result.get_transaction_id() != transaction_id:
                            temp_queue.put(result)
                    except queue.Empty:
                        break

                # Put back non-matching results
                while not temp_queue.empty():
                    try:
                        self._result_queue.put(temp_queue.get_nowait())
                    except queue.Empty:
                        break

                # Remove from result map
                self._result_map.pop(transaction_id, None)

                # Signal all waiting threads
                self._transaction_condition.notify_all()
                return None

            self._try_transaction_lock(remove_internal)
        except Exception:
            # Ignore errors during cleanup
            pass

    def _internal_run_listener(self):
        """Internal listener runner (runs in background thread)."""
        thread_name = threading.current_thread().name
        logger.info(f"BulkLoadCommitter {self.get_stream_id()} listener thread [{thread_name}] started...")

        # Once loop all result in queue means one batch
        # Read next batch after interval ms
        # For same commitResult, we will take some time to reTouch it
        # For diff commitResult, we will run listen immediately

        try:
            while self._thread_service_state:
                try:
                    batch_size = self._result_queue.qsize()
                    # Only exit if not initialized and no pending results
                    if batch_size == 0 and len(self._result_map) == 0 and not self._thread_service_state:
                        logger.info(
                            f"BulkLoadCommitter {self.get_stream_id()} listener thread [{thread_name}] exiting - no pending results")
                        return

                    while batch_size > 0:
                        try:
                            commit_result_holder = self._result_queue.get(timeout=0.2)  # 200ms timeout
                        except queue.Empty:
                            commit_result_holder = None

                        if commit_result_holder is not None:
                            transaction_id = commit_result_holder.get_transaction_id()

                            try:
                                if commit_result_holder.is_finished():
                                    logger.debug(
                                        f"BulkLoadCommitter {self.get_stream_id()} listener thread [{thread_name}] "
                                        f"removing finished transaction {transaction_id}")
                                    self._remove_result_holder(transaction_id)
                                else:
                                    self.do_listen(transaction_id, commit_result_holder)

                                    if not commit_result_holder.is_finished():
                                        # Re-add to queue if not finished and still in map
                                        def readd_to_queue():
                                            if transaction_id in self._result_map:
                                                self._result_queue.put(commit_result_holder)
                                            return None

                                        self._try_transaction_lock(readd_to_queue)
                                    else:
                                        self._remove_result_holder(transaction_id)

                                    logger.info(
                                        f"BulkLoadCommitter {self.get_stream_id()} listener transactionId {transaction_id} "
                                        f"listen state {commit_result_holder.get_commit_state()}.")
                            except Exception as e:
                                logger.error(
                                    f"BulkLoadCommitter {self.get_stream_id()} listener transactionId {transaction_id} failed.",
                                    exc_info=e)
                                commit_result_holder.set_error(e)  # This already sets the future exception
                                self._remove_result_holder(transaction_id)

                        batch_size -= 1

                    # Once batch run finished, wait for some time to next loop, or new result need to listen
                    if self._thread_service_state:
                        time.sleep(0.5)  # Reduced sleep time for faster shutdown response

                except Exception as e:
                    self._thread_service_state = False
                    logger.error(
                        f"BulkLoadCommitter {self.get_stream_id()} listener thread [{thread_name}] batch processing error: {e}",
                        exc_info=e)
                    break  # Exit the while loop on exception
        except Exception as e:
            self._thread_service_state = False
            logger.error(
                f"BulkLoadCommitter {self.get_stream_id()} listener thread [{thread_name}] crashed with unexpected error",
                exc_info=e)
        finally:
            logger.info(
                f"BulkLoadCommitter {self.get_stream_id()} listener thread [{thread_name}] finished and exiting")

    @abstractmethod
    def do_listen(self, transaction_id: str, commit_result_holder: CommitResultHolder):
        """Do listen - to be implemented by subclasses."""
        pass

    def abort_commit(self, transaction_ids: Sequence[str],
                     commit_requests: Sequence[CommitRequest[CommT]]):
        """Abort commit with transaction IDs and commit requests."""
        self._check_opened()
        min_transaction_id = self._get_min_transaction_id(transaction_ids)
        self._check_last_transaction_id(min_transaction_id)

        # Commit may not do、doing、done
        commit_result_holder_ref = self._try_transaction_lock(
            lambda: self._result_map.get(min_transaction_id) if min_transaction_id in self._result_map else None)

        logger.info(f"BulkLoadCommitter {self.get_stream_id()} abort transactionId {min_transaction_id}.")

        # Construct commit request holder
        commit_request_holder = CommitRequestHolder(
            transaction_id=min_transaction_id,
            stream_id=self.get_stream_id(),
            schema_name=self.context.schema_name,
            table_name=self.context.table_name,
            requests=commit_requests
        )

        # Create or use existing commit result holder
        commit_result_holder = CommitResultHolder(
            min_transaction_id) if commit_result_holder_ref is None else commit_result_holder_ref

        try:
            self.do_abort_commit(min_transaction_id, commit_request_holder, commit_result_holder)
            commit_result_holder.set_abort()
        except Exception as e:
            commit_result_holder.set_error(e)
        finally:
            self._remove_result_holder(min_transaction_id)

    @abstractmethod
    def do_abort_commit(self, transaction_id: str, commit_request_holder: CommitRequestHolder[CommT],
                        commit_result_holder: CommitResultHolder):
        """Do abort commit - to be implemented by subclasses."""
        pass

    def close(self, wait_time_ms: int = 5000):
        """Close the committer with wait time."""
        logger.info(
            f"BulkLoadCommitter {self.context.stream_id} {self.context.schema_name} {self.context.table_name} start to close...")

        with self._main_lock:
            if not self._initialized:
                logger.info(
                    f"BulkLoadCommitter {self.context.stream_id} {self.context.schema_name} {self.context.table_name} already closed.")
                return

            # Don't set shutdown flags immediately - let threads finish current work
            self._initialized = False
            logger.info(f"BulkLoadCommitter {self.context.stream_id} marking for shutdown")

        wait_time_seconds = wait_time_ms / 1000.0

        def wait_for_completion():
            """Wait for all commits to finish or abort."""
            import time
            start_time = time.time()

            # Wait for resultMap is empty
            if self._result_map and len(self._result_map) > 0:
                while len(self._result_map) > 0:
                    # Check if we've exceeded the total wait time
                    elapsed = time.time() - start_time
                    if elapsed >= wait_time_seconds:
                        logger.warning(f"Timeout waiting for commits to complete after {wait_time_ms}ms")
                        break

                    def wait_internal():
                        try:
                            # Wait for condition and release lock with timeout (1 second or remaining time)
                            remaining_time = min(1.0, wait_time_seconds - elapsed)
                            self._transaction_condition.wait(timeout=remaining_time)
                        except:
                            pass
                        return None

                    self._try_transaction_lock(wait_internal)

            # Wait for executor threads to complete using their futures
            self._thread_service_init = False
            # Now stop the threads after waiting
            self._thread_service_state = False
            if self._commit_timer_future is not None and not self._commit_timer_future.done():
                try:
                    elapsed = time.time() - start_time
                    remaining_time = max(0, int(wait_time_seconds - elapsed))
                    if remaining_time > 0:
                        self._commit_timer_future.result(timeout=remaining_time)
                        logger.debug("Commit thread completed successfully")
                except Exception:
                    logger.warning(f"Wait for commit thread completion timeout")

            if self._listener_future is not None and not self._listener_future.done():
                try:
                    elapsed = time.time() - start_time
                    remaining_time = max(0, int(wait_time_seconds - elapsed))
                    if remaining_time > 0:
                        self._listener_future.result(timeout=remaining_time)
                        logger.debug("Listener thread completed successfully")
                except Exception as e:
                    logger.warning(f"Error waiting for listener thread completion: {e}")

        def cleanup_finally():
            """Cleanup thread services with proper timeout handling."""
            logger.info(f"BulkLoadCommitter {self.context.stream_id} cleanup_finally() starting")

            # Signal all waiting threads to wake up and exit
            try:
                logger.debug(f"BulkLoadCommitter {self.context.stream_id} notifying all waiting threads")
                with self._transaction_condition:
                    self._transaction_condition.notify_all()
            except Exception as e:
                logger.warning(f"Failed to notify waiting threads: {e}")

            # Cleanup commit executor and thread
            try:
                if self._commit_executor is not None:
                    logger.debug(f"BulkLoadCommitter {self.context.stream_id} shutting down commit executor")
                    self._commit_executor.shutdown(wait=False)
                    self._commit_executor = None
                    self._commit_timer_future = None
                    logger.info(f"BulkLoadCommitter {self.context.stream_id} commit executor cleanup completed")
            except Exception as e:
                logger.warning(f"Error during commit executor cleanup: {e}")

            # Cleanup listener executor and thread
            try:
                if self._listener_executor is not None:
                    logger.info(f"BulkLoadCommitter {self.context.stream_id} shutting down listener executor")
                    self._listener_executor.shutdown(wait=False)
                    self._listener_executor = None
                    self._listener_future = None
                    logger.info(f"BulkLoadCommitter {self.context.stream_id} listener executor cleanup completed")
            except Exception as e:
                logger.warning(f"Error during listener executor cleanup: {e}")

            logger.info(f"BulkLoadCommitter {self.context.stream_id} cleanup_finally() completed")

        try:
            wait_for_completion()
        finally:
            cleanup_finally()

        logger.info(
            f"BulkLoadCommitter {self.context.stream_id} {self.context.schema_name} {self.context.table_name} close success.")

    def add_committable(self, committable: Committable):
        """Add a committable to the committer."""
        # Default implementation - subclasses can override
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False  # Don't suppress exceptions
