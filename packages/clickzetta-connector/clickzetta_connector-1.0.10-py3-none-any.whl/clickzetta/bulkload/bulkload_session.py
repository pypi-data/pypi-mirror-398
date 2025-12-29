from typing import Any, Dict, Optional, Union

from clickzetta.bulkload import bulkload_api
from clickzetta.bulkload.bulkload_enums import BulkLoadOptions
from clickzetta.bulkload.bulkload_stream import BulkLoadStream
from clickzetta.connector.v0.client import Client


class Session:
    """V1 Session API with V2 implementation.
    """
    
    class SessionBuilder:
        """Builder for creating Session instances."""
        
        def __init__(self) -> None:
            self._options = {}

        def _remove_config(self, key: str) -> "Session.SessionBuilder":
            self._options.pop(key, None)
            return self

        def config(self, key: str, value: Union[int, str]) -> "Session.SessionBuilder":
            """Set a single configuration option.
            
            Args:
                key: Configuration key
                value: Configuration value
                
            Returns:
                Self for method chaining
            """
            self._options[key] = value
            return self

        def configs(
            self, options: Dict[str, Union[int, str]]
        ) -> "Session.SessionBuilder":
            """Set multiple configuration options.
            
            Args:
                options: Dictionary of configuration options
                
            Returns:
                Self for method chaining
            """
            self._options = {**self._options, **options}
            return self

        def create(self) -> "Session":
            """Create a Session instance with the configured options.
            
            Returns:
                Configured Session instance
            """
            session = self._create_internal(self._options.get("url"))
            return session

        def _create_internal(self, conn: str = None) -> "Session":
            """Internal method to create a Session instance.
            
            Args:
                conn: Connection URL
                
            Returns:
                Session instance
            """
            new_session = Session(
                conn,
                self._options,
            )
            return new_session

        def __get__(self, obj, objtype=None):
            return Session.SessionBuilder()

    builder: SessionBuilder = SessionBuilder()

    def __init__(self, conn: str, options: Optional[Dict[str, Any]] = None) -> None:
        """Initialize Session with connection URL and options.
        
        Args:
            conn: ClickZetta connection URL
            options: Additional session options
        """
        self._client = Client(cz_url=conn)

    def create_bulkload_stream(self, schema_name: str, table_name: str, options: BulkLoadOptions):
        """Create a new bulkload stream.
        
        Args:
            schema_name: Schema name
            table_name: Table name
            options: BulkLoadOptions with operation, partition specs, record keys
            
        Returns:
            BulkLoadStream instance with V1 API
        """
        bulkload_meta_data = bulkload_api.create_bulkload_stream_metadata(
            self._client, schema_name, table_name, options
        )
        stream = BulkLoadStream(bulkload_meta_data, self._client)
        bulkload_meta_data.bulkload_stream = stream
        self._client.set_v1_stream_meta(bulkload_meta_data)
        return stream

    def commit_bulkload_stream(
        self,
        instance_id: int,
        workspace: str,
        schema_name: str,
        table_name: str,
        stream_id: str,
        execute_workspace: str,
        execute_vc: str,
        commit_mode,
    ):
        return bulkload_api.commit_bulkload_stream(
            self._client,
            instance_id,
            workspace,
            schema_name,
            table_name,
            stream_id,
            execute_workspace,
            execute_vc,
            commit_mode,
        )

    def get_bulkload_stream(self, schema_name: str, table_name: str, stream_id: str):
        """Get a bulkload stream v1."""
        bulkload_meta_data = bulkload_api.get_bulkload_stream(
            self._client, schema_name, table_name, stream_id
        )
        return bulkload_meta_data.get_v1_stream()

    def close(self):
        """Close the session and release resources."""
        return
