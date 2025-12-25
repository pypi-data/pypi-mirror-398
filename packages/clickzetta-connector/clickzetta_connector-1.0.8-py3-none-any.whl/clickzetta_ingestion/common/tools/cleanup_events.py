"""
Cleanup events for BulkLoad operations.
"""
from enum import Enum
from typing import List, Optional

from clickzetta_ingestion.common.tools.event import Event


class CleanupType(Enum):
    """Types of cleanup operations."""
    FILE = "FILE"
    SQL = "SQL"


class CleanFileEvent(Event[CleanupType]):
    """
    Event for cleaning up local files.
    """
    
    def __init__(self, transaction_id: str, files: List[str]):
        """
        Initialize clean file event.
        
        Args:
            transaction_id: Transaction identifier
            files: List of file paths to clean up
        """
        self.transaction_id = transaction_id
        self.files = files or []
    
    def get_type(self) -> CleanupType:
        """Get the event type."""
        return CleanupType.FILE


class CleanSQLEvent(Event[CleanupType]):
    """
    Event for executing cleanup SQL.
    """
    
    def __init__(self, transaction_id: str, sql: str):
        """
        Initialize clean SQL event.
        
        Args:
            transaction_id: Transaction identifier
            sql: SQL statement to execute for cleanup
        """
        self.transaction_id = transaction_id
        self.sql = sql
    
    def get_type(self) -> CleanupType:
        """Get the event type."""
        return CleanupType.SQL
