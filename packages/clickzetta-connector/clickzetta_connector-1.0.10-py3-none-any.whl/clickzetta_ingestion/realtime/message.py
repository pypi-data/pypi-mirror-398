import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from typing import TypeVar, Generic

from google.protobuf.message import Message

from clickzetta_ingestion._proto import ingestion_v2_pb2
from clickzetta_ingestion.realtime.arrow_row import ArrowRow
from clickzetta_ingestion.realtime.arrow_table import ArrowTable

T = TypeVar('T', bound=Message)


class RequestMessage(Generic[T], ABC):
    """Base class for request messages"""

    def __init__(self, message: T):
        self.message = message

    @abstractmethod
    def get_request_id(self) -> int:
        """Get request ID"""
        ...

    @abstractmethod
    def get_timestamp(self) -> int:
        """Get request timestamp"""
        ...

    @abstractmethod
    def get_batch_count(self) -> int:
        """Get batch count"""
        ...

    @abstractmethod
    def message_size(self) -> int:
        """Get message size"""
        ...

    def get_original(self) -> T:
        """Get original protobuf message"""
        return self.message


class ResponseMessage(Generic[T], ABC):
    """Base class for response messages"""

    def __init__(self, message: T):
        self.message = message

    @abstractmethod
    def get_request_id(self) -> int:
        """Get request ID"""
        ...

    @abstractmethod
    def get_num_rows(self) -> int:
        """Get number of rows"""
        ...

    @abstractmethod
    def get_status_code(self) -> int:
        """Get status code"""
        ...

    def get_original(self) -> T:
        """Get original protobuf message"""
        return self.message


class ArrowRequestMessage(RequestMessage[ingestion_v2_pb2.MutateRequest]):
    """Arrow mutation request message"""

    def __init__(self, message: ingestion_v2_pb2.MutateRequest):
        super().__init__(message)

    def get_request_id(self) -> int:
        return self.message.batch_id

    def get_timestamp(self) -> int:
        return self.message.write_timestamp or int(time.time() * 1000)

    def get_batch_count(self) -> int:
        return self.message.data_block.num_rows

    def message_size(self) -> int:
        return len(self.message.SerializeToString())


class ArrowResponseMessage(ResponseMessage[ingestion_v2_pb2.MutateResponse]):
    """Arrow mutation response message"""

    def __init__(self, message: ingestion_v2_pb2.MutateResponse):
        super().__init__(message)

    def get_request_id(self) -> int:
        return self.message.batch_id

    def get_num_rows(self) -> int:
        return self.message.num_rows

    def get_status_code(self) -> int:
        return self.message.status.code


@dataclass
class Message(ABC):
    """Base message interface"""

    session_id: str
    batch_id: int
    timestamp: int
    schema_name: List[str]
    table_name: List[str]
    total_rows: int
    error_rows: int = 0
    error_rows_data: Optional[List[ArrowRow]] = None

    def get_session_id(self) -> str:
        return self.session_id

    def get_batch_id(self) -> int:
        return self.batch_id

    def get_timestamp(self) -> int:
        return self.timestamp

    def get_schema_name(self) -> List[str]:
        return self.schema_name

    def get_table_name(self) -> List[str]:
        return self.table_name

    def get_total_rows_count(self) -> int:
        return self.total_rows

    def get_error_rows_count(self) -> int:
        return self.error_rows

    def get_error_rows(self) -> Optional[List[ArrowRow]]:
        return self.error_rows_data


class ArrowSuccessMessage(Message):
    """Message for successful Arrow RPC response"""

    def __init__(self, session_id: str, request: ingestion_v2_pb2.MutateRequest,
                 response: ingestion_v2_pb2.MutateResponse):
        super().__init__(
            session_id=session_id,
            batch_id=request.batch_id,
            timestamp=request.write_timestamp,
            schema_name=[request.table_ident.schema_name],
            table_name=[request.table_ident.table_name],
            total_rows=request.data_block.num_rows,
            error_rows=0,
            error_rows_data=None
        )
        self.request = request
        self.response = response


class ArrowFailureMessage(Message):
    """Message for failed Arrow RPC response"""

    def __init__(self, session_id: str, arrow_table: ArrowTable,
                 request: ingestion_v2_pb2.MutateRequest,
                 response: ingestion_v2_pb2.MutateResponse):
        super().__init__(
            session_id=session_id,
            batch_id=request.batch_id,
            timestamp=request.write_timestamp,
            schema_name=[request.table_ident.schema_name],
            table_name=[request.table_ident.table_name],
            total_rows=request.data_block.num_rows,
            error_rows=0,
            error_rows_data=None
        )
        self.request = request
        self.response = response
        self.arrow_table = arrow_table

    def get_error_rows_count(self) -> int:
        if self.response.row_status_list:
            return sum(1 for status in self.response.row_status_list
                       if status.code != ingestion_v2_pb2.Code.SUCCESS)
        return 0

    def get_error_rows(self) -> Optional[List[ArrowRow]]:
        if self.response.row_status_list:
            error_statuses = sorted(
                [status for status in self.response.row_status_list
                 if status.code != ingestion_v2_pb2.Code.SUCCESS],
                key=lambda x: x.row_index
            )
            return self._decode_arrow_row(self.request, error_statuses)
        return None

    def _decode_arrow_row(self, request: ingestion_v2_pb2.MutateRequest,
                          error_statuses: List[ingestion_v2_pb2.MutateRowStatus]) -> List[ArrowRow]:
        # TODO: Implement arrow row decoding
        return []


class ArrowErrorMessage(Message):
    """Message for Arrow errors"""
    """Message for failed Arrow RPC response"""

    def __init__(self, session_id: str, arrow_table: ArrowTable,
                 request: ingestion_v2_pb2.MutateRequest):
        super().__init__(
            session_id=session_id,
            batch_id=request.batch_id,
            timestamp=request.write_timestamp,
            schema_name=[request.table_ident.schema_name],
            table_name=[request.table_ident.table_name],
            total_rows=request.data_block.num_rows,
            error_rows=0,
            error_rows_data=None
        )
        self.request = request
        self.arrow_table = arrow_table


@dataclass
class AtomicReference:
    """Thread-safe wrapper for a value"""

    def __init__(self, initial_value=None):
        self._value = initial_value
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)

    def get(self):
        """Get current value"""
        with self._lock:
            return self._value

    def set(self, new_value):
        """Set new value"""
        with self._lock:
            self._value = new_value
            return self._value

    def compare_and_set(self, expect, update):
        """Compare and set value atomically"""
        with self._lock:
            if self._value == expect:
                self._value = update
                return True
            return False

    def get_lock_condition(self):
        """Get object lock"""
        return self._condition

    def __str__(self):
        with self._lock:
            return str(self._value)

    def __repr__(self):
        return f'{self.__class__.__name__}({self._value})'


class AtomicInteger(AtomicReference):
    def __init__(self, initial_value=0):
        super().__init__(initial_value)

    def get_and_increment(self):
        with self._lock:
            current_value = self._value
            self._value += 1
            return current_value

    def get_and_decrement(self):
        with self._lock:
            current_value = self._value
            self._value -= 1
            self._condition.notify_all()
            return current_value

    def increment_and_get(self):
        with self._lock:
            self._value += 1
            return self._value

    def decrement_and_get(self):
        with self._lock:
            self._value -= 1
            self._condition.notify_all()
            return self._value
