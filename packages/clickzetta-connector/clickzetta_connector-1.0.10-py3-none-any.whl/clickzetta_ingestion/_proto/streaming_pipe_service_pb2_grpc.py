"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from . import streaming_pipe_service_pb2 as streaming__pipe__service__pb2
GRPC_GENERATED_VERSION = '1.68.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False
try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True
if _version_not_supported:
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + f' but the generated code in streaming_pipe_service_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class StreamingPipeServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.StreamingPipe = channel.unary_unary('/cz.proto.common_api.StreamingPipeService/StreamingPipe', request_serializer=streaming__pipe__service__pb2.StreamingPipeRequest.SerializeToString, response_deserializer=streaming__pipe__service__pb2.StreamingPipeResponse.FromString, _registered_method=True)
        self.CreateChannel = channel.unary_unary('/cz.proto.common_api.StreamingPipeService/CreateChannel', request_serializer=streaming__pipe__service__pb2.CreateChannelRequest.SerializeToString, response_deserializer=streaming__pipe__service__pb2.CreateChannelResponse.FromString, _registered_method=True)
        self.ListChannel = channel.unary_unary('/cz.proto.common_api.StreamingPipeService/ListChannel', request_serializer=streaming__pipe__service__pb2.ListChannelRequest.SerializeToString, response_deserializer=streaming__pipe__service__pb2.ListChannelResponse.FromString, _registered_method=True)
        self.GetChannel = channel.unary_unary('/cz.proto.common_api.StreamingPipeService/GetChannel', request_serializer=streaming__pipe__service__pb2.GetChannelRequest.SerializeToString, response_deserializer=streaming__pipe__service__pb2.GetChannelResponse.FromString, _registered_method=True)
        self.DeleteChannel = channel.unary_unary('/cz.proto.common_api.StreamingPipeService/DeleteChannel', request_serializer=streaming__pipe__service__pb2.DeleteChannelRequest.SerializeToString, response_deserializer=streaming__pipe__service__pb2.DeleteChannelResponse.FromString, _registered_method=True)
        self.CommitFile = channel.unary_unary('/cz.proto.common_api.StreamingPipeService/CommitFile', request_serializer=streaming__pipe__service__pb2.CommitFileRequest.SerializeToString, response_deserializer=streaming__pipe__service__pb2.CommitFileResponse.FromString, _registered_method=True)

class StreamingPipeServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def StreamingPipe(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CreateChannel(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ListChannel(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetChannel(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteChannel(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CommitFile(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_StreamingPipeServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {'StreamingPipe': grpc.unary_unary_rpc_method_handler(servicer.StreamingPipe, request_deserializer=streaming__pipe__service__pb2.StreamingPipeRequest.FromString, response_serializer=streaming__pipe__service__pb2.StreamingPipeResponse.SerializeToString), 'CreateChannel': grpc.unary_unary_rpc_method_handler(servicer.CreateChannel, request_deserializer=streaming__pipe__service__pb2.CreateChannelRequest.FromString, response_serializer=streaming__pipe__service__pb2.CreateChannelResponse.SerializeToString), 'ListChannel': grpc.unary_unary_rpc_method_handler(servicer.ListChannel, request_deserializer=streaming__pipe__service__pb2.ListChannelRequest.FromString, response_serializer=streaming__pipe__service__pb2.ListChannelResponse.SerializeToString), 'GetChannel': grpc.unary_unary_rpc_method_handler(servicer.GetChannel, request_deserializer=streaming__pipe__service__pb2.GetChannelRequest.FromString, response_serializer=streaming__pipe__service__pb2.GetChannelResponse.SerializeToString), 'DeleteChannel': grpc.unary_unary_rpc_method_handler(servicer.DeleteChannel, request_deserializer=streaming__pipe__service__pb2.DeleteChannelRequest.FromString, response_serializer=streaming__pipe__service__pb2.DeleteChannelResponse.SerializeToString), 'CommitFile': grpc.unary_unary_rpc_method_handler(servicer.CommitFile, request_deserializer=streaming__pipe__service__pb2.CommitFileRequest.FromString, response_serializer=streaming__pipe__service__pb2.CommitFileResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('cz.proto.common_api.StreamingPipeService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('cz.proto.common_api.StreamingPipeService', rpc_method_handlers)

class StreamingPipeService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def StreamingPipe(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.common_api.StreamingPipeService/StreamingPipe', streaming__pipe__service__pb2.StreamingPipeRequest.SerializeToString, streaming__pipe__service__pb2.StreamingPipeResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def CreateChannel(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.common_api.StreamingPipeService/CreateChannel', streaming__pipe__service__pb2.CreateChannelRequest.SerializeToString, streaming__pipe__service__pb2.CreateChannelResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ListChannel(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.common_api.StreamingPipeService/ListChannel', streaming__pipe__service__pb2.ListChannelRequest.SerializeToString, streaming__pipe__service__pb2.ListChannelResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetChannel(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.common_api.StreamingPipeService/GetChannel', streaming__pipe__service__pb2.GetChannelRequest.SerializeToString, streaming__pipe__service__pb2.GetChannelResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def DeleteChannel(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.common_api.StreamingPipeService/DeleteChannel', streaming__pipe__service__pb2.DeleteChannelRequest.SerializeToString, streaming__pipe__service__pb2.DeleteChannelResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def CommitFile(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.common_api.StreamingPipeService/CommitFile', streaming__pipe__service__pb2.CommitFileRequest.SerializeToString, streaming__pipe__service__pb2.CommitFileResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)