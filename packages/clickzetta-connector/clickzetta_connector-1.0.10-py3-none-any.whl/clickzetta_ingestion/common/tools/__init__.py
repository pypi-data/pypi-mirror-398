"""
Dispatcher module for event-driven processing in BulkLoad operations.
"""

from clickzetta_ingestion.common.tools.event import Event, PoisonPill
from clickzetta_ingestion.common.tools.event_handler import EventHandler
from clickzetta_ingestion.common.tools.dispatcher import Dispatcher, CompositeHandler
from clickzetta_ingestion.common.tools.cleanup_events import (
    CleanupType,
    CleanFileEvent, 
    CleanSQLEvent
)
from clickzetta_ingestion.common.tools.cleanup_handlers import (
    FileEventHandler,
    SQLEventHandler,
    CompositeCleanupHandler
)

__all__ = [
    # Core dispatcher classes
    'Event',
    'PoisonPill',
    'EventHandler',
    'Dispatcher',
    'CompositeHandler',
    
    # Cleanup specific
    'CleanupType',
    'CleanFileEvent',
    'CleanSQLEvent',
    'FileEventHandler',
    'SQLEventHandler',
    'CompositeCleanupHandler',
]
