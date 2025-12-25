from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple
from typing import TYPE_CHECKING

from clickzetta.connector.v0.exceptions import CZException
from clickzetta_ingestion.realtime.message import ArrowResponseMessage, ArrowRequestMessage
from clickzetta_ingestion.realtime.realtime_options import RetryStatus
from clickzetta_ingestion.realtime.rpc_callback import RpcResponseRetryCallback

if TYPE_CHECKING:
    from clickzetta_ingestion.realtime.arrow_stream import ArrowStream

log = logging.getLogger(__name__)


@dataclass
class RpcResponseHandler:
    """Handler for RPC responses with callback mapping"""
    session: ArrowStream
    # Map of request ID to request message
    requests: Dict[int, ArrowRequestMessage] = field(default_factory=dict)
    response_callbacks: Dict[int, RpcResponseRetryCallback] = field(default_factory=dict)
    # Lock for thread safety
    handler_lock: threading.Lock = field(default_factory=threading.RLock)
    # Map of request ID to retry count
    request_retry_times: Dict[int, int] = field(default_factory=dict)
    # Set of retryable status codes
    retry_status: Set[RetryStatus] = field(default_factory=set)

    def add_rpc_request(self, request_id: int, request: ArrowRequestMessage, callback: RpcResponseRetryCallback):
        """Add callback for request

        Args:
            request_id: Request ID
            request: Request message
            callback: Callback for handling response
        """
        with self.handler_lock:
            self.requests[request_id] = request
            self.response_callbacks[request_id] = callback

    def remove_rpc_request(self, request_id: int) -> Tuple[
        Optional[ArrowRequestMessage], Optional[RpcResponseRetryCallback]]:
        """Remove and return callback for request

        Args:
            request_id: Request ID

        Returns:
            Tuple of (request, callback) if found, else (None, None)
        """
        with self.handler_lock:
            request = self.requests.pop(request_id, None)
            callback = self.response_callbacks.pop(request_id, None)
            return request, callback

    def contains_rpc_request(self, request_id: int) -> bool:
        """Check if request is outstanding

        Args:
            request_id: Request ID

        Returns:
            True if request is outstanding
        """
        with self.handler_lock:
            return request_id in self.requests

    def handle(self, response: ArrowResponseMessage):
        """Handle response by dispatching to appropriate callback

        Args:
            response: Response message
        """
        request_id = response.get_request_id()
        request, callback = self.remove_rpc_request(request_id)

        if not callback or not request:
            log.warning(
                f"Session {self.session.session_id} Ignoring response for RPC {request_id} "
                "since it is not outstanding"
            )
            return

        try:
            if response and response.get_status_code() == 0:  # Success
                callback.on_success(request, response)
            else:
                callback.on_failure(request, response,
                                    CZException(
                                        f"Request failed with status: {response.get_status_code()}, "
                                        f"e:{response.message if response.message else ''}"))

        except Exception as e:
            log.error(f"Error handling response for request {request_id}: {e}")
            self.exception_caught(e)

    def exception_caught(self, error: Exception):
        """Handle exceptions from stream observer"""
        callback_size = len(self.response_callbacks)
        if callback_size > 0:
            log.error(
                f"Session {self.session.session_id} Still have {callback_size} "
                "requests outstanding when rpc running."
            )
            self.fail_outstanding_requests(error)

    def fail_outstanding_requests(self, cause: Exception) -> None:
        """Fail all outstanding requests with error

        Args:
            cause: Exception to fail with
        """
        with self.handler_lock:
            for request_id, callback in list(self.response_callbacks.items()):
                try:
                    request = self.requests.get(request_id)
                    log.warning(f"Failing request {request_id} due to: {cause}")
                    callback.on_error(request, None, cause)
                except Exception as e:
                    log.warning(
                        f"Session {self.session.session_id} ResponseHandler.onFailure "
                        f"throws exception: {e}"
                    )

            self.response_callbacks.clear()
            self.requests.clear()

    def close(self):
        """Close handler and fail any outstanding requests"""
        with self.handler_lock:
            if self.response_callbacks:
                log.warning(f"Session {self.session.session_id} still have {len(self.response_callbacks)} "
                            "requests outstanding when session close")
                self.fail_outstanding_requests(Exception("Session closed"))
            self.response_callbacks.clear()
            self.requests.clear()
