import amsdal_glue as glue
from _typeshed import Incomplete
from amsdal_models.classes.glue_utils import model_to_data as model_to_data
from amsdal_models.classes.model import Model as Model
from amsdal_models.migration.base_migration_schemas import BaseMigrationSchemas as BaseMigrationSchemas
from amsdal_models.migration.data_classes import Action as Action
from amsdal_models.migration.executors.base import AsyncBaseMigrationExecutor as AsyncBaseMigrationExecutor, BaseMigrationExecutor as BaseMigrationExecutor
from amsdal_models.querysets.executor import LAKEHOUSE_DB_ALIAS as LAKEHOUSE_DB_ALIAS
from amsdal_utils.models.enums import ModuleType
from amsdal_utils.schemas.schema import ObjectSchema
from typing import Any, Literal

class DefaultMigrationExecutor(BaseMigrationExecutor):
    """
    Default implementation of the BaseMigrationExecutor for handling database schema migrations.

    This class provides concrete implementations for creating, updating, and deleting classes
    in the database schema. It also manages schema migration buffers and processes object schemas.
    """
    _schema_version_manager: Incomplete
    schemas: Incomplete
    _table_schemas_manager: Incomplete
    _use_foreign_keys: Incomplete
    def __init__(self, schemas: BaseMigrationSchemas, *, use_foreign_keys: bool = True) -> None: ...
    def create_class(self, schemas: BaseMigrationSchemas, class_name: str, object_schema: ObjectSchema, module_type: ModuleType) -> None:
        """
        Creates a class in the database schema.

        This method registers a new class version if the schema type is `TYPE` and the class name
            is not `BaseClasses.OBJECT`.
        Otherwise, it buffers the class migration operation for further processing.

        Args:
            schemas (BaseMigrationSchemas): The migration schemas used for the operations.
            class_name (str): The name of the class to be created.
            object_schema (ObjectSchema): The schema of the object to be created.
            module_type (ModuleType): The type of the schema.

        Returns:
            None
        """
    def update_class(self, schemas: BaseMigrationSchemas, class_name: str, object_schema: ObjectSchema, module_type: ModuleType, context: dict[str, Any]) -> None:
        """
        Buffers the class update operation.

        This method appends the given class name, object schema, and schema type to both
        the non-flushable buffer and the main buffer for further processing.

        Args:
            schemas (BaseMigrationSchemas): The migration schemas used for the operations.
            class_name (str): The name of the class to be updated.
            object_schema (ObjectSchema): The current object schema.
            module_type (ModuleType): The type of the schema.
            context (dict[str, Any]): Extra execution context

        Returns:
            None
        """
    def delete_class(self, schemas: BaseMigrationSchemas, class_name: str, module_type: ModuleType) -> None:
        """
        Deletes a class from the database schema.

        This method removes the specified class from the database schema and unregisters it from the migration schemas.

        Args:
            schemas (BaseMigrationSchemas): The migration schemas used for the operations.
            class_name (str): The name of the class to be deleted.
            module_type (ModuleType): The type of the schema.

        Returns:
            None
        """
    def flush_buffer(self) -> None:
        """
        Flushes the migration buffer and processes the buffered classes.

        This method registers the buffered classes in the migration schemas, compiles the buffered classes,
        and processes each class in the buffer to create tables, save class objects, and migrate historical data.
        Finally, it clears the main migration buffer.

        Returns:
            None
        """
    def _migrate_object_schema(self, schema_reference: glue.SchemaReference, base_class: type[Model], object_schema: ObjectSchema, using: str | None = None, *, create_table: bool = True) -> None:
        """
        Migrate ClassObject schema.

        This method handles the migration of class object schemas (Model).
        The class object schema creates the ClassObject table and the schema is stored in Object table.

        Args:
            object_schema (ObjectSchema): The schema of the object to be migrated.

        Returns:
            None
        """
    def _check_class(self, schema_reference: glue.SchemaReference, object_schema: ObjectSchema, base_class: type[Model]) -> Action: ...
    def _save_class(self, schema_reference: glue.SchemaReference, base_class: type[Model], object_schema: ObjectSchema, action: Action) -> dict[str, Any]: ...
    def _create_table(self, object_schema: ObjectSchema, schema_version: Literal[''] | str, using: str | None = None, extra_metadata: dict[str, Any] | None = None) -> tuple[bool, bool]: ...
    def _process_object_schema(self, object_schema: ObjectSchema, class_name: str, buffer: list[tuple[str, ObjectSchema, ModuleType]]) -> ObjectSchema: ...
    def register_schemas(self) -> None:
        """
        Registers the schemas in the table schemas manager.

        This method retrieves the object schemas from the database, processes them, and registers
        them in the table schemas manager. It handles `ClassObject` schema,
        and ensures that all necessary references are loaded and processed.

        Returns:
            None
        """

class DefaultAsyncMigrationExecutor(AsyncBaseMigrationExecutor):
    """
    Default implementation of the BaseMigrationExecutor for handling database schema migrations.

    This class provides concrete implementations for creating, updating, and deleting classes
    in the database schema. It also manages schema migration buffers and processes object schemas.
    """
    _schema_version_manager: Incomplete
    schemas: Incomplete
    _table_schemas_manager: Incomplete
    _use_foreign_keys: Incomplete
    def __init__(self, schemas: BaseMigrationSchemas, *, use_foreign_keys: bool = True) -> None: ...
    def create_class(self, schemas: BaseMigrationSchemas, class_name: str, object_schema: ObjectSchema, module_type: ModuleType) -> None:
        """
        Creates a class in the database schema.

        This method registers a new class version if the schema type is `TYPE` and the class name
            is not `BaseClasses.OBJECT`.
        Otherwise, it buffers the class migration operation for further processing.

        Args:
            schemas (BaseMigrationSchemas): The migration schemas used for the operations.
            class_name (str): The name of the class to be created.
            object_schema (ObjectSchema): The schema of the object to be created.
            module_type (ModuleType): The type of the schema.

        Returns:
            None
        """
    def update_class(self, schemas: BaseMigrationSchemas, class_name: str, object_schema: ObjectSchema, module_type: ModuleType, context: dict[str, Any]) -> None:
        """
        Buffers the class update operation.

        This method appends the given class name, object schema, and schema type to both
        the non-flushable buffer and the main buffer for further processing.

        Args:
            schemas (BaseMigrationSchemas): The migration schemas used for the operations.
            class_name (str): The name of the class to be updated.
            object_schema (ObjectSchema): The current object schema.
            module_type (ModuleType): The type of the schema.
            context (dict[str, Any): Extra execution context.

        Returns:
            None
        """
    async def delete_class(self, schemas: BaseMigrationSchemas, class_name: str, module_type: ModuleType) -> None:
        """
        Deletes a class from the database schema.

        This method removes the specified class from the database schema and unregisters it from the migration schemas.

        Args:
            schemas (BaseMigrationSchemas): The migration schemas used for the operations.
            class_name (str): The name of the class to be deleted.
            module_type (ModuleType): The type of the schema.

        Returns:
            None
        """
    async def flush_buffer(self) -> None:
        """
        Flushes the migration buffer and processes the buffered classes.

        This method registers the buffered classes in the migration schemas, compiles the buffered classes,
        and processes each class in the buffer to create tables, save class objects, and migrate historical data.
        Finally, it clears the main migration buffer.

        Returns:
            None
        """
    async def _migrate_object_schema(self, schema_reference: glue.SchemaReference, base_class: type[Model], object_schema: ObjectSchema, using: str | None = None, *, create_table: bool = True) -> None: ...
    async def _check_class(self, schema_reference: glue.SchemaReference, object_schema: ObjectSchema, base_class: type[Model]) -> Action: ...
    async def _save_class(self, schema_reference: glue.SchemaReference, base_class: type[Model], object_schema: ObjectSchema, action: Action) -> dict[str, Any]: ...
    async def _create_table(self, object_schema: ObjectSchema, schema_version: Literal[''] | str, using: str | None = None, extra_metadata: dict[str, Any] | None = None) -> tuple[bool, bool]: ...
    def _process_object_schema(self, object_schema: ObjectSchema, class_name: str, buffer: list[tuple[str, ObjectSchema, ModuleType]]) -> ObjectSchema: ...
    async def register_schemas(self) -> None:
        """
        Registers the schemas in the table schemas manager.

        This method retrieves the object schemas from the database, processes them, and registers
        them in the table schemas manager. It handles both `ClassObject` and `ClassObjectMeta` schemas,
        and ensures that all necessary references are loaded and processed.

        Returns:
            None
        """
