"""Connection for ClickZetta DB-API."""

import weakref
from logging import getLogger
from typing import Optional
from typing import Sequence, Any, Union

import requests
from requests.adapters import HTTPAdapter

from clickzetta.connector.v0 import _dbapi_helpers, cursor, import_ingestion_api
from clickzetta.connector.v0.client import Client
from clickzetta.connector.v0.converter import Converter
from clickzetta.connector.v0.enums import RealtimeOperation

_log = getLogger(__name__)
is_token_init = False
https_session = None
https_session_inited = False


@_dbapi_helpers.raise_on_closed("Operating on a closed connection.")
class Connection(object):
    def __init__(self, client: Optional[Client] = None):
        if client is None:
            _log.error("Connection must has a LogParams to log in.")
            raise AssertionError("Connection must has a LogParams to log in.")
        else:
            self._owns_client = True

        self._client = client
        self._client.refresh_token()
        self.converter = Converter()

        if not globals()["https_session_inited"]:
            session = requests.Session()
            session.mount(
                self._client.service,
                HTTPAdapter(pool_connections=10, pool_maxsize=client.http_pool_size, max_retries=3),
            )
            globals()["https_session"] = session
            globals()["https_session_inited"] = True

        self._client.session = globals()["https_session"]
        self._closed = False
        self._cursors_created = weakref.WeakSet()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _set_pure_arrow_decoding(self, value: bool):
        self._client._pure_arrow_decoding = value

    @property
    def pure_arrow_decoding(self):
        return self._client._pure_arrow_decoding

    def close(self):
        self._closed = True

        if self._owns_client:
            self._client.close()

        for cursor_ in self._cursors_created:
            if not cursor_._closed:
                cursor_.close()

    def commit(self):
        """No-op, but for consistency raise an error if connection is closed."""

    def cursor(self):
        """Return a new cursor object."""
        if self._client.username is not None and self._client.password is not None:
            self._client.refresh_token()
        new_cursor = cursor.Cursor(self)
        self._cursors_created.add(new_cursor)
        return new_cursor

    def create_bulkload_stream(self, **kwargs):
        """Create a bulkload stream using V2 implementation with V1 API.

        Args:
            schema: Schema name (required)
            table: Table name (required)
            operation: Operation type (BulkLoadOperation enum or string), default: APPEND
            partition_specs: Partition specifications (optional)
            record_keys: Record keys for UPSERT (optional)
            prefer_internal_endpoint: Use internal endpoint (optional, default: False)
            **kwargs: Additional options

        Returns:
            BulkLoadStream with V1-compatible API using V2 implementation
        """
        from clickzetta.bulkload.bulkload_enums import BulkLoadOptions, BulkLoadOperation

        # Extract parameters
        schema_name = kwargs.get('schema')
        table_name = kwargs.get('table')

        if not schema_name or not table_name:
            raise ValueError("Both 'schema' and 'table' are required parameters")

        # Handle operation parameter - support both enum and string
        operation = kwargs.get('operation', BulkLoadOperation.APPEND)
        if isinstance(operation, str):
            operation_upper = operation.upper()
            if operation_upper == 'APPEND':
                operation = BulkLoadOperation.APPEND
            elif operation_upper == 'OVERWRITE':
                operation = BulkLoadOperation.OVERWRITE
            elif operation_upper == 'UPSERT':
                operation = BulkLoadOperation.UPSERT
            else:
                operation = BulkLoadOperation.APPEND

        # Create V1 options
        options = BulkLoadOptions(
            operation=operation,
            partition_specs=kwargs.get('partition_specs', None),
            record_keys=kwargs.get('record_keys', None),
            prefer_internal_endpoint=kwargs.get('prefer_internal_endpoint', False)
        )

        meta = self._client.create_bulkload_stream(schema_name, table_name, options)
        return meta.get_v1_stream()

    def get_bulkload_stream(
        self, stream_id: str, schema: str = None, table: str = None
    ):
        """Get an existing bulkload stream by ID.
        
        Args:
            stream_id: Stream ID
            schema: Schema name (optional, uses client default if not provided)
            table: Table name (optional)
            
        Returns:
            BulkLoadStream with V1-compatible API using V2 implementation
        """
        meta = self._client.get_bulkload_stream(schema, table, stream_id)
        return meta.get_v1_stream()

    def create_bulkload_v2_stream(self, schema_name, table_name, options):
        from clickzetta_ingestion.bulkload.v2 import BulkLoadStreamV2
        return BulkLoadStreamV2.create_stream(self._client, schema_name, table_name, options)

    def get_bulkload_v2_stream(
            self, schema_name: str = None, table_name: str = None, stream_id: str = None, options=None
    ):
        from clickzetta_ingestion.bulkload.v2 import BulkLoadStreamV2
        return BulkLoadStreamV2.get_stream(self._client, schema_name=schema_name, table_name=table_name,
                                           stream_id=stream_id, options=options)

    def get_realtime_stream(
            self, operate: RealtimeOperation = RealtimeOperation.CDC, schema: str = None, table: str = None, options = None, tablet: int = 1
    ):
        return import_ingestion_api().create_realtime_stream(
            self._client, operate=operate, schema=schema, table=table, options=options, tablet=tablet
        )

    def get_job_profile(self, job_id: str):
        return self._client.get_job_profile(job_id)

    def get_job_result(self, job_id: str):
        return self._client.get_job_result(job_id)

    def get_job_progress(self, job_id: str):
        return self._client.get_job_progress(job_id)

    def get_job_summary(self, job_id: str):
        return self._client.get_job_summary(job_id)

    def get_job_plan(self, job_id: str):
        return self._client.get_job_plan(job_id)

    def _process_params_qmarks(self, params: Union[Sequence[Any], dict, None]) -> tuple:
        """Process parameters for client-side parameter binding.

        Args:
            params: Either a sequence, or a dictionary of parameters, if anything else
                is given then it will be put into a list and processed that way.
        """
        if params is None:
            return ()
        if isinstance(params, dict):
            ret = tuple(self._process_single_param(v) for k, v in params.items())
            _log.debug("binding parameters: %s", ret)
            return ret

        res = map(self._process_single_param, params)
        ret = tuple(res)
        _log.debug("parameters: %s", ret)
        return ret

    def get_full_sql_with_params(self, command: str, params: tuple) -> str:
        if not params:
            return command
        parts = command.split('?')
        _log.info(f"get_full_sql_with_params: {command}\n, parts size:{len(parts)}, params size:{len(params)}, "
                    f"params:{params}")
        full_sql = [parts[0]]
        for i, param in enumerate(params):
            full_sql.append(str(param))
            if i + 1 < len(parts):
                full_sql.append(parts[i + 1])
        return ''.join(full_sql)

    def _process_single_param(self, param: Any) -> Any:
        """Process a single parameter to Clickzetta understandable form.

        This is a convenience function to replace repeated multiple calls with a single
        function call.

        It calls the following underlying functions in this order:
            1. self.converter.convert_to
            2. self.converter.quote
        """
        _quote = self.converter.quote
        rst = _quote(self.converter.convert_to(param))
        return rst

    def get_client(self):
        return self._client

    def get_schema(self):
        return self._client.schema

    def use_schema(self, schema: str):
        """Set the current schema for the connection."""
        self._client.schema(schema)

    def use_workspace(self, workspace: str):
        """Set the current workspace for the connection."""
        self._client.workspace(workspace)

    def use_vcluster(self, vcluster: str):
        """Set the current vcluster for the connection."""
        self._client.vcluster(vcluster)

    def use_http(self):
        """Set the protocol to http."""
        self._client.protocol = "http"


def connect(**kwargs) -> Connection:
    client = kwargs.get("client")
    if client is None:
        # setting client or cz_url will ignore following parameters
        client = Client(**kwargs)
    return Connection(client)
