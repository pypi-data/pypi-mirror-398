from typing import Any

from amsdal_utils.models.data_models.enums import BaseClasses
from amsdal_utils.models.enums import ModuleType
from amsdal_utils.models.enums import Versions
from amsdal_utils.schemas.schema import ObjectSchema

from amsdal_models.migration.base_migration_schemas import BaseMigrationSchemas
from amsdal_models.migration.executors.base import AsyncBaseMigrationExecutor
from amsdal_models.migration.executors.base import BaseMigrationExecutor
from amsdal_models.querysets.executor import LAKEHOUSE_DB_ALIAS


class StateMigrationExecutor(BaseMigrationExecutor):
    """
    Executes state migrations for database schemas.

    This class handles the creation, updating, and deletion of classes in the database schema,
    as well as flushing buffered migration operations.

    Attributes:
        schemas (BaseMigrationSchemas): The migration schemas used for the operations.
        do_fetch_latest_version (bool): Flag indicating whether to fetch the latest version of the schema.
    """

    def __init__(
        self,
        schemas: BaseMigrationSchemas,
        *,
        do_fetch_latest_version: bool = True,
    ) -> None:
        self.schemas = schemas
        self.do_fetch_latest_version = do_fetch_latest_version
        super().__init__()

    def create_class(
        self,
        schemas: BaseMigrationSchemas,  # noqa: ARG002
        class_name: str,
        object_schema: ObjectSchema,
        module_type: ModuleType,
    ) -> None:
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
        if module_type == ModuleType.TYPE and class_name != BaseClasses.OBJECT:
            self.schemas.register_model_version(
                class_name=class_name,
                class_version='',
            )

            return

        self.buffer_class_migration(
            class_name,
            object_schema,
            module_type,
        )

    def update_class(
        self,
        schemas: BaseMigrationSchemas,  # noqa: ARG002
        class_name: str,
        object_schema: ObjectSchema,
        module_type: ModuleType,
        context: dict[str, Any],
    ) -> None:
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
        self.buffer_class_migration(
            class_name,
            object_schema,
            module_type,
            context,
        )

    def delete_class(
        self,
        schemas: BaseMigrationSchemas,
        class_name: str,
        module_type: ModuleType,  # noqa: ARG002
    ) -> None:
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
        schemas.unregister_model(class_name)

    def flush_buffer(self) -> None:
        """
        Flushes the migration buffer and processes the buffered classes.

        This method registers all classes in the migration buffer to the database schema and compiles
        the buffered classes. If the `do_fetch_latest_version` flag is set, it also fetches and registers
        the latest version of each class.

        Returns:
            None
        """
        for class_name, object_schema, module_type, _ in self._buffer:
            self.schemas.register_model(
                class_name=class_name,
                object_schema=object_schema,
                module_type=module_type,
            )

        self.schemas.compile_buffered_classes()

        if not self.do_fetch_latest_version:
            return

        for class_name, object_schema, _, _ in self._buffer:
            if class_name != BaseClasses.OBJECT:
                base_class_name = self._resolve_base_class_name(class_name, meta_class=object_schema.meta_class)
                base_class = self.schemas.get_model(base_class_name)
                class_objects = (
                    base_class.objects.using(LAKEHOUSE_DB_ALIAS)
                    .filter(
                        _address__class_version=Versions.ALL,
                        _address__object_id=class_name,
                        _address__object_version=Versions.ALL,
                    )
                    .execute()
                )

                for class_object in class_objects:
                    class_version = class_object.get_metadata().object_version

                    self.schemas.register_model_version(
                        class_name=class_name,
                        class_version=class_version,
                    )


class AsyncStateMigrationExecutor(AsyncBaseMigrationExecutor):
    """
    Executes state migrations for database schemas.

    This class handles the creation, updating, and deletion of classes in the database schema,
    as well as flushing buffered migration operations.

    Attributes:
        schemas (BaseMigrationSchemas): The migration schemas used for the operations.
        do_fetch_latest_version (bool): Flag indicating whether to fetch the latest version of the schema.
    """

    def __init__(
        self,
        schemas: BaseMigrationSchemas,
        *,
        do_fetch_latest_version: bool = True,
    ) -> None:
        self.schemas = schemas
        self.do_fetch_latest_version = do_fetch_latest_version
        super().__init__()

    def create_class(
        self,
        schemas: BaseMigrationSchemas,  # noqa: ARG002
        class_name: str,
        object_schema: ObjectSchema,
        module_type: ModuleType,
    ) -> None:
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
        if module_type == ModuleType.TYPE and class_name != BaseClasses.OBJECT:
            self.schemas.register_model_version(
                class_name=class_name,
                class_version='',
            )

            return

        self.buffer_class_migration(
            class_name,
            object_schema,
            module_type,
        )

    def update_class(
        self,
        schemas: BaseMigrationSchemas,  # noqa: ARG002
        class_name: str,
        object_schema: ObjectSchema,
        module_type: ModuleType,
        context: dict[str, Any],
    ) -> None:
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
        self.buffer_class_migration(
            class_name,
            object_schema,
            module_type,
            context,
        )

    def delete_class(
        self,
        schemas: BaseMigrationSchemas,
        class_name: str,
        module_type: ModuleType,  # noqa: ARG002
    ) -> None:
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
        schemas.unregister_model(class_name)

    async def flush_buffer(self) -> None:  # type: ignore[override]
        """
        Flushes the migration buffer and processes the buffered classes.

        This method registers all classes in the migration buffer to the database schema and compiles
        the buffered classes. If the `do_fetch_latest_version` flag is set, it also fetches and registers
        the latest version of each class.

        Returns:
            None
        """
        for class_name, object_schema, module_type, _ in self._buffer:
            self.schemas.register_model(
                class_name=class_name,
                object_schema=object_schema,
                module_type=module_type,
            )

        self.schemas.compile_buffered_classes()

        if not self.do_fetch_latest_version:
            return

        for class_name, object_schema, _, _ in self._buffer:
            if class_name != BaseClasses.OBJECT:
                base_class_name = self._resolve_base_class_name(class_name, meta_class=object_schema.meta_class)
                base_class = self.schemas.get_model(base_class_name)
                class_objects = (
                    await base_class.objects.using(LAKEHOUSE_DB_ALIAS)
                    .filter(
                        _address__class_version=Versions.ALL,
                        _address__object_id=class_name,
                        _address__object_version=Versions.ALL,
                    )
                    .aexecute()
                )

                for class_object in class_objects:
                    class_version = (await class_object.aget_metadata()).object_version

                    self.schemas.register_model_version(
                        class_name=class_name,
                        class_version=class_version,
                    )
