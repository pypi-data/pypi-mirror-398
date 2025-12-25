#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LocalBulkLoadHandler - Local implementation of BulkLoadHandler for testing purposes.
"""

import logging
import threading
import time
import uuid
from typing import Dict, Any, Optional

from clickzetta_ingestion.bulkload.bulkload_conf import BulkLoadConf, BulkLoadFileConf
from clickzetta_ingestion.bulkload.bulkload_handler import AbstractBulkLoadHandler
from clickzetta_ingestion.bulkload.bulkload_committer import CommitRequestHolder, CommitResultHolder, CommitState
from clickzetta_ingestion.bulkload.committable import Committable
from clickzetta_ingestion.bulkload.storage.file_options import FormatInterface
from clickzetta_ingestion.bulkload.table_parser import BulkLoadTable, FieldSchema

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')



class LocalBulkLoadHandler(AbstractBulkLoadHandler[Committable]):
    """Local implementation of BulkLoadHandler for testing purposes."""

    def __init__(self, properties: Optional[Dict[str, Any]] = None):
        self._properties = properties or {}
        self._bulk_load_conf: Optional[BulkLoadConf] = None
        self._initialized = False
        self._lock = threading.Lock()

        # Transaction tracking for testing
        self._transaction_counter = 0
        self._transaction_lock = threading.Lock()
        self._last_transaction_id: Optional[str] = None
        
        # State management for testing
        self._commit_failures: Dict[str, str] = {}  # transaction_id -> error_msg
        self._final_states: Dict[str, CommitState] = {}  # transaction_id -> final_state
        
        self._logger = logging.getLogger(__name__)

    def open(self, conf: BulkLoadConf):
        """Open the local bulkload handler."""
        with self._lock:
            if self._initialized:
                return
            
            self._bulk_load_conf = conf
            self._initialized = True
            self._logger.info("LocalBulkLoadHandler opened successfully")

    def _check_opened(self):
        """Check if the handler is opened."""
        if not self._initialized:
            raise RuntimeError("LocalBulkLoadHandler is not opened")

    def get_target_table(self, schema_name: str, table_name: str) -> BulkLoadTable:
        """Get target table information (mock implementation)."""
        self._check_opened()
        
        # Create mock table schema
        field_schemas = [
            FieldSchema(name="col1", field_type="int", nullable=False),
            FieldSchema(name="col2", field_type="int", nullable=True),
            FieldSchema(name="col3", field_type="string", nullable=True)
        ]
        
        return BulkLoadTable(
            table_type="NORMAL",
            schema_name=schema_name,
            table_name=table_name,
            field_schemas=field_schemas,
            primary_key_indices=[],
            partition_key_indices=[],
            partition_spec_values=[],
            partial_update_column_indices=[],
            generated_columns=[]
        )

    def get_target_format(self, table: BulkLoadTable) -> FormatInterface:
        """Get target format for the table (mock implementation)."""
        self._check_opened()
        # Return a mock format interface
        from clickzetta_ingestion.bulkload.storage.parquet_format import IcebergParquetFormat
        return IcebergParquetFormat(table)

    def generate_next_committable(self, request: BulkLoadFileConf.Request) -> BulkLoadFileConf.Response[Committable]:
        """Generate next committable for file operations."""
        self._check_opened()

        file_name = f"{request.prefix()}_{uuid.uuid4()}_{int(time.time() * 1000)}.{request.format()}"
        path = f"{request.base_path()}/{request.partition()}/{file_name}"

        # Create a simple local file committable
        committable = Committable(
            committable_type=Committable.Type.LOCAL_FILE,
            path=path,
            dst_path=f"local_volume/{path}",
            conf={}
        )

        return BulkLoadFileConf.Response(
            path=path,
            file_properties={},
            committable=committable
        )

    def prepare_commit(self, commit_request_holder: CommitRequestHolder[Committable],
                       commit_result_holder: CommitResultHolder):
        """Prepare commit request (mock implementation)."""
        self._check_opened()
        
        transaction_id = commit_request_holder.get_transaction_id()
        self._logger.info(f"LocalBulkLoadHandler preparing commit for transaction: {transaction_id}")
        
        # Just log the committables for testing
        committables = commit_request_holder.get_committables()
        for committable in committables:
            self._logger.debug(f"Preparing committable: {committable}")

    def commit(self, commit_request_holder: CommitRequestHolder[Committable],
               commit_result_holder: CommitResultHolder) -> str:
        """Commit request and return transaction ID."""
        # Note: Don't check opened status for local testing - allow commits even if not explicitly opened
        transaction_id = commit_request_holder.get_transaction_id()
        
        # Check if this transaction was marked to fail
        if transaction_id in self._commit_failures:
            error_msg = self._commit_failures[transaction_id]
            commit_result_holder.set_failed(error_msg)
            logger.info(f"LocalBulkLoadHandler set transaction {transaction_id} to failed state")
            raise RuntimeError(error_msg)

        # Simulate successful commit
        commit_result_holder.set_commit_id(f"commit_{int(time.time() * 1000)}")
        logger.info(f"LocalBulkLoadHandler set transaction {transaction_id} to succeed state")

        self._logger.info(f"LocalBulkLoadHandler committed transaction: {transaction_id}")
        return transaction_id

    def listen(self, transaction_id: str, commit_result_holder: CommitResultHolder):
        """Listen for transaction result (mock implementation)."""
        # Note: Don't check opened status for local testing
        
        # Check if final state was set for testing
        if transaction_id in self._final_states:
            final_state = self._final_states[transaction_id]
            if final_state == CommitState.FAILED:
                logger.info(f"LocalBulkLoadHandler set transaction {transaction_id} to failed state")
                commit_result_holder.set_failed("test-failed")
                return
            elif final_state == CommitState.CANCELLED:
                logger.info(f"LocalBulkLoadHandler set transaction {transaction_id} to cancelled state")
                commit_result_holder.set_abort()
                return
        
        # Default to success
        logger.info(f"LocalBulkLoadHandler set transaction {transaction_id} to succeed state")
        commit_result_holder.set_succeed()
        self._logger.info(f"LocalBulkLoadHandler listened transaction: {transaction_id}")

    def abort(self, transaction_id: str, commit_request_holder: CommitRequestHolder[Committable]):
        """Abort transaction (mock implementation)."""
        # Check transaction ordering
        if not self._initialized:
            return
        self._logger.info(f"LocalBulkLoadHandler aborted transaction: {transaction_id}")

    def close(self):
        """Close the local bulkload handler."""
        if not self._initialized:
            return
        with self._lock:
            self.clean_translation()
        self._logger.info("LocalBulkLoadHandler closed")

    def _generate_next_transaction_id(self, stream_id: str) -> str:
        """Generate next transaction ID."""
        with self._transaction_lock:
            self._transaction_counter += 1
            transaction_id = f"{stream_id}_{int(time.time() * 1000)}_{self._transaction_counter}"
            self._last_transaction_id = transaction_id
            return transaction_id


    def mock_commit_failed(self, transaction_id: str, error_msg: str):
        """Set a transaction to fail during commit (for testing)."""
        self._commit_failures[transaction_id] = error_msg

    def mock_final_state(self, transaction_id: str, state: CommitState):
        """Set final state for a transaction (for testing)."""
        with self._lock:
            self._final_states[transaction_id] = state

    def clean_translation(self):
        self._commit_failures = {}
        self._final_states = {}
        self._transaction_counter = 0
        self._last_transaction_id = None
