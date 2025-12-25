"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from . import coordinator_service_pb2 as coordinator__service__pb2
from . import service_common_pb2 as service__common__pb2
GRPC_GENERATED_VERSION = '1.68.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False
try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True
if _version_not_supported:
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + f' but the generated code in coordinator_service_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class CoordinatorServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.SubmitJob = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/SubmitJob', request_serializer=coordinator__service__pb2.SubmitJobRequest.SerializeToString, response_deserializer=coordinator__service__pb2.SubmitJobResponse.FromString, _registered_method=True)
        self.ListJobs = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/ListJobs', request_serializer=coordinator__service__pb2.ListJobsRequest.SerializeToString, response_deserializer=coordinator__service__pb2.ListJobsResponse.FromString, _registered_method=True)
        self.CancelJob = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/CancelJob', request_serializer=coordinator__service__pb2.CancelJobRequest.SerializeToString, response_deserializer=coordinator__service__pb2.CancelJobResponse.FromString, _registered_method=True)
        self.GetJob = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/GetJob', request_serializer=coordinator__service__pb2.GetJobRequest.SerializeToString, response_deserializer=coordinator__service__pb2.GetJobResponse.FromString, _registered_method=True)
        self.GetJobStatus = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/GetJobStatus', request_serializer=coordinator__service__pb2.GetJobStatusRequest.SerializeToString, response_deserializer=coordinator__service__pb2.GetJobStatusResponse.FromString, _registered_method=True)
        self.GetJobResult = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/GetJobResult', request_serializer=coordinator__service__pb2.GetJobResultRequest.SerializeToString, response_deserializer=coordinator__service__pb2.GetJobResultResponse.FromString, _registered_method=True)
        self.GetJobSummary = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/GetJobSummary', request_serializer=coordinator__service__pb2.GetJobSummaryRequest.SerializeToString, response_deserializer=coordinator__service__pb2.GetJobSummaryResponse.FromString, _registered_method=True)
        self.GetJobProfile = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/GetJobProfile', request_serializer=coordinator__service__pb2.GetJobProfileRequest.SerializeToString, response_deserializer=coordinator__service__pb2.GetJobProfileResponse.FromString, _registered_method=True)
        self.GetJobProgress = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/GetJobProgress', request_serializer=coordinator__service__pb2.GetJobProgressRequest.SerializeToString, response_deserializer=coordinator__service__pb2.GetJobProgressResponse.FromString, _registered_method=True)
        self.GetJobPlan = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/GetJobPlan', request_serializer=coordinator__service__pb2.GetJobPlanRequest.SerializeToString, response_deserializer=coordinator__service__pb2.GetJobPlanResponse.FromString, _registered_method=True)
        self.InitializeInstance = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/InitializeInstance', request_serializer=coordinator__service__pb2.InitializeInstanceRequest.SerializeToString, response_deserializer=coordinator__service__pb2.InitializeInstanceResponse.FromString, _registered_method=True)
        self.SuspendInstance = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/SuspendInstance', request_serializer=coordinator__service__pb2.SuspendInstanceRequest.SerializeToString, response_deserializer=coordinator__service__pb2.SuspendInstanceResponse.FromString, _registered_method=True)
        self.ResumeInstance = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/ResumeInstance', request_serializer=coordinator__service__pb2.ResumeInstanceRequest.SerializeToString, response_deserializer=coordinator__service__pb2.ResumeInstanceResponse.FromString, _registered_method=True)
        self.CreateWorkspace = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/CreateWorkspace', request_serializer=coordinator__service__pb2.CreateWorkspaceRequest.SerializeToString, response_deserializer=coordinator__service__pb2.CreateWorkspaceResponse.FromString, _registered_method=True)
        self.UpdateWorkspace = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/UpdateWorkspace', request_serializer=coordinator__service__pb2.UpdateWorkspaceRequest.SerializeToString, response_deserializer=coordinator__service__pb2.UpdateWorkspaceResponse.FromString, _registered_method=True)
        self.DeleteWorkspace = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/DeleteWorkspace', request_serializer=coordinator__service__pb2.DeleteWorkspaceRequest.SerializeToString, response_deserializer=coordinator__service__pb2.DeleteWorkspaceResponse.FromString, _registered_method=True)
        self.GetWorkspace = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/GetWorkspace', request_serializer=coordinator__service__pb2.GetWorkspaceRequest.SerializeToString, response_deserializer=coordinator__service__pb2.GetWorkspaceResponse.FromString, _registered_method=True)
        self.ListWorkspaces = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/ListWorkspaces', request_serializer=coordinator__service__pb2.ListWorkspacesRequest.SerializeToString, response_deserializer=coordinator__service__pb2.ListWorkspacesResponse.FromString, _registered_method=True)
        self.GetUser = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/GetUser', request_serializer=coordinator__service__pb2.GetUserRequest.SerializeToString, response_deserializer=coordinator__service__pb2.GetUserResponse.FromString, _registered_method=True)
        self.OpenTable = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/OpenTable', request_serializer=coordinator__service__pb2.OpenTableRequest.SerializeToString, response_deserializer=coordinator__service__pb2.OpenTableResponse.FromString, _registered_method=True)
        self.NetworkPolicyAccess = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/NetworkPolicyAccess', request_serializer=coordinator__service__pb2.NetworkPolicyRequest.SerializeToString, response_deserializer=coordinator__service__pb2.NetworkPolicyResponse.FromString, _registered_method=True)
        self.RefreshMetaCache = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/RefreshMetaCache', request_serializer=coordinator__service__pb2.RefreshMetaCacheRequest.SerializeToString, response_deserializer=coordinator__service__pb2.RefreshMetaCacheResponse.FromString, _registered_method=True)
        self.RescheduleJobs = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/RescheduleJobs', request_serializer=coordinator__service__pb2.RescheduleJobsRequest.SerializeToString, response_deserializer=coordinator__service__pb2.RescheduleJobsResponse.FromString, _registered_method=True)
        self.SetAccountConfig = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/SetAccountConfig', request_serializer=coordinator__service__pb2.SetAccountConfigRequest.SerializeToString, response_deserializer=coordinator__service__pb2.SetAccountConfigResponse.FromString, _registered_method=True)
        self.GetAccountConfig = channel.unary_unary('/cz.proto.coordinator.CoordinatorService/GetAccountConfig', request_serializer=coordinator__service__pb2.GetAccountConfigRequest.SerializeToString, response_deserializer=coordinator__service__pb2.GetAccountConfigResponse.FromString, _registered_method=True)

class CoordinatorServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def SubmitJob(self, request, context):
        """*
        Submit a batch of sql jobs
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ListJobs(self, request, context):
        """*
        List current jobs
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CancelJob(self, request, context):
        """*
        Cancel job
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetJob(self, request, context):
        """*
        Get job description
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetJobStatus(self, request, context):
        """*
        Get job status
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetJobResult(self, request, context):
        """*
        Get job result set
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetJobSummary(self, request, context):
        """*
        Get job summary
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetJobProfile(self, request, context):
        """*
        Get job profile
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetJobProgress(self, request, context):
        """*
        Get job progress
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetJobPlan(self, request, context):
        """*
        Get job plan(dag)
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def InitializeInstance(self, request, context):
        """*
        Initialize instance
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SuspendInstance(self, request, context):
        """*
        Suspend instance
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ResumeInstance(self, request, context):
        """*
        Resume instance

        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CreateWorkspace(self, request, context):
        """*
        Create workspace
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateWorkspace(self, request, context):
        """*
        Update workspace
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteWorkspace(self, request, context):
        """*
        Delete workspace
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetWorkspace(self, request, context):
        """*
        Get workspace
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ListWorkspaces(self, request, context):
        """*
        List workspaces
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetUser(self, request, context):
        """*
        Get user
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def OpenTable(self, request, context):
        """*
        open table
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def NetworkPolicyAccess(self, request, context):
        """*
        Check IP access
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RefreshMetaCache(self, request, context):
        """*
        Flush meta cache
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RescheduleJobs(self, request, context):
        """*
        Reschedule jobs in vc
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetAccountConfig(self, request, context):
        """*
        Set account config
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetAccountConfig(self, request, context):
        """*
        Get account config
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_CoordinatorServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {'SubmitJob': grpc.unary_unary_rpc_method_handler(servicer.SubmitJob, request_deserializer=coordinator__service__pb2.SubmitJobRequest.FromString, response_serializer=coordinator__service__pb2.SubmitJobResponse.SerializeToString), 'ListJobs': grpc.unary_unary_rpc_method_handler(servicer.ListJobs, request_deserializer=coordinator__service__pb2.ListJobsRequest.FromString, response_serializer=coordinator__service__pb2.ListJobsResponse.SerializeToString), 'CancelJob': grpc.unary_unary_rpc_method_handler(servicer.CancelJob, request_deserializer=coordinator__service__pb2.CancelJobRequest.FromString, response_serializer=coordinator__service__pb2.CancelJobResponse.SerializeToString), 'GetJob': grpc.unary_unary_rpc_method_handler(servicer.GetJob, request_deserializer=coordinator__service__pb2.GetJobRequest.FromString, response_serializer=coordinator__service__pb2.GetJobResponse.SerializeToString), 'GetJobStatus': grpc.unary_unary_rpc_method_handler(servicer.GetJobStatus, request_deserializer=coordinator__service__pb2.GetJobStatusRequest.FromString, response_serializer=coordinator__service__pb2.GetJobStatusResponse.SerializeToString), 'GetJobResult': grpc.unary_unary_rpc_method_handler(servicer.GetJobResult, request_deserializer=coordinator__service__pb2.GetJobResultRequest.FromString, response_serializer=coordinator__service__pb2.GetJobResultResponse.SerializeToString), 'GetJobSummary': grpc.unary_unary_rpc_method_handler(servicer.GetJobSummary, request_deserializer=coordinator__service__pb2.GetJobSummaryRequest.FromString, response_serializer=coordinator__service__pb2.GetJobSummaryResponse.SerializeToString), 'GetJobProfile': grpc.unary_unary_rpc_method_handler(servicer.GetJobProfile, request_deserializer=coordinator__service__pb2.GetJobProfileRequest.FromString, response_serializer=coordinator__service__pb2.GetJobProfileResponse.SerializeToString), 'GetJobProgress': grpc.unary_unary_rpc_method_handler(servicer.GetJobProgress, request_deserializer=coordinator__service__pb2.GetJobProgressRequest.FromString, response_serializer=coordinator__service__pb2.GetJobProgressResponse.SerializeToString), 'GetJobPlan': grpc.unary_unary_rpc_method_handler(servicer.GetJobPlan, request_deserializer=coordinator__service__pb2.GetJobPlanRequest.FromString, response_serializer=coordinator__service__pb2.GetJobPlanResponse.SerializeToString), 'InitializeInstance': grpc.unary_unary_rpc_method_handler(servicer.InitializeInstance, request_deserializer=coordinator__service__pb2.InitializeInstanceRequest.FromString, response_serializer=coordinator__service__pb2.InitializeInstanceResponse.SerializeToString), 'SuspendInstance': grpc.unary_unary_rpc_method_handler(servicer.SuspendInstance, request_deserializer=coordinator__service__pb2.SuspendInstanceRequest.FromString, response_serializer=coordinator__service__pb2.SuspendInstanceResponse.SerializeToString), 'ResumeInstance': grpc.unary_unary_rpc_method_handler(servicer.ResumeInstance, request_deserializer=coordinator__service__pb2.ResumeInstanceRequest.FromString, response_serializer=coordinator__service__pb2.ResumeInstanceResponse.SerializeToString), 'CreateWorkspace': grpc.unary_unary_rpc_method_handler(servicer.CreateWorkspace, request_deserializer=coordinator__service__pb2.CreateWorkspaceRequest.FromString, response_serializer=coordinator__service__pb2.CreateWorkspaceResponse.SerializeToString), 'UpdateWorkspace': grpc.unary_unary_rpc_method_handler(servicer.UpdateWorkspace, request_deserializer=coordinator__service__pb2.UpdateWorkspaceRequest.FromString, response_serializer=coordinator__service__pb2.UpdateWorkspaceResponse.SerializeToString), 'DeleteWorkspace': grpc.unary_unary_rpc_method_handler(servicer.DeleteWorkspace, request_deserializer=coordinator__service__pb2.DeleteWorkspaceRequest.FromString, response_serializer=coordinator__service__pb2.DeleteWorkspaceResponse.SerializeToString), 'GetWorkspace': grpc.unary_unary_rpc_method_handler(servicer.GetWorkspace, request_deserializer=coordinator__service__pb2.GetWorkspaceRequest.FromString, response_serializer=coordinator__service__pb2.GetWorkspaceResponse.SerializeToString), 'ListWorkspaces': grpc.unary_unary_rpc_method_handler(servicer.ListWorkspaces, request_deserializer=coordinator__service__pb2.ListWorkspacesRequest.FromString, response_serializer=coordinator__service__pb2.ListWorkspacesResponse.SerializeToString), 'GetUser': grpc.unary_unary_rpc_method_handler(servicer.GetUser, request_deserializer=coordinator__service__pb2.GetUserRequest.FromString, response_serializer=coordinator__service__pb2.GetUserResponse.SerializeToString), 'OpenTable': grpc.unary_unary_rpc_method_handler(servicer.OpenTable, request_deserializer=coordinator__service__pb2.OpenTableRequest.FromString, response_serializer=coordinator__service__pb2.OpenTableResponse.SerializeToString), 'NetworkPolicyAccess': grpc.unary_unary_rpc_method_handler(servicer.NetworkPolicyAccess, request_deserializer=coordinator__service__pb2.NetworkPolicyRequest.FromString, response_serializer=coordinator__service__pb2.NetworkPolicyResponse.SerializeToString), 'RefreshMetaCache': grpc.unary_unary_rpc_method_handler(servicer.RefreshMetaCache, request_deserializer=coordinator__service__pb2.RefreshMetaCacheRequest.FromString, response_serializer=coordinator__service__pb2.RefreshMetaCacheResponse.SerializeToString), 'RescheduleJobs': grpc.unary_unary_rpc_method_handler(servicer.RescheduleJobs, request_deserializer=coordinator__service__pb2.RescheduleJobsRequest.FromString, response_serializer=coordinator__service__pb2.RescheduleJobsResponse.SerializeToString), 'SetAccountConfig': grpc.unary_unary_rpc_method_handler(servicer.SetAccountConfig, request_deserializer=coordinator__service__pb2.SetAccountConfigRequest.FromString, response_serializer=coordinator__service__pb2.SetAccountConfigResponse.SerializeToString), 'GetAccountConfig': grpc.unary_unary_rpc_method_handler(servicer.GetAccountConfig, request_deserializer=coordinator__service__pb2.GetAccountConfigRequest.FromString, response_serializer=coordinator__service__pb2.GetAccountConfigResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('cz.proto.coordinator.CoordinatorService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('cz.proto.coordinator.CoordinatorService', rpc_method_handlers)

class CoordinatorService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def SubmitJob(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/SubmitJob', coordinator__service__pb2.SubmitJobRequest.SerializeToString, coordinator__service__pb2.SubmitJobResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ListJobs(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/ListJobs', coordinator__service__pb2.ListJobsRequest.SerializeToString, coordinator__service__pb2.ListJobsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def CancelJob(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/CancelJob', coordinator__service__pb2.CancelJobRequest.SerializeToString, coordinator__service__pb2.CancelJobResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetJob(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/GetJob', coordinator__service__pb2.GetJobRequest.SerializeToString, coordinator__service__pb2.GetJobResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetJobStatus(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/GetJobStatus', coordinator__service__pb2.GetJobStatusRequest.SerializeToString, coordinator__service__pb2.GetJobStatusResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetJobResult(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/GetJobResult', coordinator__service__pb2.GetJobResultRequest.SerializeToString, coordinator__service__pb2.GetJobResultResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetJobSummary(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/GetJobSummary', coordinator__service__pb2.GetJobSummaryRequest.SerializeToString, coordinator__service__pb2.GetJobSummaryResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetJobProfile(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/GetJobProfile', coordinator__service__pb2.GetJobProfileRequest.SerializeToString, coordinator__service__pb2.GetJobProfileResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetJobProgress(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/GetJobProgress', coordinator__service__pb2.GetJobProgressRequest.SerializeToString, coordinator__service__pb2.GetJobProgressResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetJobPlan(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/GetJobPlan', coordinator__service__pb2.GetJobPlanRequest.SerializeToString, coordinator__service__pb2.GetJobPlanResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def InitializeInstance(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/InitializeInstance', coordinator__service__pb2.InitializeInstanceRequest.SerializeToString, coordinator__service__pb2.InitializeInstanceResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def SuspendInstance(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/SuspendInstance', coordinator__service__pb2.SuspendInstanceRequest.SerializeToString, coordinator__service__pb2.SuspendInstanceResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ResumeInstance(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/ResumeInstance', coordinator__service__pb2.ResumeInstanceRequest.SerializeToString, coordinator__service__pb2.ResumeInstanceResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def CreateWorkspace(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/CreateWorkspace', coordinator__service__pb2.CreateWorkspaceRequest.SerializeToString, coordinator__service__pb2.CreateWorkspaceResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def UpdateWorkspace(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/UpdateWorkspace', coordinator__service__pb2.UpdateWorkspaceRequest.SerializeToString, coordinator__service__pb2.UpdateWorkspaceResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def DeleteWorkspace(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/DeleteWorkspace', coordinator__service__pb2.DeleteWorkspaceRequest.SerializeToString, coordinator__service__pb2.DeleteWorkspaceResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetWorkspace(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/GetWorkspace', coordinator__service__pb2.GetWorkspaceRequest.SerializeToString, coordinator__service__pb2.GetWorkspaceResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ListWorkspaces(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/ListWorkspaces', coordinator__service__pb2.ListWorkspacesRequest.SerializeToString, coordinator__service__pb2.ListWorkspacesResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetUser(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/GetUser', coordinator__service__pb2.GetUserRequest.SerializeToString, coordinator__service__pb2.GetUserResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def OpenTable(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/OpenTable', coordinator__service__pb2.OpenTableRequest.SerializeToString, coordinator__service__pb2.OpenTableResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def NetworkPolicyAccess(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/NetworkPolicyAccess', coordinator__service__pb2.NetworkPolicyRequest.SerializeToString, coordinator__service__pb2.NetworkPolicyResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RefreshMetaCache(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/RefreshMetaCache', coordinator__service__pb2.RefreshMetaCacheRequest.SerializeToString, coordinator__service__pb2.RefreshMetaCacheResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RescheduleJobs(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/RescheduleJobs', coordinator__service__pb2.RescheduleJobsRequest.SerializeToString, coordinator__service__pb2.RescheduleJobsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def SetAccountConfig(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/SetAccountConfig', coordinator__service__pb2.SetAccountConfigRequest.SerializeToString, coordinator__service__pb2.SetAccountConfigResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetAccountConfig(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorService/GetAccountConfig', coordinator__service__pb2.GetAccountConfigRequest.SerializeToString, coordinator__service__pb2.GetAccountConfigResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

class CoordinatorMasterStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetJobAddress = channel.unary_unary('/cz.proto.coordinator.CoordinatorMaster/GetJobAddress', request_serializer=coordinator__service__pb2.GetJobAddressRequest.SerializeToString, response_deserializer=coordinator__service__pb2.GetJobAddressResponse.FromString, _registered_method=True)
        self.ReportHeartbeat = channel.unary_unary('/cz.proto.coordinator.CoordinatorMaster/ReportHeartbeat', request_serializer=coordinator__service__pb2.HeartBeat.SerializeToString, response_deserializer=coordinator__service__pb2.HeartBeatResponse.FromString, _registered_method=True)
        self.ListWorker = channel.unary_unary('/cz.proto.coordinator.CoordinatorMaster/ListWorker', request_serializer=coordinator__service__pb2.ListWorkerRequest.SerializeToString, response_deserializer=coordinator__service__pb2.ListWorkerResponse.FromString, _registered_method=True)
        self.ListJobs = channel.unary_unary('/cz.proto.coordinator.CoordinatorMaster/ListJobs', request_serializer=coordinator__service__pb2.ListMasterJobsRequest.SerializeToString, response_deserializer=coordinator__service__pb2.ListJobsResponse.FromString, _registered_method=True)
        self.DeleteJob = channel.unary_unary('/cz.proto.coordinator.CoordinatorMaster/DeleteJob', request_serializer=coordinator__service__pb2.JobID.SerializeToString, response_deserializer=service__common__pb2.ResponseStatus.FromString, _registered_method=True)
        self.HotUpgrade = channel.unary_unary('/cz.proto.coordinator.CoordinatorMaster/HotUpgrade', request_serializer=coordinator__service__pb2.HotUpgradeRequest.SerializeToString, response_deserializer=coordinator__service__pb2.HotUpgradeResponse.FromString, _registered_method=True)
        self.GetHotUpgradeState = channel.unary_unary('/cz.proto.coordinator.CoordinatorMaster/GetHotUpgradeState', request_serializer=coordinator__service__pb2.GetHotUpgradeStateRequest.SerializeToString, response_deserializer=coordinator__service__pb2.GetHotUpgradeStateResponse.FromString, _registered_method=True)
        self.SetServiceRoute = channel.unary_unary('/cz.proto.coordinator.CoordinatorMaster/SetServiceRoute', request_serializer=coordinator__service__pb2.SetServiceRouteRequest.SerializeToString, response_deserializer=coordinator__service__pb2.SetServiceRouteResponse.FromString, _registered_method=True)
        self.GetServiceRoute = channel.unary_unary('/cz.proto.coordinator.CoordinatorMaster/GetServiceRoute', request_serializer=coordinator__service__pb2.GetServiceRouteRequest.SerializeToString, response_deserializer=coordinator__service__pb2.GetServiceRouteResponse.FromString, _registered_method=True)
        self.RescheduleVcJobs = channel.unary_unary('/cz.proto.coordinator.CoordinatorMaster/RescheduleVcJobs', request_serializer=coordinator__service__pb2.RescheduleVcJobsRequest.SerializeToString, response_deserializer=coordinator__service__pb2.RescheduleVcJobsResponse.FromString, _registered_method=True)
        self.SetLabelConfig = channel.unary_unary('/cz.proto.coordinator.CoordinatorMaster/SetLabelConfig', request_serializer=coordinator__service__pb2.SetLabelConfigRequest.SerializeToString, response_deserializer=coordinator__service__pb2.SetLabelConfigResponse.FromString, _registered_method=True)
        self.ApplyAllLabel = channel.unary_unary('/cz.proto.coordinator.CoordinatorMaster/ApplyAllLabel', request_serializer=coordinator__service__pb2.ApplyAllLabelRequest.SerializeToString, response_deserializer=coordinator__service__pb2.ApplyAllLabelResponse.FromString, _registered_method=True)
        self.GetLabelStatus = channel.unary_unary('/cz.proto.coordinator.CoordinatorMaster/GetLabelStatus', request_serializer=coordinator__service__pb2.GetLabelStatusRequest.SerializeToString, response_deserializer=coordinator__service__pb2.GetLabelStatusResponse.FromString, _registered_method=True)

class CoordinatorMasterServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetJobAddress(self, request, context):
        """*
        Get job coordinator address cache from master(may not equal with meta)
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ReportHeartbeat(self, request, context):
        """*
        Coordinator HB
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ListWorker(self, request, context):
        """*
        List active coordinator
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ListJobs(self, request, context):
        """*
        Internal interface: List current jobs, ignore most parameters
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteJob(self, request, context):
        """*
        Internal interface: force delete job when all coordinator crash
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def HotUpgrade(self, request, context):
        """*
        Start upgrade
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetHotUpgradeState(self, request, context):
        """*
        Get upgrade state
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetServiceRoute(self, request, context):
        """*
        Set service route
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetServiceRoute(self, request, context):
        """*
        Get service route
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RescheduleVcJobs(self, request, context):
        """*
        Reschedule queueing job to new version
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetLabelConfig(self, request, context):
        """*
        Set label config
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ApplyAllLabel(self, request, context):
        """*
        Apply all label config for version
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetLabelStatus(self, request, context):
        """*
        Get label status
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_CoordinatorMasterServicer_to_server(servicer, server):
    rpc_method_handlers = {'GetJobAddress': grpc.unary_unary_rpc_method_handler(servicer.GetJobAddress, request_deserializer=coordinator__service__pb2.GetJobAddressRequest.FromString, response_serializer=coordinator__service__pb2.GetJobAddressResponse.SerializeToString), 'ReportHeartbeat': grpc.unary_unary_rpc_method_handler(servicer.ReportHeartbeat, request_deserializer=coordinator__service__pb2.HeartBeat.FromString, response_serializer=coordinator__service__pb2.HeartBeatResponse.SerializeToString), 'ListWorker': grpc.unary_unary_rpc_method_handler(servicer.ListWorker, request_deserializer=coordinator__service__pb2.ListWorkerRequest.FromString, response_serializer=coordinator__service__pb2.ListWorkerResponse.SerializeToString), 'ListJobs': grpc.unary_unary_rpc_method_handler(servicer.ListJobs, request_deserializer=coordinator__service__pb2.ListMasterJobsRequest.FromString, response_serializer=coordinator__service__pb2.ListJobsResponse.SerializeToString), 'DeleteJob': grpc.unary_unary_rpc_method_handler(servicer.DeleteJob, request_deserializer=coordinator__service__pb2.JobID.FromString, response_serializer=service__common__pb2.ResponseStatus.SerializeToString), 'HotUpgrade': grpc.unary_unary_rpc_method_handler(servicer.HotUpgrade, request_deserializer=coordinator__service__pb2.HotUpgradeRequest.FromString, response_serializer=coordinator__service__pb2.HotUpgradeResponse.SerializeToString), 'GetHotUpgradeState': grpc.unary_unary_rpc_method_handler(servicer.GetHotUpgradeState, request_deserializer=coordinator__service__pb2.GetHotUpgradeStateRequest.FromString, response_serializer=coordinator__service__pb2.GetHotUpgradeStateResponse.SerializeToString), 'SetServiceRoute': grpc.unary_unary_rpc_method_handler(servicer.SetServiceRoute, request_deserializer=coordinator__service__pb2.SetServiceRouteRequest.FromString, response_serializer=coordinator__service__pb2.SetServiceRouteResponse.SerializeToString), 'GetServiceRoute': grpc.unary_unary_rpc_method_handler(servicer.GetServiceRoute, request_deserializer=coordinator__service__pb2.GetServiceRouteRequest.FromString, response_serializer=coordinator__service__pb2.GetServiceRouteResponse.SerializeToString), 'RescheduleVcJobs': grpc.unary_unary_rpc_method_handler(servicer.RescheduleVcJobs, request_deserializer=coordinator__service__pb2.RescheduleVcJobsRequest.FromString, response_serializer=coordinator__service__pb2.RescheduleVcJobsResponse.SerializeToString), 'SetLabelConfig': grpc.unary_unary_rpc_method_handler(servicer.SetLabelConfig, request_deserializer=coordinator__service__pb2.SetLabelConfigRequest.FromString, response_serializer=coordinator__service__pb2.SetLabelConfigResponse.SerializeToString), 'ApplyAllLabel': grpc.unary_unary_rpc_method_handler(servicer.ApplyAllLabel, request_deserializer=coordinator__service__pb2.ApplyAllLabelRequest.FromString, response_serializer=coordinator__service__pb2.ApplyAllLabelResponse.SerializeToString), 'GetLabelStatus': grpc.unary_unary_rpc_method_handler(servicer.GetLabelStatus, request_deserializer=coordinator__service__pb2.GetLabelStatusRequest.FromString, response_serializer=coordinator__service__pb2.GetLabelStatusResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('cz.proto.coordinator.CoordinatorMaster', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('cz.proto.coordinator.CoordinatorMaster', rpc_method_handlers)

class CoordinatorMaster(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetJobAddress(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorMaster/GetJobAddress', coordinator__service__pb2.GetJobAddressRequest.SerializeToString, coordinator__service__pb2.GetJobAddressResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ReportHeartbeat(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorMaster/ReportHeartbeat', coordinator__service__pb2.HeartBeat.SerializeToString, coordinator__service__pb2.HeartBeatResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ListWorker(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorMaster/ListWorker', coordinator__service__pb2.ListWorkerRequest.SerializeToString, coordinator__service__pb2.ListWorkerResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ListJobs(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorMaster/ListJobs', coordinator__service__pb2.ListMasterJobsRequest.SerializeToString, coordinator__service__pb2.ListJobsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def DeleteJob(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorMaster/DeleteJob', coordinator__service__pb2.JobID.SerializeToString, service__common__pb2.ResponseStatus.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def HotUpgrade(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorMaster/HotUpgrade', coordinator__service__pb2.HotUpgradeRequest.SerializeToString, coordinator__service__pb2.HotUpgradeResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetHotUpgradeState(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorMaster/GetHotUpgradeState', coordinator__service__pb2.GetHotUpgradeStateRequest.SerializeToString, coordinator__service__pb2.GetHotUpgradeStateResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def SetServiceRoute(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorMaster/SetServiceRoute', coordinator__service__pb2.SetServiceRouteRequest.SerializeToString, coordinator__service__pb2.SetServiceRouteResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetServiceRoute(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorMaster/GetServiceRoute', coordinator__service__pb2.GetServiceRouteRequest.SerializeToString, coordinator__service__pb2.GetServiceRouteResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RescheduleVcJobs(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorMaster/RescheduleVcJobs', coordinator__service__pb2.RescheduleVcJobsRequest.SerializeToString, coordinator__service__pb2.RescheduleVcJobsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def SetLabelConfig(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorMaster/SetLabelConfig', coordinator__service__pb2.SetLabelConfigRequest.SerializeToString, coordinator__service__pb2.SetLabelConfigResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ApplyAllLabel(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorMaster/ApplyAllLabel', coordinator__service__pb2.ApplyAllLabelRequest.SerializeToString, coordinator__service__pb2.ApplyAllLabelResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def GetLabelStatus(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cz.proto.coordinator.CoordinatorMaster/GetLabelStatus', coordinator__service__pb2.GetLabelStatusRequest.SerializeToString, coordinator__service__pb2.GetLabelStatusResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)