from logging import getLogger
from typing import Optional

from clickzetta.bulkload.bulkload_enums import (
    BulkLoadMetaData,
    BulkLoadStreamInfo, BulkLoadOptions, BulkLoadCommitOptions, BulkLoadConfig, BulkLoadState, BulkLoadOperation, )
from clickzetta.bulkload.bulkload_stream import BulkLoadStream
from clickzetta.connector.v0.client import Client

HEADERS = {"Content-Type": "application/json"}

_log = getLogger(__name__)


def create_bulkload_stream(client: Client, **kwargs):
    schema = kwargs.get("schema", client.schema)
    table = kwargs.get("table")
    if schema is None:
        schema = client.schema
    if schema is None:
        raise ValueError(f"No schema specified")
    if table is None:
        raise ValueError(f"No table specified")

    operation_str = kwargs.get("operation", "APPEND")
    bulk_operation = BulkLoadOperation.OVERWRITE
    if operation_str == "APPEND":
        bulk_operation = BulkLoadOperation.APPEND
    elif operation_str == "OVERWRITE":
        bulk_operation = BulkLoadOperation.OVERWRITE
    elif operation_str == "UPSERT":
        bulk_operation = BulkLoadOperation.UPSERT

    partition_spec = kwargs.get("partition_spec")
    record_keys = kwargs.get("record_keys")
    prefer_internal_endpoint = kwargs.get("prefer_internal_endpoint", False)

    bulkload_meta_data = client.create_bulkload_stream(
        schema,
        table,
        BulkLoadOptions(
            bulk_operation, partition_spec, record_keys, prefer_internal_endpoint
        ),
    )

    return bulkload_meta_data.bulkload_stream


def create_bulkload_stream_metadata(
        client: Client, schema_name: Optional[str], table_name: Optional[str], options: BulkLoadOptions
) -> BulkLoadMetaData:
    """Create bulkload stream metadata.

    Args:
        client: ClickZetta client
        schema_name: Schema name
        table_name: Table name
        options: BulkLoadOptions with operation, partition specs, record keys
        
    Returns:
        BulkLoadMetaData object
    """
    stream_id = client.generate_job_id()
    info = BulkLoadStreamInfo(None, schema_name, table_name, client.workspace, options, stream_id)
    return BulkLoadMetaData(client.instance_id, info)


def create_bulkload_stream_by_metadata(bulkload_meta_data, client: Client,
                                       commit_options: BulkLoadCommitOptions = None,
                                       max_rows_threshold: int = 1000000,
                                       auto_prepare_interval_seconds: int = 60) -> BulkLoadStream:
    """Create bulkload stream v1 by metadata."""
    return BulkLoadStream(bulkload_meta_data, client, commit_options, max_rows_threshold, auto_prepare_interval_seconds)


def commit_bulkload_stream(
        client: Client,
        instance_id: int,
        workspace: str,
        schema_name: str,
        table_name: str,
        stream_id: str,
        execute_workspace: str,
        execute_vc: str,
        commit_mode,
):
    stream: BulkLoadStream = client.get_bulkload_stream(schema_name, table_name, stream_id)
    commit_options = BulkLoadCommitOptions(
        workspace, execute_vc
    )
    stream.commit(commit_options)
    return stream.meta_data


def get_bulkload_stream_metadata(
    client: Client, schema_name: str, table_name: str, stream_id: str
) -> BulkLoadMetaData:
    return client.get_bulkload_stream(schema_name, table_name, stream_id)


def get_bulkload_stream(
    client: Client, stream_id: str, schema: str = None, table: str = None
):
    """Get bulkload stream v1."""
    bulkload_meta_data = client.get_bulkload_stream(schema, table, stream_id)
    return bulkload_meta_data.get_v1_stream()

def open_bulkload_stream_writer(
    client: Client,
    instance_id: int,
    workspace: str,
    schema_name: str,
    table_name: str,
    stream_id: str,
    partition_id: int,
):
    stream = get_bulkload_stream(client, stream_id, schema_name, table_name)
    writer = stream.open_writer(partition_id)
    return BulkLoadConfig(writer=writer)



def finish_bulkload_stream_writer(
    client: Client,
    instance_id: int,
    workspace: str,
    schema_name: str,
    table_name: str,
    stream_id: str,
    partition_id: int,
    written_files: list,
    written_lengths: list,
):
    stream = get_bulkload_stream(client, stream_id, schema_name, table_name)
    stream.close()
    return BulkLoadState.COMMIT_SUCCESS
