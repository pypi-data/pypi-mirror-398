import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Dict, Optional
import threading
import re
from logging import getLogger

from clickzetta.connector.v0.exceptions import CZException
from clickzetta.connector.v0.parse_url import parse_url, HTTP_PROTOCOL_PREFIX, HTTPS_PROTOCOL_PREFIX
from clickzetta_ingestion.common.configure import Configure
from clickzetta_ingestion._proto import ingestion_v2_pb2
from clickzetta_ingestion.rpc.rpc_request import RpcRequest

_log = getLogger(__name__)

# default: 450. internal: 2s
GET_WORKER_MAX_RETRY_TIMES = "get.worker.retry.times"


class IgsConnectMode(str, Enum):
    UNKNOWN = "unknown"
    DIRECT = "direct"
    GATEWAY = "gateway"


@dataclass
class CZIgsContext:
    client_id: str
    connect_mode: IgsConnectMode = IgsConnectMode.UNKNOWN
    # Direct connect mode
    crl_addrs: List[Tuple[str, int]] = field(default_factory=list)
    worker_addrs: List[Tuple[str, int]] = field(default_factory=list)
    from clickzetta.connector.v0.client import Client
    outer_client:Client = None

    # Gateway routing mode
    scheme: str = ""
    host: str = ""
    port: int = -1

    # User info
    user_id: Optional[int] = None
    user_name: str = ""
    password: str = ""

    # Common configuration
    instance_id: int = 1
    instance_name: str = ""
    workspace: str = ""
    schema: str = ""
    namespace: str = ""
    lakehouse_instance: str = ""

    # Flags and settings
    authentication: bool = False
    show_debug_log: bool = False
    is_internal: bool = False
    is_direct: bool = False
    is_direct_all: bool = False
    pooled_allocator_support: bool = True

    # Properties and configuration
    properties: Dict = field(default_factory=dict)
    _configure: Optional[Configure] = None
    _configure_lock: threading.Lock = field(default_factory=threading.Lock)

    magic_token: Optional[str] = None
    token_cache: Optional[Dict] = None


    # Router mode
    router_mode: IgsConnectMode = IgsConnectMode.UNKNOWN
    use_aws_eks: bool = False

    INVALID_CONNECT_STRING = None

    @property
    def configure(self) -> Configure:
        if self._configure is None:
            with self._configure_lock:
                if self._configure is None:
                    self._configure = Configure(self.properties)
        return self._configure

    @property
    def url(self) -> str:
        if not self.scheme or not self.host:
            return ""
        url = f"{self.scheme}://{self.host}"
        if self.port != -1:
            url += f":{self.port}"
        return url

    @property
    def token(self) -> str:
        return self.outer_client.token

    @classmethod
    def parser(cls, outer_client, client_id: str, stream_url: str = None,
               crl_addrs: List[Tuple[str, int]] = None,
               worker_addrs: List[Tuple[str, int]] = None,
               instance_id: int = None,
               workspace: str = None,
               properties: Dict = None) -> 'CZIgsContext':

        if crl_addrs:
            return cls._parser_with_addrs(
                client_id, crl_addrs, worker_addrs,
                instance_id, workspace,outer_client, properties
            )
        elif stream_url:
            return cls._parser_with_url(
                client_id, stream_url, worker_addrs,outer_client, properties
            )
        else:
            return cls.INVALID_CONNECT_STRING

    @classmethod
    def _parser_with_addrs(cls, client_id: str,
                           crl_addrs: List[Tuple[str, int]],
                           worker_addrs: List[Tuple[str, int]],
                           instance_id: int,
                           workspace: str,
                           outer_client,
                           properties: Dict = None) -> 'CZIgsContext':
        context = cls(
            client_id=client_id,
            crl_addrs=crl_addrs or [],
            worker_addrs=worker_addrs or [],
            instance_id=instance_id,
            workspace=workspace,
            outer_client=outer_client
        )

        if client_id:
            context.connect_mode = IgsConnectMode.DIRECT

        if properties:
            cls._rewrite_conf(context, properties)

        return context

    @classmethod
    def _parser_with_url(cls, client_id: str,
                         stream_url: str,
                         worker_addrs: List[Tuple[str, int]],
                         outer_client,
                         properties: Dict = None) -> 'CZIgsContext':
        logging.info(f"using CZIgsContext url: {stream_url}")

        url = stream_url.replace("jdbc:", "igs:") if stream_url and stream_url.startswith(
            "clickzetta://") else stream_url

        if not url.startswith("igs:"):
            raise CZException("Stream URL must start with 'igs:'")

        # Parse URL using common parser
        (service, username, _, password, instance,
         workspace, vcluster, schema, magic_token,
         protocol, host, port, token_expire_time_ms,
         extra_params) = parse_url(url[4:])

        # Extract scheme and port from service
        scheme = "http" if service.startswith(HTTP_PROTOCOL_PREFIX) else "https"
        service = service.replace(HTTP_PROTOCOL_PREFIX, "").replace(HTTPS_PROTOCOL_PREFIX, "")
        host_port = service.split(":")
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else -1

        # Create context
        context = cls(
            client_id=client_id,
            scheme=scheme,
            host=host,
            port=port,
            worker_addrs=worker_addrs or [],
            instance_name=instance,
            workspace=workspace,
            user_name=username,
            password=password,
            schema=schema,
            namespace=f"{workspace}.{schema}" if schema else "",
            magic_token=magic_token,
            outer_client=outer_client
        )

        # Handle properties
        if properties is None:
            properties = {}

        # Add parsed properties
        if token_expire_time_ms:
            properties["token_expire_time_ms"] = token_expire_time_ms
        if vcluster:
            properties["vcluster"] = vcluster
        properties.update(extra_params)

        # Apply properties configuration
        if properties:
            cls._rewrite_conf(context, properties)

        context.router_mode = IgsConnectMode.GATEWAY
        context.connect_mode = IgsConnectMode.GATEWAY

        return context

    @staticmethod
    def _rewrite_conf(context: 'CZIgsContext', properties: Dict):
        if not context.properties:
            context.properties = properties.copy()
        else:
            context.properties.update(properties)

        # Handle gateway URL
        if "gatewayUrl" in properties:
            gateway_url = properties["gatewayUrl"]
            if gateway_url.startswith(("http://", "https://")):
                context.scheme = "https" if gateway_url.startswith("https://") else "http"
                gateway_url = re.sub(r"^https?://", "", gateway_url)

            host_port = gateway_url.split(":")
            if len(host_port) == 2:
                context.host = host_port[0]
                context.port = int(host_port[1])
            else:
                context.host = host_port[0]

        # Handle other properties
        if "localTest" in properties:
            context.local_test = bool(properties["localTest"])
            context.scheme = "http"

        if "use_http" in properties:
            if bool(properties["use_http"]):
                context.scheme = "http"

        if "showDebugLog" in properties:
            context.show_debug_log = bool(properties["showDebugLog"])

        if "instanceId" in properties:
            context.instance_id = int(properties["instanceId"])

        if "isInternal" in properties:
            context.is_internal = bool(properties["isInternal"])
            _log.info(f"using network internal {context.is_internal}")

        if "isDirect" in properties:
            context.is_direct = bool(properties["isDirect"])
            _log.info(f"using network direct {context.is_direct}")

        if "isDirectAll" in properties:
            context.is_direct_all = bool(properties["isDirectAll"])
            _log.info(f"using network direct-all {context.is_direct_all}")

        if "magicToken" in properties:
            context.magic_token = str(properties["magicToken"])

        if "useAwsEks" in properties:
            context.useAwsEks = bool(properties["useAwsEks"])

        if "authentication" in properties:
            context.authentication = bool(properties["authentication"])



    def refresh_all(self, context: 'CZIgsContext'):
        self._rewrite_conf(self, context.properties)

    def mirror(self) -> 'CZIgsContext':
        new_context = CZIgsContext(
            outer_client=self.outer_client,
            client_id=self.client_id,
            crl_addrs=self.crl_addrs.copy(),
            worker_addrs=self.worker_addrs.copy(),
            instance_id=self.instance_id,
            workspace=self.workspace,
            user_name=self.user_name,
            password=self.password,
            lakehouse_instance=self.lakehouse_instance,
        )
        self._rewrite_conf(new_context, self.properties.copy())
        return new_context

    @property
    def account(self) -> ingestion_v2_pb2.Account:
        """Get account info for requests"""
        return RpcRequest.build_account(
            instance_id=self.instance_id,
            workspace=self.workspace,
            user_name=self.configure.get("user.name", ""),
            user_id=self.configure.get("user.id", 0),
            token=self.configure.get("auth.token", "")
        )
