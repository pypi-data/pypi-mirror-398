import json
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any
from typing import ClassVar

from amsdal_utils.models.enums import ModuleType
from amsdal_utils.models.enums import Versions
from amsdal_utils.schemas.schema import ObjectSchema

from amsdal_models.classes.model import Model
from amsdal_models.migration.base_migration_schemas import BaseMigrationSchemas
from amsdal_models.migration.data_classes import MigrateOperation
from amsdal_models.migration.data_classes import MigrationFile
from amsdal_models.migration.data_classes import OperationTypes
from amsdal_models.migration.executors.state_executor import AsyncStateMigrationExecutor
from amsdal_models.migration.executors.state_executor import StateMigrationExecutor
from amsdal_models.migration.file_migration_executor import AsyncFileMigrationExecutorManager
from amsdal_models.migration.file_migration_executor import FileMigrationExecutorManager
from amsdal_models.migration.file_migration_store import AsyncBaseMigrationStore
from amsdal_models.migration.file_migration_store import BaseMigrationStore
from amsdal_models.migration.file_migration_writer import FileMigrationWriter
from amsdal_models.migration.migrations_loader import MigrationsLoader


class StateMigrationStore(BaseMigrationStore):
    def save_migration(self, migration: MigrationFile) -> None: ...

    def delete_migration(self, migration: MigrationFile) -> None: ...

    def fetch_migrations(self) -> list[MigrationFile]:
        return []


class AsyncStateMigrationStore(AsyncBaseMigrationStore):
    async def save_migration(self, migration: MigrationFile) -> None: ...

    async def delete_migration(self, migration: MigrationFile) -> None: ...

    async def fetch_migrations(self) -> list[MigrationFile]:
        return []


class StateMigrationSchemas(BaseMigrationSchemas):
    """
    Manages the state of migration schemas.

    Attributes:
        state (dict[str, tuple[ModuleType, ObjectSchema]]): A dictionary mapping class names to their schema types
            and object schemas.
    """

    def __init__(self) -> None:
        super().__init__()
        self.state: dict[str, tuple[ModuleType, ObjectSchema]] = {}

    def register_model(
        self,
        class_name: str,
        object_schema: ObjectSchema,
        module_type: ModuleType,
        class_version: str | Versions = Versions.LATEST,  # noqa: ARG002
    ) -> None:
        """
        Registers a model with the given class name, object schema, and schema type.

        Args:
            class_name (str): The name of the class to register.
            object_schema (ObjectSchema): The object schema of the class.
            module_type (ModuleType): The type of schema.

        Returns:
            None
        """
        self.state[class_name] = (module_type, object_schema)

    def unregister_model(self, class_name: str) -> None:
        """
        Unregisters a model with the given class name.

        Args:
            class_name (str): The name of the class to unregister.

        Returns:
            None
        """
        del self.state[class_name]

    def compile_buffered_classes(self) -> None: ...

    def compile_classes(
        self,
        class_schemas: list[tuple[str, ObjectSchema, ModuleType]],  # noqa: ARG002
        namespace: dict[str, Any],  # noqa: ARG002
    ) -> list[tuple[str, type[Model]]]:
        return []


class BaseFileMigrationGenerator:
    _operations: ClassVar[dict[OperationTypes, Callable[..., MigrateOperation]]] = {
        OperationTypes.CREATE_CLASS: lambda object_schema, module_type: MigrateOperation(
            type=OperationTypes.CREATE_CLASS,
            class_name=object_schema.title,
            old_schema=None,
            new_schema=object_schema,
            module_type=module_type,
        ),
        OperationTypes.UPDATE_CLASS: lambda old_schema, new_schema, module_type: MigrateOperation(
            type=OperationTypes.UPDATE_CLASS,
            class_name=old_schema.title,
            old_schema=old_schema,
            new_schema=new_schema,
            module_type=module_type,
        ),
        OperationTypes.DELETE_CLASS: lambda object_schema, module_type: MigrateOperation(
            type=OperationTypes.DELETE_CLASS,
            class_name=object_schema.title,
            old_schema=object_schema,
            new_schema=None,
            module_type=module_type,
        ),
    }

    _migrations_loader: MigrationsLoader
    _output_migrations_path: Path
    _module_path: str
    _module_type: ModuleType
    _state: dict[str, tuple[ModuleType, ObjectSchema]]

    @classmethod
    def build_operations(
        cls,
        module_type: ModuleType,
        class_schema: ObjectSchema,
        old_class_schema: ObjectSchema | None,
    ) -> list[MigrateOperation]:
        """
        Builds migration operations based on schema changes.

        Args:
            module_type (ModuleType): The type of schema.
            class_schema (ObjectSchema): The new class schema.
            old_class_schema (ObjectSchema | None): The old class schema. Defaults to None.

        Returns:
            list[MigrateOperation]: List of migration operations.
        """
        if not old_class_schema:
            return [
                cls._operations[OperationTypes.CREATE_CLASS](class_schema, module_type),
            ]

        schema_dump = json.dumps(class_schema.model_dump(), default=str, sort_keys=True)
        old_schema_dump = json.dumps(old_class_schema.model_dump(), default=str, sort_keys=True)

        if schema_dump == old_schema_dump:
            return []

        return [
            cls._operations[OperationTypes.UPDATE_CLASS](old_class_schema, class_schema, module_type),
        ]

    def write_migration_file(self, operations: list[MigrateOperation], name: str | None = None) -> MigrationFile:
        """
        Writes migration operations to a file.

        Args:
            operations (list[MigrateOperation]): List of migration operations.
            name (str | None): The name of the migration. Defaults to None.

        Returns:
            MigrationFile: The created migration file.
        """
        if self._migrations_loader.has_initial_migration:
            _name = name or self.generate_name_from_operations(operations)
        else:
            _name = name or 'initial'

        number = self._migrations_loader.last_migration_number + 1

        file_path = self._output_migrations_path / self._get_migration_file_name(
            number=number,
            name=_name,
        )

        FileMigrationWriter.write(file_path, operations)

        return MigrationFile(
            path=file_path,
            type=ModuleType.USER,
            number=number,
            module=self._module_path,
        )

    def write_data_migration_file(self, name: str | None = None) -> MigrationFile:
        """
        Writes data migration operations to a file.

        Args:
            name (str | None): The name of the migration. Defaults to None.

        Returns:
            MigrationFile: The created data migration file.
        """
        _name = name or uuid.uuid4().hex
        number = self._migrations_loader.last_migration_number + 1

        file_path = self._output_migrations_path / self._get_migration_file_name(
            number=number,
            name=_name,
        )

        FileMigrationWriter.write_data_migration(file_path)

        return MigrationFile(
            path=file_path,
            type=ModuleType.USER,
            number=number,
            module=self._module_path,
        )

    def generate_operations(self, schemas: list[ObjectSchema]) -> list[MigrateOperation]:
        """
        Generates migration operations based on schema changes.

        Args:
            schemas (list[ObjectSchema]): The list of schemas to be checked and generated operations from.

        Returns:
            list[MigrateOperation]: List of migration operations.
        """
        all_operations: list[MigrateOperation] = []
        class_names: list[str] = []

        for object_schema in schemas:
            operations = self.build_operations(
                self._module_type,
                object_schema,
                self._state.get(object_schema.title, [None, None])[1],
            )
            class_names.append(object_schema.title)
            all_operations.extend(operations)
            self._state[object_schema.title] = (self._module_type, object_schema)

        deleted_schemas = [
            _schema
            for _type, _schema in self._state.values()
            if _type == ModuleType.USER and _schema.title not in class_names
        ]

        all_operations.extend(
            [self._operations[OperationTypes.DELETE_CLASS](_schema, self._module_type) for _schema in deleted_schemas],
        )

        return all_operations

    @staticmethod
    def generate_name_from_operations(operations: list[MigrateOperation]) -> str:
        """
        Generates a name for the migration file based on operations.

        Args:
            operations (list[MigrateOperation]): List of migration operations.

        Returns:
            str: The generated name.
        """
        return f'{operations[0].type.lower()}_{operations[0].class_name}'.lower()

    @staticmethod
    def _get_migration_file_name(number: int, name: str) -> str:
        return f'{number:04d}_{name}.py'


class SimpleFileMigrationGenerator(BaseFileMigrationGenerator):
    def __init__(
        self,
        module_path: str,
        output_migrations_path: Path,
        module_type: ModuleType,
        state: dict[str, tuple[ModuleType, ObjectSchema]] | None = None,
    ) -> None:
        self._module_path = module_path
        self._output_migrations_path = output_migrations_path
        self._module_type = module_type
        self._migrations_loader = MigrationsLoader(self._output_migrations_path, module_type, module_name=module_path)
        self._state: dict[str, tuple[ModuleType, ObjectSchema]] = state if state is not None else {}

    @property
    def migrations_loader(self) -> MigrationsLoader:
        return self._migrations_loader

    def make_migrations(
        self,
        schemas: list[ObjectSchema],
        name: str | None = None,
        *,
        is_data: bool = False,
    ) -> MigrationFile:
        """
        Creates migration files based on schema changes.

        Args:
            schemas (list[ObjectSchema]): The list of schemas to be migrated.
            name (str | None): The name of the migration. Defaults to None.
            is_data (bool): If True, creates a data migration. Defaults to False.

        Returns:
            MigrationFile: The created migration file.

        Raises:
            UserWarning: If no changes are detected.
        """
        if is_data:
            return self.write_data_migration_file(name)

        all_operations: list[MigrateOperation] = self.generate_operations(schemas)

        if not all_operations:
            msg = 'No changes detected'
            raise UserWarning(msg)

        return self.write_migration_file(all_operations, name=name)


class FileMigrationGenerator:
    """
    Generates migration files based on schema changes.
    """

    def __init__(
        self,
        core_migrations_path: Path,
        app_migrations_path: Path,
        contrib_migrations_directory_name: str,
        app_module_path: str = 'models',
        module_type: ModuleType = ModuleType.USER,
    ) -> None:
        self._core_migrations_path = core_migrations_path
        self._contrib_migrations_directory_name = contrib_migrations_directory_name
        self._state: dict[str, tuple[ModuleType, ObjectSchema]] = {}
        self._app_file_migration_generator = SimpleFileMigrationGenerator(
            module_path=app_module_path,
            output_migrations_path=app_migrations_path,
            module_type=module_type,
            state=self._state,
        )

    @property
    def app_file_migration_generator(self) -> SimpleFileMigrationGenerator:
        return self._app_file_migration_generator

    def make_migrations(
        self,
        schemas: list[ObjectSchema],
        name: str | None = None,
        *,
        is_data: bool = False,
    ) -> MigrationFile:
        """
        Creates migration files based on schema changes.

        Args:
            schemas (list[ObjectSchema]): The list of schemas to be migrated.
            name (str | None): The name of the migration. Defaults to None.
            is_data (bool): If True, creates a data migration. Defaults to False.

        Returns:
            MigrationFile: The created migration file.

        Raises:
            UserWarning: If no changes are detected.
        """
        if not is_data:
            self.init_state()

        return self._app_file_migration_generator.make_migrations(
            schemas=schemas,
            name=name,
            is_data=is_data,
        )

    def init_state(self) -> None:
        schemas = StateMigrationSchemas()
        executor = StateMigrationExecutor(schemas, do_fetch_latest_version=False)
        executor_manager = FileMigrationExecutorManager(
            core_migrations_path=self._core_migrations_path,
            app_migrations_loader=self._app_file_migration_generator.migrations_loader,
            executor=executor,
            store=StateMigrationStore(),
            contrib_migrations_directory_name=self._contrib_migrations_directory_name,
        )
        executor_manager.execute(skip_data_migrations=True)
        self._state.update(schemas.state)


class AsyncSimpleFileMigrationGenerator(BaseFileMigrationGenerator):
    def __init__(
        self,
        module_path: str,
        output_migrations_path: Path,
        module_type: ModuleType,
        state: dict[str, tuple[ModuleType, ObjectSchema]] | None = None,
    ) -> None:
        self._module_path = module_path
        self._output_migrations_path = output_migrations_path
        self._module_type = module_type
        self._migrations_loader = MigrationsLoader(self._output_migrations_path, module_type, module_name=module_path)
        self._state: dict[str, tuple[ModuleType, ObjectSchema]] = state if state is not None else {}

    @property
    def migrations_loader(self) -> MigrationsLoader:
        return self._migrations_loader

    async def make_migrations(
        self,
        schemas: list[ObjectSchema],
        name: str | None = None,
        *,
        is_data: bool = False,
    ) -> MigrationFile:
        """
        Creates migration files based on schema changes.

        Args:
            schemas (list[ObjectSchema]): The list of schemas to be migrated.
            name (str | None): The name of the migration. Defaults to None.
            is_data (bool): If True, creates a data migration. Defaults to False.

        Returns:
            MigrationFile: The created migration file.

        Raises:
            UserWarning: If no changes are detected.
        """
        if is_data:
            return self.write_data_migration_file(name)

        all_operations: list[MigrateOperation] = self.generate_operations(schemas)

        if not all_operations:
            msg = 'No changes detected'
            raise UserWarning(msg)

        return self.write_migration_file(all_operations, name=name)


class AsyncFileMigrationGenerator:
    """
    Generates migration files based on schema changes.
    """

    def __init__(
        self,
        core_migrations_path: Path,
        app_migrations_path: Path,
        contrib_migrations_directory_name: str,
        app_module_path: str = 'models',
        module_type: ModuleType = ModuleType.USER,
    ) -> None:
        self._core_migrations_path = core_migrations_path
        self._contrib_migrations_directory_name = contrib_migrations_directory_name
        self._state: dict[str, tuple[ModuleType, ObjectSchema]] = {}
        self._app_file_migration_generator = AsyncSimpleFileMigrationGenerator(
            module_path=app_module_path,
            output_migrations_path=app_migrations_path,
            module_type=module_type,
            state=self._state,
        )

    @property
    def app_file_migration_generator(self) -> AsyncSimpleFileMigrationGenerator:
        return self._app_file_migration_generator

    async def make_migrations(
        self,
        schemas: list[ObjectSchema],
        name: str | None = None,
        *,
        is_data: bool = False,
    ) -> MigrationFile:
        """
        Creates migration files based on schema changes.

        Args:
            schemas (list[ObjectSchema]): The list of schemas to be migrated.
            name (str | None): The name of the migration. Defaults to None.
            is_data (bool): If True, creates a data migration. Defaults to False.

        Returns:
            MigrationFile: The created migration file.

        Raises:
            UserWarning: If no changes are detected.
        """

        if not is_data:
            await self.init_state()

        return await self._app_file_migration_generator.make_migrations(
            schemas=schemas,
            name=name,
            is_data=is_data,
        )

    async def init_state(self) -> None:
        schemas = StateMigrationSchemas()
        executor = AsyncStateMigrationExecutor(schemas, do_fetch_latest_version=False)
        executor_manager = AsyncFileMigrationExecutorManager(
            core_migrations_path=self._core_migrations_path,
            app_migrations_loader=self._app_file_migration_generator.migrations_loader,
            executor=executor,
            store=AsyncStateMigrationStore(),
            contrib_migrations_directory_name=self._contrib_migrations_directory_name,
        )
        await executor_manager.execute(skip_data_migrations=True)
        self._state.update(schemas.state)
