"""
Dispatcher implementation for event-driven processing.
"""
import concurrent.futures
import logging
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Dict, List, Optional

from clickzetta_ingestion.common.tools.event import Event, PoisonPill
from clickzetta_ingestion.common.tools.event_handler import EventHandler

logger = logging.getLogger(__name__)


class CompositeHandler:
    """
    Composite handler that manages multiple event handlers for a specific event type.
    """

    def __init__(self, enum_type: Enum):
        """
        Initialize composite handler.
        
        Args:
            enum_type: The enum type this handler manages
        """
        self.enum_type = enum_type
        self.handlers: List[EventHandler] = []
        self.messages: queue.Queue = queue.Queue()

        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        self.event_thread: Optional[concurrent.futures.Future] = None
        self.executor: Optional[ThreadPoolExecutor] = None

        self.initialized = False
        self.closed = False

    def start(self) -> None:
        """Start the composite handler."""
        with self.lock:
            if self.initialized or self.closed:
                return
            self.initialized = True

            # Use direct Thread instead of ThreadPoolExecutor for better control
            thread_name = f"dispatcher-{self.enum_type.name if hasattr(self.enum_type, 'name') else str(self.enum_type)}_0"
            self.event_thread = threading.Thread(
                target=self._message_loop,
                name=thread_name,
                daemon=True  # Make it a daemon thread so it exits with main program
            )
            self.event_thread.start()
            self.executor = None  # Not using ThreadPoolExecutor anymore

    def started(self) -> bool:
        """Check if handler is started."""
        self._check_closed()
        return self.initialized

    def _check_closed(self) -> None:
        """Check if handler is closed and raise exception if it is."""
        if self.closed:
            raise RuntimeError("Handler already closed")

    def stop(self) -> None:
        """Stop the composite handler."""
        with self.lock:
            if not self.initialized or self.closed:
                self.closed = True
                return
            self.initialized = False
            self.closed = True

        # Post poison pill to stop message loop
        self.post_to_all(PoisonPill())

        # Wait for messages to be processed with timeout
        timeout = time.time() + 3  # Reduced to 3 second timeout for faster shutdown
        while not self.messages.empty() and time.time() < timeout:
            with self.condition:
                self.condition.wait(timeout=0.1)

        # Handle thread shutdown (now using direct Thread instead of ThreadPoolExecutor)
        if self.event_thread:
            try:
                # Wait for thread completion with timeout
                self.event_thread.join(timeout=1.0)  # 1 second timeout
                if self.event_thread.is_alive():
                    logger.warning(f"Handler thread for {self.enum_type} is still alive after timeout")
                    # Since it's a daemon thread, it will be killed when main program exits
                else:
                    logger.debug(f"Handler thread for {self.enum_type} stopped gracefully")
            except Exception as e:
                logger.warning(f"Error during thread shutdown: {e}")
            finally:
                self.event_thread = None

    def post_to_all(self, event: Event) -> None:
        """
        Post an event to all handlers.
        
        Args:
            event: The event to post
        """
        self.messages.put(event)

    def _message_loop(self) -> None:
        """Main message processing loop."""
        while not self.closed:
            try:
                # Get message with timeout
                try:
                    event = self.messages.get(timeout=0.5)
                except queue.Empty:
                    # Check if we should exit
                    if self.closed:
                        break
                    continue

                # Check for poison pill
                if isinstance(event, PoisonPill):
                    # Clear remaining messages
                    while not self.messages.empty():
                        try:
                            self.messages.get_nowait()
                        except queue.Empty:
                            break

                    # Signal completion
                    with self.condition:
                        self.condition.notify_all()
                    return

                # Skip processing if closed
                if self.closed:
                    break

                # Process event with all handlers
                with self.lock:
                    handlers_copy = list(self.handlers)

                for handler in handlers_copy:
                    try:
                        handler.handle(event)
                    except Exception as e:
                        logger.error(f"Error handling event {event} with handler {handler}: {e}")
                        handler.handle_exception(event, e)

            except Exception as e:
                logger.error(f"Unexpected error in message loop: {e}")
                # Post poison pill to stop on unexpected error
                self.post_to_all(PoisonPill())
                break


class Dispatcher:
    """
    Main dispatcher for routing events to appropriate handlers.
    """

    def __init__(self):
        """Initialize dispatcher."""
        self.handlers_map: Dict[Enum, CompositeHandler] = {}
        self.lock = threading.RLock()

    def start(self) -> None:
        """Start all registered handlers."""
        exceptions = []

        with self.lock:
            for composite_handler in self.handlers_map.values():
                try:
                    composite_handler.start()
                except Exception as e:
                    exceptions.append(e)

        if exceptions:
            raise RuntimeError(f"Failed to start dispatcher: {exceptions[0]}")

    def stop(self) -> None:
        """Stop all registered handlers."""
        exceptions = []

        with self.lock:
            handlers_to_stop = list(self.handlers_map.values())

        # Stop all handlers outside the lock to avoid deadlocks
        for composite_handler in handlers_to_stop:
            try:
                composite_handler.stop()
            except Exception as e:
                logger.warning(f"Error stopping composite handler: {e}")
                exceptions.append(e)

        # Clear handlers map after stopping
        with self.lock:
            self.handlers_map.clear()

        if exceptions:
            logger.warning(f"Some handlers failed to stop cleanly: {len(exceptions)} errors")
            # Don't raise exception to allow cleanup to continue
        logger.info(f"All dispatcher handlers stopped: {len(exceptions)} errors")

    def register(self, enum_type: Enum, handler: EventHandler) -> None:
        """
        Register an event handler for a specific event type.
        
        Args:
            enum_type: The enum value identifying the event type
            handler: The handler to register
        """
        with self.lock:
            if enum_type not in self.handlers_map:
                self.handlers_map[enum_type] = CompositeHandler(enum_type)

            composite_handler = self.handlers_map[enum_type]

            with composite_handler.lock:
                composite_handler._check_closed()
                composite_handler.handlers.append(handler)

    def unregister(self, enum_type: Enum, handler: EventHandler) -> None:
        """
        Unregister an event handler.
        
        Args:
            enum_type: The enum value identifying the event type
            handler: The handler to unregister
        """
        with self.lock:
            if enum_type not in self.handlers_map:
                return

            composite_handler = self.handlers_map[enum_type]

            with composite_handler.lock:
                composite_handler._check_closed()
                if handler in composite_handler.handlers:
                    composite_handler.handlers.remove(handler)

    def post_event(self, event: Event) -> None:
        """
        Post an event to be processed.
        
        Args:
            event: The event to post
        """
        enum_type = event.get_type()

        with self.lock:
            if enum_type not in self.handlers_map:
                logger.warning(f"No handler registered for event type: {enum_type}")
                return

            composite_handler = self.handlers_map[enum_type]

        with composite_handler.lock:
            if not composite_handler.started():
                composite_handler.start()
            composite_handler.post_to_all(event)

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
