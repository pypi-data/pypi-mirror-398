"""
Event handler interface for processing events in the dispatcher system.
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from clickzetta_ingestion.common.tools.event import Event

T = TypeVar('T', bound=Event)


class EventHandler(ABC, Generic[T]):
    """
    Interface for handling events of a specific type.
    """
    
    @abstractmethod
    def handle(self, event: T) -> None:
        """
        Handle the given event.
        
        Args:
            event: The event to handle
        """
        pass
    
    @abstractmethod
    def handle_exception(self, event: T, exception: Exception) -> None:
        """
        Handle an exception that occurred while processing an event.
        
        Args:
            event: The event that caused the exception
            exception: The exception that occurred
        """
        pass
