"""
Event interfaces and base classes for the dispatcher system.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import TypeVar, Generic, Any

E = TypeVar('E', bound=Enum)


class Event(ABC, Generic[E]):
    """
    Base interface for events in the dispatcher system.
    """
    
    @abstractmethod
    def get_type(self) -> E:
        """
        Get the type of this event.
        
        Returns:
            The event type as an Enum value
        """
        pass


class PoisonPill(Event[Enum]):
    """
    Special event used to signal shutdown of event processing.
    """
    
    class PillType(Enum):
        """Enum for poison pill type."""
        PILL = "PILL"
    
    def get_type(self) -> Enum:
        """Get the poison pill type."""
        return self.PillType.PILL
