from enum import Enum, auto
from typing import Dict, Any, Set, List
import logging
import grpc
from clickzetta_ingestion._proto import ingestion_pb2, ingestion_v2_pb2

log = logging.getLogger(__name__)

COMPRESSION_LEVEL = "arrow.compression.level"
COMPRESSION_TYPE = "arrow.compression.type"


class RetryStatus(Enum):
    """Retry status codes"""
    THROTTLED = 0
    FAILED = auto()
    NOT_FOUND = auto()
    INTERNAL_ERROR = auto()
    PRECHECK_FAILED = auto()
    STREAM_UNAVAILABLE = auto()


class RegisterStatus:
    """Registry for retry status codes"""

    def __init__(self):
        self.code_list: List = []
        self.v2_code_list: List = []

    def register_code(self, retry_status: RetryStatus):
        """Register a retry status code"""
        descriptor1 = ingestion_pb2.Code.DESCRIPTOR.values_by_name.get(retry_status.name)
        if descriptor1 is not None:
            self.code_list.append(descriptor1.number)

        descriptor2 = ingestion_v2_pb2.Code.DESCRIPTOR.values_by_name.get(retry_status.name)
        if descriptor2 is not None:
            self.v2_code_list.append(descriptor2.number)

    def get_code_list(self) -> List:
        return self.code_list

    def get_v2_code_list(self) -> List:
        return self.v2_code_list

    # Default instance
    DEFAULT = None


# Initialize the default instance
if not RegisterStatus.DEFAULT:
    RegisterStatus.DEFAULT = RegisterStatus()
    RegisterStatus.DEFAULT.register_code(RetryStatus.THROTTLED)
    RegisterStatus.DEFAULT.register_code(RetryStatus.FAILED)
    RegisterStatus.DEFAULT.register_code(RetryStatus.NOT_FOUND)
    # INTERNAL_ERROR and PRECHECK_FAILED should not be retried
    # RegisterStatus.DEFAULT.register_code(RetryStatus.INTERNAL_ERROR)
    # RegisterStatus.DEFAULT.register_code(RetryStatus.PRECHECK_FAILED)
    RegisterStatus.DEFAULT.register_code(RetryStatus.STREAM_UNAVAILABLE)


class FlushMode(str, Enum):
    AUTO_FLUSH_BACKGROUND = "auto_flush_background"
    AUTO_FLUSH_SYNC = "auto_flush_sync"
    MANUAL_FLUSH = "manual_flush"


class ErrorTypeHandler(str, Enum):
    TERMINATE_INSTANCE = "terminate_instance"
    IGNORE = "ignore"

    def on_failure(self, request, response, e):
        pass

    def on_success(self, request, response):
        pass


class RetryMode(str, Enum):
    BATCH_REQUEST_MODE = "BATCH_REQUEST_MODE"
    ROW_REQUEST_MODE = "ROW_REQUEST_MODE"
    NO_RETRY_MODE = "NO_RETRY_MODE"


class ProtocolType(str, Enum):
    V2 = "v2"


class CZSessionOptions:
    DEFAULT_FLUSH_MODE = FlushMode.AUTO_FLUSH_BACKGROUND
    DEFAULT_MUTATION_FLUSH_INTERVAL = 10 * 1000  # 10s
    DEFAULT_MUTATION_BUFFER_SIZE = 10 * 1024 * 1024  # 10MB
    DEFAULT_MUTATION_BUFFER_MAX_NUM = 10
    DEFAULT_MUTATION_LINES_NUM = 1000
    DEFAULT_ERROR_HANDLER = ErrorTypeHandler.TERMINATE_INSTANCE
    DEFAULT_REQUEST_FAILED_RETRY_ENABLE = True
    DEFAULT_REQUEST_FAILED_RETRY_MODE = RetryMode.BATCH_REQUEST_MODE
    DEFAULT_REQUEST_FAILED_RETRY_TIMES = 5
    DEFAULT_REQUEST_FAILED_RETRY_INTERNAL_MS = 5000
    DEFAULT_REQUEST_FAILED_RETRY_LOG_DEBUG_ENABLE = True
    DEFAULT_PROTOCOL_TYPE = ProtocolType.V2
    DEFAULT_GRPC_MAX_MESSAGE_LENGTH = 25 * 1024 * 1024  # 25MB
    DEFAULT_REGISTER_STATUS = RegisterStatus()
    # Only register status codes that should be retried
    DEFAULT_REGISTER_STATUS.register_code(RetryStatus.THROTTLED)
    DEFAULT_REGISTER_STATUS.register_code(RetryStatus.FAILED)
    DEFAULT_REGISTER_STATUS.register_code(RetryStatus.NOT_FOUND)
    DEFAULT_REGISTER_STATUS.register_code(RetryStatus.STREAM_UNAVAILABLE)
    # INTERNAL_ERROR and PRECHECK_FAILED should not be retried

    # Default reconnect configuration
    DEFAULT_TABLET_IDLE_RECREATE_SUPPORT = True
    # Used the original status code in grpc, STREAM_UNAVAILABLE = 6
    DEFAULT_TABLET_IDLE_STATUS = {
        ingestion_v2_pb2.Code.STREAM_UNAVAILABLE.numerator,
    }

    def __init__(self):
        self.flush_mode = self.DEFAULT_FLUSH_MODE
        self.flush_interval = self.DEFAULT_MUTATION_FLUSH_INTERVAL
        self.mutation_buffer_space = self.DEFAULT_MUTATION_BUFFER_SIZE
        self.mutation_buffer_max_num = self.DEFAULT_MUTATION_BUFFER_MAX_NUM
        self.mutation_buffer_lines_num = self.DEFAULT_MUTATION_LINES_NUM
        self.error_type_handler: ErrorTypeHandler = self.DEFAULT_ERROR_HANDLER
        self.request_failed_retry_enable = self.DEFAULT_REQUEST_FAILED_RETRY_ENABLE
        self.request_failed_retry_mode = self.DEFAULT_REQUEST_FAILED_RETRY_MODE
        self.request_failed_retry_times = self.DEFAULT_REQUEST_FAILED_RETRY_TIMES
        self.request_failed_retry_internal_ms = self.DEFAULT_REQUEST_FAILED_RETRY_INTERNAL_MS
        self.request_failed_retry_log_debug_enable = self.DEFAULT_REQUEST_FAILED_RETRY_LOG_DEBUG_ENABLE
        self.request_failed_retry_register_status = self.DEFAULT_REGISTER_STATUS
        self.protocol_type = self.DEFAULT_PROTOCOL_TYPE
        self.properties: Dict[str, Any] = {}
        self.grpc_max_message_length = self.DEFAULT_GRPC_MAX_MESSAGE_LENGTH
        self.rpc_call_options = [
            ('grpc.max_send_message_length', self.grpc_max_message_length),
            ('grpc.max_receive_message_length', self.grpc_max_message_length),
            ('grpc.default_compression_algorithm', grpc.Compression.Gzip),
            ('grpc.deadline', 10)  # 10 seconds
        ]

        # Reconnect configuration
        self.tablet_idle_recreate_support = self.DEFAULT_TABLET_IDLE_RECREATE_SUPPORT
        self.reconnect_status: Set[int] = self.DEFAULT_TABLET_IDLE_STATUS

    @classmethod
    def default(cls):
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'flush_mode': self.flush_mode,
            'flush_interval': self.flush_interval,
            'mutation_buffer_space': self.mutation_buffer_space,
            'mutation_buffer_max_num': self.mutation_buffer_max_num,
            'mutation_buffer_lines_num': self.mutation_buffer_lines_num,
            'request_failed_retry_register_status': self.request_failed_retry_register_status,
            'error_type_handler': self.error_type_handler,
            'request_failed_retry_enable': self.request_failed_retry_enable,
            'request_failed_retry_mode': self.request_failed_retry_mode,
            'request_failed_retry_times': self.request_failed_retry_times,
            'request_failed_retry_internal_ms': self.request_failed_retry_internal_ms,
            'request_failed_retry_log_debug_enable': self.request_failed_retry_log_debug_enable,
            'protocol_type': self.protocol_type,
            'properties': self.properties,
            'grpc_max_message_length': self.grpc_max_message_length
        }


class RealtimeOptionsBuilder:
    def __init__(self):
        self._options = CZSessionOptions()

    def with_flush_mode(self, flush_mode: FlushMode):
        self._options.flush_mode = flush_mode
        return self

    def with_flush_interval(self, flush_interval: int):
        """
        Set the flush interval in milliseconds. The default value is 10s.
        """
        if flush_interval < 0:
            raise ValueError("flushInterval must >= 0")
        self._options.flush_interval = flush_interval
        return self

    def with_mutation_buffer_space(self, buffer_space: int):
        if buffer_space > self._options.grpc_max_message_length:
            raise ValueError(
                f"mutation buffer space size ({buffer_space}) must <= "
                f"grpc max message size ({self._options.grpc_max_message_length})"
            )
        self._options.mutation_buffer_space = buffer_space
        return self

    def with_mutation_buffer_max_num(self, max_num: int):
        self._options.mutation_buffer_max_num = max_num
        return self

    def with_mutation_buffer_lines_num(self, lines_num: int):
        self._options.mutation_buffer_lines_num = lines_num
        return self

    def with_error_type_handler(self, handler: ErrorTypeHandler):
        self._options.error_type_handler = handler
        return self

    def with_request_failed_retry_enable(self, enabled: bool):
        self._options.request_failed_retry_enable = enabled
        return self

    def with_request_failed_retry_mode(self, mode: RetryMode):
        self._options.request_failed_retry_mode = mode
        return self

    def with_request_failed_retry_times(self, times: int):
        self._options.request_failed_retry_times = times
        return self

    def with_request_failed_retry_internal_ms(self, internal_ms: int):
        self._options.request_failed_retry_internal_ms = internal_ms
        return self

    def with_request_failed_retry_log_debug_enable(self, enabled: bool):
        self._options.request_failed_retry_log_debug_enable = enabled
        return self

    def with_request_failed_retry_status(self, retry_status) -> 'RealtimeOptionsBuilder':
        """
        Set retry status codes. Can accept a list of RetryStatus.
        
        Example:
            .with_request_failed_retry_status([RetryStatus.THROTTLED, RetryStatus.STREAM_UNAVAILABLE])
        """
        # Create a new RegisterStatus instance to avoid modifying the default
        new_register_status = RegisterStatus()
        
        # Handle list/tuple arguments
        if isinstance(retry_status, (list, tuple)):
            statuses = retry_status
        else:
            statuses = [retry_status]
                
        # Register each status
        for status in statuses:
            new_register_status.register_code(status)
            
        self._options.request_failed_retry_register_status = new_register_status
        return self

    def with_protocol_type(self, protocol_type: ProtocolType):
        self._options.protocol_type = protocol_type
        return self

    def with_properties(self, properties: Dict[str, Any]):
        if properties:
            self._options.properties.update(properties)
        return self

    def with_grpc_max_message_length(self, max_length: int):
        self._options.grpc_max_message_length = max_length
        return self

    def with_tablet_idle_recreate_support(self, enabled: bool):
        """Enable/disable tablet idle recreation support"""
        self._options.tablet_idle_recreate_support = enabled
        return self

    def with_tablet_idle_status(self, status_set: Set[RetryStatus]):
        """Set tablet idle status codes"""
        self._options.reconnect_status = {status.value for status in status_set}
        return self

    def build(self) -> CZSessionOptions:
        if (self._options.request_failed_retry_enable and
                self._options.request_failed_retry_times <= 0):
            raise ValueError("request failed retry times must be > 0 when retry is enabled")

        if self._options.request_failed_retry_internal_ms <= 0:
            raise ValueError("request retry internal ms must be > 0 when retry is enabled")

        if self._options.mutation_buffer_space > self._options.grpc_max_message_length:
            raise ValueError(
                f"mutation buffer space size ({self._options.mutation_buffer_space}) must <= "
                f"grpc max message size ({self._options.grpc_max_message_length})"
            )

        return self._options


DEFAULT = CZSessionOptions()
