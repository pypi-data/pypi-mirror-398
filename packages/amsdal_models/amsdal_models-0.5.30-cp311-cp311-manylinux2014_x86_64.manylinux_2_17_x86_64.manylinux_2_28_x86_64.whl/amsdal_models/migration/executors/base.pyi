import abc
from abc import ABC, abstractmethod
from amsdal_models.migration.base_migration_schemas import BaseMigrationSchemas as BaseMigrationSchemas
from amsdal_utils.models.enums import ModuleType as ModuleType
from amsdal_utils.schemas.schema import ObjectSchema as ObjectSchema
from pydantic import BaseModel
from typing import Any

class FieldDescription(BaseModel):
    """
    Represents a description of a field in a database schema.

    This class holds information about a field, including its name, ID, type,
    and whether it has been marked as deleted.

    Attributes:
        field_name (str): The name of the field.
        field_id (str): The unique identifier of the field.
        field_type (str): The type of the field.
        is_deleted (bool): Indicates whether the field is marked as deleted.
    """
    field_name: str
    field_id: str
    field_type: str
    is_deleted: bool

def _schema_to_table_description(schema: ObjectSchema | None) -> dict[str, str]: ...
def _compare_schemas(previous_scheme: dict[str, str], new_scheme: dict[str, str]) -> list[tuple[str, str, str]]: ...
def _id_for_column(field_name: str, iteration: str | int) -> str: ...
def _new_table_schemas(previous_scheme: ObjectSchema | None, new_scheme: ObjectSchema, iteration: int, existing_table_structure: list[FieldDescription]) -> None: ...

class BaseMigrationExecutor(ABC, metaclass=abc.ABCMeta):
    """
    Abstract base class for executing migration operations on database schemas.

    This class provides methods for creating, updating, and deleting classes in the database schema.
    It also manages schema migration buffers and generates full object schemas based on the migration history.
    """
    schemas: BaseMigrationSchemas
    _buffer: list[tuple[str, ObjectSchema, ModuleType, dict[str, Any] | None]]
    _non_flushable_buffer: list[tuple[str, ObjectSchema, ModuleType]]
    def __init__(self) -> None: ...
    def generate_full_object_schema(self, class_name: str, object_schema: ObjectSchema, buffer: list[tuple[str, ObjectSchema, ModuleType]]) -> list[FieldDescription]:
        """
        Generates the full object schema based on the migration history.

        This method constructs the full object schema for a given class by iterating through
        the migration history buffer and applying schema changes in sequence.

        Args:
            class_name (str): The name of the class for which the schema is being generated.
            object_schema (ObjectSchema): The current object schema.
            buffer (list[tuple[str, ObjectSchema, SchemaTypes]]): The migration history buffer.

        Returns:
            list[FieldDescription]: A list of field descriptions representing the full object schema.
        """
    @abstractmethod
    def create_class(self, schemas: BaseMigrationSchemas, class_name: str, object_schema: ObjectSchema, module_type: ModuleType) -> None: ...
    @abstractmethod
    def update_class(self, schemas: BaseMigrationSchemas, class_name: str, object_schema: ObjectSchema, module_type: ModuleType, context: dict[str, Any]) -> None: ...
    @abstractmethod
    def delete_class(self, schemas: BaseMigrationSchemas, class_name: str, module_type: ModuleType) -> None: ...
    def forward_schema(self, schemas: BaseMigrationSchemas, class_name: str, object_schema: ObjectSchema, module_type: ModuleType, context: dict[str, Any] | None = None) -> None:
        """
        Forwards the schema to the non-flushable buffer.

        This method appends the given class name, object schema, and schema type to the
        non-flushable buffer for further processing.

        Args:
            schemas (BaseMigrationSchemas): The migration schemas used for the operations.
            class_name (str): The name of the class for which the schema is being forwarded.
            object_schema (ObjectSchema): The current object schema.
            module_type (ModuleType): The type of the schema.
            context (dict[str, Any] | None): Extra execution context.

        Returns:
            None
        """
    @staticmethod
    def _resolve_base_class_name(class_name: str, meta_class: str) -> str: ...
    def buffer_class_migration(self, class_name: str, object_schema: ObjectSchema, module_type: ModuleType, context: dict[str, Any] | None = None) -> None:
        """
        Buffers the class migration operation.

        This method appends the given class name, object schema, and schema type to both
        the non-flushable buffer and the main buffer for further processing.

        Args:
            class_name (str): The name of the class for which the migration is being buffered.
            object_schema (ObjectSchema): The current object schema.
            module_type (ModuleType): The type of the schema.
            context (dict[str, Any]): Extra execution context

        Returns:
            None
        """
    def flush_buffer(self) -> None:
        """
        Flushes the migration buffer.

        This method clears all entries from the main migration buffer, effectively
        resetting it for future migration operations.

        Returns:
            None
        """
    @staticmethod
    def _prepare_object_schema_properties(object_schema: ObjectSchema) -> None:
        """Helper to prepare object schema properties"""
    @staticmethod
    def _normalize_object_schema_data(data: dict[str, Any]) -> dict[str, Any]: ...

class AsyncBaseMigrationExecutor(BaseMigrationExecutor, ABC, metaclass=abc.ABCMeta):
    async def flush_buffer(self) -> None:
        """
        Flushes the migration buffer.

        This method clears all entries from the main migration buffer, effectively
        resetting it for future migration operations.

        Returns:
            None
        """
