from amsdal_utils.schemas.schema import ObjectSchema
from collections.abc import Callable as Callable
from typing import Any

class ExternalSchemaConverter:
    """
    Converts external database schema information to ObjectSchema format.

    Supports schema introspection output from various database types:
    - SQLite (PRAGMA table_info output)
    - PostgreSQL (information_schema format)
    - Generic schema formats

    Example usage:
        converter = ExternalSchemaConverter()

        # Convert SQLite schema
        sqlite_columns = [
            {'cid': 0, 'name': 'id', 'type': 'INTEGER', 'notnull': 1, 'dflt_value': None, 'pk': 1},
            {'cid': 1, 'name': 'username', 'type': 'TEXT', 'notnull': 1, 'dflt_value': None, 'pk': 0},
            {'cid': 2, 'name': 'email', 'type': 'TEXT', 'notnull': 0, 'dflt_value': None, 'pk': 0},
        ]
        object_schema = converter.sqlite_schema_to_object_schema('users', sqlite_columns)

        # Now object_schema can be used for model generation
    """
    @staticmethod
    def sqlite_type_to_core_type(sqlite_type: str) -> str:
        """
        Convert SQLite type to AMSDAL CoreType.

        Args:
            sqlite_type: SQLite type name (e.g., 'INTEGER', 'TEXT', 'BLOB')

        Returns:
            str: CoreType value
        """
    @staticmethod
    def postgres_type_to_core_type(postgres_type: str) -> str:
        """
        Convert PostgreSQL type to AMSDAL CoreType.

        Args:
            postgres_type: PostgreSQL type name (e.g., 'integer', 'varchar', 'jsonb')

        Returns:
            str: CoreType value
        """
    def sqlite_schema_to_object_schema(self, table_name: str, columns: list[dict[str, Any]], connection_name: str | None = None) -> ObjectSchema:
        """
        Convert SQLite PRAGMA table_info output to ObjectSchema.

        Args:
            table_name: Name of the table
            columns: List of column info dicts from PRAGMA table_info
                     Expected format: [{'cid': int, 'name': str, 'type': str,
                                       'notnull': int, 'dflt_value': Any, 'pk': int}, ...]
            connection_name: Optional connection name for the model

        Returns:
            ObjectSchema: Schema suitable for model generation

        Example:
            columns = [
                {'cid': 0, 'name': 'id', 'type': 'INTEGER', 'notnull': 1, 'dflt_value': None, 'pk': 1},
                {'cid': 1, 'name': 'name', 'type': 'TEXT', 'notnull': 1, 'dflt_value': None, 'pk': 0},
            ]
            schema = converter.sqlite_schema_to_object_schema('users', columns)
        """
    def postgres_schema_to_object_schema(self, table_name: str, columns: list[dict[str, Any]], connection_name: str | None = None) -> ObjectSchema:
        """
        Convert PostgreSQL information_schema output to ObjectSchema.

        Args:
            table_name: Name of the table
            columns: List of column info dicts
                     Expected format: [{'column_name': str, 'data_type': str,
                                       'is_nullable': str, 'column_default': Any}, ...]
            connection_name: Optional connection name for the model

        Returns:
            ObjectSchema: Schema suitable for model generation
        """
    def generic_schema_to_object_schema(self, table_name: str, columns: list[dict[str, Any]], connection_name: str | None = None, type_converter: Callable[[str], str] | None = None) -> ObjectSchema:
        """
        Convert generic schema format to ObjectSchema.

        This is a flexible converter that works with various schema formats.
        It expects columns to have at minimum: 'name' and 'type' fields.

        Args:
            table_name: Name of the table
            columns: List of column info dicts
                     Minimum format: [{'name': str, 'type': str}, ...]
                     Optional fields: 'nullable', 'required', 'primary_key', 'default'
            connection_name: Optional connection name for the model
            type_converter: Optional callable to convert type strings to CoreTypes
                           Defaults to SQLite converter if not provided

        Returns:
            ObjectSchema: Schema suitable for model generation
        """
