"""
Load options for BulkLoad V2 storage operations.
"""
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from clickzetta_ingestion.bulkload.storage.file_options import Format


class LoadOptions:
    """
    Options for loading data in BulkLoad operations.
    """

    def __init__(self, uri: str, format_type: "Format" = None,
                 file_name_prefix='load',
                 max_row_count=100 * 1000,
                 max_file_size=128 * 1024 * 1024,  # 128MB default
                 properties: Optional[Dict[str, Any]] = None):
        """
        Initialize load options.
        
        Args:
            uri: URI for storage location
            format_type: Data format type
            properties: Additional properties
        """
        self._uri = uri
        if format_type is None:
            from clickzetta_ingestion.bulkload.storage.file_options import Format
            format_type = Format.PARQUET
        self._format = format_type
        self._file_name_prefix = file_name_prefix
        self._max_row_count = max_row_count
        self._max_file_size = max_file_size
        self._properties = properties or {}

    def get_uri(self) -> str:
        """Get the URI."""
        return self._uri

    def get_format(self) -> "Format":
        """Get the format type."""
        return self._format

    def get_file_name_prefix(self) -> str:
        """Get the file name prefix."""
        return self._file_name_prefix

    def get_max_row_count(self) -> int:
        """Get the maximum row count per file."""
        return self._max_row_count

    def get_max_file_size(self) -> int:
        """Get the maximum file size in bytes."""
        return self._max_file_size

    def get_properties(self) -> Dict[str, Any]:
        """Get all properties."""
        return self._properties.copy()

    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a specific property."""
        return self._properties.get(key, default)

    def set_property(self, key: str, value: Any):
        """Set a property."""
        self._properties[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for compatibility."""
        return {
            'uri': self._uri,
            'format': self._format.name,
            'properties': self._properties.copy()
        }

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'LoadOptions':
        """
        Create LoadOptions from dictionary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            LoadOptions instance
        """
        uri = config.get('uri', '')
        format_str = config.get('format', 'PARQUET').upper()
        format_type = Format[format_str]
        properties = config.get('properties', {})

        return cls(uri, format_type, properties)
