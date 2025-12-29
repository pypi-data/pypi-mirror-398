import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable, Any, Optional, Tuple

from clickzetta_ingestion._proto import ingestion_v2_pb2, ingestion_pb2
from clickzetta_ingestion.realtime import realtime_options
from clickzetta_ingestion.realtime.buffer import Buffer
from clickzetta_ingestion.realtime.rpc_callback import RequestStreamCallback
from clickzetta_ingestion.realtime.stream_observer import ReferenceCountedStreamObserver
from clickzetta_ingestion.realtime.task import AbstractTask
from clickzetta_ingestion.rpc.cz_igs_context import CZIgsContext
from clickzetta_ingestion.rpc.rpc_request import ServerTokenMap

log = logging.getLogger(__name__)


@dataclass
class ChannelData:
    """Channel data for gRPC communication"""
    host_port: Tuple[str, Optional[int]]
    channel: Any
    reference_stream_observer: ReferenceCountedStreamObserver
    lock: threading.Lock = threading.Lock()


class ArrowFlushTask(AbstractTask):
    """Task for flushing Arrow data"""

    def get_id(self) -> int:
        return self.batch_id

    def get_buffer(self):
        return self.buffer

    def __init__(self, batch_id: int, context: CZIgsContext, buffer: Buffer,
                 server_token_map: ServerTokenMap, channel_data_supplier: Callable[[], ChannelData],
                 request_callback):
        super().__init__()
        self.batch_id: int = batch_id
        self.buffer: Buffer = buffer
        self.priority: int = 0
        self.context: CZIgsContext = context
        self.server_token_map: ServerTokenMap = server_token_map
        self.channel_data_supplier = channel_data_supplier
        self.request_callback: RequestStreamCallback = request_callback
        self.compression_level: int = self.context.configure.get_int(realtime_options.COMPRESSION_LEVEL, -1)
        self.compression_type: str = self.context.configure.get_str(realtime_options.COMPRESSION_TYPE, "")
        self.pooled_allocator_support = context.pooled_allocator_support

    def __lt__(self, other) -> bool:
        return self.batch_id < other.batch_id

    def call_internal(self):
        """Execute the flush task in the background thread"""
        log.debug(f"Thread {threading.current_thread().name} Flushing batch {self.batch_id}...")
        if not self.buffer.is_empty():
            # Get table from first operation
            row = self.buffer.get_operations()[0].row
            if row is None:
                self.future.set_result(True)
                return
            table = row.arrow_table
            num_rows = self.buffer.get_current_lines()
            operations = self.buffer.get_operations()

            # Create batch writer
            from clickzetta_ingestion.realtime.arrow_writer import ArrowRecordBatchWriter
            writer = ArrowRecordBatchWriter(
                table,
                False,
                num_rows
            )
            writer.set_compression(self.compression_type, self.compression_level)

            try:
                # Write all operations
                for op in operations:
                    writer.write(op.row)
                writer.finish()

                # Get encoded data
                is_set_bitmap = writer.encode_is_set_bit_maps()
                arrow_payload = writer.encode_arrow_row()

                # Create request
                request = self._create_mutate_request(
                    table, num_rows,
                    writer.operation_types,
                    is_set_bitmap,
                    arrow_payload
                )

                # Send request
                # Reference source:
                # - {@link clickzetta_ingestion.realtime.arrow_stream.ArrowStream.get_channel_data_supplier}
                channel_data = self.channel_data_supplier()
                with channel_data.lock:
                    self.request_callback.target_host = channel_data.host_port
                    try:
                        self.request_callback.on_success(request, self.future)
                        channel_data.reference_stream_observer.on_next(request)
                    except Exception as e:
                        log.warning(f"Thread {threading.current_thread().name} Failed to send request: {e}")
                        # roll back rpcRequestCallback onSuccess.
                        self.request_callback.on_failure(request, self.future, e)

            finally:
                writer.close()

        else:  # empty buffer then skip call
            self.future.set_result(True)

    def _create_mutate_request(self, table, num_rows, operation_types, is_set_bitmap,
                               arrow_payload) -> ingestion_v2_pb2.MutateRequest:
        """Create mutation request"""
        # Create account info
        account = ingestion_v2_pb2.Account()
        user_ident = ingestion_v2_pb2.UserIdentifier()
        user_ident.instance_id = self.context.instance_id
        user_ident.workspace = self.context.workspace
        if self.context.user_name:
            user_ident.user_name = self.context.user_name
        if self.context.authentication:
            if self.context.user_id is not None:
                user_ident.user_id = self.context.user_id
            if self.context.token:
                account.token = self.context.token
        account.user_ident.CopyFrom(user_ident)

        # Create request
        request = ingestion_v2_pb2.MutateRequest(
            batch_id=self.batch_id,
            write_timestamp=int(time.time() * 1000),
            table_ident=ingestion_v2_pb2.TableIdentifier(
                instance_id=self.context.instance_id,
                workspace=self.context.workspace,
                schema_name=table.schema_name,
                table_name=table.table_name
            ),
            account=account
        )

        # Add server tokens if required
        if self.server_token_map:
            if self.server_token_map.is_legacy_server_token_required():
                request.server_token = self.server_token_map.get_legacy_server_token()
            request.server_tokens.update(self.server_token_map.server_tokens)

        # Create data block
        data_block = ingestion_v2_pb2.DataBlock(
            arrow_payload=arrow_payload,
            num_rows=num_rows,
            # The old version of the PK table need it, currently, it is not used
            is_set_bitmaps_payload=is_set_bitmap
        )

        # Handle operation types
        if table.igs_table_type != ingestion_pb2.IGSTableType.ACID:
            # For non-ACID tables, only INSERT is supported
            if len(operation_types) != 1 or operation_types[0] != ingestion_v2_pb2.OperationType.INSERT:
                raise ValueError("Common & ClusterTable only support Insert Operation")
            data_block.block_op_type = operation_types[0]
        else:
            # For ACID tables, multiple operation types are supported
            op_type_list = ingestion_v2_pb2.OperationTypeList()
            op_type_list.op_types.extend(operation_types)
            data_block.row_op_type_list.CopyFrom(op_type_list)

        request.data_block.CopyFrom(data_block)
        return request
