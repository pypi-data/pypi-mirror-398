import string


class CZTable:
    def __init__(self, table_meta, schema_name: string, table_name: string):
        self.schema_name = schema_name
        self.table_name = table_name
        self.table_meta = table_meta
        self.schema = {}
        if table_meta:
            fields = table_meta.data_fields
            for field in fields:
                self.schema[field.name] = field.field_type
