"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from . import ingestion_pb2 as ingestion__pb2
GRPC_GENERATED_VERSION = '1.68.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False
try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True
if _version_not_supported:
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + f' but the generated code in ingestion_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class IGSControllerServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GatewayRpcCall = channel.unary_unary('/cz.proto.ingestion.IGSControllerService/GatewayRpcCall', request_serializer=ingestion__pb2.GatewayRequest.SerializeToString, response_deserializer=ingestion__pb2.GatewayResponse.FromString, _registered_method=True)

class IGSControllerServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GatewayRpcCall(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_IGSControllerServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {'GatewayRpcCall': grpc.unary_unary_rpc_method_handler(servicer.GatewayRpcCall, request_deserializer=ingestion__pb2.GatewayRequest.FromString, response_serializer=ingestion__pb2.GatewayResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('cz.proto.ingestion.IGSControllerService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('cz.proto.ingestion.IGSControllerService', rpc_method_handlers)

class IGSControllerService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GatewayRpcCall(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.IGSControllerService/GatewayRpcCall', ingestion__pb2.GatewayRequest.SerializeToString, ingestion__pb2.GatewayResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)