from __future__ import absolute_import
from __future__ import annotations
from __future__ import division

import logging
import threading
from dataclasses import dataclass, field
from typing import Dict, Optional
from typing import TYPE_CHECKING
from clickzetta_ingestion._proto import ingestion_v2_pb2

from clickzetta.connector.v0.exceptions import CZException
from clickzetta_ingestion.realtime.message import ArrowSuccessMessage, \
    ArrowFailureMessage, ArrowErrorMessage, Message

if TYPE_CHECKING:
    from clickzetta_ingestion.realtime.arrow_stream import ArrowStream

log = logging.getLogger(__name__)
import logging
from abc import ABC, abstractmethod
from concurrent.futures import Future
from typing import Any, TYPE_CHECKING

from clickzetta_ingestion.realtime.message import ArrowRequestMessage, ArrowResponseMessage

if TYPE_CHECKING:
    from clickzetta_ingestion.realtime.arrow_stream import ArrowStream

log = logging.getLogger(__name__)


class RpcCallback(ABC):
    """Base interface for RPC callbacks"""

    @abstractmethod
    def on_success(self, request: Any, response: Any):
        """Handle successful response"""
        pass

    @abstractmethod
    def on_failure(self, request: Any, response: Any, error: Exception):
        """Handle failed response"""
        pass

    @abstractmethod
    def on_error(self, request: Any, response: Any, error: Exception):
        """Handle error"""
        pass


class RequestStreamCallback:
    """Callback for handling stream requests"""

    def __init__(self, stream: ArrowStream):
        self.stream = stream
        self.target_host = None

        # Initialize reconnect configuration from options
        self.reconnect_support = stream.options.tablet_idle_recreate_support

    def on_success(self, request: Any, future: Future):
        """Handle successful request

        Args:
            request: Request message
            future: Future for async completion
        """
        self.stream.increment_requests()
        try:
            # Build request message
            request_message = ArrowRequestMessage(request)

            # Add request to response handler with callbacks
            self.stream.response_handler.add_rpc_request(
                request_message.get_request_id(),
                request_message,
                RpcResponseRetryCallback(self.stream, future)
            )

        except Exception as e:
            log.error(
                f"Failed to handle request on_success: {e} in targetHost: {self.target_host} ,"
                f"requestId: {request.request_id}")
            future.set_exception(e)
            self.stream.decrement_requests()

    def on_failure(self, request: Any, response: Future, error: Exception):
        """Handle failed response.
        be careful to call on_failure in RequestStreamCallback.
        onFailure only should catch exception after call RequestStreamCallback.on_success.
        it only should be called to roll back on_success status.
        """
        request_message = ArrowRequestMessage(request)
        if self.reconnect_support:
            if self.stream.response_handler.contains_rpc_request(request_message.get_request_id()):
                retry_response = RpcResponseRetryCallback.build_retry_response_message(request_message.get_request_id(),
                                                                                       request_message.message)
                self.stream.response_handler.handle(ArrowResponseMessage(retry_response))
                # This will not be set a future and decrement here, it will be processed by the corresponding
                # callback in the response_handler.
                # This future has been set in the on_success method of the RequestStreamCallback.
                return
        elif self.stream.response_handler.remove_rpc_request(request_message.get_request_id()):
            self.stream.decrement_requests()
        response.set_exception(error)


@dataclass
class RpcResponseRetryCallback:
    """Callback for handling RPC responses with retry support"""

    session: ArrowStream
    request_future: Future
    # Map of request ID to retry count
    request_retry_times: Dict[int, int] = field(default_factory=dict)
    # Lock for thread safety
    _request_retry_times_lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self):
        """Initialize after instance creation"""
        self.options = self.session.options

        # Initialize retry configuration
        self.retry_enable = self.options.request_failed_retry_enable
        self.retry_mode = self.options.request_failed_retry_mode
        self.max_retry = self.options.request_failed_retry_times
        self.retry_interval_ms = self.options.request_failed_retry_internal_ms
        self.retry_status = set(self.options.request_failed_retry_register_status.get_v2_code_list())

    def retry_condition(self, response: ArrowResponseMessage) -> bool:
        """Check if response meets retry conditions"""
        # Convert response status code to RetryStatus enum
        return response.get_status_code() in self.retry_status

    def build_success_message(self, request: ArrowRequestMessage, response: ArrowResponseMessage) -> Message:
        """Build success message"""
        return ArrowSuccessMessage(
            session_id=self.session.session_id,
            request=request.message,
            response=response.message
        )

    def build_failure_message(self, request: ArrowRequestMessage, response: ArrowResponseMessage) -> Message:
        """Build failure message"""
        return ArrowFailureMessage(
            session_id=self.session.session_id,
            request=request.message,
            response=response.message,
            arrow_table=self.session.arrow_table
        )

    def build_error_message(self, request: ArrowRequestMessage) -> Message:
        """Build error message"""
        return ArrowErrorMessage(
            session_id=self.session.session_id,
            arrow_table=self.session.arrow_table,
            request=request.message,
        )

    @staticmethod
    def build_retry_response_message(request_id: int,
                                     request: ingestion_v2_pb2.MutateRequest) -> ingestion_v2_pb2.MutateResponse:
        builder = ingestion_v2_pb2.MutateResponse()
        builder.batch_id = request_id
        builder.status.code = ingestion_v2_pb2.Code.STREAM_UNAVAILABLE
        builder.num_rows = request.data_block.num_rows

        for i in range(request.data_block.num_rows):
            mutate_row_status = ingestion_v2_pb2.MutateRowStatus()
            mutate_row_status.row_index = i
            mutate_row_status.code = ingestion_v2_pb2.Code.FAILED
            mutate_row_status.error_message = "hit need retry exception. build retry response message"
            builder.row_status_list.append(mutate_row_status)
        return builder

    def on_success(self, request: ArrowRequestMessage, response: ArrowResponseMessage):
        """Handle successful response"""
        try:
            # Update metrics
            # self.session.metrics.push_data_qps.mark()
            # self.session.metrics.push_data_record_count.mark(request.batch_count)
            # self.session.metrics.push_data_e2e_latency.update(time.time() - request.timestamp)
            self.session.options.error_type_handler.on_success(request, response)

            with self._request_retry_times_lock:
                self.request_retry_times.pop(request.get_request_id(), None)

            # Report RPC status
            self.session.report_last_rpc_status(
                request.get_request_id(),
                response.get_status_code(),
                request.message,
                response.message
            )
        except Exception as e:
            log.error(f"Error in on_success for request {request.get_request_id()}: {e}")
            raise
        finally:
            self.request_future.set_result(True)
            self.session.decrement_requests()

    def on_failure(self, request: ArrowRequestMessage, response: ArrowResponseMessage, error: Exception):
        """Handle failed response with retry"""
        # Build failure message
        failure_msg = self.build_failure_message(request, response)

        try:
            if self.retry_enable and self.retry_condition(response):
                retry_count = self.request_retry_times.get(request.get_request_id(), 0)

                if retry_count < self.max_retry:
                    if self.options.request_failed_retry_log_debug_enable:
                        error_msg = (
                            f"mutate data with sessionId {self.session.session_id}, "
                            f"table [{self.session.arrow_table.schema_name}."
                            f"{self.session.arrow_table.table_name}], "
                            f"batch id {request.get_request_id()} failed. "
                            f"rows {failure_msg.get_total_rows_count()}, "
                            f"error row nums {failure_msg.get_error_rows_count()}. "
                            f"will retry in {retry_count + 1} times."
                        )
                        log.info(error_msg, exc_info=error)

                    with self._request_retry_times_lock:
                        self.request_retry_times[request.get_request_id()] = self.request_retry_times.get(
                            request.get_request_id(), 0) + 1

                    try:
                        def callback():
                            """Create retry callback"""
                            try:
                                return self.session.send_stream_request(
                                    internal_ms=self.retry_interval_ms * (retry_count + 1),
                                    retry_mode=self.retry_mode,
                                    request=request.message,
                                    response=response.message
                                )
                            except Exception as e:
                                raise CZException(f"Failed to create retry task: {e}")

                        # Report status and execute callback if needed
                        supplier = self.session.report_last_rpc_status(
                            request.get_request_id(),
                            response.get_status_code(),
                            request.message,
                            response.message,
                            callback
                        )

                        if supplier:
                            supplier()
                        return

                    except Exception as e:
                        error_msg = (
                            f"mutate data with sessionId {self.session.session_id} "
                            f"table [{self.session.arrow_table.schema_name}."
                            f"{self.session.arrow_table.table_name}] "
                            f"batch id {request.get_request_id()} failed in onFailure. "
                            f"rows {failure_msg.get_total_rows_count()} "
                            f"error row nums {failure_msg.get_error_rows_count()}."
                        )
                        log.error(error_msg, exc_info=e)

            # Update metrics
            # self.session.metrics.push_data_failed_qps.mark()

            with self._request_retry_times_lock:
                self.request_retry_times.pop(request.get_request_id(), None)

            # Default is terminate instance on error
            if self.options.error_type_handler == "terminate_instance":
                self.session.root_cause.set(error)

            self.options.error_type_handler.on_failure(request, response, error)

        except Exception as e:
            log.error(f"Error handling failure for request {request.get_request_id()}: {e}")
            raise
        finally:
            self.request_future.set_result(False)
            self.session.decrement_requests()

    def on_error(self, request: ArrowRequestMessage, response: Optional[ArrowResponseMessage], error: Exception):
        """Handle error from stream observer"""
        try:
            if request:
                log.error(f"Error for request {request.get_request_id()}: {error}")
                self.options.error_type_handler.on_failure(request, response, error)
        except Exception as e:
            log.error(f"Failed to handle error: {e}")
        finally:
            self.request_retry_times.pop(request.get_request_id(), None)
            self.request_future.set_result(False)
            self.session.decrement_requests()
