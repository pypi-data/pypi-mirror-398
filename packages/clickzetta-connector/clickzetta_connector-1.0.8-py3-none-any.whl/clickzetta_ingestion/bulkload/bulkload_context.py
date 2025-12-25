from dataclasses import dataclass


class BulkLoadContext:
    def __init__(self, schema_name: str = None, table_name: str = None, stream_id: str = None, partition_id: int = -1):
        self.schema_name = schema_name
        self.table_name = table_name
        self.stream_id = stream_id
        self.partition_id = partition_id


@dataclass
class FieldSchema:
    def __init__(self, name: str, field_type: str, nullable: bool = True):
        self.name = name
        self.type = field_type
        self.nullable = nullable
