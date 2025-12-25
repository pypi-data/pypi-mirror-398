from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any, TYPE_CHECKING

from clickzetta_ingestion.bulkload.bulkload_conf import BulkLoadConf, BulkLoadFileConf
from clickzetta_ingestion.bulkload.storage.file_options import FormatInterface
from clickzetta_ingestion.common.row import Row as ArrowRow

if TYPE_CHECKING:
    from clickzetta_ingestion.bulkload.bulkload_committer import CommitRequestHolder, CommitResultHolder

C = TypeVar('C')

class AbstractBulkLoadHandler(ABC, Generic[C]):
    """Handler for bulkload operations."""

    @abstractmethod
    def open(self, conf: BulkLoadConf):
        """Open the bulkload handler with configuration."""
        pass

    @abstractmethod
    def get_target_table(self, schema_name: str, table_name: str) -> Any:
        """Get target table information."""
        pass

    @abstractmethod
    def generate_next_committable(self, request: BulkLoadFileConf.Request) -> BulkLoadFileConf.Response[C]:
        """Generate next committable for file operations."""
        pass

    @abstractmethod
    def prepare_commit(self, commit_request_holder: "CommitRequestHolder[C]",
                       commit_result_holder: "CommitResultHolder"):
        """Prepare commit request with commit result."""
        pass

    @abstractmethod
    def commit(self, commit_request_holder: "CommitRequestHolder[C]",
               commit_result_holder: "CommitResultHolder") -> str:
        """Commit request and return transactionId with commit result."""
        pass

    @abstractmethod
    def listen(self, transaction_id: str, commit_result_holder: "CommitResultHolder"):
        """Listen target transactionId with commit result."""
        pass

    @abstractmethod
    def abort(self, transaction_id: str, commit_request_holder: "CommitRequestHolder[C]"):
        """Abort transactionId which maybe not exists & use commit request to clean up."""
        pass

    @abstractmethod
    def close(self):
        """Close the bulkload handler."""
        pass

    @abstractmethod
    def get_target_format(self, table: Any) -> FormatInterface[ArrowRow]:
        """Get target format for the table."""
        pass
