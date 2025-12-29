import logging
import threading
import uuid
from enum import Enum
from functools import wraps
from typing import List, Tuple, Union, Callable, TypeVar, Optional, Any

from apscheduler.schedulers.background import BackgroundScheduler

from clickzetta.connector.common.notify_executor import NotifyScheduledExecutor
from clickzetta.connector.v0.connection import Client
from clickzetta.connector.v0.enums import RealtimeOperation
from clickzetta.connector.v0.exceptions import CZException
from clickzetta_ingestion._proto import ingestion_v2_pb2
from clickzetta_ingestion.realtime.arrow_flusher import Flusher
from clickzetta_ingestion.realtime.arrow_row import ArrowRow
from clickzetta_ingestion.realtime.arrow_table import ArrowTable
from clickzetta_ingestion.realtime.buffer import Buffer
from clickzetta_ingestion.realtime.channel_manager import ChannelManager
from clickzetta_ingestion.common.configure import Configure
from clickzetta_ingestion.realtime.arrow_flush_task import ChannelData, ArrowFlushTask
from clickzetta_ingestion.realtime.message import AtomicReference, AtomicInteger
from clickzetta_ingestion.realtime.realtime_options import CZSessionOptions, RetryMode
from clickzetta_ingestion.realtime.response_handler import RpcResponseHandler
from clickzetta_ingestion.realtime.row_pool import RowQueuePool, RowPool
from clickzetta_ingestion.realtime.rpc_callback import RequestStreamCallback
from clickzetta_ingestion.realtime.size_manager import WriteOperation
from clickzetta_ingestion.realtime.stream_observer import ResponseStreamObserver
from clickzetta_ingestion.rpc.cz_igs_context import CZIgsContext
from clickzetta_ingestion.rpc.rpc_request import ServerTokenMap
from clickzetta_ingestion.realtime.stream_task import ArrowStreamTask

log = logging.getLogger(__name__)
R = TypeVar('R')


def run_or_wait_in_commit(timeout_ms: int = 1000):
    """Decorator to handle commit state and waiting"""

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(self: 'ArrowStream', *args, **kwargs) -> R:
            # Wait for any ongoing commit
            with self.stream_lock:
                while self.in_commit:
                    try:
                        self.validate()  # Check for root cause
                        self.stream_condition.wait(timeout_ms / 1000)
                    except Exception as e:
                        log.error(f"Failed to run_or_wait_in_commit! e:{e}")
                        if self.root_cause.get() is None:
                            raise self.root_cause.set(e)
                        return None
                self.in_commit = True
                log.debug(f"Thread {threading.current_thread().name} running function {func.__name__}() in commit")
                try:
                    # Execute the actual function
                    return func(self, *args, **kwargs)
                finally:
                    # Reset commit state and notify waiters
                    log.debug(
                        f"Thread {threading.current_thread().name} finished function [{func.__name__}()] in commit")
                    self.in_commit = False
                    return None

        return wrapper

    return decorator


def commit_with_lock():
    """Decorator to handle commit state and waiting with lock"""

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(self: 'ArrowStream', *args, **kwargs) -> R:
            if not self.in_commit:
                log.error("Cannot commit while not in commit status")
                raise CZException("Cannot commit while not in commit status")

            with self.stream_condition:
                try:
                    return func(self, *args, **kwargs)
                finally:
                    self.stream_condition.notify_all()

        return wrapper

    return decorator


class RowOperation(Enum):
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    UPSERT = "upsert"


class RowOperator(Enum):
    INSERT = "INSERT"
    INSERT_IGNORE = "INSERT_IGNORE"
    UPDATE = "UPDATE"
    UPSERT = "UPSERT"
    DELETE = "DELETE"
    DELETE_IGNORE = "DELETE_IGNORE"


class ArrowStream:
    def __init__(self, client: Client, arrow_table: ArrowTable, options: CZSessionOptions,
                 operation: RealtimeOperation):
        self._closed = False
        self.client = client
        self.arrow_table = arrow_table
        self.options: CZSessionOptions = options
        self.client_context: CZIgsContext = client.igs_client.client_context
        self.session_id = str(uuid.uuid4())
        self.operation = operation

        # Configuration
        self.configure: Configure = self.client_context.configure
        self.complex_type_recheck = self.configure.get_bool("arrow.row.format.check", True)
        self.memory_tracking = self.configure.get_bool("on.heap.memory.support", False)
        self.memory_factor = self.configure.get_float("on.heap.memory.factor", 0.4)

        # Initialize locks and state
        self.stream_lock = threading.RLock()
        self.stream_condition = threading.Condition(self.stream_lock)
        self.current_buffer: Optional[Buffer] = None
        self.commit_wait_timeout_ms: int = 1000
        self.in_commit: bool = False
        self.batch_id_lock = threading.Lock()
        self.current_batch_id = 0
        self.flush_atomic_lock = threading.Lock()
        self.should_flush: bool = False

        # Server token management
        self.server_token_map = ServerTokenMap(
            arrow_table.schema_name,
            arrow_table.table_name
        )

        # Initialize row pool
        self.row_pool: Optional[RowPool] = None
        self.pool_support = self.configure.get_bool("row.pool.support", False)
        if self.pool_support:
            pool_size = min(
                self.configure.get_int("row.pool.max.size", 20000),
                options.mutation_buffer_lines_num * options.mutation_buffer_max_num + 1
            )
            self.row_pool = RowQueuePool(
                pool_size=pool_size,
                row_loader=self._create_empty_row
            )
            self.init_row_pool()

        # Initialize callbacks and listeners
        self.request_callback = RequestStreamCallback(self)
        self.response_stream_observer = ResponseStreamObserver(self)

        # Initialize async flusher
        self.flusher: Flusher = Flusher.build(options, self.configure, self.stream_condition)

        # shared exception from flusher.
        self.root_cause: AtomicReference = self.flusher.get_exception_holder()

        # Initialize metrics
        self.metrics = None
        self.initialized = True

        # Channel data management
        self._channel_data = None
        self._channel_lock = threading.Lock()
        self.channel_manager: Optional[ChannelManager] = None
        self.response_handler = RpcResponseHandler(self)

        # Timer related
        self.flush_interval = options.flush_interval
        self.timer_thread_pool = BackgroundScheduler()
        self.timer_thread_pool.start()
        self._flush_timer_lock = threading.Lock()
        if self.flush_interval > 0:
            self._start_flush_to_queue_timer()

        # Add request tracking
        self.request_in_flight = 0
        self._request_lock = threading.RLock()

        # Connection retry related
        self.retry_executor = NotifyScheduledExecutor("arrow-stream-retry-executor")
        self.retry_request_count = AtomicInteger(0)

    def init_row_pool(self):
        """Initialize row pool if enabled"""
        if not self.pool_support or not self.row_pool:
            return

        try:
            # Pre-create some rows but don't fill the pool completely
            init_size = self.row_pool.pool_size // 2
            for _ in range(init_size):
                row = self._create_empty_row()
                try:
                    self.row_pool.queue.put_nowait(row)
                except Exception as e:  # Queue is full
                    log.error(f"Failed to initialize row pool: {e}")
                    break

            log.info(f"Pre-created {init_size} rows in pool")

        except Exception as e:
            log.error(f"Failed to initialize row pool: {e}")
            raise

    def _create_empty_row(self) -> ArrowRow:
        """Create an empty row with default settings"""
        return ArrowRow(
            arrow_table=self.arrow_table,
            operation_type=None,  # Will be set when row is acquired
            complex_type_recheck=self.complex_type_recheck
        )

    def get_row(self, operation_type) -> ArrowRow:
        """Get a row from pool or create new one"""
        if not self.pool_support or not self.row_pool:
            return self._create_empty_row()

        try:
            row: ArrowRow = self.row_pool.acquire_row()
            row.reset_row_meta(self.arrow_table, operation_type)
            return row
        except Exception as e:
            log.error(f"Failed to get row from pool: {e}")
            # Fallback to creating new row
            return self._create_empty_row()

    def return_row(self, row: ArrowRow):
        """Return a row to the pool"""
        if not self.pool_support or not self.row_pool:
            return

        try:
            self.row_pool.release_row(row)
        except Exception as e:
            log.error(f"Failed to return row to pool: {e}")

    def init_rpc_connection(self, workers: List[Tuple[str, int]]):
        """Initialize RPC connection and register reconnect task"""
        try:
            self.validate()

            if not self.channel_manager:
                self.channel_manager = ChannelManager(
                    outer_stream=self,
                    session_id=self.session_id,
                    root_cause=self.root_cause,
                    options=self.options,
                )

                # Build channels
                success = self.channel_manager.build_channels(
                    host_ports=workers,
                    rpc_call_options=self.options.rpc_call_options,
                    callback=None
                )
                if not success:
                    error_msg = f"Failed to initialize channel connections: {workers}, can not build channel."
                    self.root_cause.set(CZException(error_msg))
                    raise CZException(error_msg)

            # Register reconnect task if enabled
            def reconnect_task():
                """Task to handle reconnection"""
                try:
                    log.info(f"Starting reconnect for session {self.session_id}")

                    # Get new tablet workers through RPC proxy
                    from clickzetta_ingestion.realtime.realtime_stream_api import IGS_TABLET_NUM
                    tablet_num = self.configure.get_int(IGS_TABLET_NUM, 1)
                    new_workers = self.client.igs_client.rebuild_idle_tablet(self.client,
                                                                             self.arrow_table.schema_name,
                                                                             self.arrow_table.table_name,
                                                                             tablet_num)
                    # Re-initialize channels with new workers
                    self.channel_manager.rebuild_channels(
                        host_ports=new_workers,
                        rpc_call_options=self.options.rpc_call_options,
                    )
                    log.info(f"Reconnect completed for session {self.session_id}")

                except Exception as e:
                    log.error(f"Failed to reconnect: {e}")
                    raise

            # Register the reconnect task with channel manager
            self.channel_manager.register_reconnect_task(reconnect_task)
            log.info(f"Registered reconnect task for session {self.session_id}")

        except Exception as e:
            log.error(f"Failed to initialize RPC connection: {e}")
            raise CZException(f"Failed to initialize RPC connection: {e}")

    @run_or_wait_in_commit()
    def flush(self):
        """Flush current buffer if needed"""
        _should_flush: bool
        with self.flush_atomic_lock:
            _should_flush = self.should_flush
            self.should_flush = False
        self.send_one_rpc_message()
        self.wait_on_no_buffer_in_flight()
        self.commit_if_needed(_should_flush)

    def close(self):
        """Close stream and cleanup resources"""
        self.initialized = False
        self._closed = True
        log.info(f"Closing session {self.session_id}...")

        with self.stream_lock:
            self.stream_condition.notify_all()

        self.validate()
        # final buffer flush.
        self.send_one_rpc_message()

        try:
            log.info(f"Closing {self.session_id} Flush-Timer-Thread...")
            # 1. Stop flush timer if running
            with self._flush_timer_lock:
                self.initialized = False
                if self.timer_thread_pool and self.timer_thread_pool.running:
                    try:
                        # Remove all scheduled jobs first
                        self.timer_thread_pool.remove_all_jobs()
                        self.timer_thread_pool.shutdown(wait=False)
                    except Exception as e:
                        log.warning(f"Error shutting down timer thread pool: {e}")
                        # Force shutdown
                        try:
                            self.timer_thread_pool.shutdown(wait=False)
                        except Exception:
                            pass
                    self.timer_thread_pool = None
        except Exception as e:
            log.debug(f"Failed to close Flush-Timer-Thread: {e}")

        try:
            # 2. Wait for all in-flight buffers to complete
            log.info(f"Waiting for all in-flight buffers to complete...")
            self.wait_and_commit_message_if_needed()

            # 3. Close channel manager
            if self.channel_manager:
                self.channel_manager.close()
        except Exception as e:
            log.error(f"Failed to close channel manager: {e}")
            self.root_cause.set(CZException(str(e)))

        # 4. Close flusher
        try:
            if self.flusher:
                self.flusher.close(wait=True)  # Wait for all tasks to complete
        except Exception as e:
            log.error(f"Failed to close flusher: {e}")
            self.root_cause.set(CZException(str(e)))

        # 5. Clean up row pool
        try:
            if self.row_pool:
                self.row_pool.close()
        except Exception as e:
            log.error(f"Failed to close row pool: {e}")
            self.root_cause.set(CZException(str(e)))

        self.retry_executor.notify_all_scheduled_tasks()
        try:
            log.debug(f"Wait for all retry request count to 0, currently: {self.retry_request_count.get()}")
            while True:
                if self.retry_request_count.get() <= 0:
                    break
                with self.retry_request_count.get_lock_condition():
                    self.retry_request_count.get_lock_condition().wait(0.1)

            if not self.retry_executor.is_stopped:
                self.retry_executor.close()

            if self.response_handler:
                self.response_handler.close()

        except Exception as e:
            log.error(f"Failed to close retry executor: {e}")
            raise

        self.validate()
        log.info(f"Session {self.session_id} closed successfully")

    def wait_on_no_buffer_in_flight(self, timeout_ms: int = 1000):
        """Wait for all in-flight buffers to complete"""
        self.validate()
        self.flusher.wait_on_no_buffer_in_flight()
        self.retry_executor.notify_all_scheduled_tasks()
        log.debug("All in-flight buffers completed, checking for _request_in_flight count. "
                  f"Current request_in_flight: {self.request_in_flight},"
                  f"retry_request_count: {self.retry_request_count.get()}")
        while self.request_in_flight > 0 or self.retry_request_count.get() > 0:
            with self.stream_condition:
                self.stream_condition.wait(timeout=timeout_ms / 1000)
            self.validate()
        log.debug("Checked for _request_in_flight count successfully")

    def get_server_token_map(self):
        return self.server_token_map

    def reset_server_token(self):
        """Reset server token after commit"""
        if self.server_token_map:
            self.server_token_map.reset()

    def create_row(self, operator: Union[str, RowOperator]) -> ArrowRow:
        """Creates a new row with the specified operation type"""
        if isinstance(operator, str):
            try:
                op = RowOperator(operator.upper())
            except ValueError:
                raise ValueError(f"Invalid operator: {operator}")
        else:
            op = operator

        if (self.operation == RealtimeOperation.APPEND_ONLY and
                op not in (RowOperator.INSERT, RowOperator.INSERT_IGNORE)):
            raise ValueError("Append Only stream only support INSERT operation, but got %s" % op.name)

        operation_type = getattr(ingestion_v2_pb2.OperationType, op.name)
        if self.row_pool and self.row_pool.pool_support:
            # Get from pool and reset
            row: ArrowRow = self.row_pool.acquire_row()
            row.reset_row_meta(self.arrow_table, operation_type)
            return row

        return ArrowRow(
            arrow_table=self.arrow_table,
            operation_type=operation_type,
            complex_type_recheck=self.complex_type_recheck
        )

    def apply(self, *rows: ArrowRow):
        """Apply one or more rows to the stream"""
        self.validate()

        for row in rows:
            try:
                if not isinstance(row, ArrowRow):
                    raise TypeError("Row must be ArrowRow type")
                # Validate row before sending
                row.validate()
                self.validate()
                row_size = row.get_memory_size()

                with self.stream_condition:
                    try:
                        while self.in_commit:
                            self.stream_condition.wait(timeout=self.commit_wait_timeout_ms / 1000)
                            self.validate()

                        # first check buffer limit.
                        if self.current_buffer and self.current_buffer.is_full(row_size, pre_check=True):
                            self.send_one_rpc_message()

                        # second allocate new buffer.
                        if not self.current_buffer:
                            self.current_buffer = self.flusher.acquire_buffer()
                            if self.current_buffer is None:
                                raise CZException(
                                    f"Failed to acquire buffer from flusher! thread: {threading.current_thread().name}")

                        if not self.should_flush:
                            with self.flush_atomic_lock:
                                self.should_flush = True

                        self.current_buffer.add_operation(WriteOperation(
                            row=row,
                            pooled=bool(self.row_pool and self.row_pool.pool_support)
                        ))

                        # third double check buffer isFull.
                        if self.current_buffer.is_full(row_size, pre_check=False):
                            self.send_one_rpc_message()

                        # Return row to pool if supported
                        if self.pool_support and self.row_pool:
                            self.row_pool.release_row(row)
                    finally:
                        self.stream_condition.notify_all()

            except Exception as e:
                log.error(e)
                raise CZException(e)

    def get_metrics(self):
        """Get stream metrics"""
        return self.metrics

    @commit_with_lock()
    def commit_if_needed(self, need_flush: bool = False):
        """Handle commit logic with token management"""
        try:
            need_commit = self.arrow_table.is_require_commit()
            log.debug(f"Committing data need_flush: {need_flush}, is_require_commit: {need_commit}")
            if self.client.igs_client and need_commit and need_flush:
                context = self.client.igs_client.client_context
                commit_id = self.client.igs_client.async_commit(
                    client=self.client,
                    instance_id=context.instance_id,
                    workspace=context.workspace,
                    table_idents=[(self.arrow_table.schema_name, self.arrow_table.table_name)],
                    server_token_maps=[self.server_token_map]
                )
                log.info(f"Async commit id: {commit_id}")

                self.client.igs_client.check_commit_result(
                    client=self.client,
                    instance_id=context.instance_id,
                    workspace=context.workspace,
                    commit_id=commit_id
                )
                log.info(f"Commit id {commit_id} success.")

                # Foreach upsert mutate. token reset like:
                # /clear(t0)/(null)(t1)(t1)(t1)/clear(t1)/(null)(t2)(t2)/clear(t2)/...../
                # / commit /------------------/ commit /---------------/ commit /------/
                self.reset_server_token()

        except Exception as e:
            log.error(f"Commit operation failed: {e}")
            raise CZException(f"Commit operation failed: {e}")

    def send_one_rpc_message(self):
        """Send one RPC message with current buffer data"""
        self.validate()
        if not self.current_buffer or self.current_buffer.is_empty():
            return

        # Create flush task
        task = ArrowFlushTask(
            batch_id=self.current_batch_id,
            context=self.client_context,
            buffer=self.current_buffer,
            server_token_map=self.server_token_map,
            channel_data_supplier=self.get_channel_data_supplier(),
            request_callback=self.request_callback,
        )

        with self.stream_lock:
            with self.batch_id_lock:
                self.current_batch_id += 1

            # Submit task to flusher
            self.flusher.submit_task(task)
            self.current_buffer = None
            self.stream_condition.notify_all()

    def validate(self):
        """Validate stream state and raise exception if needed"""
        if self.root_cause.get():
            raise self.root_cause.get()

    def get_channel_data_supplier(self) -> Callable[[], ChannelData]:
        def supplier() -> ChannelData:
            try:
                log.debug(
                    f"Start to get_channel in_reconnect:{self.channel_manager.in_reconnect}")
                channel_data: ChannelData = self.channel_manager.get_channel()
                self.channel_manager.valid_channel_active_with_max_retry(
                    channel_data,
                    3,
                )

                self.validate()
                return channel_data

            except Exception as e:
                log.error(f"Failed to get channel data: {e}")
                raise RuntimeError(f"Failed to get channel data: {e}")

        return supplier

    def _start_flush_to_queue_timer(self):
        """Start the flush timer to submit flush tasks"""
        log.info(f"Starting Flush-timer-trigger-Thread with interval: {self.flush_interval} ms")

        def timer_trigger_action():
            try:
                self.flush()
            except Exception as e:
                # if there is no new record in. only timer flusher trigger to send old buffer (2 record like).
                # and validChannelActiveWithMaxRetry with channel IDLE state throw an exception.
                # if ignore timer flusher with sendOneRpcMessage exception.
                # it will try to send same old buffer with delay next time.
                # at same time. some new record in but not full a new buffer.
                # it will append to old buffer. and still send failed in flushTimerTrigger.
                # here we handle exception in timer flusher. so new record apply will break the main thread.
                log.error(f"Timer trigger action failed: {e}")
                self.root_cause.set(CZException(str(e)))

        self.timer_thread_pool.add_job(timer_trigger_action, "interval", seconds=self.flush_interval / 1000,
                                       id=f"flush-timer-trigger-{self.session_id}",
                                       name=f"Flush timer trigger",
                                       max_instances=2,
                                       coalesce=True)

    def increment_requests(self):
        with self._request_lock:
            self.request_in_flight += 1

    def decrement_requests(self):
        with self._request_lock:
            self.request_in_flight -= 1

    @run_or_wait_in_commit()
    def commit_all_rows(self):
        self.commit_if_needed(True)

    def wait_and_commit_message_if_needed(self):
        self.wait_on_no_buffer_in_flight()

        # need to commit all rows if needed.
        self.commit_all_rows()

    def report_last_rpc_status(self,
                               request_id: int,
                               status_code: int,
                               request: Any,
                               response: Any,
                               callback: Optional[Callable[[], Callable[[], None]]] = None
                               ) -> Optional[Callable[[], None]]:
        """Report RPC status and handle retries
        
        Args:
            request_id: Request ID
            status_code: Response status code
            request: Original request
            response: Response message
            callback: Optional callback for retry. Used for send_stream_request when request on failure
            
        Returns:
            Retry action if needed
            
        Notes:
            Not thread safe. Multiple response observers will call this function.
            
            Use responseHandler.getRequests().size() to check there is no request in flight.
            responseHandler will remove requestId & callback first then call callback onSuccess or onFailure.
            So when size = 0 means all rpc responses received & reported their RPC Status.
        """
        if self.arrow_table.is_require_commit():
            if response.server_tokens and response.server_tokens.__len__() > 0:
                self.server_token_map.update(response.server_tokens)
            elif response.server_token:
                self.server_token_map.update(response.server_token)

        # Report status to channel manager
        in_reconnect = self.channel_manager.report_last_rpc_status(status_code)

        # If RPC success, callback & supplier is null
        supplier = None
        if callback is not None:
            supplier = callback()

        if not in_reconnect:
            # Conditions:
            # 1. Not support reconnect
            # 2. Support reconnect and RPC status (success or failed) but no idle status received before
            self.channel_manager.add_reconnect_finish_task(
                None,
                lambda has_future: has_future and len(self.response_handler.requests) == 0
            )
            return supplier
        else:
            # Condition:
            # 1. Support reconnect and receive other RPC status (success or failed) after last RPC failed with idle status
            self.channel_manager.add_reconnect_finish_task(
                supplier,
                lambda has_future: has_future and len(self.response_handler.requests) == 0
            )
            return None

    def send_stream_request(self,
                            internal_ms: int,
                            retry_mode: RetryMode,
                            request: Any,
                            response: Any) -> Optional[Callable[[], None]]:
        """Send stream request with retry support
        
        Args:
            internal_ms: Retry interval in milliseconds
            retry_mode: Retry mode
            request: Request to send
            response: Original response
            
        Returns:
            Retry action
        """
        self.retry_request_count.get_and_increment()

        def retry_action():
            try:
                task = ArrowStreamTask(
                    batch_id=request.batch_id,
                    retry_count=self.retry_request_count,
                    internal_ms=internal_ms,
                    retry_mode=retry_mode,
                    request=request,
                    response=response,
                    server_token_map=self.server_token_map,
                    channel_data_supplier=self.get_channel_data_supplier(),
                    request_callback=self.request_callback,
                    retry_executor=self.retry_executor
                )

                self.flusher.submit_task(task)
            except Exception:
                self.retry_request_count.get_and_decrement()
                raise

        return retry_action
