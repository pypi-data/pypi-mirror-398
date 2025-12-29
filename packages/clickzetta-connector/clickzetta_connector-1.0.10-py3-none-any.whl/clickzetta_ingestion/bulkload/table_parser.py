from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Dict, Tuple, Any

from clickzetta_ingestion.bulkload.bulkload_context import FieldSchema


class IGSTableType:
    NORMAL = "NORMAL"
    ACID = "ACID"


@dataclass
class BulkLoadTable:
    """Bulkload table information."""
    table_type: str
    schema_name: str
    table_name: str
    field_schemas: List[FieldSchema]
    primary_key_indices: List[int]
    partition_key_indices: List[int]
    partition_spec_values: List[object]
    partial_update_column_indices: List[int]
    generated_columns: List[FieldSchema]

    def __post_init__(self):
        self.column_names = [field.name for field in self.field_schemas]
        self.column_names_map = {field.name: i for i, field in enumerate(self.field_schemas)}
        self.column_types_map = {field.name: field.type for field in self.field_schemas}
        self.primary_key_names = [self.field_schemas[i].name for i in self.primary_key_indices]
        self.partition_key_names = [self.field_schemas[i].name for i in self.partition_key_indices]
        self.partial_update_column_names = [self.field_schemas[i].name for i in self.partial_update_column_indices]
        self.special_column_names = {field.name: BulkLoadTable.make_compatible_name(field.name) for field in
                                     self.field_schemas}

    def get_table_type(self) -> str:
        return self.table_type

    def get_igs_table_type(self) -> str:
        return self.table_type

    def get_schema_name(self) -> str:
        return self.schema_name

    def get_table_name(self) -> str:
        return self.table_name

    def get_table_schema(self) -> List[FieldSchema]:
        return self.field_schemas

    def get_primary_key_indices(self) -> List[int]:
        return self.primary_key_indices

    def get_partition_key_indices(self) -> List[int]:
        return self.partition_key_indices

    def get_partition_spec_values(self) -> List[object]:
        return self.partition_spec_values

    def get_partition_static_value(self) -> List[object]:
        return self.partition_spec_values

    def get_partial_update_column_indices(self) -> List[int]:
        return self.partial_update_column_indices

    def get_generated_columns(self) -> List[FieldSchema]:
        return self.generated_columns

    def get_column_names(self) -> List[str]:
        return self.column_names

    def get_column_names_map(self) -> Dict[str, int]:
        return self.column_names_map

    def get_column_types_map(self) -> Dict[str, str]:
        return self.column_types_map

    def get_primary_key_names(self) -> List[str]:
        return self.primary_key_names

    def get_partition_key_names(self) -> List[str]:
        return self.partition_key_names

    def get_partial_update_columns(self) -> List[str]:
        return self.partial_update_column_names

    def get_special_column_names(self) -> Dict[str, str]:
        return self.special_column_names

    @staticmethod
    def make_compatible_name(name: str) -> str:
        """Convert any string to a valid Avro name with optimal performance."""
        return name
        # if not name or (not name[0].isalpha() and name[0] != '_'):
        #     needs_sanitization = True
        # else:
        #     needs_sanitization = False
        #     for char in name[1:]:
        #         if not (char.isalnum() or char == '_'):
        #             needs_sanitization = True
        #             break
        #
        # if not needs_sanitization:
        #     return name
        #
        # def sanitize_char(c: str) -> str:
        #     if c.isalpha() or c == '_':
        #         return c
        #     return f"_{c}" if c.isdigit() else f"_x{ord(c):X}"
        #
        # result = [sanitize_char(name[0]) if not name[0].isalpha() and name[0] != '_' else name[0]]
        #
        # for char in name[1:]:
        #     if char.isalnum() or char == '_':
        #         result.append(char)
        #     else:
        #         result.append(sanitize_char(char))
        #
        # return ''.join(result)


class TableParser:
    """Parser for table schema information."""

    def __init__(self):
        self._generated_column_pattern = re.compile(r'^\s*`?(\w+)`?.+?GENERATED\s+ALWAYS\s+AS', re.IGNORECASE)

    def parse_table_metadata(self, describe_extended_result: List[Tuple[Any, ...]], show_create_table_result: str) -> \
            Tuple[
                str, List[FieldSchema], Dict[Any, int], List[int], List[int], List[Any], List[FieldSchema]]:
        """
        Parses the output of Hive's DESCRIBE EXTENDED and SHOW CREATE TABLE commands to extract table metadata.

        Args:
            describe_extended_result: A list of rows from the DESCRIBE EXTENDED query result.
                                      Each row is expected to be a sequence (e.g., tuple, list) with at least two elements.
            show_create_table_result: The full string output from the SHOW CREATE TABLE command.

        Returns:
            A tuple containing the parsed metadata:
            - table_type: The type of the table (e.g., IGSTableType.NORMAL, IGSTableType.ACID).
            - field_schemas: A list of FieldSchema objects representing the table columns.
            - name_to_id_map: A dictionary mapping lowercase column names to their index in field_schemas.
            - primary_key: A list of indices representing the primary key columns in field_schemas.
            - partition_key: A list of indices representing the partition key columns in field_schemas.
            - partial_update_columns: A placeholder list
            - generated_columns: A list of FieldSchema objects that are generated columns.
        """

        # Initialize the results as specified
        table_type = IGSTableType.NORMAL
        field_schemas = []
        name_to_id_map = {}
        primary_key_indices = []
        partition_key_indices = []
        partial_update_columns = []
        generated_columns = []

        # Lists to hold the parsed keys and values from DESCRIBE EXTENDED
        key_list = []
        value_list = []

        # Extract the first two columns from the DESCRIBE EXTENDED result
        for row in describe_extended_result:
            if len(row) >= 2:
                key_list.append(str(row[0]) if row[0] is not None else None)
                value_list.append(str(row[1]) if row[1] is not None else None)

        # Parser state
        name_list = []
        data_type_list = []
        find_all_column_names = True
        pos = 0

        while pos < len(key_list):
            key = key_list[pos]
            value = value_list[pos]

            # Section 1: Parse regular column definitions
            # Stop when we hit the partition information or an empty/null key
            if find_all_column_names and (
                    key is None or key == '' or (key and key.strip().lower() == '# partition information')):
                # Convert parsed names and types into FieldSchema objects
                for name, data_type_with_nullable in zip(name_list, data_type_list):
                    if name and data_type_with_nullable:  # Ensure they are not None or empty
                        # Parse nullability from type string
                        data_type_str = data_type_with_nullable.strip()
                        
                        # Check for NOT NULL keyword (case insensitive)
                        not_null_match = re.search(r'\s+(NOT\s+)?NULL\s*$', data_type_str, re.IGNORECASE)
                        if not_null_match:
                            # If we found NULL/NOT NULL keywords
                            nullable = not ('NOT' in not_null_match.group(0).upper())
                            # Remove the nullability keywords from type
                            clean_type = re.sub(r'\s+(NOT\s+)?NULL\s*$', '', data_type_str, flags=re.IGNORECASE).strip()
                        else:
                            # Default to nullable if no explicit nullability specified
                            nullable = True
                            clean_type = data_type_str
                        
                        # Create FieldSchema object
                        field_schema = FieldSchema(
                            name=name.strip(),
                            field_type=clean_type,
                            nullable=nullable
                        )
                        field_schemas.append(field_schema)

                # Create the name-to-id map
                for index, field_schema in enumerate(field_schemas):
                    name_to_id_map[field_schema.name.lower()] = index

                find_all_column_names = False

            # If we are still in the column definition section, collect the name and type
            if find_all_column_names:
                if key and value:
                    name_list.append(key)
                    data_type_list.append(value.strip())  # Keep original type with nullability info
            else:
                # Section 2: Parse partition keys
                # Look for the partition information section and collect partition column names
                if key and key.strip().lower() == '# partition information':
                    pos += 1
                    while pos < len(key_list):
                        partition_column_name = key_list[pos]
                        if partition_column_name and partition_column_name.strip() != '':
                            partition_column_name = partition_column_name.strip()
                            if partition_column_name.lower() in name_to_id_map:
                                partition_key_indices.append(name_to_id_map[partition_column_name.lower()])
                            pos += 1
                        else:
                            break
                    continue  # Skip the pos increment at the end of the loop

                # Section 3: Parse primary key
                # Look for a property key 'primary_key' and extract column names from its value
                elif key and key.strip().lower() == 'primary_key':
                    # Use regex to find content within parentheses
                    pattern = re.compile(r"\(([^)]+)\)")
                    matcher = pattern.search(value)
                    if matcher:
                        group = matcher.group(1)
                        # Split the string on comma, accounting for potential spaces
                        parts = [part.strip() for part in group.split(',')]
                        for part in parts:
                            part_lower = part.lower()
                            if part_lower in name_to_id_map:
                                primary_key_indices.append(name_to_id_map[part_lower])
                        table_type = IGSTableType.ACID

            pos += 1  # Move to the next row

        # Section 4: Identify generated columns using SHOW CREATE TABLE
        # Split the DDL into lines and check each field against a regex pattern
        col_str_lines = [line.strip() for line in show_create_table_result.split('\n')]
        generated_column_names = set()

        # First, identify which columns are generated
        for field_schema in field_schemas:
            for line in col_str_lines:
                match = self._generated_column_pattern.match(line)
                if match and match.group(1) == field_schema.name:
                    generated_column_names.add(field_schema.name)
                    generated_columns.append(field_schema)
                    break

        # Store original field_schemas for index mapping
        original_field_schemas = field_schemas[:]
        
        # Then, create new lists excluding generated columns
        filtered_field_schemas = []
        new_name_to_id_map = {}
        
        for field_schema in field_schemas:
            if field_schema.name not in generated_column_names:
                # Add to filtered list
                new_index = len(filtered_field_schemas)
                filtered_field_schemas.append(field_schema)
                new_name_to_id_map[field_schema.name.lower()] = new_index
        
        # Update primary key and partition key indices to match the new field_schemas indices
        updated_primary_key_indices = []
        for old_index in primary_key_indices:
            # Find the field name from the original field schema list
            if old_index < len(original_field_schemas):
                field_name = original_field_schemas[old_index].name
                if field_name.lower() in new_name_to_id_map:
                    updated_primary_key_indices.append(new_name_to_id_map[field_name.lower()])
        
        updated_partition_key_indices = []
        for old_index in partition_key_indices:
            # Find the field name from the original field schema list
            if old_index < len(original_field_schemas):
                field_name = original_field_schemas[old_index].name
                if field_name.lower() in new_name_to_id_map:
                    updated_partition_key_indices.append(new_name_to_id_map[field_name.lower()])
        
        # Update the field_schemas and name_to_id_map
        field_schemas = filtered_field_schemas
        name_to_id_map = new_name_to_id_map

        # Return all the collected results
        return (table_type, field_schemas, name_to_id_map, updated_primary_key_indices, updated_partition_key_indices,
                partial_update_columns, generated_columns)
