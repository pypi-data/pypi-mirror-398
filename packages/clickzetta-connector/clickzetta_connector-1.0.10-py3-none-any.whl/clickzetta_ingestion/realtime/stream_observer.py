import datetime
import logging
import threading
from enum import Enum
from typing import Any, Set, Tuple, OrderedDict

import grpc

from clickzetta.connector.v0.exceptions import CZException
from clickzetta_ingestion._proto import ingestion_v2_pb2
from clickzetta_ingestion.realtime.message import ArrowResponseMessage

log = logging.getLogger(__name__)


class ErrorStatus(Enum):
    """Error status for stream observer"""
    NO_CAUSE = "no_cause"  # Ignore error
    SET_CAUSE = "set_cause"  # Set root cause and exit
    NEED_RETRY = "need_retry"  # Need retry with reconnect


class ReferenceCountedStreamObserver:
    """Stream request observer with reference counting and channel management."""

    def __init__(self, channel, request_observer: Any, loop=None):
        self.loop = loop
        self.channel = channel
        self.request_stream_observer = request_observer  # inner class ClientCallStreamObserver
        self._ref_count_lock = threading.Lock()
        self._ref_count = 0
        self.canceled = False
        self._observers_lock = threading.Lock()
        self.old_request_observers = set()

    def get_request_stream_observer(self):
        """Get current request stream observer"""
        return self.request_stream_observer

    def replace_with_new(self, new_stream_observer: 'ReferenceCountedStreamObserver'):
        """Replace current observer with new one"""
        if self.request_stream_observer and new_stream_observer:
            with self._observers_lock:
                self.old_request_observers.add(self.request_stream_observer)
        if new_stream_observer and new_stream_observer.get_request_stream_observer():
            self.request_stream_observer = new_stream_observer.get_request_stream_observer()

    def retain(self):
        """Increment reference count"""
        with self._ref_count_lock:
            self._ref_count += 1
        return self

    def get_channel(self):
        """Get associated channel"""
        return self.channel

    def on_next(self, request: Any):
        """Handle next value and return response future"""
        try:
            self._valid_on_cancel()
            if self.request_stream_observer:
                self.request_stream_observer.on_next(request)
        except Exception as e:
            log.error(f"Failed to handle next in ReferenceCountedStreamObserver: {e}")
            raise
        finally:
            with self._ref_count_lock:
                self._ref_count -= 1

    def on_error(self, error: Exception):
        """Handle error"""
        self._valid_on_cancel()
        if self.request_stream_observer:
            self.request_stream_observer.on_error(error)

    def on_completed(self):
        """Handle completion"""
        if self.canceled:
            return
        self._close_internal(completed=True)

    def on_cancel(self):
        """Handle cancellation"""
        self.canceled = True
        self._close_internal(completed=False)

    def _close_internal(self, completed: bool = True):
        """Internal close handling"""
        if self.request_stream_observer:
            log.debug(f"[_close_internal] Closing channel and request observer...")
            if completed:
                # Normal completion
                self.request_stream_observer.on_completed()
                for old_observer in self.old_request_observers:
                    old_observer.on_completed()
            else:
                self.request_stream_observer.cancel()
                for old_observer in self.old_request_observers:
                    old_observer.cancel()

        if self.channel:
            try:
                self.channel.close()
                self.channel = None
            except Exception as e:
                # Ignore channel close failure
                log.debug(f"Channel close failed: {e}")
        log.info(f"Channel close successfully")

    def _valid_on_cancel(self):
        """Validate canceled state"""
        if self.canceled:
            raise RuntimeError("RequestStreamObserver has already been canceled")

    @property
    def ref_cnt(self) -> int:
        """Get current reference count"""
        with self._ref_count_lock:
            return self._ref_count

    def __str__(self):
        return (f"ReferenceCountedStreamObserver("
                f"request_observer={self.request_stream_observer}, "
                f"channel={self.channel}, "
                f"ref_count={self._ref_count}, "
                f"canceled={self.canceled}, "
                f"old_observers={len(self.old_request_observers)})")


class ResponseStreamObserver:
    def __init__(self, outer):
        from clickzetta_ingestion.realtime.arrow_stream import ArrowStream
        self.outer: ArrowStream = outer
        self.outstanding_requests_future = None
        self._lock = threading.Lock()

        # Messages that should trigger retry
        self.retry_msgs: Set[Tuple[int, str]] = {
            (grpc.StatusCode.UNAVAILABLE.value[0], "Network closed for unknown reason"),
            (grpc.StatusCode.UNAVAILABLE.value[0], "io exception"),
            (grpc.StatusCode.CANCELLED.value[0], "RST_STREAM closed stream")
        }

    def _get_error_status(self, error: Exception) -> ErrorStatus:
        """Determine error status based on error type and message"""
        if isinstance(error, grpc.RpcError):
            # Get status code value directly from RpcError
            log.debug(f"Session {self.outer.session_id} mutate data hit RpcError: {error}, retry to handle it...")
            status = error.code().value[0]  # Get integer status code
            description = error.details() if error.details() else ""

            # Check if error should trigger retry
            for retry_code, retry_msg in self.retry_msgs:
                if status == retry_code and retry_msg in description:
                    return ErrorStatus.NEED_RETRY

        return ErrorStatus.SET_CAUSE

    def on_next(self, response: ingestion_v2_pb2.MutateResponse):
        self.outer.response_handler.handle(ArrowResponseMessage(response))

    def on_error(self, error: Exception):
        """Handle stream error based on error status"""
        try:
            error_status = self._get_error_status(error)

            if error_status == ErrorStatus.SET_CAUSE:
                # Set root cause and exit
                self.outer.root_cause.set(error)
                self.outer.response_handler.exception_caught(error)
                log.error(f"Session {self.outer.session_id} mutate data hit SET_CAUSE error! will exit soon...",
                          exc_info=error)

            elif error_status == ErrorStatus.NEED_RETRY:
                # Need retry with reconnect
                if self.outer.options.tablet_idle_recreate_support:
                    log.info(f"Session {self.outer.session_id} mutate data hit NEED_RETRY error! "
                             f"on_error left requestInFight {self.outer.request_in_flight} "
                             f"retry_request_count {self.outer.retry_request_count} "
                             f"requests ids {self.outer.response_handler.requests.keys()} "
                             f"outstanding_requests_future {self.outstanding_requests_future}",
                             f"will retry soon...", )

                    with self._lock:
                        if self.outstanding_requests_future is None:
                            # mark it in reconnect status first.
                            self.outer.channel_manager.report_last_rpc_status(-1)
                            self.outstanding_requests_future = self.outer.timer_thread_pool.add_job(
                                self.trigger_outstanding_requests_retry,
                                trigger='date',
                                next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=10),
                                args=(error,),
                                id='trigger_outstanding_requests_retry'
                            )
                else:
                    # No reconnect support, treat as fatal error
                    self.outer.root_cause.set(error)
                    self.outer.response_handler.exception_caught(error)
                    log.error(f"Session {self.outer.session_id} mutate data hit NEED_RETRY error! will exit soon...",
                              exc_info=error)

            elif error_status == ErrorStatus.NO_CAUSE:
                self.outer.response_handler.exception_caught(error)
                log.info(f"Session {self.outer.session_id} mutate data hit NO_CAUSE error. ignore it",
                         exc_info=error)

        except Exception as e:
            log.error(f"Failed to handle stream error: {e}", exc_info=e)
            self.outer.root_cause.set(e)

    def on_completed(self):
        pass

    def trigger_outstanding_requests_retry(self, error: Exception):
        """Trigger retry for all outstanding requests
        
        Args:
            error: Error that triggered retry
        """
        try:
            # Build response messages for retry
            resp_tree_map = OrderedDict[int, ArrowResponseMessage]()

            with self.outer.response_handler.handler_lock:
                for request_id, request in self.outer.response_handler.requests.items():
                    try:
                        # Build retry response message
                        response = self._build_retry_response_message(request_id, request.message)
                        resp_tree_map[request_id] = response
                    except Exception as e:
                        log.error(
                            f"Failed to build retry response for request {request_id}: {e}",
                            exc_info=True
                        )
                        self.outer.root_cause.set(CZException(str(e)))

            log.info(
                f"Triggering outstanding requests retry. Current requests in flight: "
                f"{self.outer.request_in_flight}, retry count: {self.outer.retry_request_count}, "
                f"outstanding request IDs: {list(resp_tree_map.keys())}"
            )

            need_reset = True
            try:
                # Ensure that it is processed in the order of request_id
                resp_tree_map = OrderedDict[int, ArrowResponseMessage](
                    sorted(resp_tree_map.items(), key=lambda t: t[0]))
                for request_id, response in resp_tree_map.items():
                    if self.outer.response_handler.contains_rpc_request(request_id):
                        self.outer.response_handler.handle(response)
                        # If the retry request is handle successfully
                        # (the corresponding request is found in responseHandler),
                        # set need_reset to false, indicating that the reconnection status does not need to be reset.
                        need_reset = False
            except Exception as e:
                log.error(f"Failed to handle retry responses: {e}")
                self.outer.root_cause.set(CZException(str(e)))

            log.info(
                f"After retry trigger. Current requests in flight: {self.outer.request_in_flight}, "
                f"retry count: {self.outer.retry_request_count}, "
                f"outstanding request IDs: {list(resp_tree_map.keys())}"
            )

            if self.outer.retry_request_count.get() > 0 and not resp_tree_map:
                # Double NEED_RETRY onError exception case
                self.outer.root_cause.set(CZException(str(error)))
            elif (self.outer.request_in_flight == 0 and
                  self.outer.retry_request_count.get() == 0 and
                  not resp_tree_map):
                # Handle empty request or RPC hit.
                # There are no requests that need to be retried before, and the system can safely
                # add a reconnect completion task, allowing the system to reconnect.
                need_reset = False
                self.outer.channel_manager.add_reconnect_finish_task(
                    None,
                    lambda trigger: True
                )

            # Reset reconnect status if needed
            if need_reset:
                self.outer.channel_manager.reset_reconnect_status(False)

            # Clear outstanding requests future
            if hasattr(self, 'outstanding_requests_future'):
                with self._lock:
                    if hasattr(self, 'outstanding_requests_future'):
                        self.outstanding_requests_future = None

        except Exception as e:
            log.error(f"Failed to trigger outstanding requests retry: {e}")
            raise

    def _build_retry_response_message(self, request_id: int, request: Any) -> ArrowResponseMessage:
        """Build response message for retry
        
        Args:
            request_id: Request ID
            request: Original request
            
        Returns:
            Response message for retry
        """
        # Create retry response
        response: ingestion_v2_pb2.MutateResponse = ingestion_v2_pb2.MutateResponse()
        response.batch_id = request_id
        response.status.code = ingestion_v2_pb2.Code.STREAM_UNAVAILABLE
        response.status.error_message = "Retry triggered by stream error"

        return ArrowResponseMessage(response)
