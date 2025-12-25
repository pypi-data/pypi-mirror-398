from _typeshed import Incomplete
from amsdal_models.migration.base_migration_schemas import BaseMigrationSchemas as BaseMigrationSchemas
from amsdal_models.migration.executors.base import AsyncBaseMigrationExecutor as AsyncBaseMigrationExecutor, BaseMigrationExecutor as BaseMigrationExecutor
from amsdal_models.querysets.executor import LAKEHOUSE_DB_ALIAS as LAKEHOUSE_DB_ALIAS
from amsdal_utils.models.enums import ModuleType
from amsdal_utils.schemas.schema import ObjectSchema as ObjectSchema
from typing import Any

class StateMigrationExecutor(BaseMigrationExecutor):
    """
    Executes state migrations for database schemas.

    This class handles the creation, updating, and deletion of classes in the database schema,
    as well as flushing buffered migration operations.

    Attributes:
        schemas (BaseMigrationSchemas): The migration schemas used for the operations.
        do_fetch_latest_version (bool): Flag indicating whether to fetch the latest version of the schema.
    """
    schemas: Incomplete
    do_fetch_latest_version: Incomplete
    def __init__(self, schemas: BaseMigrationSchemas, *, do_fetch_latest_version: bool = True) -> None: ...
    def create_class(self, schemas: BaseMigrationSchemas, class_name: str, object_schema: ObjectSchema, module_type: ModuleType) -> None:
        """
        Creates a class in the database schema.

        This method registers a new class in the database schema or buffers the class migration
        operation based on the schema type and class name.

        Args:
            schemas (BaseMigrationSchemas): The migration schemas used for the operations.
            class_name (str): The name of the class to be created.
            object_schema (ObjectSchema): The current object schema.
            module_type (ModuleType): The type of the schema.

        Returns:
            None
        """
    def update_class(self, schemas: BaseMigrationSchemas, class_name: str, object_schema: ObjectSchema, module_type: ModuleType, context: dict[str, Any]) -> None:
        """
        Buffers the class update operation.

        This method adds the class update operation to the migration buffer, which will be processed
        when the buffer is flushed.

        Args:
            schemas (BaseMigrationSchemas): The migration schemas used for the operations.
            class_name (str): The name of the class to be updated.
            object_schema (ObjectSchema): The current object schema.
            module_type (ModuleType): The type of the schema.
            context (dict[str, Any): Extra execution context.

        Returns:
            None
        """
    def delete_class(self, schemas: BaseMigrationSchemas, class_name: str, module_type: ModuleType) -> None:
        """
        Deletes a class from the database schema.

        This method unregisters a class from the database schema based on the provided class name
        and schema type.

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

        This method registers all classes in the migration buffer to the database schema and compiles
        the buffered classes. If the `do_fetch_latest_version` flag is set, it also fetches and registers
        the latest version of each class.

        Returns:
            None
        """

class AsyncStateMigrationExecutor(AsyncBaseMigrationExecutor):
    """
    Executes state migrations for database schemas.

    This class handles the creation, updating, and deletion of classes in the database schema,
    as well as flushing buffered migration operations.

    Attributes:
        schemas (BaseMigrationSchemas): The migration schemas used for the operations.
        do_fetch_latest_version (bool): Flag indicating whether to fetch the latest version of the schema.
    """
    schemas: Incomplete
    do_fetch_latest_version: Incomplete
    def __init__(self, schemas: BaseMigrationSchemas, *, do_fetch_latest_version: bool = True) -> None: ...
    def create_class(self, schemas: BaseMigrationSchemas, class_name: str, object_schema: ObjectSchema, module_type: ModuleType) -> None:
        """
        Creates a class in the database schema.

        This method registers a new class in the database schema or buffers the class migration
        operation based on the schema type and class name.

        Args:
            schemas (BaseMigrationSchemas): The migration schemas used for the operations.
            class_name (str): The name of the class to be created.
            object_schema (ObjectSchema): The current object schema.
            module_type (ModuleType): The type of the schema.

        Returns:
            None
        """
    def update_class(self, schemas: BaseMigrationSchemas, class_name: str, object_schema: ObjectSchema, module_type: ModuleType, context: dict[str, Any]) -> None:
        """
        Buffers the class update operation.

        This method adds the class update operation to the migration buffer, which will be processed
        when the buffer is flushed.

        Args:
            schemas (BaseMigrationSchemas): The migration schemas used for the operations.
            class_name (str): The name of the class to be updated.
            object_schema (ObjectSchema): The current object schema.
            module_type (ModuleType): The type of the schema.
            context (dict[str, Any): Extra execution context.

        Returns:
            None
        """
    def delete_class(self, schemas: BaseMigrationSchemas, class_name: str, module_type: ModuleType) -> None:
        """
        Deletes a class from the database schema.

        This method unregisters a class from the database schema based on the provided class name
        and schema type.

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

        This method registers all classes in the migration buffer to the database schema and compiles
        the buffered classes. If the `do_fetch_latest_version` flag is set, it also fetches and registers
        the latest version of each class.

        Returns:
            None
        """
