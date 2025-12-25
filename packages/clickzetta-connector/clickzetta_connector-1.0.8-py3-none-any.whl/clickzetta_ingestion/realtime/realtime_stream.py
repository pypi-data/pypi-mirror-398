from clickzetta.connector.v0.enums import RealtimeOperation
from clickzetta_ingestion.realtime.arrow_stream import ArrowStream, RowOperator
from clickzetta_ingestion.realtime.arrow_row import ArrowRow, ArrowIGSTableMeta


class RealtimeStream:
    """Synchronous interface for realtime streaming operations"""

    def __init__(self, meta_data: ArrowIGSTableMeta, client, operation, arrow_table, arrow_stream):
        self.meta_data = meta_data
        self.client = client
        self.operate: RealtimeOperation = operation
        self.operation = operation
        self._closed = False
        self.arrow_table = arrow_table
        self.stream: ArrowStream = arrow_stream

    def create_row(self, operator=RowOperator.INSERT) -> ArrowRow:
        """Create a new row with specified operation"""
        if self._closed:
            raise RuntimeError("Stream is closed, cannot create new row")

        return self.stream.create_row(operator)

    def apply(self, *rows: ArrowRow):
        """Apply one or more rows to the stream"""
        if self._closed:
            raise RuntimeError("Stream is closed")

        self.stream.apply(*rows)

    def flush(self):
        """Flush the stream"""
        if self._closed:
            raise RuntimeError("Stream is closed")

        self.stream.flush()

    def close(self):
        """Close the stream and cleanup resources"""
        if self.stream:
            self.stream.flush()
            self.stream.close()
        self._closed = True
