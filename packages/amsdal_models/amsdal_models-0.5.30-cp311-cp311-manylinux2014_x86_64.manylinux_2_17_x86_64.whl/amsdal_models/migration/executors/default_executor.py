import json
from typing import Any
from typing import Literal

import amsdal_glue as glue
from amsdal_data.application import AsyncDataApplication
from amsdal_data.application import DataApplication
from amsdal_data.connections.historical.schema_version_manager import AsyncHistoricalSchemaVersionManager
from amsdal_data.connections.historical.schema_version_manager import HistoricalSchemaVersionManager
from amsdal_data.services.table_schema_manager import AsyncTableSchemasManager
from amsdal_data.services.table_schema_manager import TableSchemasManager
from amsdal_data.utils import object_schema_to_glue_schema
from amsdal_utils.models.data_models.enums import BaseClasses
from amsdal_utils.models.data_models.enums import MetaClasses
from amsdal_utils.models.enums import ModuleType
from amsdal_utils.models.enums import Versions
from amsdal_utils.schemas.schema import ObjectSchema
from amsdal_utils.schemas.schema import PropertyData
from amsdal_utils.utils.identifier import get_identifier

from amsdal_models.classes.glue_utils import model_to_data
from amsdal_models.classes.model import Model
from amsdal_models.migration.base_migration_schemas import BaseMigrationSchemas
from amsdal_models.migration.data_classes import Action
from amsdal_models.migration.executors.base import AsyncBaseMigrationExecutor
from amsdal_models.migration.executors.base import BaseMigrationExecutor
from amsdal_models.querysets.executor import LAKEHOUSE_DB_ALIAS


class DefaultMigrationExecutor(BaseMigrationExecutor):
    """
    Default implementation of the BaseMigrationExecutor for handling database schema migrations.

    This class provides concrete implementations for creating, updating, and deleting classes
    in the database schema. It also manages schema migration buffers and processes object schemas.
    """

    def __init__(self, schemas: BaseMigrationSchemas, *, use_foreign_keys: bool = True) -> None:
        self._schema_version_manager = HistoricalSchemaVersionManager()
        self.schemas = schemas
        self._table_schemas_manager = TableSchemasManager()
        self._use_foreign_keys = use_foreign_keys

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
        if module_type == ModuleType.TYPE:
            self.schemas.register_model_version(
                class_name=class_name,
                class_version='',
            )

            if class_name != BaseClasses.OBJECT:
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
        context: dict[str, Any],  # noqa: ARG002
    ) -> None:
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
        self.buffer_class_migration(
            class_name,
            object_schema,
            module_type,
        )

    def delete_class(
        self,
        schemas: BaseMigrationSchemas,
        class_name: str,
        module_type: ModuleType,  # noqa: ARG002
    ) -> None:
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
        base_class_name = self._resolve_base_class_name(class_name, meta_class=MetaClasses.CLASS_OBJECT)

        self._table_schemas_manager.delete_class_object_schema(
            schema_reference=glue.SchemaReference(
                name=base_class_name,
                version=Versions.LATEST,
            ),
            class_object_id=class_name,
        )
        schemas.unregister_model(class_name)

    def flush_buffer(self) -> None:
        """
        Flushes the migration buffer and processes the buffered classes.

        This method registers the buffered classes in the migration schemas, compiles the buffered classes,
        and processes each class in the buffer to create tables, save class objects, and migrate historical data.
        Finally, it clears the main migration buffer.

        Returns:
            None
        """
        for class_name, object_schema, module_type, _ in self._buffer:
            self.schemas.register_model(
                class_name=class_name,
                object_schema=object_schema,
                module_type=module_type,
                class_version='' if class_name == BaseClasses.OBJECT else Versions.LATEST,
            )

        self.schemas.compile_buffered_classes()

        for class_name, object_schema, module_type, context in self._buffer:
            object_schema.module_type = module_type  # type: ignore[attr-defined]
            self._prepare_object_schema_properties(object_schema)

            if class_name == BaseClasses.OBJECT:
                self._create_table(
                    object_schema,
                    schema_version='',
                    using=LAKEHOUSE_DB_ALIAS,
                    extra_metadata=context,
                )
                continue

            is_meta_class_object = object_schema.meta_class == MetaClasses.CLASS_OBJECT
            base_class = self.schemas.get_model(BaseClasses.OBJECT.value)
            schema_reference = glue.SchemaReference(
                name=BaseClasses.OBJECT.value,
                version='',
            )
            using: str | None = LAKEHOUSE_DB_ALIAS
            create_table = is_meta_class_object

            if is_meta_class_object and class_name != BaseClasses.CLASS_OBJECT:
                base_class = self.schemas.get_model(BaseClasses.CLASS_OBJECT.value)
                schema_reference = glue.SchemaReference(
                    name=BaseClasses.CLASS_OBJECT.value,
                    version=Versions.LATEST,
                )
                # Crete table in both State and Lakehouse
                using = LAKEHOUSE_DB_ALIAS if DataApplication().is_lakehouse_only else None

            self._migrate_object_schema(
                schema_reference=schema_reference,
                base_class=base_class,
                object_schema=object_schema,
                using=using,
                create_table=create_table,
            )

        super().flush_buffer()

    def _migrate_object_schema(
        self,
        schema_reference: glue.SchemaReference,
        base_class: type[Model],
        object_schema: ObjectSchema,
        using: str | None = None,
        *,
        create_table: bool = True,
    ) -> None:
        """
        Migrate ClassObject schema.

        This method handles the migration of class object schemas (Model).
        The class object schema creates the ClassObject table and the schema is stored in Object table.

        Args:
            object_schema (ObjectSchema): The schema of the object to be migrated.

        Returns:
            None
        """

        action: Action = self._check_class(
            schema_reference=schema_reference,
            object_schema=object_schema,
            base_class=base_class,
        )

        if action == Action.NO_ACTION:
            return

        # Generate a new version for the schema
        new_version = get_identifier()
        if create_table:
            self._create_table(
                object_schema,
                schema_version=new_version,
                using=using,
            )

        # Register last class version
        self._schema_version_manager.register_last_version(
            schema_name=object_schema.title,
            schema_version=new_version,
        )

        self._save_class(
            schema_reference=schema_reference,
            base_class=base_class,
            object_schema=object_schema,
            action=action,
        )

    def _check_class(
        self,
        schema_reference: glue.SchemaReference,
        object_schema: ObjectSchema,
        base_class: type[Model],
    ) -> Action:
        data: dict[str, Any] | None = self._table_schemas_manager.search_latest_class_object(
            schema_reference=schema_reference,
            class_object_name=object_schema.title,
        )

        if not data:
            return Action.CREATE

        latest_class_object = base_class(**data)
        schema_dump = base_class(**self._normalize_object_schema_data(object_schema.model_dump())).model_dump()
        new_class_schema = json.dumps(schema_dump, default=str, sort_keys=True)
        existing_class_schema = json.dumps(
            self._normalize_object_schema_data(latest_class_object.model_dump()),
            default=str,
            sort_keys=True,
        )

        if new_class_schema == existing_class_schema:
            return Action.NO_ACTION

        return Action.UPDATE

    def _save_class(
        self,
        schema_reference: glue.SchemaReference,
        base_class: type[Model],
        object_schema: ObjectSchema,
        action: Action,
    ) -> dict[str, Any]:
        class_object = base_class(
            **object_schema.model_dump(),
            _object_id=object_schema.title,
        )
        class_object_data = model_to_data(class_object)

        if action == Action.CREATE:
            return self._table_schemas_manager.insert_class_object_schema(
                schema_reference=schema_reference,
                class_object_data=class_object_data,
            )
        else:
            return self._table_schemas_manager.update_class_object_schema(
                schema_reference=schema_reference,
                class_object_data=class_object_data,
            )

    def _create_table(
        self,
        object_schema: ObjectSchema,
        schema_version: Literal[''] | str,
        using: str | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> tuple[bool, bool]:
        from amsdal_data.application import DataApplication

        is_lakehouse_only = using == LAKEHOUSE_DB_ALIAS or DataApplication().is_lakehouse_only
        schema = object_schema_to_glue_schema(
            object_schema,
            is_lakehouse_only=is_lakehouse_only,
            use_foreign_keys=self._use_foreign_keys,
            schema_names=self.schemas.registered_model_names(),
            extra_metadata=extra_metadata,
        )
        schema.version = schema_version

        return self._table_schemas_manager.register_table(
            schema,
            using=using,
        )

    def _process_object_schema(
        self,
        object_schema: ObjectSchema,
        class_name: str,
        buffer: list[tuple[str, ObjectSchema, ModuleType]],
    ) -> ObjectSchema:
        fields = self.generate_full_object_schema(
            class_name,
            object_schema,
            buffer,
        )
        new_object_schema = object_schema.model_copy(deep=True)
        properties = new_object_schema.properties or {}
        new_object_schema.properties = {}

        for field in fields:
            field_id = field.field_id
            if not field.is_deleted and field.field_name in properties:
                new_object_schema.properties[field_id] = properties[field.field_name]
                new_object_schema.properties[field_id].field_id = field.field_id
                new_object_schema.properties[field_id].field_name = field.field_name
                new_object_schema.properties[field_id].is_deleted = False
            else:
                new_object_schema.properties[field_id] = PropertyData(
                    title=field.field_name,
                    is_deleted=field.is_deleted,
                    field_name=field.field_name,
                    field_id=field.field_id,
                    type=field.field_type,
                    default=None,
                    items=None,
                    options=None,
                    read_only=False,
                )
        return new_object_schema

    def register_schemas(self) -> None:
        """
        Registers the schemas in the table schemas manager.

        This method retrieves the object schemas from the database, processes them, and registers
        them in the table schemas manager. It handles `ClassObject` schema,
        and ensures that all necessary references are loaded and processed.

        Returns:
            None
        """
        buffer = []

        object_class = self.schemas.get_model(BaseClasses.OBJECT.value)
        for object_object in (
            object_class.objects.using(LAKEHOUSE_DB_ALIAS)
            .filter(title=BaseClasses.CLASS_OBJECT.value)
            .order_by('_metadata__updated_at')
            .execute()
        ):
            object_schema = ObjectSchema(**object_object.model_dump())
            buffer.append((object_schema.title, object_schema, ModuleType.CORE))
            schema = object_schema_to_glue_schema(
                self._process_object_schema(object_schema, object_schema.title, buffer),
                schema_names=self.schemas.registered_model_names(),
            )
            schema.version = object_object.get_metadata().object_version
            schema.name = object_schema.title


class DefaultAsyncMigrationExecutor(AsyncBaseMigrationExecutor):
    """
    Default implementation of the BaseMigrationExecutor for handling database schema migrations.

    This class provides concrete implementations for creating, updating, and deleting classes
    in the database schema. It also manages schema migration buffers and processes object schemas.
    """

    def __init__(self, schemas: BaseMigrationSchemas, *, use_foreign_keys: bool = True) -> None:
        self._schema_version_manager = AsyncHistoricalSchemaVersionManager()
        self.schemas = schemas
        self._table_schemas_manager = AsyncTableSchemasManager()
        self._use_foreign_keys = use_foreign_keys

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
        if module_type == ModuleType.TYPE:
            AsyncHistoricalSchemaVersionManager().register_last_version(
                schema_name=class_name,
                schema_version='',
            )

            if class_name != BaseClasses.OBJECT:
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
        context: dict[str, Any],  # noqa: ARG002
    ) -> None:
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
        self.buffer_class_migration(
            class_name,
            object_schema,
            module_type,
        )

    async def delete_class(  # type: ignore[override]
        self,
        schemas: BaseMigrationSchemas,
        class_name: str,
        module_type: ModuleType,  # noqa: ARG002
    ) -> None:
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
        base_class_name = self._resolve_base_class_name(class_name, meta_class=MetaClasses.CLASS_OBJECT)

        await self._table_schemas_manager.delete_class_object_schema(
            schema_reference=glue.SchemaReference(
                name=base_class_name,
                version=Versions.LATEST,
            ),
            class_object_id=class_name,
        )
        schemas.unregister_model(class_name)

    async def flush_buffer(self) -> None:  # type: ignore[override]
        """
        Flushes the migration buffer and processes the buffered classes.

        This method registers the buffered classes in the migration schemas, compiles the buffered classes,
        and processes each class in the buffer to create tables, save class objects, and migrate historical data.
        Finally, it clears the main migration buffer.

        Returns:
            None
        """
        for class_name, object_schema, module_type, _ in self._buffer:
            self.schemas.register_model(
                class_name=class_name,
                object_schema=object_schema,
                module_type=module_type,
                class_version='' if class_name == BaseClasses.OBJECT else Versions.LATEST,
            )

        self.schemas.compile_buffered_classes()

        for class_name, object_schema, module_type, context in self._buffer:
            object_schema.module_type = module_type  # type: ignore[attr-defined]
            self._prepare_object_schema_properties(object_schema)

            if class_name == BaseClasses.OBJECT:
                await self._create_table(
                    object_schema,
                    schema_version='',
                    using=LAKEHOUSE_DB_ALIAS,
                    extra_metadata=context,
                )
                continue

            is_meta_class_object = object_schema.meta_class == MetaClasses.CLASS_OBJECT
            base_class = self.schemas.get_model(BaseClasses.OBJECT.value)
            schema_reference = glue.SchemaReference(
                name=BaseClasses.OBJECT.value,
                version='',
            )
            using: str | None = LAKEHOUSE_DB_ALIAS
            create_table = is_meta_class_object

            if is_meta_class_object and class_name != BaseClasses.CLASS_OBJECT:
                base_class = self.schemas.get_model(BaseClasses.CLASS_OBJECT.value)
                schema_reference = glue.SchemaReference(
                    name=BaseClasses.CLASS_OBJECT.value,
                    version=Versions.LATEST,
                )
                # Crete table in both State and Lakehouse
                using = LAKEHOUSE_DB_ALIAS if AsyncDataApplication().is_lakehouse_only else None

            await self._migrate_object_schema(
                schema_reference=schema_reference,
                base_class=base_class,
                object_schema=object_schema,
                using=using,
                create_table=create_table,
            )

        await super().flush_buffer()

    async def _migrate_object_schema(
        self,
        schema_reference: glue.SchemaReference,
        base_class: type[Model],
        object_schema: ObjectSchema,
        using: str | None = None,
        *,
        create_table: bool = True,
    ) -> None:
        action: Action = await self._check_class(
            schema_reference=schema_reference,
            object_schema=object_schema,
            base_class=base_class,
        )

        if action == Action.NO_ACTION:
            return

        # Generate a new version for the schema
        new_version = get_identifier()
        if create_table:
            await self._create_table(
                object_schema,
                schema_version=new_version,
                using=using,
            )

        # Register last class version
        self._schema_version_manager.register_last_version(
            schema_name=object_schema.title,
            schema_version=new_version,
        )

        await self._save_class(
            schema_reference=schema_reference,
            base_class=base_class,
            object_schema=object_schema,
            action=action,
        )

    async def _check_class(
        self,
        schema_reference: glue.SchemaReference,
        object_schema: ObjectSchema,
        base_class: type[Model],
    ) -> Action:
        data: dict[str, Any] | None = await self._table_schemas_manager.search_latest_class_object(
            schema_reference=schema_reference,
            class_object_name=object_schema.title,
        )

        if not data:
            return Action.CREATE

        latest_class_object = base_class(**data)
        schema_dump = base_class(**object_schema.model_dump()).model_dump()
        new_class_schema = json.dumps(schema_dump, default=str, sort_keys=True)
        existing_class_schema = json.dumps(
            self._normalize_object_schema_data(latest_class_object.model_dump()),
            default=str,
            sort_keys=True,
        )

        if new_class_schema == existing_class_schema:
            return Action.NO_ACTION

        return Action.UPDATE

    async def _save_class(
        self,
        schema_reference: glue.SchemaReference,
        base_class: type[Model],
        object_schema: ObjectSchema,
        action: Action,
    ) -> dict[str, Any]:
        class_object = base_class(
            **object_schema.model_dump(),
            _object_id=object_schema.title,
        )
        class_object_data = model_to_data(class_object)

        if action == Action.CREATE:
            return await self._table_schemas_manager.insert_class_object_schema(
                schema_reference=schema_reference,
                class_object_data=class_object_data,
            )
        else:
            return await self._table_schemas_manager.update_class_object_schema(
                schema_reference=schema_reference,
                class_object_data=class_object_data,
            )

    async def _create_table(
        self,
        object_schema: ObjectSchema,
        schema_version: Literal[''] | str,
        using: str | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> tuple[bool, bool]:
        from amsdal_data.application import AsyncDataApplication

        is_lakehouse_only = using == LAKEHOUSE_DB_ALIAS or AsyncDataApplication().is_lakehouse_only
        schema = object_schema_to_glue_schema(
            object_schema,
            is_lakehouse_only=is_lakehouse_only,
            use_foreign_keys=self._use_foreign_keys,
            schema_names=self.schemas.registered_model_names(),
            extra_metadata=extra_metadata,
        )
        schema.version = schema_version

        return await self._table_schemas_manager.register_table(schema, using=using)

    def _process_object_schema(
        self,
        object_schema: ObjectSchema,
        class_name: str,
        buffer: list[tuple[str, ObjectSchema, ModuleType]],
    ) -> ObjectSchema:
        fields = self.generate_full_object_schema(
            class_name,
            object_schema,
            buffer,
        )
        new_object_schema = object_schema.model_copy(deep=True)
        properties = new_object_schema.properties or {}
        new_object_schema.properties = {}

        for field in fields:
            field_id = field.field_id
            if not field.is_deleted and field.field_name in properties:
                new_object_schema.properties[field_id] = properties[field.field_name]
                new_object_schema.properties[field_id].field_id = field.field_id
                new_object_schema.properties[field_id].field_name = field.field_name
                new_object_schema.properties[field_id].is_deleted = False
            else:
                new_object_schema.properties[field_id] = PropertyData(
                    title=field.field_name,
                    is_deleted=field.is_deleted,
                    field_name=field.field_name,
                    field_id=field.field_id,
                    type=field.field_type,
                    default=None,
                    items=None,
                    options=None,
                    read_only=False,
                )
        return new_object_schema

    async def register_schemas(self) -> None:
        """
        Registers the schemas in the table schemas manager.

        This method retrieves the object schemas from the database, processes them, and registers
        them in the table schemas manager. It handles both `ClassObject` and `ClassObjectMeta` schemas,
        and ensures that all necessary references are loaded and processed.

        Returns:
            None
        """
        buffer = []

        object_class = self.schemas.get_model(BaseClasses.OBJECT.value)
        for object_object in await (
            object_class.objects.using(LAKEHOUSE_DB_ALIAS)
            .filter(title=BaseClasses.CLASS_OBJECT.value)
            .order_by('_metadata__updated_at')
            .aexecute()
        ):
            object_schema = ObjectSchema(**object_object.model_dump())
            buffer.append((object_schema.title, object_schema, ModuleType.CORE))
            schema = object_schema_to_glue_schema(
                self._process_object_schema(object_schema, object_schema.title, buffer),
                schema_names=self.schemas.registered_model_names(),
            )
            schema.version = object_object.get_metadata().object_version
            schema.name = object_schema.title
