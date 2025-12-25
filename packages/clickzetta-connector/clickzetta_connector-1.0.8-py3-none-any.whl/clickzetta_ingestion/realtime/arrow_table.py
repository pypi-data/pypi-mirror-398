import logging
from typing import List, Optional

from clickzetta_ingestion._proto import ingestion_pb2
from clickzetta_ingestion.realtime.arrow_row import ArrowIGSTableMeta, DataField
from clickzetta_ingestion.rpc import arrow_utils

logger = logging.getLogger(__name__)


class ArrowTable:
    def __init__(self, igs_table_meta: ArrowIGSTableMeta):
        self.table_id = -1
        self.schema_name = igs_table_meta.schema_name
        self.table_name = igs_table_meta.table_name
        self.meta: ArrowIGSTableMeta = igs_table_meta
        self.igs_table_type = igs_table_meta.table_type
        self.buckets_num: int = self._init_number_of_buckets()

        from clickzetta_ingestion.realtime.arrow_schema import ArrowSchema
        self.arrow_schema: ArrowSchema = arrow_utils.convert_to_external_schema(
            self.meta.table_meta,
            self.meta.data_fields
        )

    def _init_number_of_buckets(self) -> int:
        if self.igs_table_type != ingestion_pb2.IGSTableType.NORMAL:
            return self.meta.dist_spec.num_buckets if self.meta.dist_spec else 0
        return 0

    def get_column_index(self, column_name: str) -> Optional[int]:
        """Get column index by name"""
        for i, field in enumerate(self.meta.data_fields):
            if field.name == column_name:
                return i
        return None

    def get_column_by_index(self, index: int) -> Optional[DataField]:
        """Get column field by index"""
        if 0 <= index < len(self.meta.data_fields):
            return self.meta.data_fields[index]
        return None

    def get_column_names(self) -> List[str]:
        """Get list of column names"""
        return [field.name for field in self.meta.data_fields]

    def is_require_commit(self) -> bool:
        """Check if table requires commit"""
        return self.meta.require_commit

    def set_require_commit(self, require_commit: bool):
        """Set whether table requires commit"""
        self.meta.require_commit = require_commit
