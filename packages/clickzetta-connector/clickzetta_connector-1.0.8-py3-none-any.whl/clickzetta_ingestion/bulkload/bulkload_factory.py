from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from clickzetta_ingestion.bulkload.bulkload_context import BulkLoadContext
from clickzetta_ingestion.bulkload.bulkload_conf import BulkLoadConf
from clickzetta_ingestion.bulkload.bulkload_handler import AbstractBulkLoadHandler
from clickzetta_ingestion.bulkload.bulkload_writer import BulkLoadWriter
from clickzetta_ingestion.bulkload.bulkload_committer import BulkLoadCommitter

T = TypeVar('InputT')
C = TypeVar('CommT')


class BulkLoadFactory(ABC, Generic[T, C]):
    """Factory interface for creating writers and committers."""

    @abstractmethod
    def create_writer(self, context: BulkLoadContext, conf: BulkLoadConf) -> BulkLoadWriter[T, C]:
        """Create a BulkLoadWriter instance."""
        pass

    @abstractmethod
    def create_committer(self, context: BulkLoadContext, conf: BulkLoadConf) -> BulkLoadCommitter[C]:
        """Create a BulkLoadCommitter instance."""
        pass


class BulkLoadFactoryImpl(BulkLoadFactory[T, C]):
    """Default implementation of BulkLoadFactory."""

    def __init__(self, bulk_load_handler: AbstractBulkLoadHandler[C]):
        """Initialize with a bulk load handler."""
        self.bulk_load_handler = bulk_load_handler

    def create_writer(self, context: BulkLoadContext, conf: BulkLoadConf) -> BulkLoadWriter[T, C]:
        """Create a BulkLoadWriter instance."""
        from clickzetta_ingestion.bulkload.bulkload_writer_impl import BulkLoadWriterImpl
        return BulkLoadWriterImpl(context, conf, self.bulk_load_handler)

    def create_committer(self, context: BulkLoadContext, conf: BulkLoadConf) -> BulkLoadCommitter[C]:
        """Create a BulkLoadCommitter instance."""
        from clickzetta_ingestion.bulkload.bulkload_committer_impl import BulkLoadCommitterImpl
        return BulkLoadCommitterImpl(context, conf, self.bulk_load_handler)
