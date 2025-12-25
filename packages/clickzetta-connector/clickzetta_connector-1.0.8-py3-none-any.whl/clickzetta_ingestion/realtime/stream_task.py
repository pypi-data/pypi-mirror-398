import logging
from concurrent.futures import Future
from typing import Callable, Optional

from clickzetta.connector.common.notify_executor import NotifyScheduledExecutor
from clickzetta_ingestion._proto import ingestion_v2_pb2
from clickzetta_ingestion.realtime.arrow_flush_task import ChannelData
from clickzetta_ingestion.realtime.message import AtomicInteger
from clickzetta_ingestion.realtime.realtime_options import RetryMode
from clickzetta_ingestion.realtime.rpc_callback import RequestStreamCallback
from clickzetta_ingestion.realtime.task import AbstractTask
from clickzetta_ingestion.rpc.rpc_request import ServerTokenMap

log = logging.getLogger(__name__)


class ArrowStreamTask(AbstractTask):
    """Task for retrying Arrow stream requests"""

    def get_id(self) -> int:
        return self.batch_id

    def skip_call(self, t: Optional[Exception] = None) -> Future:
        try:
            return super().skip_call(t)
        finally:
            self.retry_count.get_and_decrement()

    def __init__(self,
                 batch_id: int,
                 retry_count: AtomicInteger,
                 internal_ms: int,
                 retry_mode: RetryMode,
                 request: ingestion_v2_pb2.MutateRequest,
                 response: ingestion_v2_pb2.MutateResponse,
                 server_token_map: ServerTokenMap,
                 channel_data_supplier: Callable[[], ChannelData],
                 request_callback: RequestStreamCallback,
                 retry_executor: NotifyScheduledExecutor):
        """Initialize stream task
        
        Args:
            batch_id: Batch ID
            retry_count: Number of retries remaining
            internal_ms: Retry interval in milliseconds  
            retry_mode: Retry mode
            request: Original mutate request
            server_token_map: Server token map
            channel_data_supplier: Supplier for channel data
            request_callback: Callback for request handling
        """
        super().__init__()
        self.batch_id = batch_id
        self.retry_count = retry_count
        self.internal_ms = internal_ms
        self.retry_mode = retry_mode
        self.request = request
        self.response = response
        self.server_token_map = server_token_map
        self.channel_data_supplier = channel_data_supplier
        self.request_callback = request_callback
        self.retry_executor = retry_executor

    def call_internal(self):
        """Execute the retry task"""

        def _retry():
            try:
                log.debug(f"Retry request by stream task batch_id {self.batch_id}...")
                if self.retry_mode in (RetryMode.BATCH_REQUEST_MODE, RetryMode.ROW_REQUEST_MODE):
                    channel_data = self.channel_data_supplier()
                    self.request_callback.target_host = str(channel_data.host_port)

                    request = self._reset_server_tokens(self.request)
                    self.request_callback.on_success(request, self.future)
                    try:
                        with channel_data.lock:
                            channel_data.reference_stream_observer.on_next(request)
                            log.debug(f"Retry request by stream task {self.batch_id} sent")
                    except Exception as e:
                        log.warning(
                            f"Failed to send request by stream task {self.batch_id}, {self.retry_count} "
                            f"retrying this request, reason: {e}")
                        self.request_callback.on_failure(request, self.future, e)

            except Exception as e:
                log.error(f"Failed to retry request by stream task {self.batch_id}", e)
                self.future.set_exception(e)
            finally:
                self.retry_count.get_and_decrement()
                log.debug(f"Retry request by stream task finished {self.batch_id}. retry_count: {self.retry_count}")

        self.retry_executor.add_task(
            _retry,
            self.internal_ms * (self.retry_count.get() + 1)
        )

    def _reset_server_tokens(self, request: ingestion_v2_pb2.MutateRequest) -> ingestion_v2_pb2.MutateRequest:
        """Reset server tokens in request"""
        if not self.server_token_map or not self.server_token_map.server_tokens:
            # Clear all tokens
            request.ClearField('server_token')
            request.ClearField('server_tokens')
        elif self.server_token_map.is_legacy_server_token_required():
            # Set legacy token and new tokens
            request.server_token = self.server_token_map.get_legacy_server_token()
            request.ClearField('server_tokens')
            request.server_tokens.update(self.server_token_map.server_tokens)
        else:
            # Only set new tokens
            request.ClearField('server_token')
            request.ClearField('server_tokens')
            request.server_tokens.update(self.server_token_map.server_tokens)
        return request
