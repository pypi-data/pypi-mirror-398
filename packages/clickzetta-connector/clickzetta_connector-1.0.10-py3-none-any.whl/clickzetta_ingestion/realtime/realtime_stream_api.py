from logging import getLogger

from clickzetta.connector.v0.client import Client
from clickzetta.connector.v0.enums import RealtimeOperation
from clickzetta_ingestion.realtime import realtime_options
from clickzetta_ingestion.realtime.realtime_options import CZSessionOptions
from clickzetta_ingestion.realtime.realtime_stream import RealtimeStream

log = getLogger(__name__)

IGS_TABLET_NUM = "igs.tablet.num"


def create_realtime_stream(client: Client, **kwargs) -> "RealtimeStream":
    schema = kwargs.get("schema", client.schema)
    table = kwargs.get("table")
    if schema is None:
        schema = client.schema
    if schema is None:
        raise ValueError("No schema specified")
    if table is None:
        raise ValueError("No table specified")

    operate: RealtimeOperation = kwargs.get("operate") or RealtimeOperation.CDC
    options: CZSessionOptions = kwargs.get("options") or realtime_options.DEFAULT
    if "tablet" in kwargs:
        options.properties[IGS_TABLET_NUM] = kwargs.get("tablet") or 1

    arrow_stream = client.igs_client.create_arrow_row_stream(client, schema, table, options, operate)

    return RealtimeStream(
        meta_data=arrow_stream.meta_data,
        client=client,
        operation=operate,
        arrow_table=arrow_stream.arrow_table,
        arrow_stream=arrow_stream
    )
