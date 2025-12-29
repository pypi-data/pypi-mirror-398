import logging
import os
import threading
import time
import uuid
from contextlib import contextmanager
from typing import Dict, Any, List, Optional, Collection, Tuple, Set

from clickzetta import connect
from clickzetta.connector.v0.connection import Connection
from clickzetta.connector.v0.cursor import Cursor
from clickzetta.connector.v0.utils import try_with_finally
from clickzetta_ingestion.bulkload.bulkload_context import FieldSchema
from clickzetta_ingestion.bulkload.bulkload_committer import CommitRequestHolder, CommitResultHolder
from clickzetta_ingestion.bulkload.bulkload_conf import BulkLoadConf, BulkLoadFileConf
from clickzetta_ingestion.bulkload.bulkload_conf import BulkLoadOperation
from clickzetta_ingestion.bulkload.bulkload_handler import AbstractBulkLoadHandler
from clickzetta_ingestion.bulkload.committable import Committable
from clickzetta_ingestion.common.tools import (
    Dispatcher,
    CompositeCleanupHandler
)
from clickzetta_ingestion.bulkload.storage.csv_format import CsvFormat
from clickzetta_ingestion.bulkload.storage.file_options import FormatInterface
from clickzetta_ingestion.bulkload.storage.parquet_format import IcebergParquetFormat
from clickzetta_ingestion.bulkload.storage.text_format import TextFormat
from clickzetta_ingestion.bulkload.table_parser import TableParser, BulkLoadTable
from clickzetta_ingestion.common.loading_cache import LoadingCache
from clickzetta_ingestion.common.row import Row as ArrowRow
from clickzetta_ingestion.rpc import arrow_utils


class TableCacheKey:
    """Cache key for table metadata - combines connection URL, schema, and table name."""

    def __init__(self, connection_url: str, schema_name: str, table_name: str,
                 bulk_load_conf: BulkLoadConf, properties: Dict[str, Any]):
        self.connection_url = connection_url
        self.schema_name = schema_name
        self.table_name = table_name
        self.bulk_load_conf = bulk_load_conf
        self.properties = properties

    def __eq__(self, other) -> bool:
        if not isinstance(other, TableCacheKey):
            return False
        return (self.connection_url == other.connection_url and
                self.schema_name == other.schema_name and
                self.table_name == other.table_name)

    def __hash__(self) -> int:
        return hash((self.connection_url, self.schema_name, self.table_name))

    def __str__(self) -> str:
        return f"TableCacheKey({self.connection_url}, {self.schema_name}, {self.table_name})"


class BulkLoadHandler(AbstractBulkLoadHandler[Committable]):
    """bulkload handler implementation using ClickZetta connection."""

    # Static table cache
    _table_cache: Optional[LoadingCache] = None
    _bulkload_handler_lock = threading.Lock()

    def __init__(self, connection_url: str, properties: Optional[Dict[str, Any]] = None):
        self._connection_url = connection_url
        self._properties = properties or {}
        self._bulk_load_conf: Optional[BulkLoadConf] = None
        self._initialized = False
        self._lock = threading.Lock()

        # SQL properties for connection configuration
        self._sql_properties: Optional[Dict[str, str]] = None

        self._table_meta_connection: Optional[Connection] = None
        self._query_connection: Optional[Connection] = None

        # Auto file index
        self._file_index = 0
        self._file_index_lock = threading.Lock()

        # Dispatcher for async cleanup operations
        self._cleanup_dispatcher: Optional[Dispatcher] = None
        self._cleanup_handler: Optional[CompositeCleanupHandler] = None

        self._logger = logging.getLogger(__name__)

    def _close_connection_internal(self, connection: Any):
        """Close connection internal."""
        try:
            if connection:
                connection.close()
        except Exception as e:
            raise RuntimeError(f"Failed to close connection: {e}")

    def _open_connection_internal(self, connection_url: str, properties: Dict[str, Any],
                                  config: Optional[Dict[str, str]] = None) -> Connection:
        connection = None
        try:
            from clickzetta.connector.v0.parse_url import parse_url
            (
                service,
                username,
                driver_name,
                password,
                instance,
                workspace,
                vcluster,
                schema,
                magic_token,
                protocol,
                host,
                port,
                token_expire_time_ms,
                query,
            ) = parse_url(connection_url)

            service = host if port is None or port == -1 else f"{host}:{port}"

            if properties:
                # Extract lakehouse service
                if properties.get("lh_service") is not None:
                    lakehouse_instance = properties.get("lh_service")
                    self._logger.info(f"lakehouseInstance from property: {lakehouse_instance}")
                    service = lakehouse_instance

                # Extract username (check both 'username' and 'user')
                if properties.get("username") is not None:
                    username = properties.get("username")
                    self._logger.info(f"username from property: {username}")
                elif properties.get("user") is not None:
                    username = properties.get("user")
                    self._logger.info(f"user from property: {username}")

                if properties.get("schema") is not None:
                    schema = properties.get("schema")
                    self._logger.info(f"schema from property: {schema}")
                if properties.get("vcluster") is not None:
                    vcluster = properties.get("vcluster")
                    self._logger.info(f"vcluster from property: {vcluster}")
                if properties.get("workspace") is not None:
                    workspace = properties.get("workspace")
                    self._logger.info(f"workspace from property: {workspace}")

                # Extract password
                if properties.get("password") is not None:
                    password = properties.get("password")
                    self._logger.info("password from property: ********")

                # Extract use_object_store_https
                if properties.get("use_object_store_https") is not None:
                    use_object_store_https = str(properties.get("use_object_store_https")).lower() == 'true'
                    self._logger.info(f"use_object_store_https from property: {use_object_store_https}")
                    # Store this flag for potential use in connection configuration

            # Override VC if specified in bulk load conf
            vc = vcluster
            if self._bulk_load_conf and self._bulk_load_conf.get_connection_vc():
                vc = self._bulk_load_conf.get_connection_vc()

            # Create connection using parsed values
            connection = connect(
                username=username,
                password=password,
                service=service,
                instance=instance,
                workspace=workspace,
                schema=schema,
                vcluster=vc,
                protocol=protocol
            )

            # Apply SQL configuration hints if provided
            if config and connection:
                cursor = connection.cursor()
                for key, value in config.items():
                    cursor.execute(f"SET {key}={value}")
                cursor.close()

            return connection

        except Exception as e:
            try:
                self._close_connection_internal(connection)
            except:
                pass  # Ignore close errors
            raise RuntimeError(f"Failed to open connection: {e}")

    def _get_sql_properties(self) -> Dict[str, str]:
        """Get SQL properties as map."""
        config: Dict[str, str] = {}
        if self._sql_properties:
            config.update(self._sql_properties)
        return config

    def _check_opened(self):
        """Check if handler is properly opened."""
        if not self._initialized:
            raise RuntimeError("JdbcBulkLoadHandler is not opened yet")
        if not self._table_meta_connection or not self._query_connection:
            raise RuntimeError("Connections are not initialized")

    def _lazy_init_cleanup_dispatcher(self):
        """Lazy initialize cleanup dispatcher."""
        if self._cleanup_dispatcher is None:
            with self._lock:
                if self._cleanup_dispatcher is None:
                    self._cleanup_dispatcher = Dispatcher()
                    # Create cleanup handler with query connection supplier
                    self._cleanup_handler = CompositeCleanupHandler(
                        self._cleanup_dispatcher,
                        lambda: self._query_connection
                    )
                    # Start dispatcher
                    self._cleanup_dispatcher.start()
                    self._logger.debug("Cleanup dispatcher initialized and started")

    def _post_file_cleanup(self, transaction_id: str, files: List[str]):
        """Post file cleanup event."""
        if self._cleanup_handler and files:
            try:
                self._cleanup_handler.post_file_cleanup(transaction_id, files)
                self._logger.debug(f"Posted file cleanup event for transaction {transaction_id}: {len(files)} files")
            except Exception as e:
                self._logger.warning(f"Failed to post file cleanup event: {e}")

    def _post_sql_cleanup(self, transaction_id: str, sql: str):
        """Post SQL cleanup event."""
        if self._cleanup_handler and sql:
            try:
                self._cleanup_handler.post_sql_cleanup(transaction_id, sql)
                self._logger.debug(f"Posted SQL cleanup event for transaction {transaction_id}")
            except Exception as e:
                self._logger.warning(f"Failed to post SQL cleanup event: {e}")

    def _close_cleanup_dispatcher(self):
        """Close cleanup dispatcher."""
        try:
            if self._cleanup_handler:
                self._cleanup_handler.unregister()
                self._cleanup_handler = None

            if self._cleanup_dispatcher:
                self._cleanup_dispatcher.stop()
                self._cleanup_dispatcher = None
                self._logger.debug("Cleanup dispatcher stopped")
        except Exception as e:
            self._logger.error(f"Error closing cleanup dispatcher: {e}")

    def open(self, conf):
        """Open the handler and initialize connections."""
        with BulkLoadHandler._bulkload_handler_lock:
            if self._initialized:
                return

            self._bulk_load_conf = conf
            # Initialize SQL properties
            self._sql_properties = conf.get_sql_properties()

            # Initialize static table cache
            if BulkLoadHandler._table_cache is None:
                BulkLoadHandler._table_cache = LoadingCache(
                    loader=self._get_table_internal_loader,
                    max_size=128
                )

            # Open table metadata connection
            self._table_meta_connection = self._open_connection_internal(
                self._connection_url, self._properties, self._sql_properties)

            # Open query connection  
            self._query_connection = self._open_connection_internal(
                self._connection_url, self._properties, self._sql_properties)

            # Initialize cleanup dispatcher
            self._lazy_init_cleanup_dispatcher()

            self._initialized = True
            self._logger.info(f"JdbcBulkLoadHandler {self} open success.")

    def _get_table_internal_loader(self, cache_key: TableCacheKey) -> BulkLoadTable:
        """
        This function gets called by LoadingCache when a key is not found in cache.
        """
        return self._get_table_internal(
            cache_key.connection_url,
            cache_key.schema_name,
            cache_key.table_name,
            cache_key.properties,
            cache_key.bulk_load_conf
        )

    def get_target_table(self, schema_name: str, table_name: str) -> BulkLoadTable:
        """
        Get target table information using LoadingCache
        """
        self._check_opened()

        try:
            # Create cache key
            cache_key = TableCacheKey(
                self._connection_url,
                schema_name,
                table_name,
                self._bulk_load_conf,
                self._properties
            )
            return BulkLoadHandler._table_cache.get(cache_key)

        except Exception as e:
            self._logger.error(f"Error getting target table {schema_name}.{table_name}: {e}")
            raise

    def _get_table_internal(self, connection_url: str, schema_name: str, table_name: str,
                            properties: Dict[str, Any], bulk_load_conf: BulkLoadConf) -> BulkLoadTable:
        """
        Internal method to get table information from ClickZetta
        """

        if not schema_name or not table_name or not connection_url:
            raise RuntimeError("get table meta with null string %s.%s using jdbcUrl: %s"
                               .format(schema_name, table_name, connection_url))

        # All table config in get table internal
        get_table_config = {
            'sdk.job.timeout': str(bulk_load_conf.get_sql_timeout())
        }

        try:
            # Open connection with table config
            with self._open_connection_internal_context(connection_url, properties, get_table_config) as conn:
                show_create_sql = f"SHOW CREATE TABLE `{schema_name}`.`{table_name}`"
                show_create_result = self._execute_query_with_connection(conn, show_create_sql)

                if not show_create_result or len(show_create_result) == 0:
                    raise RuntimeError(f"get show create table result empty for {schema_name}.{table_name}")
                if len(show_create_result[0]) > 1 and not show_create_result[0][0].lower().startswith("create "):
                    create_table_sql = show_create_result[0][1]
                else:
                    create_table_sql = show_create_result[0][0]
                if not create_table_sql or create_table_sql.strip() == "":
                    raise RuntimeError(f"show create table result is empty for {schema_name}.{table_name}")

                # Also get DESC EXTENDED for additional metadata
                desc_sql = f"DESC EXTENDED `{schema_name}`.`{table_name}`"
                desc_result = self._execute_query(conn, desc_sql)

                if not desc_result:
                    raise RuntimeError(f"get desc extended result empty for {schema_name}.{table_name}")

                # Parse using table parser
                if self._bulk_load_conf.get_show_create_table():
                    raise NotImplementedError("Parsing SHOW CREATE TABLE antlr4 based parser is not implemented yet")
                return self._get_table_by_parser(schema_name, table_name, create_table_sql, desc_result, bulk_load_conf)

        except Exception as e:
            self._logger.error(f"Error in getTableInternal for {schema_name}.{table_name}: {e}")
            raise RuntimeError(f"Failed to get table internal for {schema_name}.{table_name}: {e}")

    @contextmanager
    def _open_connection_internal_context(self, jdbc_url: str, properties: Dict[str, Any], config: Dict[str, str]):
        """Context manager for opening connection with config"""
        connection = None
        try:
            connection = self._open_connection_internal(jdbc_url, properties, config)
            yield connection
        finally:
            if connection:
                self._close_connection_internal(connection)

    def _execute_query_with_connection(self, connection: Any, sql: str) -> List[tuple]:
        """Execute query with specific connection."""
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            self._logger.error(f"Error executing SQL '{sql}': {e}")
            raise

    def _get_table_by_parser(self, schema_name: str, table_name: str, show_create_table_sql: str,
                             desc_result: List[Tuple[Any, ...]],
                             bulk_load_conf: BulkLoadConf) -> BulkLoadTable:
        """
        Parse table using SQL parser
        """
        try:
            # Use the TableParser to parse the CREATE TABLE SQL
            parser = TableParser()

            # Parse SHOW CREATE TABLE for column definitions and constraints
            # partition_key_indices is start with 0
            (table_type, field_schemas, name_to_id_map, primary_key_indices, partition_key_indices,
             partial_update_columns, generated_columns) = parser.parse_table_metadata(
                describe_extended_result=desc_result, show_create_table_result=show_create_table_sql)

            # check table type and get table type or partition type if used upsert for pk.
            if bulk_load_conf.get_bulk_load_options().get_operation() == BulkLoadOperation.UPSERT:
                # Check bulkload options first
                record_keys:List[str] = bulk_load_conf.get_bulk_load_options().get_record_keys()
                if record_keys and len(record_keys) > 0:
                    primary_key_indices.clear()
                    for record_key in record_keys:
                        record_key_lower = record_key.lower()
                        if record_key_lower not in name_to_id_map:
                            raise RuntimeError(f"recordKey [{record_key}] not exists in table schema.")
                        primary_key_indices.append(name_to_id_map[record_key_lower])
                    table_type = "ACID"

                # Add partial update support - filter field schemas if needed
                partial_update_column_names = bulk_load_conf.get_bulk_load_options().get_partial_update_columns()
                if partial_update_column_names and len(partial_update_column_names) > 0:
                    sub_primary_key = []
                    sub_partition_key = []
                    sub_partial_update_columns = []

                    # Validate partial update columns exist in schema
                    for partial_update_column in partial_update_column_names:
                        partial_update_column_lower = partial_update_column.lower()
                        if partial_update_column_lower not in name_to_id_map:
                            raise RuntimeError(
                                f"partialUpdateColumn [{partial_update_column}] not exists in table schema.")
                        if partial_update_column_lower not in sub_partial_update_columns:
                            sub_partial_update_columns.append(partial_update_column_lower)

                    # Build column name lists for primary key and partition key
                    sub_primary_key.extend([field_schemas[i].name.lower() for i in primary_key_indices])
                    sub_partition_key.extend([field_schemas[i].name.lower() for i in partition_key_indices])

                    # Create required columns set
                    required_columns = set()
                    required_columns.update(sub_primary_key)
                    required_columns.update(sub_partition_key)
                    required_columns.update(sub_partial_update_columns)

                    # Filter field schemas to only include required columns
                    field_schemas = [fs for fs in field_schemas
                                     if fs.name.lower() in required_columns]

                    # Rebuild name-to-index mapping and remark indices
                    name_to_id_map.clear()
                    for i, field_schema in enumerate(field_schemas):
                        name_to_id_map[field_schema.name.lower()] = i

                    # Rebuild primary key, partition key, and partial update column indices
                    primary_key_indices.clear()
                    partition_key_indices.clear()
                    partial_update_columns.clear()

                    primary_key_indices.extend([name_to_id_map[key] for key in sub_primary_key])
                    partition_key_indices.extend([name_to_id_map[key] for key in sub_partition_key])
                    partial_update_columns.extend([name_to_id_map[col] for col in sub_partial_update_columns])

            # Parse partition specs if provided in bulk load conf
            partition_spec_values = []
            if bulk_load_conf.get_partition_specs():
                partition_spec_values = self._get_partition_spec_values(
                    field_schemas, partition_key_indices, bulk_load_conf.get_partition_specs()
                )

            # reset field_schemas nullable
            for idx in primary_key_indices:
                if 0 <= idx < len(field_schemas):
                    field_schemas[idx].nullable = False

            return BulkLoadTable(
                table_type=table_type,
                schema_name=schema_name,
                table_name=table_name,
                field_schemas=field_schemas,
                primary_key_indices=primary_key_indices,  # primaryKey
                partition_key_indices=partition_key_indices,  # partitionKey
                partition_spec_values=partition_spec_values,  # partitionSpecValues
                partial_update_column_indices=partial_update_columns,  # equivalent + partial update
                generated_columns=generated_columns or []  # generatedColumns
            )

        except Exception as e:
            self._logger.error(f"Error parsing table schema for {schema_name}.{table_name}: {e}")
            raise RuntimeError(f"Failed to parse table schema: {e}")

    def _get_partition_spec_values(self, field_schemas: List[FieldSchema],
                                   partition_key_indices: List[int], partition_specs: str) -> List[object]:
        """
        Get partition spec values
        """
        try:
            partition_spec_values = self._parse_partition_spec_values_sql(field_schemas, partition_specs)
            return [partition_spec_values.get(field_schemas[idx].name.lower())
                    for idx in partition_key_indices]
        except Exception as e:
            self._logger.warning(f"Error parsing partition specs: {e}")
            return []

    def _parse_partition_spec_values_sql(self, field_schemas: List[FieldSchema], partition_spec: str) -> Dict[
        str, object]:
        """
        Parse partition specification SQL
        """
        result = {}

        try:
            if '=' in partition_spec:
                # Remove common SQL keywords and clean up
                cleaned_spec = partition_spec.replace('PARTITION', '').replace('(', '').replace(')', '').strip()

                pairs = []
                current_pair = ""
                in_quotes = False
                quote_char = None

                # Parse while respecting quotes
                for char in cleaned_spec:
                    if char in ['"', "'"] and not in_quotes:
                        in_quotes = True
                        quote_char = char
                        current_pair += char
                    elif char == quote_char and in_quotes:
                        in_quotes = False
                        quote_char = None
                        current_pair += char
                    elif char == ',' and not in_quotes:
                        pairs.append(current_pair.strip())
                        current_pair = ""
                    else:
                        current_pair += char

                if current_pair.strip():
                    pairs.append(current_pair.strip())

                # Process each key=value pair
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        # Remove quotes from value
                        if (value.startswith('"') and value.endswith('"')) or \
                                (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]

                        # Find the field schema for this partition column
                        field = None
                        for field_schema in field_schemas:
                            if field_schema.name.lower() == key.lower():
                                field = field_schema
                                break

                        if not field:
                            raise RuntimeError(f"Partition column '{key}' not found in table schema.")
                        # Convert value using type-aware conversion
                        converted_value = arrow_utils.convert_to_field_type(field.type, value)
                        result[key.lower()] = converted_value

        except Exception as e:
            self._logger.warning(f"Error parsing partition spec '{partition_spec}': {e}")

        return result

    def _execute_query(self, connection: Any, sql: str) -> List[tuple]:
        """Execute a SQL query and return results."""
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            self._logger.error(f"Error executing SQL '{sql}': {e}")
            raise

    def _execute_query_with_hints(self, cursor: Cursor, sql: str, hints: Optional[Dict[str, str]] = None) -> List[
        tuple]:
        """
        Execute a SQL query with hints and return results.
        """
        try:
            # Apply hints if provided (Python SDK uses parameters for hints)
            if hints:
                cursor.execute(sql, parameters={'hints': hints})
            else:
                cursor.execute(sql)

            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            self._logger.error(f"Error executing SQL '{sql}' with hints {hints}: {e}")
            raise

    def generate_next_committable(self, request: BulkLoadFileConf.Request) -> BulkLoadFileConf.Response[Committable]:
        """Generate next committable for file operations."""
        self._check_opened()

        if request.uri().startswith("file://") or request.uri().startswith("objectstore_local://"):
            with self._file_index_lock:
                file_index = self._file_index
                self._file_index += 1

            file_name = f"{request.prefix()}_{uuid.uuid4()}_{int(time.time() * 1000)}_{file_index}.{request.format()}"
            path = f"{request.base_path()}/{request.partition()}/{file_name}"

            # Normalize path
            normalized_path = os.path.normpath(path)

            return BulkLoadFileConf.Response(
                path=normalized_path,
                file_properties={},
                committable=Committable(
                    committable_type=Committable.Type.LOCAL_FILE,
                    path=normalized_path
                )
            )
        else:
            raise NotImplementedError(
                "Not support uri with objectstore:// use objectstore_local:// instead."
            )

    def prepare_commit(self, commit_request_holder: CommitRequestHolder[Committable],
                       commit_result_holder: CommitResultHolder):
        """Prepare commit request with commit result."""
        self._check_opened()

        # Get the first committable
        committables = commit_request_holder.get_committables()
        if not committables:
            return

        committable: Committable = committables[0]

        # If dst path already set, just skip put file
        if committable.get_dst_path() and commit_request_holder.get_table_name() in committable.get_dst_path():
            return

        committable_type = committable.get_type()

        if committable_type == Committable.Type.LOCAL_FILE:
            self._put_local_file_to_table_volume(commit_request_holder, commit_result_holder)
        else:
            raise NotImplementedError("Only support LOCAL_FILE committable type for now.")

    def _put_local_file_to_table_volume(self, commit_request_holder: CommitRequestHolder[Committable],
                                        commit_result_holder: CommitResultHolder):
        """Put local file to table volume using real ClickZetta connection."""
        committables = commit_request_holder.get_committables()

        # Get target conf from committable
        outside_conf = {}
        for committable in committables:
            if committable and committable.get_conf():
                outside_conf.update(committable.get_conf())

        # Generate configuration SQL
        conf_set_sql = self._generate_conf_set_sql(outside_conf)

        # Add internal endpoint configuration if needed
        if self._bulk_load_conf and self._bulk_load_conf.is_prefer_internal_endpoint():
            conf_set_sql = "set cz.sql.volume.file.transfer.force.external=false;\n" + conf_set_sql

        # Combine SQL statements
        final_sql = conf_set_sql + "\n" + self._generate_put_local_file_sql(
            commit_request_holder.get_transaction_id(),
            commit_request_holder.get_schema_name(),
            commit_request_holder.get_table_name(),
            [c.get_path() for c in committables]
        )

        try:
            # Log file information for debugging
            file_paths = [c.get_path() for c in committables]
            total_file_size = 0
            file_info_list = []
            for path in file_paths:
                try:
                    import os
                    file_size = os.path.getsize(path)
                    total_file_size += file_size
                    file_info_list.append(f"{os.path.basename(path)}({file_size} bytes)")
                except:
                    file_info_list.append(f"{path}(size unknown)")

            self._logger.info(
                f"Preparing to upload {len(file_paths)} file(s), "
                f"total size: {total_file_size} bytes, "
                f"transaction_id: {commit_request_holder.get_transaction_id()}"
            )
            self._logger.debug(f"File details: {', '.join(file_info_list)}")

            self._logger.info(f"Executing put local file SQL: {final_sql}")
            hints = self._get_sql_properties()
            cursor = self._query_connection.cursor()
            try:
                result = self._execute_query_with_hints(cursor, final_sql, hints)

                # Parse result to get file mappings
                local_to_target_volume_files = {}
                if result:
                    for row in result:
                        if len(row) >= 3:
                            local_file = row[0]
                            volume_file = row[1]
                            status = row[2]

                            if status == "FAILED":
                                raise RuntimeError(
                                    f"put local file [{local_file}] to table volume [{volume_file}] failed.")
                            # localFile may not be lowerCase & volumeFile must be lowerCase.
                            local_to_target_volume_files[local_file] = volume_file

                # Set dst path for committables
                for committable in committables:
                    local_file = committable.get_path()
                    target_volume_file = local_to_target_volume_files.get(local_file.lower())
                    if not target_volume_file:
                        raise RuntimeError(
                            "local file [%s] put to table volume [%s] with empty target volume file.".format(
                                committable.get_path(), commit_request_holder.get_table_name()))
                    committable.set_dst_path(target_volume_file)
            finally:
                commit_result_holder.set_commit_id(cursor.get_job_id())

        except Exception as e:
            self._logger.error(f"Error putting local file to table volume: {e}")
            raise RuntimeError(f"Failed to put local file to table volume: {e}")
        finally:
            # Schedule local file cleanup if enabled
            if self._bulk_load_conf and self._bulk_load_conf.get_enable_local_file_cleanup():
                local_files = [c.get_path() for c in committables if c.get_path()]
                if local_files:
                    self._post_file_cleanup(commit_request_holder.get_transaction_id(), local_files)

    def commit(self, commit_request_holder: CommitRequestHolder[Committable],
               commit_result_holder: CommitResultHolder) -> str:
        """Commit request and return transactionId with commit result."""
        self._check_opened()

        committables = commit_request_holder.get_committables()

        # Get target conf from committable
        outside_conf = {}
        for committable in committables:
            if committable and committable.get_conf():
                outside_conf.update(committable.get_conf())

        # Generate configuration SQL
        conf_set_sql = self._generate_conf_set_sql(outside_conf)

        # Check if primary key table
        schema_name = commit_request_holder.get_schema_name()
        table_name = commit_request_holder.get_table_name()
        table: BulkLoadTable = self.get_target_table(schema_name, table_name)

        is_pk_upsert = False
        operator_type = ""

        operation = self._bulk_load_conf.get_bulk_load_options().get_operation()
        if operation == "APPEND":
            operator_type = "INTO"
        elif operation == "OVERWRITE":
            operator_type = operation
        else:  # UPSERT
            is_pk_upsert = True

        final_sql = None
        committable_type = committables[0].get_type()

        if committable_type == Committable.Type.LOCAL_FILE:
            # Merge all table volume subdirectory files
            sub_dir_files = set()
            for committable in committables:
                if committable:
                    if committable.get_dst_path():
                        sub_dir_files.add(committable.get_dst_path())
                    else:
                        raise RuntimeError(
                            f"Committable dstPath is empty for local file: {committable.get_path()}")

            # Generate final commit SQL
            file_format = self._bulk_load_conf.get_load_format().lower() if self._bulk_load_conf.get_load_format() else "parquet"

            if not is_pk_upsert:
                copy_sql = self._generate_copy_table_volume_sql(
                    table, sub_dir_files, commit_request_holder.get_table_name(),
                    operator_type, file_format,
                    self._bulk_load_conf.get_enable_purge_file() if self._bulk_load_conf else False
                )
                final_sql = conf_set_sql + "\n" + copy_sql
            else:
                final_sql = self._generate_merge_into_sql(table, file_format, sub_dir_files)

        if final_sql:
            final_sql = final_sql.strip()
            self._logger.info(f"Final commit SQL: {final_sql}")

        cursor = self._query_connection.cursor()
        job_id = None
        try:
            # Execute the commit SQL
            if final_sql:
                # Log detailed commit information for debugging
                self._logger.info(
                    f"Executing commit for table {table.schema_name}.{table.table_name}, "
                    f"operation={operation}, "
                    f"num_files={len(committables)}, "
                    f"file_format={file_format if 'file_format' in locals() else 'N/A'}, "
                    f"is_pk_upsert={is_pk_upsert}"
                )

                # Log table structure for troubleshooting
                column_info = []
                for col_name, col_type in table.get_column_types_map().items():
                    column_info.append(f"{col_name}:{col_type}")
                self._logger.info(f"Table columns: {', '.join(column_info)}")

                hints = self._get_sql_properties()
                result = self._execute_query_with_hints(cursor, final_sql, hints)
                job_id = cursor.get_job_id()
                self._logger.info(f"Commit SQL executed successfully: {result}, job_id: {job_id}")

            # Schedule table volume cleanup if enabled
            if self._bulk_load_conf and self._bulk_load_conf.get_enable_table_volume_cleanup():
                self._schedule_table_volume_cleanup(commit_request_holder, job_id)

            return job_id

        except Exception as e:
            self._logger.error(f"Error executing commit SQL: {e}")
            raise RuntimeError(f"Failed to execute commit SQL: {e}")
        finally:
            commit_result_holder.set_commit_id(job_id)

    def listen(self, job_id: str, commit_result_holder: CommitResultHolder):
        """Listen target transactionId with commit result."""
        self._check_opened()

        if not job_id:
            commit_result_holder.set_failed(f"No job_id provided.")
            return

        try:
            with self._query_connection.cursor() as cursor:
                is_job_finished = cursor.is_job_finished(job_id)

                if is_job_finished:
                    result = cursor.get_result_set(job_id)
                    from clickzetta.connector.v0.client import Client
                    if result and Client.verify_result_dict_finished(result):
                        commit_result_holder.set_succeed()
                    else:
                        commit_result_holder.set_failed(f"${cursor.get_job_status().get_error_message()}")

        except Exception as e:
            self._logger.error(f"Error listening to job_id {job_id}: {e}")
            raise RuntimeError(f"Failed to listen to job_id {job_id}: {e}")

    def abort(self, transaction_id: str, commit_request_holder: CommitRequestHolder[Committable]):
        """Abort transactionId which maybe not exists & use commit request to clean up."""
        self._check_opened()

        try:
            # Try to cancel the job if it exists
            try:
                with self._query_connection.cursor() as cursor:
                    cursor.cancel(transaction_id)
                    self._logger.info(f"Successfully cancelled job: {transaction_id}")
            except Exception as cancel_error:
                self._logger.warning(f"Failed to cancel job {transaction_id}: {cancel_error}")

            # Schedule table volume cleanup for abort
            if self._bulk_load_conf and self._bulk_load_conf.get_enable_table_volume_cleanup():
                self._schedule_table_volume_cleanup(commit_request_holder, transaction_id)

            self._logger.info(f"Aborted transaction with cleanup: {transaction_id}")
        except Exception as e:
            self._logger.error(f"Error aborting transaction with cleanup {transaction_id}: {e}")
            raise RuntimeError(f"Failed to abort transaction {transaction_id}: {e}")

    def abort_job(self, transaction_id: str, commit_result_holder: CommitResultHolder):
        """Abort job by transaction ID only (without cleanup)."""
        self._check_opened()

        try:
            with self._query_connection.cursor() as cursor:
                cursor.cancel(transaction_id)
                self._logger.info(f"Successfully cancelled job: {transaction_id}")
                commit_result_holder.set_abort()
        except Exception as e:
            self._logger.error(f"Error cancelling job {transaction_id}: {e}")
            commit_result_holder.set_failed(f"Failed to cancel job: {e}")
            raise RuntimeError(f"Failed to cancel job {transaction_id}: {e}")

    def _schedule_table_volume_cleanup(self, commit_request_holder: CommitRequestHolder[Committable],
                                       transaction_id: str):
        """Schedule table volume cleanup."""
        try:
            # Collect subdirectory files from committables
            sub_dir_files = set()
            for committable in commit_request_holder.get_committables():
                if committable and committable.get_dst_path():
                    sub_dir_files.add(committable.get_dst_path())

            if sub_dir_files:
                cleanup_sql = self._generate_cleanup_table_volume_sql(
                    commit_request_holder.get_schema_name(),
                    commit_request_holder.get_table_name(),
                    sub_dir_files
                )
                self._post_sql_cleanup(transaction_id, cleanup_sql)

        except Exception as e:
            self._logger.warning(f"Failed to schedule table volume cleanup! Skip to cleanup. err: {e}")

    def _generate_cleanup_table_volume_sql(self, schema_name: str, table_name: str, sub_files: Set[str]) -> str:
        """Generate cleanup SQL for table volume files."""
        try:
            if not sub_files:
                return ""

            # Create REGEXP pattern
            pattern = "|".join(sub_files)
            cleanup_sql = f"REMOVE TABLE VOLUME `{schema_name}`.`{table_name}` REGEXP '{pattern}'"
            return cleanup_sql.lower()
        except Exception as e:
            self._logger.warning(f"Error generating cleanup SQL: {e}")
            return ""

    def close(self):
        """Close the bulkload handler."""
        with self._lock:
            if not self._initialized:
                return

            self._initialized = False

        # Always try to clean up resources even if exceptions occur
        cleanup_errors = []

        # Clean up table cache
        try:
            if BulkLoadHandler._table_cache:
                BulkLoadHandler._table_cache.invalidate_all()
        except Exception as e:
            cleanup_errors.append(f"Table cache cleanup error: {e}")

        # Clean up dispatcher (most important for thread cleanup)
        try:
            self._close_cleanup_dispatcher()
        except Exception as e:
            cleanup_errors.append(f"Dispatcher cleanup error: {e}")

        # Clean up connections
        try:
            try_with_finally(
                lambda: self._close_connection(self._table_meta_connection),
                lambda: self._close_connection(self._query_connection)
            )
        except Exception as e:
            cleanup_errors.append(f"Connection cleanup error: {e}")

        if cleanup_errors:
            self._logger.warning(f"Cleanup errors during close: {cleanup_errors}")
        else:
            self._logger.info(f"JdbcBulkLoadHandler {self} close success.")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False  # Don't suppress exceptions

    def get_target_format(self, table: BulkLoadTable) -> FormatInterface[ArrowRow]:
        """Get target format for the table."""
        if not self._bulk_load_conf:
            raise RuntimeError("BulkLoadConf not set")

        # Create format based on load_format (case-insensitive comparison)
        load_format_upper = self._bulk_load_conf.get_load_format().upper()

        # Initialize with static partition value filling
        def fill_partition_callable(row):
            self._fill_static_partition_value(table, row)
            return row

        if load_format_upper == "PARQUET":
            internal_format = IcebergParquetFormat(
                table,
                self._bulk_load_conf.get_complex_type_pre_check(),
                self._bulk_load_conf.get_cz_bitmap_type_check()
            )

            internal_format.init_input_format(fill_partition_callable)
            format_instance = internal_format

        elif load_format_upper in ["JSON", "TEXT"]:
            internal_format = TextFormat(table)
            internal_format.init_input_format(fill_partition_callable)
            format_instance = internal_format
            raise NotImplementedError(f"not support format: {load_format_upper}")

        elif load_format_upper == "CSV":
            internal_format = CsvFormat(table)
            internal_format.init_input_t_format(fill_partition_callable)
            format_instance = internal_format
            raise NotImplementedError(f"not support format: {load_format_upper}")
        else:
            raise NotImplementedError(f"not support format: {load_format_upper}")

        return format_instance

    def _fill_static_partition_value(self, bulk_load_table: BulkLoadTable, row):
        """
        Fill static partition values for IcebergRow. Only support static partition.
        The dynamic partition should be written by the writer.

        Args:
            bulk_load_table: BulkLoadTable with partition information
            row: IcebergRow to fill with partition values
        """
        try:
            partition_keys = bulk_load_table.get_partition_key_names()
            partition_values = bulk_load_table.get_partition_spec_values()

            if (partition_keys and partition_values and
                    len(partition_keys) > 0 and len(partition_values) > 0):

                # Fill static partition values
                for i in range(min(len(partition_keys), len(partition_values))):
                    partition_key = partition_keys[i]
                    partition_value = partition_values[i]

                    if partition_value is not None:
                        row.set_value(partition_key, partition_value)
        except Exception as e:
            self._logger.warning(f"Error filling static partition values for IcebergRow: {e}")

    def _close_connection(self, connection):
        """Close a ClickZetta connection."""
        if connection:
            try:
                connection.close()
            except Exception as e:
                self._logger.warning(f"Error closing connection: {e}")

    def _generate_conf_set_sql(self, conf: Dict[str, str]) -> str:
        """Generate configuration set SQL."""
        conf_set_sql = (
            "set cz.sql.allow.insert.table.with.pk=true;\n"
            "set cz.sql.copy.write.history.table.enabled=false;\n"
            "set cz.storage.parquet.enable.read.vector.from.binary=true;\n"
        )

        if conf:
            for key, value in conf.items():
                conf_set_sql += f"set {key}={value};\n"

        return conf_set_sql.lower()

    def _generate_put_local_file_sql(self, request_transaction_id: str, schema_name: str, table_name: str,
                                     file_list: Collection[str]) -> str:
        """Generate put local file to table volume SQL."""
        if not file_list:
            raise ValueError("file_list must not be empty")

        max_parallel = min(
            len(file_list),
            self._bulk_load_conf.get_max_put_parallel(),
        )

        return (
            f"""PUT '{"','".join(file_list)}' TO TABLE VOLUME `{schema_name}`.`{table_name}` """
            f"SUBDIRECTORY '{request_transaction_id}' PARALLEL = {max_parallel};"
        ).lower()

    def _generate_copy_table_volume_sql(self, table: BulkLoadTable, sub_dir_files: set,
                                        table_name: str, operator_type: str, format: str,
                                        purge_enable: bool) -> str:
        """Generate copy table volume SQL."""
        (target_fields, table_volume_source_fields) = BulkLoadHandler._get_special_type_convert(table)
        return (
            f"COPY {operator_type} `{table.schema_name}`.`{table_name}` "
            f"FROM "
            f"  ("
            f"      SELECT "
            f"      {target_fields} "
            f"      FROM TABLE VOLUME `{table.schema_name}`.`{table_name}`{table_volume_source_fields} "
            f"""    USING {format} FILES ('{"','".join(sub_dir_files)}')"""
            f") PURGE = {str(purge_enable)};"
        ).lower()

    @staticmethod
    def _get_special_type_convert(table: BulkLoadTable) -> Tuple[str, str]:
        """
        Get special type conversion for target fields and table volume source fields.
        
        Returns:
            Tuple of (target_fields, table_volume_source_fields)
        """
        target_fields = "*"
        table_volume_source_fields = ""

        # Get original column types map and special column names
        column_types_map = table.get_column_types_map()
        # Python does not need special_column conversion, only Java has column name conversion issues,
        # this is retained in case it is needed in the future
        special_column_names_map = table.get_special_column_names()

        # Convert DataType objects to string representation for comparison
        column_type_map = {col_name: str(data_type).lower() for col_name, data_type in column_types_map.items()}

        # Check if we need special handling
        contains_bitmap_type = "bitmap" in column_type_map.values()
        has_generated_columns = bool(table.get_generated_columns())
        has_special_column_names = bool(special_column_names_map)

        if contains_bitmap_type or has_generated_columns or has_special_column_names:
            # Reuse original column types map if special column names map is empty
            if not special_column_names_map:
                special_column_names_map = {col: col for col in column_type_map.keys()}

            target_field_to_types = []
            table_volume_field_to_types = []

            for column_name, column_type_str in column_type_map.items():
                special_name = special_column_names_map.get(column_name, column_name)

                if column_type_str != "bitmap":
                    target_field_to_types.append(f"`{special_name}` as `{column_name}`")
                    table_volume_field_to_types.append(f"`{special_name}` {column_type_str}")
                else:
                    target_field_to_types.append(f"RB64_TO_BITMAP(`{special_name}`) AS `{column_name}`")
                    table_volume_field_to_types.append(f"`{special_name}` binary")

            target_fields = ", ".join(target_field_to_types)
            table_volume_source_fields = f"({', '.join(table_volume_field_to_types)})"

        return target_fields, table_volume_source_fields

    @staticmethod
    def _generate_merge_into_sql(table: BulkLoadTable, file_format: str,
                                 sub_dir_files: set) -> str:
        """
        Generate merge into SQL.

        Example:
            set cz.sql.allow.insert.table.with.pk=true;
            set cz.sql.copy.write.history.table.enabled=false;
            set cz.storage.parquet.enable.read.vector.from.binary=true;
            copy into `meta_warehouse`.`liulei_tmp_test_partition_table_1` from   (      select       `col1` as `col1`, `col2` as `col2`, `col3` as `col3`, `col4` as `col4`, `col5` as `col5`       from table volume `meta_warehouse`.`liulei_tmp_test_partition_table_1`(`col1` int, `col2` int, `col3` string, `col4` string, `col5` string)     using parquet files ('default-stream-id_20ae1193a74d4bb68116fe7b6e944f39_1764661476573_1/bulkload_44c4b295-263e-4515-840b-24fc197437d8_1764661476564_1.parquet','default-stream-id_20ae1193a74d4bb68116fe7b6e944f39_1764661476573_1/bulkload_7d2324a6-b5f5-498d-b1c4-df8402419586_1764661476504_0.parquet')) purge = true;
        """
        if not table.get_primary_key_names():
            raise ValueError("Generate merge into sql must have primary key.")

        table_name = table.get_table_name()
        
        # Get special type conversion for target fields and table volume source fields
        # This handles bitmap types, generated columns, and special column names
        (target_fields, table_volume_source_fields) = BulkLoadHandler._get_special_type_convert(table)
        
        # Use target_fields as the select column from volume
        select_column_from_volume = target_fields

        # Build primary key conditions
        primary_key_conditions = []
        for pk_name in table.get_primary_key_names():
            primary_key_conditions.append(f"DST.`{pk_name}` = SRC.`{pk_name}`")

        # Build update, source, and insert conditions
        update_conditions = []
        source_conditions = []
        insert_conditions = []

        for column_name in table.get_column_names():
            update_conditions.append(f"DST.`{column_name}` = SRC.`{column_name}`")
            source_conditions.append(f"SRC.`{column_name}`")
            insert_conditions.append(f"`{column_name}`")

        primary_key = " AND ".join(primary_key_conditions)
        update_column_name = ", ".join(update_conditions)
        source_column_name = ", ".join(source_conditions)
        insert_column_name = ", ".join(insert_conditions)

        merge_sql = (
            f"MERGE INTO `{table.schema_name}`.`{table_name}` AS DST USING "
            f"("
            f"SELECT {select_column_from_volume} FROM TABLE VOLUME "
            f"`{table.schema_name}`.`{table_name}`{table_volume_source_fields} "
            f"""USING {file_format} FILES ('{"','".join(sub_dir_files)}')
            ) SRC """
            f"ON {primary_key} "
            f"WHEN MATCHED THEN UPDATE SET {update_column_name} "
            f"WHEN NOT MATCHED THEN INSERT ({insert_column_name}) VALUES ({source_column_name});"
        )

        return merge_sql.lower()

    def count_table(self, schema_name: str, table_name: str) -> int:
        """
        Count records in table.
        
        Args:
            schema_name: Schema name
            table_name: Table name
            
        Returns:
            Number of records in table
        """
        self._check_opened()

        count_sql = f"SELECT COUNT(1) FROM `{schema_name}`.`{table_name}`"
        count = 0

        try:
            cursor = self._query_connection.cursor()
            cursor.execute(count_sql)
            result = cursor.fetchone()
            if result:
                count = int(result[0])
            cursor.close()
        except Exception as e:
            self._logger.warning(f"Error counting table {schema_name}.{table_name}: {e}")

        return count

    def truncate_table(self, schema_name: str, table_name: str):
        """
        Truncate table.
        
        Args:
            schema_name: Schema name
            table_name: Table name
        """
        self._check_opened()

        truncate_sql = f"TRUNCATE TABLE `{schema_name}`.`{table_name}`"

        try:
            cursor = self._query_connection.cursor()
            cursor.execute(truncate_sql)
            cursor.close()
            self._logger.info(f"Successfully truncated table: {schema_name}.{table_name}")
        except Exception as e:
            self._logger.warning(f"Error truncating table {schema_name}.{table_name}: {e}")

    def function_table(self, sql_query: str, properties: Dict[str, Any],
                       caller: callable) -> None:
        """
        Execute SQL query and call function with result set.
        
        Args:
            sql_query: SQL query to execute
            properties: Query properties (hints)
            caller: Function to call with result set
        """
        self._check_opened()

        try:
            cursor = self._query_connection.cursor()

            # Apply properties as hints if provided
            if properties:
                for key, value in properties.items():
                    cursor.execute(f"SET {key}={value}")

            # Execute the main query
            cursor.execute(sql_query)

            # Call the function with the result set
            # The caller function should handle fetching results
            caller(cursor.fetchall())

            cursor.close()

        except Exception as e:
            self._logger.warning(f"Error executing query '{sql_query}': {e}")
            raise
