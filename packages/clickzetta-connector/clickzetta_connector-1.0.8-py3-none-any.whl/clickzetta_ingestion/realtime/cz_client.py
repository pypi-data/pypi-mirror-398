import threading
import uuid
from logging import getLogger
from typing import List, Tuple, Dict, Optional

from clickzetta.connector.v0.enums import RealtimeOperation
from clickzetta.connector.v0.exceptions import InternalError, CZException
from clickzetta_ingestion._proto import ingestion_pb2, ingestion_v2_pb2
from clickzetta_ingestion.realtime.arrow_row import ArrowIGSTableMeta
from clickzetta_ingestion.realtime.arrow_stream import ArrowStream
from clickzetta_ingestion.realtime.arrow_table import ArrowTable
from clickzetta_ingestion.realtime.realtime_options import CZSessionOptions, FlushMode
from clickzetta_ingestion.realtime.realtime_stream import RealtimeStream
from clickzetta_ingestion.realtime.realtime_stream_api import IGS_TABLET_NUM
from clickzetta_ingestion.rpc.cz_igs_context import CZIgsContext
from clickzetta_ingestion.rpc.gateway_rpc_proxy import GatewayRpcProxy
from clickzetta_ingestion.rpc.rpc_request import RpcRequest, ServerTokenMap

log = getLogger(__name__)


class CZClient:
    def __init__(self):
        self.client_id = None
        self.client_context: Optional[CZIgsContext] = None
        self._rpc_proxy: Optional[GatewayRpcProxy] = None
        self._rpc_proxy_lock = threading.Lock()
        self.initialized = False
        self.outer_client = None

    def open(self):
        """Initialize RPC proxy if not already initialized"""
        if self.initialized:
            return
        with self._rpc_proxy_lock:
            self._valid_rpc_proxy_init()

    def close(self):
        """Close client and cleanup resources"""
        if not self.initialized:
            return
        self.initialized = False

    def _valid_rpc_proxy_init(self):
        """Validate and initialize RPC proxy if needed"""
        if self.initialized:
            return

        if not self._rpc_proxy:
            self._rpc_proxy = self._create_rpc_proxy()

        self.initialized = True

    def _create_rpc_proxy(self):
        """Create and open RPC proxy with retry mechanism"""
        try:
            proxy = self._build_rpc_proxy()
            return proxy
        except Exception as e:
            raise InternalError(f"Failed to create RPC proxy: {e}")

    def _build_rpc_proxy(self) -> 'GatewayRpcProxy':
        """Build RPC proxy with client context settings"""
        if not self.client_context:
            raise InternalError("Client context not initialized")

        return GatewayRpcProxy(context=self.client_context)

    @staticmethod
    def refresh_instance_id(client, new_instance_id: int):
        client_context: CZIgsContext = client.igs_client.client_context
        client_props: Dict = client_context.properties
        if "instanceId" not in client_props:
            client_props["instanceId"] = new_instance_id
            client.instance_id = new_instance_id
            client_context.refresh_all(client_context)

    def create_arrow_row_stream(self, client, schema_name: str, table_name: str,
                                options: CZSessionOptions, operation: RealtimeOperation) -> RealtimeStream:
        log.info(
            f"start to create stream for schema [{schema_name}.{table_name}] extra properties {options.properties}.")

        with self._rpc_proxy_lock:
            self._valid_rpc_proxy_init()

        try:
            tablet = options.properties.get(IGS_TABLET_NUM)
            igs_table_meta: ArrowIGSTableMeta = self._rpc_proxy.create_or_get_stream_v2(
                client,
                schema_name,
                table_name,
                tablet
            )

            self.client_context.properties.update(options.properties)

            # Refresh instance ID if needed
            self.refresh_instance_id(client, igs_table_meta.instance_id)

            # Handle ACID table flush mode
            if igs_table_meta.table_type == ingestion_pb2.IGSTableType.ACID and options.flush_mode == FlushMode.AUTO_FLUSH_BACKGROUND:
                log.warning("acid table not support flushMode with AUTO_FLUSH_BACKGROUND. reset to AUTO_FLUSH_SYNC.")
                options.flush_mode = FlushMode.AUTO_FLUSH_SYNC

            # Get workers with retry
            workers = self._rpc_proxy.get_route_workers(
                client,
                schema_name,
                table_name,
                tablet,
            )
            log.info(f"Get workers: {workers}")
            if not workers:
                raise ValueError("No workers available for RPC connection")

            # Create Arrow components
            arrow_table = ArrowTable(igs_table_meta)
            arrow_stream = ArrowStream(client, arrow_table, options, operation)

            # Initialize RPC connection using workers
            arrow_stream.init_rpc_connection(workers)

            return RealtimeStream(
                meta_data=igs_table_meta,
                client=client,
                operation=operation,
                arrow_table=arrow_table,
                arrow_stream=arrow_stream
            )

        finally:
            self.close()

    def rebuild_idle_tablet(self, client, schema_name, table_name, tablet=None):
        with self._rpc_proxy_lock:
            self._valid_rpc_proxy_init()
        # Get workers with retry
        workers = self._rpc_proxy.get_route_workers(
            client,
            schema_name,
            table_name,
            tablet,
        )
        log.info(f"Get workers when rebuild idle tablet: {workers}")
        if not workers:
            raise ValueError("No workers available for RPC connection")
        return workers

    def async_commit(self, client, instance_id: int, workspace: str,
                     table_idents: List[Tuple[str, str]],
                     server_token_maps: Optional[List[ServerTokenMap]] = None) -> int:
        """
        Async commit for tables with server tokens

        Args:
            instance_id: Instance ID
            workspace: Workspace name
            table_idents: List of table identifiers
            server_token_maps: Optional list of server token maps

        Returns:
            Commit ID
        """
        response = None
        try:
            # Build commit request
            request = ingestion_v2_pb2.CommitRequest()

            # Add table identifiers
            for table_ident in table_idents:
                ident = ingestion_v2_pb2.TableIdentifier(
                    instance_id=instance_id,
                    workspace=workspace,
                    schema_name=table_ident[0],
                    table_name=table_ident[1]
                )
                request.table_ident.append(ident)

            # Add server tokens if provided
            if server_token_maps:
                token_list_builder = ingestion_v2_pb2.ServerTokenList()

                legacy_tokens = []
                should_set_legacy_token = True

                for token_map in server_token_maps:
                    if token_map is None:
                        # Add empty token map
                        token_list_builder.server_token_map.append(
                            ingestion_v2_pb2.ServerTokenMap()
                        )
                    else:
                        # Add token map with server tokens
                        token_map_msg = ingestion_v2_pb2.ServerTokenMap()
                        token_map_msg.server_tokens.update(token_map.server_tokens)
                        token_list_builder.server_token_map.append(token_map_msg)

                    if should_set_legacy_token:
                        if token_map and not token_map.is_legacy_server_token_required():
                            should_set_legacy_token = False
                            legacy_tokens = []
                        else:
                            legacy_tokens.append(token_map.get_legacy_server_token() if token_map else "")

                if legacy_tokens:
                    token_list_builder.server_token.extend(legacy_tokens)

                request.server_token_list.CopyFrom(token_list_builder)

            # Create RPC request
            rpc_request = self._rebuild_request_message(
                RpcRequest(
                    method=ingestion_pb2.MethodEnum.ASYNC_COMMIT_V2,
                    message=request
                )
            )

            if self.client_context.authentication:
                rpc_request.account(self.client_context.user_name, self.client_context.user_id)

            # Log request info
            prefix = f"Async commit for instance [{instance_id}] workspace [{workspace}]"

            def predicate(response_pb):
                """Check if response needs retry"""
                return response_pb.status.code in (
                    ingestion_v2_pb2.Code.NEED_REDIRECT,
                    ingestion_v2_pb2.Code.STREAM_UNAVAILABLE
                )

            def process_response(response_pb):
                """Process successful response"""
                if response_pb.status.code == ingestion_v2_pb2.Code.SUCCESS:
                    return response_pb.commit_id

                raise CZException(f"Failed to async commit: {response_pb.status.error_message}")

            return self._rpc_proxy.handle_retry_rpc_call_framework(
                client=client,
                prefix=prefix,
                request=rpc_request,
                retry_support=True,
                method=ingestion_pb2.MethodEnum.ASYNC_COMMIT_V2,
                predicate=predicate,
                process_response=process_response
            )

        except Exception as e:
            if response:
                log.error(f"Async commit failed: {response}")
                raise CZException(f"Failed to async commit: {response}")
            else:
                log.error(f"Failed to async commit: {e}")
                raise CZException(f"Failed to async commit: {e}")

    def _rebuild_request_message(self, request: RpcRequest) -> RpcRequest:
        """Rebuild request message with client context"""
        # Add account info
        request.account(
            user_name=self.client_context.user_name,
            user_id=self.client_context.user_id
        )
        return request

    def check_commit_result(self, client, instance_id: int, workspace: str, commit_id: int):
        """
        Check commit result with retry

        Args:
            client: Client instance
            instance_id: Instance ID
            workspace: Workspace name
            commit_id: Commit ID to check
        """
        try:
            # Build request
            request = ingestion_v2_pb2.CheckCommitResultRequest(
                commit_id=commit_id,
                table_ident=ingestion_v2_pb2.TableIdentifier(
                    instance_id=instance_id,
                    workspace=workspace
                )
            )

            # Create RPC request
            rpc_request = RpcRequest(
                method=ingestion_pb2.MethodEnum.CHECK_COMMIT_RESULT_V2,
                message=request
            )
            if self.client_context.authentication:
                rpc_request.account(self.client_context.user_name, self.client_context.user_id)

            prefix = f"Check commit result for commitId [{commit_id}]"

            def predicate(response) -> bool:
                return response.status.code != ingestion_v2_pb2.Code.SUCCESS or not response.finished

            def process_response(response) -> bool:
                if response.status.code == ingestion_v2_pb2.Code.SUCCESS and response.finished:
                    return True
                raise CZException(f"Failed to check commit result: {response}")

            return self._rpc_proxy.handle_retry_rpc_call_framework(
                client=client,
                prefix=prefix,
                request=rpc_request,
                retry_support=True,
                method=ingestion_pb2.MethodEnum.CHECK_COMMIT_RESULT_V2,
                predicate=predicate,
                process_response=process_response
            )

        except Exception as e:
            log.error(f"Check commit result failed: {e}")
            raise CZException(f"Failed to check commit result: {e}")


class CZClientBuilder:
    """Builder for CZClient"""

    def __init__(self):
        self.crl_addrs: List[Tuple[str, int]] = []
        self.worker_addrs: List[Tuple[str, int]] = []
        self.instance_id = 1
        self.workspace = "default"
        self.stream_url = None
        self.properties: dict = {}
        self.outer_client = None

    def with_crl_addr(self, host: str, port: int):
        self._add_or_ignore_addr(self.crl_addrs, host, port)
        return self

    def with_worker_addr(self, host: str, port: int):
        self._add_or_ignore_addr(self.worker_addrs, host, port)
        return self

    def with_authenticate(self, authentication: bool):
        self.properties["authentication"] = authentication
        return self

    def with_stream_url(self, url: str):
        self.stream_url = url
        return self

    def with_properties(self, props: Dict):
        self.properties.update(props)
        return self

    def with_outer_client(self, client):
        self.outer_client = client
        return self

    def build(self) -> CZClient:
        """Build and return configured CZClient instance"""
        client_id = str(uuid.uuid4())
        if self.crl_addrs:
            igs_context = self._create_context_with_addrs(client_id)
        else:
            igs_context = self._create_context_with_url(client_id)

        if not igs_context:
            raise InternalError("Invalid IGS connection configuration")

        # build real client.
        client = CZClient()
        client.client_id = igs_context.client_id
        client.client_context = igs_context
        client.outer_client = self.outer_client

        return client

    def _create_context_with_addrs(self, client_id: str):
        """Create context using CRL addresses"""
        return CZIgsContext.parser(
            outer_client=self.outer_client,
            client_id=client_id,
            crl_addrs=self.crl_addrs,
            worker_addrs=self.worker_addrs,
            instance_id=self.instance_id,
            workspace=self.workspace,
            properties=self.properties
        )

    def _create_context_with_url(self, client_id: str):
        """Create context using stream URL"""
        return CZIgsContext.parser(
            outer_client=self.outer_client,
            client_id=client_id,
            stream_url=self.stream_url,
            worker_addrs=self.worker_addrs,
            properties=self.properties
        )

    @staticmethod
    def _add_or_ignore_addr(addr_list: List[Tuple[str, int]], host: str, port: int):
        """Add address to list if not already present"""
        addr = (host, port)
        if addr not in addr_list:
            addr_list.append(addr)
