#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import TypeVar

from clickzetta_ingestion.bulkload.bulkload_committer import BulkLoadCommitter
from clickzetta_ingestion.bulkload.bulkload_conf import BulkLoadConf
from clickzetta_ingestion.bulkload.bulkload_context import BulkLoadContext
from clickzetta_ingestion.bulkload.bulkload_factory import BulkLoadFactory
from clickzetta_ingestion.bulkload.bulkload_stream import AbstractBulkLoadStream
from clickzetta_ingestion.bulkload.bulkload_writer import BulkLoadWriter

InputT = TypeVar('InputT')
CommT = TypeVar('CommT')

logger = logging.getLogger(__name__)


class BulkLoadStreamImpl(AbstractBulkLoadStream[InputT, CommT]):
    """Final implementation of BulkLoadStream using factory pattern."""

    def __init__(self, schema_name: str, table_name: str, factory: BulkLoadFactory[InputT, CommT]):
        super().__init__(schema_name, table_name)
        if factory is None:
            raise ValueError("bulkLoad factory cannot be None.")
        self._factory = factory

    def internal_build_writer(self, context: BulkLoadContext, conf: BulkLoadConf) -> BulkLoadWriter[InputT, CommT]:
        """Create writer using factory."""
        return self._factory.create_writer(context, conf)

    def internal_build_committer(self, context: BulkLoadContext, conf: BulkLoadConf) -> BulkLoadCommitter[CommT]:
        """Create committer using factory."""
        return self._factory.create_committer(context, conf)
