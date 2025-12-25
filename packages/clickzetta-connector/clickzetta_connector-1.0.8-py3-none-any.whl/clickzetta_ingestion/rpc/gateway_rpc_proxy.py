from __future__ import annotations

import json
import logging
import time
from typing import List, Tuple, Any, Optional, Callable

import requests
from google.protobuf.json_format import MessageToJson, ParseDict, Parse

from clickzetta.connector.v0.exceptions import CZException
from clickzetta_ingestion._proto import ingestion_pb2, ingestion_v2_pb2
from clickzetta_ingestion.realtime.arrow_row import ArrowIGSTableMeta
from clickzetta_ingestion.rpc.cz_igs_context import CZIgsContext, GET_WORKER_MAX_RETRY_TIMES, IgsConnectMode
from clickzetta_ingestion.rpc.rpc_request import RpcRequest
from clickzetta_ingestion.rpc.response_constructor import ResponseConstructor

log = logging.getLogger(__name__)

VERSION_NAME = "clickzetta-ingestion-python"
VERSION_NUMBER = 1


class GatewayRpcProxy:
    """
    Gateway RPC proxy implemented with new version proto, supports asynchronous call to gateway service
    """

    def __init__(self, context: CZIgsContext):
        self.context = context

    @staticmethod
    def handle_rpc_call_framework(prefix: str, client, rpcRequest: RpcRequest, caller: callable):
        try:
            response = _gate_way_call(
                client=client,
                request=rpcRequest.get(),
                method=rpcRequest.method()
            )
            # Parse json type response to protobuf message
            return caller(response)

        except CZException as e:
            log.error(f"{prefix} failed with error: {str(e)}")
            raise
        except Exception as e:
            log.error(f"{prefix} encountered an unexpected error: {str(e)}")
            raise CZException(f"{prefix} failed due to an unexpected error: {str(e)}")

    @staticmethod
    def handle_retry_rpc_call_framework(client, prefix: str, request: RpcRequest, retry_support: bool,
                                        method: ingestion_pb2.MethodEnum,
                                        predicate: Optional[Callable[[Any], bool]] = None,
                                        process_response: Optional[Callable[[Any], Any]] = None) -> Any:
        """Generic retry framework for RPC calls
        Args:
            client: Client instance
            prefix: Prefix for log messages
            request: RpcRequest object
            retry_support: Flag to indicate if retry is supported
            method: Method enum value. It is used to parse response from
                    {@link clickzetta_ingestion.rpc.response_constructor.ResponseConstructor.get_response}
            predicate: Predicate function to check if response needs retry
            process_response: Processor function to handle successful response
        """

        def default_predicate(response: Any) -> bool:
            """Default predicate checks if response needs retry"""
            return (response.status.code != ingestion_v2_pb2.Code.SUCCESS if 
                   hasattr(response, 'status') else False)
            
        def default_processor(response: Any) -> Any:
            """Default processor handles successful response"""
            if hasattr(response, 'status'):
                if response.status.code != ingestion_v2_pb2.Code.SUCCESS:
                    raise CZException(f"RPC call failed: {response}")
            return response

        predicate = predicate or default_predicate
        process_response = process_response or default_processor

        context: CZIgsContext = client.igs_client.client_context
        # default: 3
        max_retries = context.configure.get_int("client.rpc.retry.times", 3)
        # default: 5 * 1000 MS
        retry_interval_ms = context.configure.get_int("client.rpc.retry.interval.ms", 5 * 1000)
        last_response = None

        for attempt in range(max_retries):
            try:
                response_str = _gate_way_call(
                    client=client,
                    request=request.get(),
                    method=request.method()
                )

                last_response = response_str

                # Convert to specific response pb
                response = ResponseConstructor.get_response(method, response_str)
                
                if not predicate(response):
                    return process_response(response)
                    
                if attempt < max_retries - 1:
                    time.sleep(retry_interval_ms / 1000)
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    error_msg = f"{prefix} failed: {str(e)}"
                    raise CZException(f"{error_msg} after {max_retries} attempts: {e}")
                time.sleep(retry_interval_ms / 1000)

        # Handle retry exhausted
        if not retry_support:
            error_msg = f"{prefix} failed! last response: {last_response}"
        else:
            error_msg = f"{prefix} failed after {max_retries} retries! last response: {last_response}"

        log.error(error_msg)
        raise CZException(error_msg)

    def create_or_get_stream_v2(self, client, schema_name: str, table_name: str, 
                               tablet: int) -> ArrowIGSTableMeta:
        """Create or get stream with retry logic"""
        cz_client = client.igs_client
        context: CZIgsContext = cz_client.client_context

        # Build request
        request = ingestion_v2_pb2.CreateOrGetStreamRequest()
        table_identifier = ingestion_v2_pb2.TableIdentifier()
        table_identifier.instance_id = context.instance_id
        table_identifier.workspace = context.workspace
        table_identifier.schema_name = schema_name
        table_identifier.table_name = table_name
        request.table_ident.CopyFrom(table_identifier)

        if tablet:
            if tablet <= 0:
                raise ValueError("tablet must be greater than 0")
            request.num_tablets = tablet

        # Create RPC request
        rpc_request = RpcRequest(
            ingestion_pb2.MethodEnum.CREATE_OR_GET_STREAM_V2, 
            request
        )
        if context.authentication:
            rpc_request.account(context.user_name, context.user_id)

        prefix = f"Create stream for table [{schema_name}.{table_name}]"

        def predicate(response_pb):
            """Check if response needs retry"""
            return response_pb.status.code in (
                ingestion_v2_pb2.Code.NEED_REDIRECT,
                ingestion_v2_pb2.Code.STREAM_UNAVAILABLE
            )

        def process_response(response_pb):
            """Process successful response"""
            if response_pb.status.code == ingestion_v2_pb2.Code.SUCCESS:
                return ArrowIGSTableMeta(
                    instance_id=response_pb.table_ident.instance_id,
                    schema_name=schema_name,
                    table_name=table_name,
                    table_meta=response_pb.data_schema,
                    require_commit=response_pb.require_commit
                )
                
            raise CZException(f"Failed to create stream: {response_pb.status.error_message}")

        return self.handle_retry_rpc_call_framework(
            client=client,
            prefix=prefix,
            request=rpc_request,
            retry_support=True,
            method=ingestion_pb2.MethodEnum.CREATE_OR_GET_STREAM_V2,
            predicate=predicate,
            process_response=process_response
        )

    def get_route_workers(self, client, schema_name: str, table_name: str, tablet: int) -> List[
        Tuple[str, int]]:
        """
        try to get tablet workers with retry.
        """
        retry_count = 0
        context: CZIgsContext = client.igs_client.client_context
        max_retries = context.configure.get_int(GET_WORKER_MAX_RETRY_TIMES, 450)
        while retry_count < max_retries:
            get_workers_request = ingestion_v2_pb2.GetRouteWorkersRequest()

            table_identifier = ingestion_v2_pb2.TableIdentifier()
            table_identifier.instance_id = client.instance_id
            table_identifier.workspace = client.workspace
            table_identifier.schema_name = schema_name
            table_identifier.table_name = table_name
            get_workers_request.table_ident.CopyFrom(table_identifier)

            if context.connect_mode == IgsConnectMode.GATEWAY:
                get_workers_request.connect_mode = ingestion_v2_pb2.ConnectMode.GATEWAY
            else:
                raise CZException("Only support gateway mode, but got: " + str(context.connect_mode))

            rpc_request = RpcRequest(ingestion_pb2.MethodEnum.GET_ROUTE_WORKER_V2, get_workers_request)

            response_pb = self.handle_rpc_call_framework(
                prefix=f"Get route workers for table [{schema_name}.{table_name}]",
                client=client,
                rpcRequest=rpc_request,
                caller=lambda r: Parse(
                    r,
                    ingestion_v2_pb2.GetRouteWorkersResponse(),
                    ignore_unknown_fields=True
                )
            )

            workers = [(worker.host, worker.port) for worker in response_pb.tuple if worker.host]
            if workers:
                return workers

            retry_count += 1
            log.info(
                f"Can not get route workers! sleep & retry to get all tablet loaded. Retry {retry_count} "
                f"to get all tablet loaded for table {schema_name}.{table_name} .")
            time.sleep(2)  # 2 seconds delay between retries

            if retry_count % 15 == 0:  # Every 30s, try to create stream again
                self.create_or_get_stream_v2(client, schema_name, table_name, tablet)

        raise TimeoutError(f"Failed to get workers after {max_retries} retries")

    def open(self):
        """Initialize resources"""
        pass

    def close(self):
        """Cleanup resources"""
        pass

HEADERS = {"Content-Type": "application/json"}


def _gate_way_call(client, request, method):
    path = "/igs/gatewayEndpoint"
    gate_way_request = ingestion_pb2.GatewayRequest()
    gate_way_request.methodEnumValue = method
    gate_way_request.message = MessageToJson(request)

    # Add version info
    gate_way_request.versionInfo.name = (
                VERSION_NAME + "{" + client.username + "@" + client.instance + "." + client.service + "}")
    gate_way_request.versionInfo.version = VERSION_NUMBER

    headers = {
        "Content-Type": "application/json",
        "instanceName": client.instance,
        "X-ClickZetta-Token": client.token
    }

    try:
        api_response = requests.post(
            client.service + path,
            data=MessageToJson(gate_way_request),
            headers=headers,
            timeout=30
        )
        api_response.encoding = "utf-8"

        if api_response.status_code != 200:
            raise CZException(
                f"Gateway call failed with status code: {api_response.status_code}, response: {api_response.text}")

        result = api_response.text
        try:
            result_dict = json.loads(result)
        except json.JSONDecodeError:
            log.error(f"Failed to parse gateway response: {result}")
            raise CZException(f"Invalid gateway response: {result}")

        result_status = ParseDict(
            result_dict["status"],
            ingestion_pb2.ResponseStatus(),
            ignore_unknown_fields=True
        )

        if not result_status or result_status.code != ingestion_pb2.Code.SUCCESS:
            code = result_status.code if result_status else "Unknown"
            raise CZException(f"Gateway call failed! code:{code}, : {result}")

        return result_dict["message"]
    except Exception as e:
        log.error(f"Unexpected error in gateway call: {e}")
        raise CZException(f"Unexpected error in gateway call: {e}")
