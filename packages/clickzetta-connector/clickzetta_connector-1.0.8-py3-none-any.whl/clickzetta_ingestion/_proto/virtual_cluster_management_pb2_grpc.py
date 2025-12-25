"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from . import virtual_cluster_management_pb2 as virtual__cluster__management__pb2
GRPC_GENERATED_VERSION = '1.68.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False
try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True
if _version_not_supported:
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + f' but the generated code in virtual_cluster_management_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class VirtualClusterManagerServiceStub(object):
    """=============================== service =====================================
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.createVirtualCluster = channel.unary_unary('/com.clickzetta.rm.VirtualClusterManagerService/createVirtualCluster', request_serializer=virtual__cluster__management__pb2.CreateVirtualClusterRequest.SerializeToString, response_deserializer=virtual__cluster__management__pb2.CreateVirtualClusterResponse.FromString, _registered_method=True)
        self.updateVirtualCluster = channel.unary_unary('/com.clickzetta.rm.VirtualClusterManagerService/updateVirtualCluster', request_serializer=virtual__cluster__management__pb2.UpdateVirtualClustersRequest.SerializeToString, response_deserializer=virtual__cluster__management__pb2.UpdateVirtualClusterResponse.FromString, _registered_method=True)
        self.startVirtualCluster = channel.unary_unary('/com.clickzetta.rm.VirtualClusterManagerService/startVirtualCluster', request_serializer=virtual__cluster__management__pb2.StartVirtualClusterRequest.SerializeToString, response_deserializer=virtual__cluster__management__pb2.StartVirtualClusterResponse.FromString, _registered_method=True)
        self.stopVirtualCluster = channel.unary_unary('/com.clickzetta.rm.VirtualClusterManagerService/stopVirtualCluster', request_serializer=virtual__cluster__management__pb2.StopVirtualClusterRequest.SerializeToString, response_deserializer=virtual__cluster__management__pb2.StopVirtualClusterResponse.FromString, _registered_method=True)
        self.resizeVirtualCluster = channel.unary_unary('/com.clickzetta.rm.VirtualClusterManagerService/resizeVirtualCluster', request_serializer=virtual__cluster__management__pb2.ResizeVirtualClusterRequest.SerializeToString, response_deserializer=virtual__cluster__management__pb2.ResizeVirtualClusterResponse.FromString, _registered_method=True)
        self.listVirtualCluster = channel.unary_unary('/com.clickzetta.rm.VirtualClusterManagerService/listVirtualCluster', request_serializer=virtual__cluster__management__pb2.ListVirtualClusterRequest.SerializeToString, response_deserializer=virtual__cluster__management__pb2.ListVirtualClustersResponse.FromString, _registered_method=True)
        self.describeVirtualCluster = channel.unary_unary('/com.clickzetta.rm.VirtualClusterManagerService/describeVirtualCluster', request_serializer=virtual__cluster__management__pb2.DescribeVirtualClusterRequest.SerializeToString, response_deserializer=virtual__cluster__management__pb2.DescribeVirtualClusterResponse.FromString, _registered_method=True)
        self.deleteVirtualCluster = channel.unary_unary('/com.clickzetta.rm.VirtualClusterManagerService/deleteVirtualCluster', request_serializer=virtual__cluster__management__pb2.DeleteVirtualClusterRequest.SerializeToString, response_deserializer=virtual__cluster__management__pb2.DeleteVirtualClusterResponse.FromString, _registered_method=True)
        self.cancelAllJobs = channel.unary_unary('/com.clickzetta.rm.VirtualClusterManagerService/cancelAllJobs', request_serializer=virtual__cluster__management__pb2.CancelAllJobsRequest.SerializeToString, response_deserializer=virtual__cluster__management__pb2.CancelAllJobsResponse.FromString, _registered_method=True)
        self.terminateVirtualClusterStatusChange = channel.unary_unary('/com.clickzetta.rm.VirtualClusterManagerService/terminateVirtualClusterStatusChange', request_serializer=virtual__cluster__management__pb2.TerminateVirtualClusterStatusChangeRequest.SerializeToString, response_deserializer=virtual__cluster__management__pb2.TerminateVirtualClusterStatusChangeResponse.FromString, _registered_method=True)
        self.upgradeVirtualCluster = channel.unary_unary('/com.clickzetta.rm.VirtualClusterManagerService/upgradeVirtualCluster', request_serializer=virtual__cluster__management__pb2.UpgradeVirtualClusterRequest.SerializeToString, response_deserializer=virtual__cluster__management__pb2.UpgradeVirtualClusterResponse.FromString, _registered_method=True)
        self.abortUpgradeVirtualCluster = channel.unary_unary('/com.clickzetta.rm.VirtualClusterManagerService/abortUpgradeVirtualCluster', request_serializer=virtual__cluster__management__pb2.AbortUpgradeVirtualClusterRequest.SerializeToString, response_deserializer=virtual__cluster__management__pb2.AbortUpgradeVirtualClusterResponse.FromString, _registered_method=True)
        self.finishSwitchVirtualCluster = channel.unary_unary('/com.clickzetta.rm.VirtualClusterManagerService/finishSwitchVirtualCluster', request_serializer=virtual__cluster__management__pb2.FinishSwitchVirtualClusterRequest.SerializeToString, response_deserializer=virtual__cluster__management__pb2.FinishSwitchVirtualClusterResponse.FromString, _registered_method=True)
        self.getUpgradeStatus = channel.unary_unary('/com.clickzetta.rm.VirtualClusterManagerService/getUpgradeStatus', request_serializer=virtual__cluster__management__pb2.GetVirtualClusterUpgradeStatusRequest.SerializeToString, response_deserializer=virtual__cluster__management__pb2.GetVirtualClusterUpgradeStatusResponse.FromString, _registered_method=True)

class VirtualClusterManagerServiceServicer(object):
    """=============================== service =====================================
    """

    def createVirtualCluster(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def updateVirtualCluster(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def startVirtualCluster(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def stopVirtualCluster(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def resizeVirtualCluster(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def listVirtualCluster(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def describeVirtualCluster(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def deleteVirtualCluster(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def cancelAllJobs(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def terminateVirtualClusterStatusChange(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def upgradeVirtualCluster(self, request, context):
        """upgrade apis
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def abortUpgradeVirtualCluster(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def finishSwitchVirtualCluster(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def getUpgradeStatus(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_VirtualClusterManagerServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {'createVirtualCluster': grpc.unary_unary_rpc_method_handler(servicer.createVirtualCluster, request_deserializer=virtual__cluster__management__pb2.CreateVirtualClusterRequest.FromString, response_serializer=virtual__cluster__management__pb2.CreateVirtualClusterResponse.SerializeToString), 'updateVirtualCluster': grpc.unary_unary_rpc_method_handler(servicer.updateVirtualCluster, request_deserializer=virtual__cluster__management__pb2.UpdateVirtualClustersRequest.FromString, response_serializer=virtual__cluster__management__pb2.UpdateVirtualClusterResponse.SerializeToString), 'startVirtualCluster': grpc.unary_unary_rpc_method_handler(servicer.startVirtualCluster, request_deserializer=virtual__cluster__management__pb2.StartVirtualClusterRequest.FromString, response_serializer=virtual__cluster__management__pb2.StartVirtualClusterResponse.SerializeToString), 'stopVirtualCluster': grpc.unary_unary_rpc_method_handler(servicer.stopVirtualCluster, request_deserializer=virtual__cluster__management__pb2.StopVirtualClusterRequest.FromString, response_serializer=virtual__cluster__management__pb2.StopVirtualClusterResponse.SerializeToString), 'resizeVirtualCluster': grpc.unary_unary_rpc_method_handler(servicer.resizeVirtualCluster, request_deserializer=virtual__cluster__management__pb2.ResizeVirtualClusterRequest.FromString, response_serializer=virtual__cluster__management__pb2.ResizeVirtualClusterResponse.SerializeToString), 'listVirtualCluster': grpc.unary_unary_rpc_method_handler(servicer.listVirtualCluster, request_deserializer=virtual__cluster__management__pb2.ListVirtualClusterRequest.FromString, response_serializer=virtual__cluster__management__pb2.ListVirtualClustersResponse.SerializeToString), 'describeVirtualCluster': grpc.unary_unary_rpc_method_handler(servicer.describeVirtualCluster, request_deserializer=virtual__cluster__management__pb2.DescribeVirtualClusterRequest.FromString, response_serializer=virtual__cluster__management__pb2.DescribeVirtualClusterResponse.SerializeToString), 'deleteVirtualCluster': grpc.unary_unary_rpc_method_handler(servicer.deleteVirtualCluster, request_deserializer=virtual__cluster__management__pb2.DeleteVirtualClusterRequest.FromString, response_serializer=virtual__cluster__management__pb2.DeleteVirtualClusterResponse.SerializeToString), 'cancelAllJobs': grpc.unary_unary_rpc_method_handler(servicer.cancelAllJobs, request_deserializer=virtual__cluster__management__pb2.CancelAllJobsRequest.FromString, response_serializer=virtual__cluster__management__pb2.CancelAllJobsResponse.SerializeToString), 'terminateVirtualClusterStatusChange': grpc.unary_unary_rpc_method_handler(servicer.terminateVirtualClusterStatusChange, request_deserializer=virtual__cluster__management__pb2.TerminateVirtualClusterStatusChangeRequest.FromString, response_serializer=virtual__cluster__management__pb2.TerminateVirtualClusterStatusChangeResponse.SerializeToString), 'upgradeVirtualCluster': grpc.unary_unary_rpc_method_handler(servicer.upgradeVirtualCluster, request_deserializer=virtual__cluster__management__pb2.UpgradeVirtualClusterRequest.FromString, response_serializer=virtual__cluster__management__pb2.UpgradeVirtualClusterResponse.SerializeToString), 'abortUpgradeVirtualCluster': grpc.unary_unary_rpc_method_handler(servicer.abortUpgradeVirtualCluster, request_deserializer=virtual__cluster__management__pb2.AbortUpgradeVirtualClusterRequest.FromString, response_serializer=virtual__cluster__management__pb2.AbortUpgradeVirtualClusterResponse.SerializeToString), 'finishSwitchVirtualCluster': grpc.unary_unary_rpc_method_handler(servicer.finishSwitchVirtualCluster, request_deserializer=virtual__cluster__management__pb2.FinishSwitchVirtualClusterRequest.FromString, response_serializer=virtual__cluster__management__pb2.FinishSwitchVirtualClusterResponse.SerializeToString), 'getUpgradeStatus': grpc.unary_unary_rpc_method_handler(servicer.getUpgradeStatus, request_deserializer=virtual__cluster__management__pb2.GetVirtualClusterUpgradeStatusRequest.FromString, response_serializer=virtual__cluster__management__pb2.GetVirtualClusterUpgradeStatusResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('com.clickzetta.rm.VirtualClusterManagerService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('com.clickzetta.rm.VirtualClusterManagerService', rpc_method_handlers)

class VirtualClusterManagerService(object):
    """=============================== service =====================================
    """

    @staticmethod
    def createVirtualCluster(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/com.clickzetta.rm.VirtualClusterManagerService/createVirtualCluster', virtual__cluster__management__pb2.CreateVirtualClusterRequest.SerializeToString, virtual__cluster__management__pb2.CreateVirtualClusterResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def updateVirtualCluster(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/com.clickzetta.rm.VirtualClusterManagerService/updateVirtualCluster', virtual__cluster__management__pb2.UpdateVirtualClustersRequest.SerializeToString, virtual__cluster__management__pb2.UpdateVirtualClusterResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def startVirtualCluster(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/com.clickzetta.rm.VirtualClusterManagerService/startVirtualCluster', virtual__cluster__management__pb2.StartVirtualClusterRequest.SerializeToString, virtual__cluster__management__pb2.StartVirtualClusterResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def stopVirtualCluster(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/com.clickzetta.rm.VirtualClusterManagerService/stopVirtualCluster', virtual__cluster__management__pb2.StopVirtualClusterRequest.SerializeToString, virtual__cluster__management__pb2.StopVirtualClusterResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def resizeVirtualCluster(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/com.clickzetta.rm.VirtualClusterManagerService/resizeVirtualCluster', virtual__cluster__management__pb2.ResizeVirtualClusterRequest.SerializeToString, virtual__cluster__management__pb2.ResizeVirtualClusterResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def listVirtualCluster(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/com.clickzetta.rm.VirtualClusterManagerService/listVirtualCluster', virtual__cluster__management__pb2.ListVirtualClusterRequest.SerializeToString, virtual__cluster__management__pb2.ListVirtualClustersResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def describeVirtualCluster(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/com.clickzetta.rm.VirtualClusterManagerService/describeVirtualCluster', virtual__cluster__management__pb2.DescribeVirtualClusterRequest.SerializeToString, virtual__cluster__management__pb2.DescribeVirtualClusterResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def deleteVirtualCluster(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/com.clickzetta.rm.VirtualClusterManagerService/deleteVirtualCluster', virtual__cluster__management__pb2.DeleteVirtualClusterRequest.SerializeToString, virtual__cluster__management__pb2.DeleteVirtualClusterResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def cancelAllJobs(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/com.clickzetta.rm.VirtualClusterManagerService/cancelAllJobs', virtual__cluster__management__pb2.CancelAllJobsRequest.SerializeToString, virtual__cluster__management__pb2.CancelAllJobsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def terminateVirtualClusterStatusChange(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/com.clickzetta.rm.VirtualClusterManagerService/terminateVirtualClusterStatusChange', virtual__cluster__management__pb2.TerminateVirtualClusterStatusChangeRequest.SerializeToString, virtual__cluster__management__pb2.TerminateVirtualClusterStatusChangeResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def upgradeVirtualCluster(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/com.clickzetta.rm.VirtualClusterManagerService/upgradeVirtualCluster', virtual__cluster__management__pb2.UpgradeVirtualClusterRequest.SerializeToString, virtual__cluster__management__pb2.UpgradeVirtualClusterResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def abortUpgradeVirtualCluster(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/com.clickzetta.rm.VirtualClusterManagerService/abortUpgradeVirtualCluster', virtual__cluster__management__pb2.AbortUpgradeVirtualClusterRequest.SerializeToString, virtual__cluster__management__pb2.AbortUpgradeVirtualClusterResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def finishSwitchVirtualCluster(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/com.clickzetta.rm.VirtualClusterManagerService/finishSwitchVirtualCluster', virtual__cluster__management__pb2.FinishSwitchVirtualClusterRequest.SerializeToString, virtual__cluster__management__pb2.FinishSwitchVirtualClusterResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def getUpgradeStatus(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/com.clickzetta.rm.VirtualClusterManagerService/getUpgradeStatus', virtual__cluster__management__pb2.GetVirtualClusterUpgradeStatusRequest.SerializeToString, virtual__cluster__management__pb2.GetVirtualClusterUpgradeStatusResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)