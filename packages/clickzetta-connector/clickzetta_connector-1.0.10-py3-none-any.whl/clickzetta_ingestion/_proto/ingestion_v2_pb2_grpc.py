"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from . import ingestion_v2_pb2 as ingestion__v2__pb2
GRPC_GENERATED_VERSION = '1.68.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False
try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True
if _version_not_supported:
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + f' but the generated code in ingestion_v2_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class IngestionControllerServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CreateOrGetStream = channel.unary_unary('/cz.proto.ingestion.v2.IngestionControllerService/CreateOrGetStream', request_serializer=ingestion__v2__pb2.CreateOrGetStreamRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.CreateOrGetStreamResponse.FromString, _registered_method=True)
        self.CloseStream = channel.unary_unary('/cz.proto.ingestion.v2.IngestionControllerService/CloseStream', request_serializer=ingestion__v2__pb2.CloseStreamRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.CloseStreamResponse.FromString, _registered_method=True)
        self.GetRouteWorkers = channel.unary_unary('/cz.proto.ingestion.v2.IngestionControllerService/GetRouteWorkers', request_serializer=ingestion__v2__pb2.GetRouteWorkersRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.GetRouteWorkersResponse.FromString, _registered_method=True)
        self.Commit = channel.unary_unary('/cz.proto.ingestion.v2.IngestionControllerService/Commit', request_serializer=ingestion__v2__pb2.CommitRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.CommitResponse.FromString, _registered_method=True)
        self.AsyncCommit = channel.unary_unary('/cz.proto.ingestion.v2.IngestionControllerService/AsyncCommit', request_serializer=ingestion__v2__pb2.CommitRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.CommitResponse.FromString, _registered_method=True)
        self.CheckCommitResult = channel.unary_unary('/cz.proto.ingestion.v2.IngestionControllerService/CheckCommitResult', request_serializer=ingestion__v2__pb2.CheckCommitResultRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.CheckCommitResultResponse.FromString, _registered_method=True)
        self.MaintainTablets = channel.unary_unary('/cz.proto.ingestion.v2.IngestionControllerService/MaintainTablets', request_serializer=ingestion__v2__pb2.MaintainTabletRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.MaintainTabletResponse.FromString, _registered_method=True)
        self.CreateBulkLoadStream = channel.unary_unary('/cz.proto.ingestion.v2.IngestionControllerService/CreateBulkLoadStream', request_serializer=ingestion__v2__pb2.CreateBulkLoadStreamRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.CreateBulkLoadStreamResponse.FromString, _registered_method=True)
        self.GetBulkLoadStream = channel.unary_unary('/cz.proto.ingestion.v2.IngestionControllerService/GetBulkLoadStream', request_serializer=ingestion__v2__pb2.GetBulkLoadStreamRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.GetBulkLoadStreamResponse.FromString, _registered_method=True)
        self.CommitBulkLoadStream = channel.unary_unary('/cz.proto.ingestion.v2.IngestionControllerService/CommitBulkLoadStream', request_serializer=ingestion__v2__pb2.CommitBulkLoadStreamRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.CommitBulkLoadStreamResponse.FromString, _registered_method=True)
        self.OpenBulkLoadStreamWriter = channel.unary_unary('/cz.proto.ingestion.v2.IngestionControllerService/OpenBulkLoadStreamWriter', request_serializer=ingestion__v2__pb2.OpenBulkLoadStreamWriterRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.OpenBulkLoadStreamWriterResponse.FromString, _registered_method=True)
        self.FinishBulkLoadStreamWriter = channel.unary_unary('/cz.proto.ingestion.v2.IngestionControllerService/FinishBulkLoadStreamWriter', request_serializer=ingestion__v2__pb2.FinishBulkLoadStreamWriterRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.FinishBulkLoadStreamWriterResponse.FromString, _registered_method=True)
        self.GetBulkLoadStreamStsToken = channel.unary_unary('/cz.proto.ingestion.v2.IngestionControllerService/GetBulkLoadStreamStsToken', request_serializer=ingestion__v2__pb2.GetBulkLoadStreamStsTokenRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.GetBulkLoadStreamStsTokenResponse.FromString, _registered_method=True)
        self.UpdateRouteRuleBroadcast = channel.unary_unary('/cz.proto.ingestion.v2.IngestionControllerService/UpdateRouteRuleBroadcast', request_serializer=ingestion__v2__pb2.UpdateRouteRuleBroadcastRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.UpdateRouteRuleBroadcastResponse.FromString, _registered_method=True)
        self.HandleSchemaChange = channel.unary_unary('/cz.proto.ingestion.v2.IngestionControllerService/HandleSchemaChange', request_serializer=ingestion__v2__pb2.SchemaChangeRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.SchemaChangeResponse.FromString, _registered_method=True)

class IngestionControllerServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def CreateOrGetStream(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CloseStream(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetRouteWorkers(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Commit(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AsyncCommit(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CheckCommitResult(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def MaintainTablets(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CreateBulkLoadStream(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetBulkLoadStream(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CommitBulkLoadStream(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def OpenBulkLoadStreamWriter(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def FinishBulkLoadStreamWriter(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetBulkLoadStreamStsToken(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateRouteRuleBroadcast(self, request, context):
        """internal
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def HandleSchemaChange(self, request, context):
        """schema change
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_IngestionControllerServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {'CreateOrGetStream': grpc.unary_unary_rpc_method_handler(servicer.CreateOrGetStream, request_deserializer=ingestion__v2__pb2.CreateOrGetStreamRequest.FromString, response_serializer=ingestion__v2__pb2.CreateOrGetStreamResponse.SerializeToString), 'CloseStream': grpc.unary_unary_rpc_method_handler(servicer.CloseStream, request_deserializer=ingestion__v2__pb2.CloseStreamRequest.FromString, response_serializer=ingestion__v2__pb2.CloseStreamResponse.SerializeToString), 'GetRouteWorkers': grpc.unary_unary_rpc_method_handler(servicer.GetRouteWorkers, request_deserializer=ingestion__v2__pb2.GetRouteWorkersRequest.FromString, response_serializer=ingestion__v2__pb2.GetRouteWorkersResponse.SerializeToString), 'Commit': grpc.unary_unary_rpc_method_handler(servicer.Commit, request_deserializer=ingestion__v2__pb2.CommitRequest.FromString, response_serializer=ingestion__v2__pb2.CommitResponse.SerializeToString), 'AsyncCommit': grpc.unary_unary_rpc_method_handler(servicer.AsyncCommit, request_deserializer=ingestion__v2__pb2.CommitRequest.FromString, response_serializer=ingestion__v2__pb2.CommitResponse.SerializeToString), 'CheckCommitResult': grpc.unary_unary_rpc_method_handler(servicer.CheckCommitResult, request_deserializer=ingestion__v2__pb2.CheckCommitResultRequest.FromString, response_serializer=ingestion__v2__pb2.CheckCommitResultResponse.SerializeToString), 'MaintainTablets': grpc.unary_unary_rpc_method_handler(servicer.MaintainTablets, request_deserializer=ingestion__v2__pb2.MaintainTabletRequest.FromString, response_serializer=ingestion__v2__pb2.MaintainTabletResponse.SerializeToString), 'CreateBulkLoadStream': grpc.unary_unary_rpc_method_handler(servicer.CreateBulkLoadStream, request_deserializer=ingestion__v2__pb2.CreateBulkLoadStreamRequest.FromString, response_serializer=ingestion__v2__pb2.CreateBulkLoadStreamResponse.SerializeToString), 'GetBulkLoadStream': grpc.unary_unary_rpc_method_handler(servicer.GetBulkLoadStream, request_deserializer=ingestion__v2__pb2.GetBulkLoadStreamRequest.FromString, response_serializer=ingestion__v2__pb2.GetBulkLoadStreamResponse.SerializeToString), 'CommitBulkLoadStream': grpc.unary_unary_rpc_method_handler(servicer.CommitBulkLoadStream, request_deserializer=ingestion__v2__pb2.CommitBulkLoadStreamRequest.FromString, response_serializer=ingestion__v2__pb2.CommitBulkLoadStreamResponse.SerializeToString), 'OpenBulkLoadStreamWriter': grpc.unary_unary_rpc_method_handler(servicer.OpenBulkLoadStreamWriter, request_deserializer=ingestion__v2__pb2.OpenBulkLoadStreamWriterRequest.FromString, response_serializer=ingestion__v2__pb2.OpenBulkLoadStreamWriterResponse.SerializeToString), 'FinishBulkLoadStreamWriter': grpc.unary_unary_rpc_method_handler(servicer.FinishBulkLoadStreamWriter, request_deserializer=ingestion__v2__pb2.FinishBulkLoadStreamWriterRequest.FromString, response_serializer=ingestion__v2__pb2.FinishBulkLoadStreamWriterResponse.SerializeToString), 'GetBulkLoadStreamStsToken': grpc.unary_unary_rpc_method_handler(servicer.GetBulkLoadStreamStsToken, request_deserializer=ingestion__v2__pb2.GetBulkLoadStreamStsTokenRequest.FromString, response_serializer=ingestion__v2__pb2.GetBulkLoadStreamStsTokenResponse.SerializeToString), 'UpdateRouteRuleBroadcast': grpc.unary_unary_rpc_method_handler(servicer.UpdateRouteRuleBroadcast, request_deserializer=ingestion__v2__pb2.UpdateRouteRuleBroadcastRequest.FromString, response_serializer=ingestion__v2__pb2.UpdateRouteRuleBroadcastResponse.SerializeToString), 'HandleSchemaChange': grpc.unary_unary_rpc_method_handler(servicer.HandleSchemaChange, request_deserializer=ingestion__v2__pb2.SchemaChangeRequest.FromString, response_serializer=ingestion__v2__pb2.SchemaChangeResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('cz.proto.ingestion.v2.IngestionControllerService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('cz.proto.ingestion.v2.IngestionControllerService', rpc_method_handlers)

class IngestionControllerService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def CreateOrGetStream(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IngestionControllerService/CreateOrGetStream', ingestion__v2__pb2.CreateOrGetStreamRequest.SerializeToString, ingestion__v2__pb2.CreateOrGetStreamResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def CloseStream(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IngestionControllerService/CloseStream', ingestion__v2__pb2.CloseStreamRequest.SerializeToString, ingestion__v2__pb2.CloseStreamResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetRouteWorkers(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IngestionControllerService/GetRouteWorkers', ingestion__v2__pb2.GetRouteWorkersRequest.SerializeToString, ingestion__v2__pb2.GetRouteWorkersResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Commit(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IngestionControllerService/Commit', ingestion__v2__pb2.CommitRequest.SerializeToString, ingestion__v2__pb2.CommitResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def AsyncCommit(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IngestionControllerService/AsyncCommit', ingestion__v2__pb2.CommitRequest.SerializeToString, ingestion__v2__pb2.CommitResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def CheckCommitResult(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IngestionControllerService/CheckCommitResult', ingestion__v2__pb2.CheckCommitResultRequest.SerializeToString, ingestion__v2__pb2.CheckCommitResultResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def MaintainTablets(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IngestionControllerService/MaintainTablets', ingestion__v2__pb2.MaintainTabletRequest.SerializeToString, ingestion__v2__pb2.MaintainTabletResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def CreateBulkLoadStream(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IngestionControllerService/CreateBulkLoadStream', ingestion__v2__pb2.CreateBulkLoadStreamRequest.SerializeToString, ingestion__v2__pb2.CreateBulkLoadStreamResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetBulkLoadStream(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IngestionControllerService/GetBulkLoadStream', ingestion__v2__pb2.GetBulkLoadStreamRequest.SerializeToString, ingestion__v2__pb2.GetBulkLoadStreamResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def CommitBulkLoadStream(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IngestionControllerService/CommitBulkLoadStream', ingestion__v2__pb2.CommitBulkLoadStreamRequest.SerializeToString, ingestion__v2__pb2.CommitBulkLoadStreamResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def OpenBulkLoadStreamWriter(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IngestionControllerService/OpenBulkLoadStreamWriter', ingestion__v2__pb2.OpenBulkLoadStreamWriterRequest.SerializeToString, ingestion__v2__pb2.OpenBulkLoadStreamWriterResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def FinishBulkLoadStreamWriter(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IngestionControllerService/FinishBulkLoadStreamWriter', ingestion__v2__pb2.FinishBulkLoadStreamWriterRequest.SerializeToString, ingestion__v2__pb2.FinishBulkLoadStreamWriterResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetBulkLoadStreamStsToken(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IngestionControllerService/GetBulkLoadStreamStsToken', ingestion__v2__pb2.GetBulkLoadStreamStsTokenRequest.SerializeToString, ingestion__v2__pb2.GetBulkLoadStreamStsTokenResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def UpdateRouteRuleBroadcast(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IngestionControllerService/UpdateRouteRuleBroadcast', ingestion__v2__pb2.UpdateRouteRuleBroadcastRequest.SerializeToString, ingestion__v2__pb2.UpdateRouteRuleBroadcastResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def HandleSchemaChange(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IngestionControllerService/HandleSchemaChange', ingestion__v2__pb2.SchemaChangeRequest.SerializeToString, ingestion__v2__pb2.SchemaChangeResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

class IngestionWorkerServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Mutate = channel.stream_stream('/cz.proto.ingestion.v2.IngestionWorkerService/Mutate', request_serializer=ingestion__v2__pb2.MutateRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.MutateResponse.FromString, _registered_method=True)
        self.MultiMutate = channel.stream_stream('/cz.proto.ingestion.v2.IngestionWorkerService/MultiMutate', request_serializer=ingestion__v2__pb2.MultiMutateRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.MultiMutateResponse.FromString, _registered_method=True)

class IngestionWorkerServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Mutate(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def MultiMutate(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_IngestionWorkerServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {'Mutate': grpc.stream_stream_rpc_method_handler(servicer.Mutate, request_deserializer=ingestion__v2__pb2.MutateRequest.FromString, response_serializer=ingestion__v2__pb2.MutateResponse.SerializeToString), 'MultiMutate': grpc.stream_stream_rpc_method_handler(servicer.MultiMutate, request_deserializer=ingestion__v2__pb2.MultiMutateRequest.FromString, response_serializer=ingestion__v2__pb2.MultiMutateResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('cz.proto.ingestion.v2.IngestionWorkerService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('cz.proto.ingestion.v2.IngestionWorkerService', rpc_method_handlers)

class IngestionWorkerService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Mutate(request_iterator, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.stream_stream(request_iterator, target, '/cz.proto.ingestion.v2.IngestionWorkerService/Mutate', ingestion__v2__pb2.MutateRequest.SerializeToString, ingestion__v2__pb2.MutateResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def MultiMutate(request_iterator, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.stream_stream(request_iterator, target, '/cz.proto.ingestion.v2.IngestionWorkerService/MultiMutate', ingestion__v2__pb2.MultiMutateRequest.SerializeToString, ingestion__v2__pb2.MultiMutateResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

class IGSRouterServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetControllerAddress = channel.unary_unary('/cz.proto.ingestion.v2.IGSRouterService/GetControllerAddress', request_serializer=ingestion__v2__pb2.GetControllerAddressRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.GetControllerAddressResponse.FromString, _registered_method=True)
        self.UpdateRouteRule = channel.unary_unary('/cz.proto.ingestion.v2.IGSRouterService/UpdateRouteRule', request_serializer=ingestion__v2__pb2.UpdateRouteRuleRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.UpdateRouteRuleResponse.FromString, _registered_method=True)
        self.RemoveRouteRule = channel.unary_unary('/cz.proto.ingestion.v2.IGSRouterService/RemoveRouteRule', request_serializer=ingestion__v2__pb2.RemoveRouteRuleRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.RemoveRouteRuleResponse.FromString, _registered_method=True)
        self.ClearRouteRule = channel.unary_unary('/cz.proto.ingestion.v2.IGSRouterService/ClearRouteRule', request_serializer=ingestion__v2__pb2.ClearRouteRuleRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.ClearRouteRuleResponse.FromString, _registered_method=True)
        self.ChangeDefaultService = channel.unary_unary('/cz.proto.ingestion.v2.IGSRouterService/ChangeDefaultService', request_serializer=ingestion__v2__pb2.ChangeDefaultServiceRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.ChangeDefaultServiceResponse.FromString, _registered_method=True)
        self.RegisterNewService = channel.unary_unary('/cz.proto.ingestion.v2.IGSRouterService/RegisterNewService', request_serializer=ingestion__v2__pb2.RegisterNewServiceRequest.SerializeToString, response_deserializer=ingestion__v2__pb2.RegisterNewServiceResponse.FromString, _registered_method=True)

class IGSRouterServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetControllerAddress(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateRouteRule(self, request, context):
        """route maintains api
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RemoveRouteRule(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ClearRouteRule(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ChangeDefaultService(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RegisterNewService(self, request, context):
        """controller will call this api to register to router
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_IGSRouterServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {'GetControllerAddress': grpc.unary_unary_rpc_method_handler(servicer.GetControllerAddress, request_deserializer=ingestion__v2__pb2.GetControllerAddressRequest.FromString, response_serializer=ingestion__v2__pb2.GetControllerAddressResponse.SerializeToString), 'UpdateRouteRule': grpc.unary_unary_rpc_method_handler(servicer.UpdateRouteRule, request_deserializer=ingestion__v2__pb2.UpdateRouteRuleRequest.FromString, response_serializer=ingestion__v2__pb2.UpdateRouteRuleResponse.SerializeToString), 'RemoveRouteRule': grpc.unary_unary_rpc_method_handler(servicer.RemoveRouteRule, request_deserializer=ingestion__v2__pb2.RemoveRouteRuleRequest.FromString, response_serializer=ingestion__v2__pb2.RemoveRouteRuleResponse.SerializeToString), 'ClearRouteRule': grpc.unary_unary_rpc_method_handler(servicer.ClearRouteRule, request_deserializer=ingestion__v2__pb2.ClearRouteRuleRequest.FromString, response_serializer=ingestion__v2__pb2.ClearRouteRuleResponse.SerializeToString), 'ChangeDefaultService': grpc.unary_unary_rpc_method_handler(servicer.ChangeDefaultService, request_deserializer=ingestion__v2__pb2.ChangeDefaultServiceRequest.FromString, response_serializer=ingestion__v2__pb2.ChangeDefaultServiceResponse.SerializeToString), 'RegisterNewService': grpc.unary_unary_rpc_method_handler(servicer.RegisterNewService, request_deserializer=ingestion__v2__pb2.RegisterNewServiceRequest.FromString, response_serializer=ingestion__v2__pb2.RegisterNewServiceResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('cz.proto.ingestion.v2.IGSRouterService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('cz.proto.ingestion.v2.IGSRouterService', rpc_method_handlers)

class IGSRouterService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetControllerAddress(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IGSRouterService/GetControllerAddress', ingestion__v2__pb2.GetControllerAddressRequest.SerializeToString, ingestion__v2__pb2.GetControllerAddressResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def UpdateRouteRule(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IGSRouterService/UpdateRouteRule', ingestion__v2__pb2.UpdateRouteRuleRequest.SerializeToString, ingestion__v2__pb2.UpdateRouteRuleResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RemoveRouteRule(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IGSRouterService/RemoveRouteRule', ingestion__v2__pb2.RemoveRouteRuleRequest.SerializeToString, ingestion__v2__pb2.RemoveRouteRuleResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ClearRouteRule(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IGSRouterService/ClearRouteRule', ingestion__v2__pb2.ClearRouteRuleRequest.SerializeToString, ingestion__v2__pb2.ClearRouteRuleResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ChangeDefaultService(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IGSRouterService/ChangeDefaultService', ingestion__v2__pb2.ChangeDefaultServiceRequest.SerializeToString, ingestion__v2__pb2.ChangeDefaultServiceResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RegisterNewService(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.ingestion.v2.IGSRouterService/RegisterNewService', ingestion__v2__pb2.RegisterNewServiceRequest.SerializeToString, ingestion__v2__pb2.RegisterNewServiceResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)