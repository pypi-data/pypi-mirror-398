from typing import Optional

from clickzetta_ingestion.bulkload.storage.output_format import Stats


class BulkLoadStats:
    """Statistics for bulk load operations."""

    def __init__(self, output_stats: Optional[Stats] = None):
            self.output_stats = output_stats

    def get_rows_written(self) -> int:
        return self.output_stats.total_count()

    def get_files_written(self) -> int:
        # Not implemented yet
        return 0

    def get_bytes_written(self) -> int:
        return self.output_stats.total_size()
