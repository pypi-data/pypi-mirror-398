from typing import TypeVar, Any

from google.protobuf.json_format import Parse

from clickzetta_ingestion._proto import ingestion_pb2, ingestion_v2_pb2

T = TypeVar('T')


class ResponseConstructor:
    """Protobuf response constructor for different method types"""

    @staticmethod
    def get_response(method: ingestion_pb2.MethodEnum, response_str: str) -> Any:
        """
        Get appropriate response object based on method type
        
        Args:
            method: Method enum value
            response_str: Response string in JSON format
            
        Returns:
            Parsed protobuf message
        """
        # Handle gateway response first
        if method == ingestion_pb2.MethodEnum.GATEWAY_RPC_CALL:
            return Parse(response_str, ingestion_pb2.GatewayResponse(), ignore_unknown_fields=True)

        # Handle specific response types
        if method == ingestion_pb2.MethodEnum.CREATE_OR_GET_STREAM_V2:
            return Parse(response_str, ingestion_v2_pb2.CreateOrGetStreamResponse(), ignore_unknown_fields=True)

        if method == ingestion_pb2.MethodEnum.CHECK_COMMIT_RESULT_V2:
            return Parse(response_str, ingestion_v2_pb2.CheckCommitResultResponse(), ignore_unknown_fields=True)

        if method in (ingestion_pb2.MethodEnum.COMMIT_V2, ingestion_pb2.MethodEnum.ASYNC_COMMIT_V2):
            return Parse(response_str, ingestion_v2_pb2.CommitResponse(), ignore_unknown_fields=True)

        # For future extension, we can add more response types here
        raise ValueError(f"Unsupported method type: {method}")
