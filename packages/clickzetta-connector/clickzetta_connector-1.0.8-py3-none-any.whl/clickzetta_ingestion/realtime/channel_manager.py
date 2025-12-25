import datetime
import logging
import queue
import socket
import threading
import time
from concurrent.futures import Future
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Optional, Callable, Any

import grpc
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from clickzetta.connector.v0.exceptions import CZException
from clickzetta_ingestion._proto import ingestion_v2_pb2_grpc
from clickzetta_ingestion.realtime.arrow_flush_task import ChannelData
from clickzetta_ingestion.realtime.message import AtomicReference
from clickzetta_ingestion.realtime.stream_observer import ReferenceCountedStreamObserver, ResponseStreamObserver

log = logging.getLogger(__name__)

RPC_CLIENT_STREAM_ID = "stream_id"
ACTIVE_STATES = {
    grpc.ChannelConnectivity.CONNECTING,
    grpc.ChannelConnectivity.READY
}


@dataclass
class ChannelOptions:
    """Channel configuration options"""
    max_inbound_message_size: int = 25 * 1024 * 1024  # 25MB
    max_outbound_message_size: int = 25 * 1024 * 1024  # 25MB
    keep_alive_time: int = 600
    keep_alive_timeout: int = 180
    keep_alive_without_calls: bool = True
    enable_retry: bool = True
    multi_enable: bool = False
    channel_num: int = 1
    rpc_call_options: List = field(default_factory=list)


class ChannelState(Enum):
    IDLE = 0
    CONNECTING = 1
    READY = 2
    TRANSIENT_FAILURE = 3
    SHUTDOWN = 4


@dataclass
class ReconnectTask:
    """Task for handling reconnection"""
    action: Callable[[], None]
    condition: Callable[[bool], bool]


class ExpireCleaner:
    """Cleaner for expired stream observers"""

    def __init__(self, stream_observers: List[ReferenceCountedStreamObserver]):
        self.stream_observers: List[ReferenceCountedStreamObserver] = stream_observers.copy()

    def call(self) -> List[Any]:
        """Clean expired observers and return remaining ones
        
        Returns:
            List of observers that are still in use
        """
        remain = []
        for observer in self.stream_observers:
            if observer.ref_cnt <= 0:
                # Close the invalid observer without waiting for the observer to complete
                observer.on_cancel()
                log.info(f"RequestStreamObserver expire clean success with {observer}")
            else:
                remain.append(observer)
        return remain


class ChannelManager:
    def __init__(self, outer_stream, session_id, root_cause, options):
        self.outer_stream = outer_stream
        self.session_id = session_id
        self.root_cause = root_cause
        self.reconnect_exception = AtomicReference(None)
        self.options = options

        self._channel_datas: List[ChannelData] = []
        self._host_ports: List[Tuple[str, Optional[int]]] = []
        self._current_index = 0
        self._channel_lock = threading.RLock()
        self._channel_condition = threading.Condition(self._channel_lock)
        self.stream_observers: List[Any] = []
        self.channel_options = ChannelOptions()

        # Add reconnect task support
        self._task_condition = threading.Condition(threading.RLock())
        self.in_reconnect = False
        self.reconnect_task: Optional[ReconnectTask] = None
        self.reconnect_future: Optional[Future] = None
        self.reconnect_thread = BackgroundScheduler()
        self.reconnect_thread.start()

        # Add cleaner queue and service
        self.cleaner_queue = queue.Queue()
        self.cleaner_scheduler = BackgroundScheduler()
        self._cleaner_initialized = False

    def reset_reconnect_status(self, status: bool):
        """Reset reconnect status"""
        with self._task_condition:
            self.in_reconnect = status

    @staticmethod
    def generator_stream_id(session_id: str, args: List[str] = None) -> str:
        local_ip_address = None
        hostname = None
        try:
            hostname = socket.gethostname()
            local_ip_address = socket.gethostbyname(socket.gethostname())
        except Exception:
            if hostname:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(('8.8.8.8', 80))
                    local_ip_address = s.getsockname()[0]
                except Exception:
                    pass
        if not local_ip_address:
            local_ip_address = '127.0.0.1'
        prefix = f"{session_id}-{local_ip_address}"
        if args:
            prefix = f"{prefix}-{'-'.join(args)}"
        return prefix

    def channel_build(self, host: str, port: Optional[int], channel_options,
                      callback: Optional[Callable[[grpc.Channel], Any]]) -> bool:
        try:
            with self._channel_lock:
                # Build channel based on whether port is provided
                if port is not None and port != -1:
                    channel = grpc.insecure_channel(
                        f"{host}:{port}",
                        options=channel_options,
                    )
                else:
                    channel = grpc.insecure_channel(
                        host,
                        options=channel_options
                    )

                # Store host/port pair
                self._host_ports.append((host, port))

                # Initialize stream observer if callback provided
                if callback is not None:
                    # Return the ReferenceCountedStreamObserver for reference counting
                    observer = callback(channel)
                    if observer is not None:
                        self.stream_observers.append(observer)
                        channel_data = ChannelData(
                            host_port=(host, port),
                            channel=channel,
                            reference_stream_observer=observer,
                        )
                        self._channel_datas.append(channel_data)

                log.info(f"Successfully built channel to {host}:{port}")
                return True

        except Exception as e:
            log.error(f"Failed to build channel to {host}:{port}: {e}")
            return False

    def build_channels(self, host_ports: List[Tuple[str, int]],
                       callback: Optional[Callable[[grpc.Channel], Any]], rpc_call_options: List) -> bool:
        """Build multiple channel connections"""
        success = True
        has_pair = False
        with self._channel_lock:
            callback = self.build_init_rpc_stream_observer if callback is None else callback
            for host, port in host_ports:
                if not host:
                    continue
                if not self.channel_build(host, port, rpc_call_options, callback):
                    success = False
                else:
                    has_pair = True
            return has_pair and success

    def get_channel(self) -> Optional[ChannelData]:
        """Get next cached available channel using round-robin"""
        # wait until no reconnect. No need to acquire _channel_lock here
        self.wait_on_no_in_reconnect()

        with self._channel_lock:
            host_port = ()
            observer = None
            try:
                # When the channel_manager is closed, the stream_observers have been cleared, so you need to judge here
                if self._current_index < len(self.stream_observers):
                    host_port = self._host_ports[self._current_index]
                    observer = self.stream_observers[self._current_index]
                    observer.retain()

                channel_data = ChannelData(
                    host_port=host_port,
                    channel=observer.channel if observer else None,
                    reference_stream_observer=observer,
                )
            except IndexError as e:
                log.error(f"Failed to access channel data at index {self._current_index}! "
                          f"Total channels: {len(self._channel_datas)}")
                raise CZException(f"Channel access error: {str(e)}")

            self._current_index = (self._current_index + 1) % len(self.stream_observers) if self.stream_observers else 0
            return channel_data

    def valid_channel_active_with_max_retry(self, channel_data: ChannelData, max_retries: int):
        """Validate channel with retry mechanism"""
        retry_count = 0
        last_error = None
        timeout_sec = 15
        with self._channel_lock:
            if not channel_data or not channel_data.channel:
                raise CZException("Invalid channel data! Channel is empty.")
            while retry_count < max_retries and max_retries > 0:
                try:
                    # Check channel readiness
                    if not self.is_channel_ready(channel_data.channel, timeout_sec):
                        if retry_count == max_retries - 1:
                            log.warning(
                                f"Channel {str(channel_data.host_port)} is not active with max retries, try to wait_for_state_change...")
                            self.get_channel_state(channel_data.channel)
                    else:
                        # Try to validate channel with provided validator
                        stream_observer = self.build_init_rpc_stream_observer(channel_data.channel)
                        if stream_observer:
                            channel_data.reference_stream_observer = stream_observer
                            return True

                except Exception as e:
                    last_error = e
                    log.warning(f"Channel validation failed (attempt {retry_count + 1}/{max_retries}), will retry: {e}")

                    # Close current channel
                    try:
                        if channel_data and channel_data.channel:
                            channel_data.channel.close()
                    except Exception as ce:
                        log.warning(f"Failed to close channel: {ce}")

                    # Get new channel
                    try:
                        new_channel_data = self.get_channel()
                        if new_channel_data:
                            channel_data = new_channel_data
                    except Exception as ge:
                        log.warning(f"Failed to get new channel: {ge}")

                retry_count += 1
                if retry_count < max_retries:
                    with self._channel_condition:
                        self._channel_condition.wait(timeout=1)

        raise CZException(f"Channel validation failed after {max_retries} attempts: {last_error}")

    def build_init_rpc_stream_observer(self, channel):
        """Build initial RPC stream observer

        Args:
            channel: gRPC channel

        Returns:
            Stream observer for requests
        """
        try:
            return ReferenceCountedStreamObserver(
                channel=channel,
                request_observer=self._create_init_rpc_request_observer(channel),
            )
        except Exception as e:
            self.outer_stream.root_cause.set(CZException(str(e)))
            log.error(f"Failed to build RPC stream observer: {e}")
            raise CZException(f"Failed to build RPC stream observer: {e}")

    def _create_init_rpc_request_observer(self, channel: grpc.Channel):
        """Create RPC response observer for bidirectional streaming

        Args:
            channel: gRPC channel
            proxy_observer: Proxy observer for responses

        Returns:
            Tuple of request iterator and response observer
        """
        try:
            # Start bidirectional streaming RPC with metadata
            metadata = [(RPC_CLIENT_STREAM_ID, self.generator_stream_id(self.outer_stream.session_id))]

            # Create response observer
            class ClientCallStreamObserver:
                def __init__(self, proxy, client_channel):
                    self.response_stream_observer: ResponseStreamObserver = proxy
                    self._closed = False
                    self.stub = ingestion_v2_pb2_grpc.IngestionWorkerServiceStub(client_channel)

                def on_next(self, request):
                    if self._closed:
                        raise RuntimeError("Stream is closed")

                    try:
                        for response in self.stub.Mutate(
                                iter((request,)),
                                metadata=metadata
                        ):
                            if self.response_stream_observer:
                                self.response_stream_observer.on_next(response)
                    except Exception as e1:
                        log.warning(f"Error processing response: {e1}")
                        if not self._closed:
                            self._closed = True
                            if self.response_stream_observer:
                                self.response_stream_observer.on_error(e1)

                def on_error(self, error):
                    self._closed = True
                    if self.response_stream_observer:
                        self.response_stream_observer.on_error(error)

                def on_completed(self):
                    self._closed = True
                    if self.response_stream_observer:
                        self.response_stream_observer.on_completed()
                        self.response_stream_observer = None

                def cancel(self):
                    self._closed = True

            return ClientCallStreamObserver(self.outer_stream.response_stream_observer, channel)

        except Exception as e:
            log.error(f"Failed to create RPC observer: {e}")
            raise CZException(f"Failed to create RPC observer: {e}")

    def report_last_rpc_status(self, status_code: int) -> bool:
        """Report last RPC status and check if reconnect is needed"""
        if not self.options.tablet_idle_recreate_support:
            return False

        try:
            if status_code in self.options.reconnect_status:
                if not self.in_reconnect:
                    with self._task_condition:
                        if not self.in_reconnect:
                            self.in_reconnect = True
                return True
        except ValueError as e:
            log.warning(f"Invalid status code: {status_code}, error: {e}. Skipping reconnect check.")
            pass
        return False

    def add_reconnect_finish_task(self,
                                  action: Optional[Callable[[], None]],
                                  condition: Callable[[bool], bool]):
        """
        Add reconnect finish task with condition
        
        Args:
            action: Action to execute after reconnect
            condition: Condition to check if task should execute
            
        Note:
            Not thread safe. Multiple response observers will call this function.
            Use responseHandler.getRequests().size() to check there is no request in flight.
            responseHandler will remove requestId & callback first then call callback onSuccess or onFailure.
            So when size = 0 means all rpc responses received & reported their RPC Status.
        """
        if not self.options.tablet_idle_recreate_support:
            return

        if action:
            # Execute action callback like resend stream task
            action()

        with self._task_condition:
            if self.in_reconnect and condition(self.reconnect_future is None):
                def _run_task():
                    log.info(f"Starting reconnect task. The in_reconnect: {self.in_reconnect}, "
                             f"request_in_flight: {self.outer_stream.request_in_flight}, "
                             f"retry_request_count: {self.outer_stream.retry_request_count}")
                    try:
                        if self.reconnect_task:
                            self.reconnect_task.action()
                        self.reconnect_future.set_result(True)
                    except Exception as e:
                        log.error(f"Reconnect task failed: {e.__class__} {e}")
                        self.reconnect_exception.set(e)
                    finally:
                        self.in_reconnect = False
                        self.reconnect_future = None
                    log.info(f"Reconnect task completed")

                self.reconnect_future = Future()
                self.reconnect_thread.add_job(_run_task, id=f"idle-reconnect-thread-{self.session_id}",
                                              replace_existing=True,
                                              trigger='date', next_run_time=datetime.datetime.now())

    def wait_on_no_in_reconnect(self, timeout_ms: int = 200):
        """Wait for any ongoing reconnect to complete"""
        if self.options.tablet_idle_recreate_support and self.in_reconnect:
            log.debug(f"Start to wait_on_no_in_reconnect. in_reconnect={self.in_reconnect}")
            with self._task_condition:
                while self.in_reconnect:
                    self._task_condition.wait(min(0.2, timeout_ms / 1000))
                log.debug(f"Waiting for reconnect finished for session {self.session_id}")
                self._task_condition.notify_all()
            if self.reconnect_exception.get():
                raise self.reconnect_exception.get()
        log.debug(f"Reconnect finished for session {self.session_id}")

    def register_reconnect_task(self, task_action: Callable[[], None]):
        """Register reconnect task
        
        Args:
            task_action: Action to execute during reconnect
        """
        with self._task_condition:
            self.reconnect_task = ReconnectTask(
                action=task_action,
                condition=lambda has_future: True  # Default condition
            )
            log.info(f"Registered reconnect task for session {self.session_id}")

    def _start_cleaner_service(self):
        """Start the cleaner service using APScheduler"""
        if self._cleaner_initialized:
            return

        def cleaner_task():
            """Periodic task to clean expired observers"""
            try:
                remain = []
                while not self.cleaner_queue.empty():
                    cleaner = self.cleaner_queue.get()
                    remain.extend(cleaner.call())
                if remain:
                    self.cleaner_queue.put(ExpireCleaner(remain))
            except Exception as e:
                log.error(f"Error in cleaner service: {e}")

        self.cleaner_scheduler.add_job(
            cleaner_task,
            trigger=IntervalTrigger(seconds=60),
            id=f'channel_cleaner_{self.session_id}',
            name='Channel Cleaner',
            replace_existing=True
        )

        # Start scheduler if not already running
        if not self.cleaner_scheduler.running:
            self.cleaner_scheduler.start()

        self._cleaner_initialized = True
        log.info("Started channel cleaner scheduler")

    def rebuild_channels(self, rpc_call_options: List, host_ports: List[Tuple[str, int]],
                         callback: Optional[Callable[[grpc.Channel], Any]] = None):
        """Rebuild all channels with new configuration
        
        Args:
            rpc_call_options: Channel rpc_call_options
            host_ports: List of (host, port) pairs
            callback: Optional callback for channel initialization
        """
        if not host_ports:
            raise ValueError("rebuildChannels needs non-empty hostPorts")

        with self._channel_lock:
            if not self.cleaner_scheduler.running:
                self._start_cleaner_service()

            # Add current observers to cleaner queue
            self.cleaner_queue.put(ExpireCleaner(self.stream_observers))

            # Clear current state
            self.stream_observers.clear()
            self._host_ports.clear()
            self._current_index = 0

            callback = self.build_init_rpc_stream_observer if callback is None else callback

            self.build_channels(host_ports, callback, rpc_call_options)

    def close(self):
        """Close all channels and cleanup resources"""
        try:
            log.info("ChannelManager close called...")

            with self._channel_condition:
                self._channel_condition.notify_all()

            if self.reconnect_thread and self.reconnect_thread.running:
                try:
                    # Remove all scheduled jobs first
                    self.reconnect_thread.remove_all_jobs()
                    self.reconnect_thread.shutdown(wait=False)
                except Exception as e:
                    log.warning(f"Error shutting down reconnect thread: {e}")
                    # Force shutdown
                    try:
                        self.reconnect_thread.shutdown(wait=False)
                    except Exception:
                        pass

            # Close all channels
            with self._channel_lock:
                for channel_data in self._channel_datas:
                    try:
                        if channel_data.channel:
                            channel_data.channel.close()
                    except Exception as e:
                        host, port = channel_data.host_port
                        log.warning(f"Failed to close channel {host}:{port}: {e}")
                self._channel_datas.clear()

            # Clean up observers
            for observer in self.stream_observers:
                observer.on_completed()

            # Shutdown scheduler
            if self.cleaner_scheduler.running:
                try:
                    # Remove all scheduled jobs first
                    self.cleaner_scheduler.remove_all_jobs()
                    # Clean remaining tasks in cleaner queue
                    if not self.cleaner_queue.empty():
                        time.sleep(0.5)
                    self.cleaner_scheduler.shutdown(wait=False)
                except Exception as e:
                    log.warning(f"Error shutting down cleaner scheduler: {e}")
                    # Force shutdown
                    try:
                        self.cleaner_scheduler.shutdown(wait=False)
                    except Exception:
                        pass

            # Clean remaining tasks in cleaner queue
            while not self.cleaner_queue.empty():
                cleaner = self.cleaner_queue.get()
                for old_observer in cleaner.stream_observers:
                    old_observer.on_cancel()

            # Reset state
            self._current_index = 0
            self.stream_observers.clear()
            self.cleaner_queue.queue.clear()
            self._host_ports.clear()

            log.info("ChannelManager close success.")

        except Exception as e:
            log.error(f"Error during channel manager close: {e}")
            raise

    @staticmethod
    def get_channel_state(channel, try_to_connect=True) -> bool:
        """Get channel connectivity state"""
        try:
            # try_to_connect=True means it will try to connect if in IDLE state
            state = channel.check_connectivity_state(try_to_connect=try_to_connect)
            if state in ACTIVE_STATES:
                return True
        except Exception as e:
            log.error(f"Failed to get channel state: {e}")
        return False

    @staticmethod
    def is_channel_ready(channel: grpc.Channel, timeout_sec: int = 15) -> bool:
        """Check if channel is ready with timeout"""
        try:
            grpc.channel_ready_future(channel).result(timeout=timeout_sec)  # This will block until ready or timeout
            return True
        except grpc.FutureTimeoutError:
            log.warning(f"Channel not ready after {timeout_sec} seconds")
            return False
        except Exception as e:
            log.error(f"Channel check failed: {e}")
            return False
