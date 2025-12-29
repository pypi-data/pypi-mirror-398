from typing import Dict, Any, Optional, List, Generic, TypeVar
from clickzetta_ingestion.common.configure import Configure

C = TypeVar('C')

class BulkLoadOperation:
    """BulkLoad operation types."""
    APPEND = "APPEND"
    OVERWRITE = "OVERWRITE"
    UPSERT = "UPSERT"


class BulkLoadOptions:
    """Options to create BulkLoadStream for bulk load."""
    
    def __init__(self, operation: str, partition_specs: Optional[str] = None, 
                 record_keys: Optional[List[str]] = None, partial_update_columns: Optional[List[str]] = None,
                 prefer_internal_endpoint: bool = False, properties: Optional[Dict[str, Any]] = None):
        self._operation = operation
        self._partition_specs = partition_specs
        self._record_keys = record_keys or []
        self._partial_update_columns = partial_update_columns or []
        self._prefer_internal_endpoint = prefer_internal_endpoint
        self._properties = properties or {}
    
    def get_operation(self) -> str:
        """Supported operations: APPEND, UPSERT, OVERWRITE."""
        return self._operation
    
    def get_partition_specs(self) -> Optional[str]:
        """
        Static partition specs.
        
        e.g. "ds=20230101" or "ds=20230101,hh=9,mm=30"
        If not provided, dynamic partition is applied.
        """
        return self._partition_specs
    
    def get_record_keys(self) -> List[str]:
        """
        Names of field that uniquely identify a record.
        Used by COPY command for UPSERT.
        """
        return self._record_keys
    
    def get_partial_update_columns(self) -> List[str]:
        """Columns to be updated in partial update operations."""
        return self._partial_update_columns
    
    def is_prefer_internal_endpoint(self) -> bool:
        """
        Whether to use internal endpoint to write data on the cloud object store.
        
        If true, the bulk load will be sent to internal endpoint.
        If false, the bulk load will be sent to external endpoint.
        
        Default value is false.
        """
        return self._prefer_internal_endpoint
    
    def get_configure(self) -> Configure:
        """Get Conf Set ini Options."""
        return Configure(self._properties)
    
    @staticmethod
    def new_builder():
        """Create a new builder instance."""
        return BulkLoadOptions.Builder()
    
    class Builder:
        """Builder for BulkLoadOptions."""
        
        def __init__(self):
            self._operation = BulkLoadOperation.APPEND
            self._partition_specs = None
            self._record_keys = []
            self._partial_update_columns = []
            self._prefer_internal_endpoint = False
            self._properties = {}
        
        def with_operation(self, operation: str):
            """Set the operation type."""
            self._operation = operation
            return self
        
        def with_partition_specs(self, partition_specs: Optional[str]):
            """Set the partition specs."""
            self._partition_specs = partition_specs
            return self
        
        def with_record_keys(self, record_keys: List[str]):
            """Set the record keys."""
            self._record_keys = record_keys
            return self
        
        def with_partial_update_columns(self, partial_update_columns: List[str]):
            """Set the partial update columns."""
            self._partial_update_columns = partial_update_columns
            return self
        
        def with_prefer_internal_endpoint(self, prefer_internal_endpoint: bool):
            """Set whether to prefer internal endpoint."""
            self._prefer_internal_endpoint = prefer_internal_endpoint
            return self
        
        def with_properties(self, key: str, value: Any):
            """Add a property."""
            self._properties[key] = value
            return self
        
        def with_properties_dict(self, properties: Dict[str, Any]):
            """Add multiple properties."""
            if properties:
                self._properties.update(properties)
            return self
        
        def _validate(self):
            """Validate the configuration."""
            if self._operation == BulkLoadOperation.UPSERT and not self._record_keys:
                raise ValueError("recordKeys must be provided for UPSERT operation")
            if self._operation != BulkLoadOperation.UPSERT and self._partial_update_columns:
                raise ValueError("partialUpdateColumns only provided for UPSERT operation")
        
        def build(self):
            """Build the BulkLoadOptions instance."""
            self._validate()
            return BulkLoadOptions(
                operation=self._operation,
                partition_specs=self._partition_specs,
                record_keys=self._record_keys,
                partial_update_columns=self._partial_update_columns,
                prefer_internal_endpoint=self._prefer_internal_endpoint,
                properties=self._properties
            )


class BulkLoadCommitOptions:
    """Options for bulkload commit operations."""
    
    def __init__(self, vc: str, workspace: Optional[str] = None, access_token: Optional[str] = None):
        self._vc = vc
        self._workspace = workspace
        self._access_token = access_token
    
    def get_vc(self) -> str:
        """Get the virtual cluster."""
        return self._vc
    
    def get_workspace(self) -> Optional[str]:
        """Get the workspace."""
        return self._workspace
    
    def get_access_token(self) -> Optional[str]:
        """Get the access token."""
        return self._access_token
    
    @staticmethod
    def new_builder():
        """Create a new builder instance."""
        return BulkLoadCommitOptions.Builder()
    
    class Builder:
        """Builder for BulkLoadCommitOptions."""
        
        def __init__(self):
            self._vc = None
            self._workspace = None
            self._access_token = None
        
        def with_vc(self, vc: str):
            """Set the virtual cluster."""
            self._vc = vc
            return self
        
        def with_workspace(self, workspace: str):
            """Set the workspace."""
            self._workspace = workspace
            return self
        
        def with_access_token(self, access_token: str):
            """Set the access token."""
            self._access_token = access_token
            return self
        
        def _validate(self):
            """Validate the configuration."""
            if not self._vc:
                raise ValueError("vc is required")
        
        def build(self):
            """Build the BulkLoadCommitOptions instance."""
            self._validate()
            return BulkLoadCommitOptions(
                vc=self._vc,
                workspace=self._workspace,
                access_token=self._access_token
            )


class BulkLoadConf:
    """Configuration for bulkload operations"""
    
    # Base conf prefix
    CONF_PREFIX = "cz.bulkload."
    
    # SQL conf prefix
    SQL_CONF_PREFIX = CONF_PREFIX + "sql."
    
    # Object store conf prefix
    OBJECTSTORE_CONF_PREFIX = "objectstore."
    
    # Base bulkLoad conf constants
    PREFER_INTERNAL_ENDPOINT = CONF_PREFIX + "prefer.internal.endpoint"
    
    # Connection URL for ClickZetta (Python SDK format)
    CONNECTION_URL = CONF_PREFIX + "connection.url"
    CONNECTION_VC = CONF_PREFIX + "connection.vc"
    CONNECTION_WORKSPACE = CONF_PREFIX + "connection.workspace"
    
    LOAD_FORMAT = CONF_PREFIX + "load.format"
    LOAD_URI = CONF_PREFIX + "load.uri"
    LOAD_PREFIX = CONF_PREFIX + "load.prefix"
    
    MAX_FILE_SIZE = CONF_PREFIX + "max.file.size"
    MAX_ROW_COUNT = CONF_PREFIX + "max.row.count"
    
    ENABLE_FILE_PURGE = CONF_PREFIX + "file.purge.enable"
    MAX_PUT_PARALLEL = CONF_PREFIX + "max.put.parallel"
    ENABLE_LOCAL_FILE_CLEANUP = CONF_PREFIX + "local.file.cleanup.enable"
    ENABLE_TABLE_VOLUME_CLEANUP = CONF_PREFIX + "table.volume.cleanup.enable"
    ENABLE_COMPLEX_TYPE_PRE_CHECK = CONF_PREFIX + "complex.type.precheck.enable"
    ENABLE_CZ_BITMAP_TYPE_CHECK = CONF_PREFIX + "cz.bitmap.type.enable"
    
    GET_SHOW_CREATE_TABLE = CONF_PREFIX + "get.show.create.table"

    def __init__(self, options: BulkLoadOptions):
        """
        Initialize BulkLoadConf with BulkLoadOptions. Only wrap options here, and options properties is mutable.
        
        Args:
            options: BulkLoadOptions instance containing the configuration
        """
        self.options = options
        self.conf = options.get_configure()
        
        # Create property shortcuts for common access patterns
        self.load_format = self.get_load_format()
        self.load_uri = self.get_load_uri()
        self.load_prefix = self.get_load_prefix()
        self.max_file_size = self.get_max_file_size()
        self.max_row_count = self.get_max_row_count()
        self.properties = self.get_properties()

    # Adapt bulkLoad v1 options
    def get_operation(self) -> str:
        """Get the bulk load operation type."""
        return self.options.get_operation()

    def get_partition_specs(self) -> Optional[str]:
        """Get partition specifications."""
        return self.options.get_partition_specs()

    def get_record_keys(self) -> List[str]:
        """Get record keys for UPSERT operations."""
        return self.options.get_record_keys()

    def get_partial_update_columns(self) -> List[str]:
        """Get partial update columns for UPSERT operations."""
        return self.options.get_partial_update_columns()

    def is_prefer_internal_endpoint(self) -> bool:
        """Check if internal endpoint is preferred."""
        return self.options.is_prefer_internal_endpoint() or self.conf.get_bool(
            self.PREFER_INTERNAL_ENDPOINT, False)

    # BulkLoad v2 options
    def get_connection_url(self) -> str:
        """
        Get the ClickZetta connection URL.
        
        Returns the connection URL in Python SDK format:
        clickzetta://username:password@host:port/workspace?virtualcluster=default&schema=public&magic_token=xxx&protocol=https
        """
        return self.conf.get_str(self.CONNECTION_URL, "")

    def get_connection_vc(self) -> str:
        """Get the virtual cluster for SQL connection."""
        return self.conf.get_str(self.CONNECTION_VC, "")

    def get_connection_workspace(self) -> str:
        """Get the workspace for SQL connection."""
        return self.conf.get_str(self.CONNECTION_WORKSPACE, "")

    def get_sql_properties(self) -> Dict[str, Any]:
        """Get SQL-related properties with SQL prefix."""
        return self.conf.get_properties(self.SQL_CONF_PREFIX, self.SQL_CONF_PREFIX, "")

    def get_load_format(self) -> str:
        """Get the load format (default: parquet)."""
        return self.conf.get_str(self.LOAD_FORMAT, "parquet")

    def get_load_uri(self) -> str:
        """Get the load URI (default: objectstore_local://)."""
        return self.conf.get_str(self.LOAD_URI, "objectstore_local://")

    def get_load_prefix(self) -> str:
        """Get the load prefix (default: bulkload)."""
        return self.conf.get_str(self.LOAD_PREFIX, "bulkload")

    def get_max_file_size(self) -> int:
        """Get maximum file size in bytes (default: 64MB)."""
        return self.conf.get_int(self.MAX_FILE_SIZE, 64 * 1024 * 1024)

    def get_max_row_count(self) -> int:
        """Get maximum row count per file (default: 1,000,000)."""
        return self.conf.get_int(self.MAX_ROW_COUNT, 1000 * 1000)

    def get_enable_purge_file(self) -> bool:
        """Check if file purging is enabled (default: True)."""
        return self.conf.get_bool(self.ENABLE_FILE_PURGE, True)

    def get_max_put_parallel(self) -> int:
        """Get maximum parallel PUT operations (default: 8)."""
        return self.conf.get_int(self.MAX_PUT_PARALLEL, 8)

    def get_enable_local_file_cleanup(self) -> bool:
        """Check if local file cleanup is enabled (default: True)."""
        return self.conf.get_bool(self.ENABLE_LOCAL_FILE_CLEANUP, True)

    def get_enable_table_volume_cleanup(self) -> bool:
        """Check if table volume cleanup is enabled (default: True)."""
        return self.conf.get_bool(self.ENABLE_TABLE_VOLUME_CLEANUP, True)

    def get_complex_type_pre_check(self) -> bool:
        """Check if complex type pre-check is enabled (default: True)."""
        return self.conf.get_bool(self.ENABLE_COMPLEX_TYPE_PRE_CHECK, True)

    def get_cz_bitmap_type_check(self) -> bool:
        """Check if complex type pre-check is enabled (default: True)."""
        return self.conf.get_bool(self.ENABLE_CZ_BITMAP_TYPE_CHECK, True)

    def get_show_create_table(self) -> bool:
        """Check if show create table is enabled (default: False)."""
        return self.conf.get_bool(self.GET_SHOW_CREATE_TABLE, False)

    def get_properties(self) -> Dict[str, Any]:
        """Get all properties from the configuration."""
        return self.conf.get_properties()

    def get_bulk_load_options(self) -> BulkLoadOptions:
        """Get the original BulkLoadOptions instance."""
        return self.options

    def get_sql_timeout(self) -> int:
        """Get SQL timeout in seconds (default: 300)."""
        return self.conf.get_int("cz.sql.timeout", 300)


class BulkLoadFileConf:
    """Configuration for bulkload file operations."""

    class Request:
        """Request for file operations."""

        def __init__(self, partition: int = 0, uri: str = "", base_path: str = "",
                     prefix: str = "", format_name: str = ""):
            self._partition = partition
            self._uri = uri
            self._base_path = base_path
            self._prefix = prefix
            self._format = format_name

        def partition(self) -> int:
            return self._partition

        def uri(self) -> str:
            return self._uri

        def base_path(self) -> str:
            return self._base_path

        def prefix(self) -> str:
            return self._prefix

        def format(self) -> str:
            return self._format

    class Response(Generic[C]):
        """Response for file operations."""

        def __init__(self, path: str, file_properties: dict = None, committable: C = None):
            self.path = path
            self.file_properties = file_properties or {}
            self._committable = committable

        def properties(self) -> dict:
            """Backward compatibility method."""
            return self.file_properties

        def committable(self) -> C:
            return self._committable