from __future__ import annotations

import abc
import logging
import queue
import threading
from concurrent.futures import Future
from queue import PriorityQueue
from typing import Optional

from clickzetta.connector.v0.exceptions import CZException
from clickzetta_ingestion.realtime.buffer import Buffer, DefaultBuffer
from clickzetta_ingestion.common.configure import Configure
from clickzetta_ingestion.realtime.message import AtomicReference
from clickzetta_ingestion.realtime.realtime_options import CZSessionOptions, FlushMode
from clickzetta_ingestion.realtime.task import Task, AbstractTask

log = logging.getLogger(__name__)


class Flusher(abc.ABC):
    """Interface defining flusher behavior"""
    
    @abc.abstractmethod
    def init(self):
        """Initialize the flusher"""
        pass
    
    @abc.abstractmethod
    def acquire_buffer(self) -> Optional[Buffer]:
        """Acquire a buffer from the pool"""
        pass
        
    @abc.abstractmethod
    def return_buffer(self, buffer: Buffer):
        """Return a buffer to the pool"""
        pass
        
    @abc.abstractmethod
    def submit_task(self, task: Task):
        """Submit a task for execution"""
        pass
        
    @abc.abstractmethod
    def wait_on_no_buffer_in_flight(self, timeout_ms: int = 200) -> bool:
        """Wait until no buffers are in flight"""
        pass
        
    @abc.abstractmethod
    def close(self, wait: bool = True):
        """Close the flusher"""
        pass
        
    @abc.abstractmethod
    def get_exception_holder(self) -> AtomicReference:
        """Get the exception holder"""
        pass

    @classmethod
    def build(cls, options: CZSessionOptions, configure: Configure,
              stream_condition, buffer_type: str = "default") -> Flusher:
        """
        Factory method to build the appropriate Flusher instance based on options.

        Args:
            options: Session options containing flush mode settings
            configure: Configuration settings
            stream_condition: Condition variable for synchronization
            buffer_type: Type of buffer to use (default: "default")

        Returns:
            Appropriate Flusher implementation based on flush mode

        Raises:
            ValueError: If flush mode is not supported
        """
        flush_mode = options.flush_mode

        if flush_mode == FlushMode.AUTO_FLUSH_BACKGROUND:
            return AsyncFlusher(options, configure, stream_condition)
        elif flush_mode in (FlushMode.AUTO_FLUSH_SYNC, FlushMode.MANUAL_FLUSH):
            return SyncFlusher(options, configure, stream_condition)
        else:
            raise ValueError(f"Unsupported flush mode: {flush_mode}")


class BaseFlusher(Flusher):
    """Base implementation of Flusher interface"""

    def __init__(self, options: CZSessionOptions, configure: Configure, stream_condition, buffer_type: str = "default"):
        self.configure = configure
        self.options: CZSessionOptions = options
        self.mutation_buffer_max_num = self.options.mutation_buffer_max_num
        self.mutation_buffer_lines_num = self.options.mutation_buffer_lines_num
        self.mutation_buffer_space = self.options.mutation_buffer_space
        self.buffer_type = buffer_type
        self.stream_condition = stream_condition
        
        # Initialize queues
        self.flush_queue: PriorityQueue = PriorityQueue(maxsize=self.mutation_buffer_max_num * 2)
        self.buffer_queue = queue.Queue(maxsize=self.mutation_buffer_max_num)
        
        # Exception handling
        self._exception = AtomicReference()
        
        self.init()
        
    def init(self):
        """Initialize buffers"""
        strict_mode = self.configure.get_bool("mutation.buffer.memory.strict.mode", False)
        
        # Initialize buffer pool
        for _ in range(self.mutation_buffer_max_num):
            buffer = DefaultBuffer(
                self.mutation_buffer_lines_num,
                self.mutation_buffer_space,
                strict_mode
            )
            self.buffer_queue.put(buffer)
            
        log.info("Session Flusher Start Success")
        
    def acquire_buffer(self) -> Optional[Buffer]:
        """Acquire buffer from pool"""
        try:
            buffer = None
            while buffer is None:
                self.valid_call_exception()
                try:
                    buffer = self.buffer_queue.get(timeout=0.2)
                except queue.Empty:
                    continue
            return buffer
        except Exception as e:
            log.error(f"Failed to acquire buffer: {e}")
            self.exception = e
            return None
            
    def return_buffer(self, buffer: Buffer):
        """Return buffer to pool"""
        if buffer:
            try:
                buffer.reset()
                self.buffer_queue.put(buffer)
                with self.stream_condition:
                    self.stream_condition.notify_all()
            except Exception as e:
                log.warning(f"Failed to return buffer to pool: {e}")
                self.exception = e
                
    def valid_call_exception(self):
        """Check for stored exception"""
        if self._exception.get():
            raise self._exception.get()
            
    @property
    def exception(self):
        return self._exception.get()
        
    @exception.setter 
    def exception(self, e: Exception):
        self._exception.set(e)
        
    def get_exception_holder(self) -> AtomicReference:
        return self._exception
        
    def wait_on_no_buffer_in_flight(self, timeout_ms: int = 200) -> bool:
        try:
            with self.stream_condition:
                while (self.flush_queue.qsize() != 0 or 
                       self.buffer_queue.qsize() != self.mutation_buffer_max_num):
                    self.valid_call_exception()
                    self.stream_condition.wait(timeout=timeout_ms / 1000.0)
            return True
        except Exception as e:
            log.error(f"Failed to wait on no buffer in flight: {e}")
            self.exception = e
            return False
            
    def close(self, wait: bool = True):
        try:
            if wait:
                if self.wait_on_no_buffer_in_flight():
                    log.info("Session flusher close successfully")
                else:
                    log.error("Failed to close session flusher")
        except Exception as e:
            log.error(f"Failed to close flusher: {e}")


class AsyncFlusher(BaseFlusher):
    """Asynchronous implementation of Flusher"""
    
    def __init__(self, options: CZSessionOptions, configure: Configure, stream_condition):
        super().__init__(options, configure, stream_condition)
        self._flush_thread: Optional[threading.Thread] = None
        self.terminate = AtomicReference(False)
        self.init_async()
        
    def init_async(self):
        """Initialize async worker thread"""
        def _flush_worker():
            log.info("Flush-Worker-Thread started...")
            while True:
                try:
                    if self.terminate.get():
                        log.info("Flush worker terminated, flush queue size: %d", self.flush_queue.qsize())
                        break
                    try:
                        task: AbstractTask = self.flush_queue.get(timeout=0.2)
                    except queue.Empty:
                        continue

                    if task:
                        try:
                            if not self.exception:
                                future = task.call()
                            else:
                                future = task.skip_call(self.exception)

                            def done_callback(fut):
                                try:
                                    if fut.exception():
                                        self.exception = fut.exception()
                                finally:
                                    self.return_buffer(task.get_buffer())
                                    self.flush_queue.task_done()

                            future.add_done_callback(done_callback)

                        except Exception as e:
                            msg = f"AsyncFlusher task failed: {e}"
                            log.error(msg)
                            self.exception = CZException(msg)
                            self.return_buffer(task.get_buffer())
                            self.flush_queue.task_done()

                except Exception as e:
                    log.error(f"Flush worker error: {e}")
                    self.exception = e
                    break

        self._flush_thread = threading.Thread(
            target=_flush_worker,
            name="Flush-Worker-Thread",
            daemon=True
        )
        self._flush_thread.start()
        
    def submit_task(self, task: Task):
        """Submit task to flush queue"""
        try:
            self.flush_queue.put(task, block=True)
        except queue.Full:
            log.error("Flush queue is full, task discarded")
            raise CZException("Flush queue is full, task discarded")
            
    def close(self, wait: bool = True):
        """Close flusher and cleanup"""
        try:
            if wait:
                super().close(wait)
        finally:
            if self._flush_thread and self._flush_thread.is_alive():
                self.terminate.set(True)
                try:
                    self._flush_thread.join(timeout=0.2)
                except Exception:
                    pass


class SyncFlusher(BaseFlusher):
    """Synchronous implementation of Flusher"""
    
    def __init__(self, options: CZSessionOptions, configure: Configure, stream_condition):
        super().__init__(options, configure, stream_condition)
        self._flush_thread: Optional[threading.Thread] = None
        self.terminate = AtomicReference(False)
        self.init_sync()
        
    def init_sync(self):
        """Initialize sync worker thread"""
        def _flush_worker():
            log.info("Sync-Flush-Thread started...")
            while not self.terminate.get():
                try:
                    try:
                        task = self.flush_queue.get(timeout=0.2)
                    except queue.Empty:
                        continue
                        
                    if task:
                        try:
                            future: Future
                            if self.exception:
                                future = task.skip_call(self.exception)
                            else:
                                future = task.call()
                                
                            # Wait for completion
                            try:
                                future.result()
                            except Exception as e:
                                self.exception = e
                            finally:
                                self.return_buffer(task.get_buffer())
                                
                        except Exception as e:
                            log.error(f"Failed to execute task: {e}")
                            self.exception = e
                            
                except Exception as e:
                    if not isinstance(e, InterruptedError):
                        log.error(f"Sync flush worker error: {e}")
                        self.exception = e
                    break
                    
        self._flush_thread = threading.Thread(
            target=_flush_worker,
            name="Sync-Flush-Thread",
            daemon=True
        )
        self._flush_thread.start()
        
    def submit_task(self, task: Task):
        """Submit task synchronously"""
        try:
            self.valid_call_exception()
            self.flush_queue.put(task, block=True)
        except Exception as e:
            raise CZException(f"Failed to submit task: {e}")
            
    def close(self, wait: bool = True):
        """Close flusher and cleanup"""
        try:
            if wait:
                with self.stream_condition:
                    while self.flush_queue.qsize() > 0:
                        self.valid_call_exception()
                        self.stream_condition.wait(0.2)
                        
            super().close(wait)
        finally:
            if self._flush_thread and self._flush_thread.is_alive():
                self.terminate.set(True)
                try:
                    self._flush_thread.join(timeout=0.2)
                except Exception:
                    pass
