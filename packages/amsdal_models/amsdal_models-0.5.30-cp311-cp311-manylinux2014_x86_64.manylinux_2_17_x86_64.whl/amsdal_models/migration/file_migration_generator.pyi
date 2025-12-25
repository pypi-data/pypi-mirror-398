from _typeshed import Incomplete
from amsdal_models.classes.model import Model as Model
from amsdal_models.migration.base_migration_schemas import BaseMigrationSchemas as BaseMigrationSchemas
from amsdal_models.migration.data_classes import MigrateOperation as MigrateOperation, MigrationFile as MigrationFile, OperationTypes as OperationTypes
from amsdal_models.migration.executors.state_executor import AsyncStateMigrationExecutor as AsyncStateMigrationExecutor, StateMigrationExecutor as StateMigrationExecutor
from amsdal_models.migration.file_migration_executor import AsyncFileMigrationExecutorManager as AsyncFileMigrationExecutorManager, FileMigrationExecutorManager as FileMigrationExecutorManager
from amsdal_models.migration.file_migration_store import AsyncBaseMigrationStore as AsyncBaseMigrationStore, BaseMigrationStore as BaseMigrationStore
from amsdal_models.migration.file_migration_writer import FileMigrationWriter as FileMigrationWriter
from amsdal_models.migration.migrations_loader import MigrationsLoader as MigrationsLoader
from amsdal_utils.models.enums import ModuleType, Versions
from amsdal_utils.schemas.schema import ObjectSchema as ObjectSchema
from collections.abc import Callable as Callable
from pathlib import Path
from typing import Any, ClassVar

class StateMigrationStore(BaseMigrationStore):
    def save_migration(self, migration: MigrationFile) -> None: ...
    def delete_migration(self, migration: MigrationFile) -> None: ...
    def fetch_migrations(self) -> list[MigrationFile]: ...

class AsyncStateMigrationStore(AsyncBaseMigrationStore):
    async def save_migration(self, migration: MigrationFile) -> None: ...
    async def delete_migration(self, migration: MigrationFile) -> None: ...
    async def fetch_migrations(self) -> list[MigrationFile]: ...

class StateMigrationSchemas(BaseMigrationSchemas):
    """
    Manages the state of migration schemas.

    Attributes:
        state (dict[str, tuple[ModuleType, ObjectSchema]]): A dictionary mapping class names to their schema types
            and object schemas.
    """
    state: dict[str, tuple[ModuleType, ObjectSchema]]
    def __init__(self) -> None: ...
    def register_model(self, class_name: str, object_schema: ObjectSchema, module_type: ModuleType, class_version: str | Versions = ...) -> None:
        """
        Registers a model with the given class name, object schema, and schema type.

        Args:
            class_name (str): The name of the class to register.
            object_schema (ObjectSchema): The object schema of the class.
            module_type (ModuleType): The type of schema.

        Returns:
            None
        """
    def unregister_model(self, class_name: str) -> None:
        """
        Unregisters a model with the given class name.

        Args:
            class_name (str): The name of the class to unregister.

        Returns:
            None
        """
    def compile_buffered_classes(self) -> None: ...
    def compile_classes(self, class_schemas: list[tuple[str, ObjectSchema, ModuleType]], namespace: dict[str, Any]) -> list[tuple[str, type[Model]]]: ...

class BaseFileMigrationGenerator:
    _operations: ClassVar[dict[OperationTypes, Callable[..., MigrateOperation]]]
    _migrations_loader: MigrationsLoader
    _output_migrations_path: Path
    _module_path: str
    _module_type: ModuleType
    _state: dict[str, tuple[ModuleType, ObjectSchema]]
    @classmethod
    def build_operations(cls, module_type: ModuleType, class_schema: ObjectSchema, old_class_schema: ObjectSchema | None) -> list[MigrateOperation]:
        """
        Builds migration operations based on schema changes.

        Args:
            module_type (ModuleType): The type of schema.
            class_schema (ObjectSchema): The new class schema.
            old_class_schema (ObjectSchema | None): The old class schema. Defaults to None.

        Returns:
            list[MigrateOperation]: List of migration operations.
        """
    def write_migration_file(self, operations: list[MigrateOperation], name: str | None = None) -> MigrationFile:
        """
        Writes migration operations to a file.

        Args:
            operations (list[MigrateOperation]): List of migration operations.
            name (str | None): The name of the migration. Defaults to None.

        Returns:
            MigrationFile: The created migration file.
        """
    def write_data_migration_file(self, name: str | None = None) -> MigrationFile:
        """
        Writes data migration operations to a file.

        Args:
            name (str | None): The name of the migration. Defaults to None.

        Returns:
            MigrationFile: The created data migration file.
        """
    def generate_operations(self, schemas: list[ObjectSchema]) -> list[MigrateOperation]:
        """
        Generates migration operations based on schema changes.

        Args:
            schemas (list[ObjectSchema]): The list of schemas to be checked and generated operations from.

        Returns:
            list[MigrateOperation]: List of migration operations.
        """
    @staticmethod
    def generate_name_from_operations(operations: list[MigrateOperation]) -> str:
        """
        Generates a name for the migration file based on operations.

        Args:
            operations (list[MigrateOperation]): List of migration operations.

        Returns:
            str: The generated name.
        """
    @staticmethod
    def _get_migration_file_name(number: int, name: str) -> str: ...

class SimpleFileMigrationGenerator(BaseFileMigrationGenerator):
    _module_path: Incomplete
    _output_migrations_path: Incomplete
    _module_type: Incomplete
    _migrations_loader: Incomplete
    _state: dict[str, tuple[ModuleType, ObjectSchema]]
    def __init__(self, module_path: str, output_migrations_path: Path, module_type: ModuleType, state: dict[str, tuple[ModuleType, ObjectSchema]] | None = None) -> None: ...
    @property
    def migrations_loader(self) -> MigrationsLoader: ...
    def make_migrations(self, schemas: list[ObjectSchema], name: str | None = None, *, is_data: bool = False) -> MigrationFile:
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

class FileMigrationGenerator:
    """
    Generates migration files based on schema changes.
    """
    _core_migrations_path: Incomplete
    _contrib_migrations_directory_name: Incomplete
    _state: dict[str, tuple[ModuleType, ObjectSchema]]
    _app_file_migration_generator: Incomplete
    def __init__(self, core_migrations_path: Path, app_migrations_path: Path, contrib_migrations_directory_name: str, app_module_path: str = 'models', module_type: ModuleType = ...) -> None: ...
    @property
    def app_file_migration_generator(self) -> SimpleFileMigrationGenerator: ...
    def make_migrations(self, schemas: list[ObjectSchema], name: str | None = None, *, is_data: bool = False) -> MigrationFile:
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
    def init_state(self) -> None: ...

class AsyncSimpleFileMigrationGenerator(BaseFileMigrationGenerator):
    _module_path: Incomplete
    _output_migrations_path: Incomplete
    _module_type: Incomplete
    _migrations_loader: Incomplete
    _state: dict[str, tuple[ModuleType, ObjectSchema]]
    def __init__(self, module_path: str, output_migrations_path: Path, module_type: ModuleType, state: dict[str, tuple[ModuleType, ObjectSchema]] | None = None) -> None: ...
    @property
    def migrations_loader(self) -> MigrationsLoader: ...
    async def make_migrations(self, schemas: list[ObjectSchema], name: str | None = None, *, is_data: bool = False) -> MigrationFile:
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

class AsyncFileMigrationGenerator:
    """
    Generates migration files based on schema changes.
    """
    _core_migrations_path: Incomplete
    _contrib_migrations_directory_name: Incomplete
    _state: dict[str, tuple[ModuleType, ObjectSchema]]
    _app_file_migration_generator: Incomplete
    def __init__(self, core_migrations_path: Path, app_migrations_path: Path, contrib_migrations_directory_name: str, app_module_path: str = 'models', module_type: ModuleType = ...) -> None: ...
    @property
    def app_file_migration_generator(self) -> AsyncSimpleFileMigrationGenerator: ...
    async def make_migrations(self, schemas: list[ObjectSchema], name: str | None = None, *, is_data: bool = False) -> MigrationFile:
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
    async def init_state(self) -> None: ...
