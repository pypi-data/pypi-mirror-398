import copy
import logging
import string
from enum import Enum
from typing import List, Optional

from pyarrow import fs

from clickzetta.bulkload.cz_table import CZTable
from clickzetta.connector.v0._dbapi import Field
from clickzetta_ingestion.bulkload.bulkload_context import FieldSchema

logger = logging.getLogger(__name__)

MAX_NUM_ROWS_PER_FILE = 64 << 20
MAX_FILE_SIZE_IN_BYTES_PER_FILE = 256 << 20


class FileFormatType(Enum):
    TEXT = 'text'
    PARQUET = 'parquet'
    ORC = 'orc'
    AVRO = 'avro'
    CSV = 'csv'
    ARROW = 'arrow'
    HIVE_RESULT = 'hive_result'
    DUMMY = 'dummy'
    MEMORY = 'memory'
    ICEBERG = 'iceberg'


class StagingConfig:
    def __init__(self, path: string, id: string, secret: string, token: string, endpoint: string, type: None):
        self.path = path
        self.id = id
        self.secret = secret
        self.token = token
        self.endpoint = endpoint
        self.type = type

    def create_file_io(self):
        return fs.LocalFileSystem()


class BulkLoadConfig:
    def __init__(self, config=None, writer=None):
        self.config = config
        self.writer = writer

    def get_staging_config(self, prefer_internal_endpoint=False):
        return None

    def get_file_format(self):
        return FileFormatType.PARQUET

    def get_max_rows_per_file(self):
        return MAX_NUM_ROWS_PER_FILE

    def get_max_file_size_per_file(self):
        return MAX_FILE_SIZE_IN_BYTES_PER_FILE


class BulkLoadOperation(Enum):
    APPEND = 1
    UPSERT = 2
    OVERWRITE = 3


class BulkLoadState(Enum):
    CREATED = 1
    SEALED = 2
    COMMIT_SUBMITTED = 3
    COMMIT_SUCCESS = 4
    COMMIT_FAILED = 5
    ABORTED = 6


class BulkLoadOptions:
    def __init__(self, operation: BulkLoadOperation, partition_specs: Optional[str], record_keys=None,
                 prefer_internal_endpoint=False, load_uri=None) -> None:
        if record_keys is None:
            record_keys = {}
        self.operation = operation
        self.partition_specs = partition_specs
        self.record_keys = record_keys
        self.prefer_internal_endpoint = prefer_internal_endpoint
        self._properties = {'operation': operation, 'partition_specs': partition_specs, 'record_keys': record_keys,
                            'prefer_internal_endpoint': prefer_internal_endpoint}
        self.load_uri = load_uri


    def to_api_repr(self) -> dict:
        return copy.deepcopy(self._properties)


class StreamSchema:
    def __init__(self, data_fields: List[Field]):
        self.data_fields = data_fields


class TableIdentifier:
    def __init__(self, schema_name: str, table_name: str, workspace: str) -> None:
        self.schema_name = schema_name
        self.table_name = table_name
        self.workspace = workspace


class BulkLoadStreamInfo:
    DEFAULT_STREAM_ID = "default-stream-id"

    def __init__(self, stream_schema, schema_name, table_name, workspace, options: BulkLoadOptions, stream_id: Optional[str] = None):
        self.stream_id = stream_id or BulkLoadStreamInfo.DEFAULT_STREAM_ID
        self.identifier = TableIdentifier(schema_name, table_name, workspace)
        self.stream_schema = stream_schema
        self.options = options
        self.stream_state = BulkLoadState.CREATED
        if self.options:
            self.partition_spec = options.partition_specs
            self.prefer_internal_endpoint = options.prefer_internal_endpoint
            self.record_keys = options.record_keys
        else:
            self.partition_specs = None
            self.prefer_internal_endpoint = False
            self.record_keys = None


class BulkLoadMetaData:
    def __init__(self, instance_id: int, info):
        self.instance_id = instance_id
        self.info: BulkLoadStreamInfo = info
        self.bulkload_stream = None
        self.table: Optional[CZTable] = None
        if info.options and info.options.load_uri:
            self.load_uri = info.options.load_uri
        else:
            # Set default local storage path
            import tempfile
            import os
            self.load_uri = os.path.join(tempfile.gettempdir(), "clickzetta_bulkload")

    def get_instance_id(self):
        return self.instance_id

    def get_workspace(self):
        return self.info.identifier.workspace

    def get_schema_name(self):
        return self.info.identifier.schema_name

    def get_table_name(self):
        return self.info.identifier.table_name

    def get_v1_stream(self):
        return self.bulkload_stream

    def get_v2_stream(self):
        if self.bulkload_stream:
            return self.bulkload_stream.get_v2_stream()
        else:
            return None

    def get_stream_id(self):
        return self.info.stream_id

    def get_table(self):
        if self.bulkload_stream is None:
            logger.error("Cannot get bulkload stream. Should have been created")
            return None
        if self.table is None:
            temp_writer = self.bulkload_stream.open_writer(0)
            bulkload_v2_table = temp_writer.get_table()
            field_schemas: List[FieldSchema] = bulkload_v2_table.get_table_schema()
            data_fields = [Field(name=schema.name, field_type=schema.type, nullable=schema.nullable) for schema in
                           field_schemas]
            table_meta = StreamSchema(data_fields)
            self.table = CZTable(table_meta, self.get_schema_name(), self.get_table_name())
        return self.table

    def get_prefer_internal_endpoint(self):
        return self.info.prefer_internal_endpoint

    def get_operation(self):
        if self.info.options:
            return self.info.options.operation
        else:
            return BulkLoadOperation.OVERWRITE

    def get_state(self):
        return self.info.stream_state

    def get_sql_error_msg(self):
        return None

    def get_partition_specs(self):
        return self.info.partition_spec

    def get_record_keys(self):
        record_keys = []
        for key in self.info.record_keys:
            record_keys.append(key)

        return record_keys

    def get_load_uri(self):
        return self.load_uri


class BulkLoadCommitOptions:
    def __init__(self, workspace: string, vc: string):
        self.workspace = workspace
        self.vc = vc


class BulkLoadCommitMode(Enum):
    COMMIT_STREAM = 1
    ABORT_STREAM = 2
