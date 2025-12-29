"""
Cleanup event handlers for BulkLoad operations.
"""
import os
import logging
from typing import Optional, Callable, Any, List

from clickzetta_ingestion.common.tools.event_handler import EventHandler
from clickzetta_ingestion.common.tools.cleanup_events import CleanFileEvent, CleanSQLEvent

logger = logging.getLogger(__name__)


class FileEventHandler(EventHandler[CleanFileEvent]):
    """
    Handler for file cleanup events.
    """
    
    def handle(self, event: CleanFileEvent) -> None:
        """
        Handle file cleanup event.
        
        Args:
            event: The file cleanup event
        """
        logger.debug(f"FileEventHandler.handle called for transaction {event.transaction_id}")
        
        # Filter out empty file paths
        files = [f for f in event.files if f and f.strip()]
        
        if not files:
            logger.debug(f"Transaction {event.transaction_id}: No files to clean up")
            return
        
        logger.info(f"Transaction {event.transaction_id} cleaning up {len(files)} local files:\n"
                   f"|-----------------------------------------\n"
                   f"{chr(10).join(files)}\n"
                   f"|-----------------------------------------")
        
        for file_path in files:
            try:
                if os.path.exists(file_path):
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.debug(f"Deleted file: {file_path}")
                    elif os.path.isdir(file_path):
                        # Recursively delete directory
                        import shutil
                        shutil.rmtree(file_path)
                        logger.debug(f"Deleted directory: {file_path}")
                else:
                    logger.debug(f"File does not exist: {file_path}")
            except Exception as e:
                # Log but don't fail - best effort cleanup
                logger.warning(f"Failed to delete file {file_path}: {e}")
    
    def handle_exception(self, event: CleanFileEvent, exception: Exception) -> None:
        """
        Handle exception during file cleanup.
        
        Args:
            event: The file cleanup event
            exception: The exception that occurred
        """
        logger.error(f"Exception during file cleanup for transaction {event.transaction_id}: {exception}")


class SQLEventHandler(EventHandler[CleanSQLEvent]):
    """
    Handler for SQL cleanup events.
    """
    
    def __init__(self, get_connection_func: Optional[Callable[[], Any]] = None):
        """
        Initialize SQL event handler.
        
        Args:
            get_connection_func: Function to get database connection for executing SQL
        """
        self.get_connection_func = get_connection_func
    
    def handle(self, event: CleanSQLEvent) -> None:
        """
        Handle SQL cleanup event.
        
        Args:
            event: The SQL cleanup event

        Example:
              remove table volume `meta_warehouse`.`liulei_tmp_test_partition_table_1` regexp 'default-stream-id_20ae1193a74d4bb68116fe7b6e944f39_1764661476573_1/bulkload_44c4b295-263e-4515-840b-24fc197437d8_1764661476564_1.parquet|default-stream-id_20ae1193a74d4bb68116fe7b6e944f39_1764661476573_1/bulkload_7d2324a6-b5f5-498d-b1c4-df8402419586_1764661476504_0.parquet'
        """
        if not event.sql or not event.sql.strip():
            logger.debug(f"Transaction {event.transaction_id}: No SQL to execute")
            return
        
        final_cleanup_sql = event.sql.strip()
        
        logger.info(f"Transaction {event.transaction_id} executing cleanup SQL:\n"
                   f"|-----------------------------------------\n"
                   f"{final_cleanup_sql}\n"
                   f"|-----------------------------------------")
        
        if not self.get_connection_func:
            logger.warning(f"No connection function provided, cannot execute SQL: {final_cleanup_sql}")
            return
        
        try:
            # Get connection from the provided function
            connection = self.get_connection_func()
            
            # Try to execute the SQL
            # This assumes the connection has an execute method or similar
            cursor = connection.cursor()
            cursor.execute(final_cleanup_sql)
            cursor.close()
            logger.debug(f"Successfully executed cleanup SQL for transaction {event.transaction_id}")
        except Exception as e:
            # Log but don't fail - best effort cleanup
            logger.warning(f"Failed to execute cleanup SQL for transaction {event.transaction_id}: {e}")
    
    def handle_exception(self, event: CleanSQLEvent, exception: Exception) -> None:
        """
        Handle exception during SQL cleanup.
        
        Args:
            event: The SQL cleanup event
            exception: The exception that occurred
        """
        logger.error(f"Exception during SQL cleanup for transaction {event.transaction_id}: {exception}")


class CompositeCleanupHandler:
    """
    Composite handler that manages both file and SQL cleanup.
    """
    
    def __init__(self, dispatcher, get_connection_func: Optional[Callable[[], Any]] = None):
        """
        Initialize composite cleanup handler.
        
        Args:
            dispatcher: The dispatcher to register handlers with
            get_connection_func: Function to get database connection for SQL cleanup
        """
        self.dispatcher = dispatcher
        self.file_handler = FileEventHandler()
        self.sql_handler = SQLEventHandler(get_connection_func)
        
        # Register handlers
        from clickzetta_ingestion.common.tools.cleanup_events import CleanupType
        self.dispatcher.register(CleanupType.FILE, self.file_handler)
        self.dispatcher.register(CleanupType.SQL, self.sql_handler)
    
    def post_file_cleanup(self, transaction_id: str, files: List[str]) -> None:
        """
        Post a file cleanup event.
        
        Args:
            transaction_id: Transaction identifier
            files: List of files to clean up
        """
        event = CleanFileEvent(transaction_id, files)
        self.dispatcher.post_event(event)
    
    def post_sql_cleanup(self, transaction_id: str, sql: str) -> None:
        """
        Post a SQL cleanup event.
        
        Args:
            transaction_id: Transaction identifier
            sql: SQL to execute for cleanup
        """
        event = CleanSQLEvent(transaction_id, sql)
        self.dispatcher.post_event(event)
    
    def unregister(self) -> None:
        """Unregister all handlers from dispatcher."""
        from clickzetta_ingestion.common.tools.cleanup_events import CleanupType
        self.dispatcher.unregister(CleanupType.FILE, self.file_handler)
        self.dispatcher.unregister(CleanupType.SQL, self.sql_handler)
