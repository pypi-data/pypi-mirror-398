import logging
from asyncio import iscoroutine
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from amsdal_data.transactions import async_transaction
from amsdal_data.transactions import transaction
from amsdal_utils.models.data_models.address import Address
from amsdal_utils.models.enums import ModuleType

from amsdal_models.migration.data_classes import MigrationDirection
from amsdal_models.migration.data_classes import MigrationFile
from amsdal_models.migration.data_classes import MigrationResult
from amsdal_models.migration.executors.base import AsyncBaseMigrationExecutor
from amsdal_models.migration.executors.base import BaseMigrationExecutor
from amsdal_models.migration.executors.state_executor import AsyncStateMigrationExecutor
from amsdal_models.migration.executors.state_executor import StateMigrationExecutor
from amsdal_models.migration.file_migration_store import AsyncBaseMigrationStore
from amsdal_models.migration.file_migration_store import AsyncFileMigrationStore
from amsdal_models.migration.file_migration_store import BaseMigrationStore
from amsdal_models.migration.file_migration_store import FileMigrationStore
from amsdal_models.migration.migrations import MigrateData
from amsdal_models.migration.migrations_loader import MigrationsLoader
from amsdal_models.migration.utils import build_migrations_module_name
from amsdal_models.migration.utils import contrib_to_module_root_path

if TYPE_CHECKING:
    from amsdal_models.migration.migrations import Migration

logger = logging.getLogger(__name__)


class BaseMigrationExecutorManager:
    migration_address: Address = Address.from_string('resource#Migration')
    _applied_migrations: list[MigrationFile]
    _module_type: ModuleType

    def _is_migration_applied(self, migration: MigrationFile) -> bool:
        for applied_migration in self._applied_migrations:
            if (
                applied_migration.number == migration.number
                and applied_migration.type == self._module_type
                and applied_migration.module == migration.module
            ):
                return True

        return False

    @staticmethod
    def get_migration_class(migration: MigrationFile) -> type['Migration']:
        """
        Retrieves the migration class from the migration file.

        Args:
            migration (MigrationFile): The migration file.

        Returns:
            type[Migration]: The migration class.
        """
        content = migration.path.read_text()
        code = compile(content, migration.path, 'exec')
        globs: dict[str, Any] = {}
        eval(code, globs)  # noqa: S307

        return globs['Migration']


class SimpleFileMigrationExecutorManager(BaseMigrationExecutorManager):
    def __init__(
        self,
        migrations_loader: MigrationsLoader,
        executor: BaseMigrationExecutor,
        module_type: ModuleType,
        applied_migrations: list[MigrationFile],
        store: BaseMigrationStore | None = None,
    ) -> None:
        self._migrations_loader = migrations_loader
        self._executor = executor
        self._module_type = module_type
        self._applied_migrations = applied_migrations
        self._store = store or FileMigrationStore(migrations_loader.migrations_dir)

    def execute(
        self,
        migration_number: int | None = None,
        *,
        fake: bool = False,
        skip_data_migrations: bool = False,
    ) -> list[MigrationResult]:
        """
        Executes the migrations.

        Args:
            migration_number (int | None): The migration number to execute up to. Defaults to None.
            fake (bool): If True, simulates the migration without applying changes. Defaults to False.
            skip_data_migrations (bool): If True, skips data migrations. Defaults to False.

        Returns:
            list[MigrationResult]: List of results from the migration execution.
        """
        self._store.init_migration_table()
        return self._apply(migration_number, fake=fake, skip_data_migrations=skip_data_migrations)  # type: ignore[arg-type]

    @transaction
    def _apply(
        self,
        migration_number: int | None = None,
        *,
        fake: bool = False,
        skip_data_migrations: bool = False,
    ) -> list[MigrationResult]:
        result: list[MigrationResult] = []

        migrations = [
            _migration
            for _migration in self._migrations_loader
            if migration_number is None or _migration.number <= migration_number
        ]

        last_migration = next(iter(migrations[-1:]), None)
        last_number = migration_number or getattr(last_migration, 'number', None)
        backward_migrations = sorted(
            [
                _migration
                for _migration in self._applied_migrations
                if last_number is not None and _migration.number > last_number
            ],
            key=lambda x: x.number,
            reverse=True,
        )

        self._init_state_from_applied_migrations(migrations)

        for _migration in backward_migrations:
            if _migration.module in (None, ModuleType.CORE):
                if str(_migration.path).startswith('migrations/'):
                    _migration.path = self._migrations_loader.migrations_dir / str(_migration.path).split('/', 1)[1]

            if not _migration.path.exists():
                logger.warning(
                    'Migration %s (%s) does not exist. Skipping backward migration.',
                    _migration.number,
                    _migration.path,
                )
                continue

            migration_class = self.get_migration_class(_migration)
            migration_class_instance = migration_class()

            if not fake:
                for _operation in migration_class_instance.operations:
                    if isinstance(_operation, MigrateData) and skip_data_migrations:
                        continue

                    _operation.backward(self._executor)

            self._store.delete_migration(_migration)

            result.append(
                MigrationResult(
                    direction=MigrationDirection.BACKWARD,
                    migration=_migration,
                ),
            )

        for _migration in migrations:
            migration_class = self.get_migration_class(_migration)
            migration_class_instance = migration_class()

            if self._is_migration_applied(_migration):
                for _operation in migration_class_instance.operations:
                    _operation.forward_schema(self._executor)

                continue

            if not fake:
                for _operation in migration_class_instance.operations:
                    if isinstance(_operation, MigrateData):
                        self._executor.flush_buffer()

                    if isinstance(_operation, MigrateData) and skip_data_migrations:
                        continue

                    _operation.forward(self._executor)

                self._executor.flush_buffer()

            self._store.save_migration(_migration)

            result.append(
                MigrationResult(
                    direction=MigrationDirection.FORWARD,
                    migration=_migration,
                ),
            )

        self._register_schemas(self._executor)

        return result

    def _init_state_from_applied_migrations(self, migrations: list[MigrationFile]) -> None:
        for _migration in migrations:
            migration_class = self.get_migration_class(_migration)
            migration_class_instance = migration_class()

            if self._is_migration_applied(_migration):
                state_executor = StateMigrationExecutor(
                    self._executor.schemas,
                    do_fetch_latest_version=True,
                )

                for _operation in migration_class_instance.operations:
                    if isinstance(_operation, MigrateData):
                        state_executor.flush_buffer()
                        continue

                    _operation.forward(state_executor)

                state_executor.flush_buffer()

    @staticmethod
    def _register_schemas(executor: BaseMigrationExecutor) -> None:
        if hasattr(executor, 'register_schemas'):
            executor.register_schemas()


class FileMigrationExecutorManager:
    """
    Manager class for executing file migrations.

    Attributes:
        migration_address (Address): The address associated with the migration.
        core_loader (MigrationsLoader): Loader for core migrations.
        contrib_loaders (list[MigrationsLoader]): List of loaders for contributed migrations.
        app_loader (MigrationsLoader): Loader for application migrations.
        executor (BaseMigrationExecutor): The executor responsible for running migrations.
        store (BaseMigrationStore): The store for managing migration files.
    """

    migration_address: Address = Address.from_string('resource#Migration')

    def __init__(
        self,
        core_migrations_path: Path,
        app_migrations_loader: MigrationsLoader,
        executor: BaseMigrationExecutor,
        store: BaseMigrationStore | None = None,
        contrib: list[str] | None = None,
        contrib_migrations_directory_name: str = 'migrations',
    ) -> None:
        self.core_loader = MigrationsLoader(
            migrations_dir=core_migrations_path,
            module_type=ModuleType.CORE,
            module_name=build_migrations_module_name(
                'amsdal',
                '__migrations__',
            ),
        )
        self.contrib_loaders = self._get_contrib_loaders(contrib or [], contrib_migrations_directory_name)
        self.app_loader = app_migrations_loader
        self.executor = executor
        self._applied_migration_files: list[MigrationFile] = []
        self._core_executor_manager: SimpleFileMigrationExecutorManager | None = None
        self._contrib_executor_managers: list[SimpleFileMigrationExecutorManager] = []
        self._app_executor_manager: SimpleFileMigrationExecutorManager | None = None

        self.store = store or FileMigrationStore(app_migrations_loader.migrations_dir)

    @property
    def app_executor_manager(self) -> SimpleFileMigrationExecutorManager:
        if self._app_executor_manager is None:
            msg = 'App executor manager is not initialized.'
            raise ValueError(msg)
        return self._app_executor_manager

    @property
    def core_executor_manager(self) -> SimpleFileMigrationExecutorManager:
        if self._core_executor_manager is None:
            msg = 'Core executor manager is not initialized.'
            raise ValueError(msg)
        return self._core_executor_manager

    def execute(
        self,
        migration_number: int | None = None,
        module_type: ModuleType | None = None,
        *,
        fake: bool = False,
        skip_data_migrations: bool = False,
    ) -> list[MigrationResult]:
        """
        Executes the migrations.

        Args:
            migration_number (int | None): The migration number to execute up to. Defaults to None.
            module_type (ModuleType | None): The type of module to migrate. Defaults to None.
            fake (bool): If True, simulates the migration without applying changes. Defaults to False.
            skip_data_migrations (bool): If True, skips data migrations. Defaults to False.

        Returns:
            list[MigrationResult]: List of results from the migration execution.
        """
        self.store.init_migration_table()
        self._applied_migration_files = self.store.fetch_migrations()
        self._core_executor_manager = SimpleFileMigrationExecutorManager(
            migrations_loader=self.core_loader,
            executor=self.executor,
            module_type=ModuleType.CORE,
            applied_migrations=[
                _migration for _migration in self._applied_migration_files if _migration.type == ModuleType.CORE
            ],
            store=self.store,
        )

        for _loader in self.contrib_loaders:
            self._contrib_executor_managers.append(
                SimpleFileMigrationExecutorManager(
                    migrations_loader=_loader,
                    executor=self.executor,
                    module_type=ModuleType.CONTRIB,
                    applied_migrations=[
                        _migration
                        for _migration in self._applied_migration_files
                        if _migration.type == ModuleType.CONTRIB and _migration.module == _loader._module_name
                    ],
                    store=self.store,
                ),
            )

        self._app_executor_manager = SimpleFileMigrationExecutorManager(
            migrations_loader=self.app_loader,
            executor=self.executor,
            module_type=ModuleType.USER,
            applied_migrations=[
                _migration for _migration in self._applied_migration_files if _migration.type == ModuleType.USER
            ],
            store=self.store,
        )

        return self._apply(  # type: ignore[call-arg]
            migration_number=migration_number,
            module_type=module_type,
            fake=fake,
            skip_data_migrations=skip_data_migrations,
        )

    @staticmethod
    def _get_contrib_loaders(contrib: list[str], contrib_migrations_directory_name: str) -> list[MigrationsLoader]:
        _loaders: list[MigrationsLoader] = []

        for _contrib in contrib:
            contrib_root_path = contrib_to_module_root_path(_contrib)

            _loaders.append(
                MigrationsLoader(
                    migrations_dir=contrib_root_path / contrib_migrations_directory_name,
                    module_type=ModuleType.CONTRIB,
                    module_name=build_migrations_module_name(
                        '.'.join(_contrib.split('.')[:-2]),
                        contrib_migrations_directory_name,
                    ),
                ),
            )

        return _loaders

    @transaction
    def _apply(
        self,
        migration_number: int | None = None,
        module_type: ModuleType | None = None,
        *,
        fake: bool = False,
        skip_data_migrations: bool = False,
    ) -> list[MigrationResult]:
        _migrations: list[MigrationResult] = []

        if module_type == ModuleType.CORE:
            return self.core_executor_manager.execute(
                migration_number=migration_number,
                fake=fake,
                skip_data_migrations=skip_data_migrations,
            )
        else:
            _migrations.extend(
                self.core_executor_manager.execute(
                    skip_data_migrations=skip_data_migrations,
                ),
            )

        if module_type == ModuleType.CONTRIB:
            for _manager in self._contrib_executor_managers:
                _migrations.extend(
                    _manager.execute(
                        migration_number=migration_number,
                        fake=fake,
                        skip_data_migrations=skip_data_migrations,
                    ),
                )

            return _migrations
        else:
            for _manager in self._contrib_executor_managers:
                _migrations.extend(
                    _manager.execute(
                        skip_data_migrations=skip_data_migrations,
                    ),
                )

        _migrations.extend(
            self.app_executor_manager.execute(
                migration_number=migration_number,
                fake=fake,
                skip_data_migrations=skip_data_migrations,
            ),
        )

        return _migrations


class AsyncSimpleFileMigrationExecutorManager(BaseMigrationExecutorManager):
    def __init__(
        self,
        migrations_loader: MigrationsLoader,
        executor: AsyncBaseMigrationExecutor,
        module_type: ModuleType,
        applied_migrations: list[MigrationFile],
        store: AsyncBaseMigrationStore | None = None,
    ) -> None:
        self._migrations_loader = migrations_loader
        self._executor = executor
        self._module_type = module_type
        self._applied_migrations = applied_migrations
        self._store = store or AsyncFileMigrationStore(migrations_loader.migrations_dir)

    async def execute(
        self,
        migration_number: int | None = None,
        *,
        fake: bool = False,
        skip_data_migrations: bool = False,
    ) -> list[MigrationResult]:
        """
        Executes the migrations.

        Args:
            migration_number (int | None): The migration number to execute up to. Defaults to None.
            fake (bool): If True, simulates the migration without applying changes. Defaults to False.
            skip_data_migrations (bool): If True, skips data migrations. Defaults to False.

        Returns:
            list[MigrationResult]: List of results from the migration execution.
        """
        await self._store.init_migration_table()
        return await self._apply(migration_number, fake=fake, skip_data_migrations=skip_data_migrations)  # type: ignore[arg-type]

    @async_transaction
    async def _apply(
        self,
        migration_number: int | None = None,
        *,
        fake: bool = False,
        skip_data_migrations: bool = False,
    ) -> list[MigrationResult]:
        result: list[MigrationResult] = []

        migrations = [
            _migration
            for _migration in self._migrations_loader
            if migration_number is None or _migration.number <= migration_number
        ]

        last_migration = next(iter(migrations[-1:]), None)
        last_number = migration_number or getattr(last_migration, 'number', None)
        backward_migrations = sorted(
            [
                _migration
                for _migration in self._applied_migrations
                if last_number is not None and _migration.number > last_number
            ],
            key=lambda x: x.number,
            reverse=True,
        )
        has_upapplied_migrations = any(True for _migration in migrations if not self._is_migration_applied(_migration))

        await self._init_state_from_applied_migrations(migrations)

        for _migration in backward_migrations:
            if _migration.module in (None, ModuleType.CORE):
                if str(_migration.path).startswith('migrations/'):
                    _migration.path = self._migrations_loader.migrations_dir / str(_migration.path).split('/', 1)[1]

            if not _migration.path.exists():
                logger.warning(
                    'Migration %s (%s) does not exist. Skipping backward migration.',
                    _migration.number,
                    _migration.path,
                )
                continue

            migration_class = self.get_migration_class(_migration)
            migration_class_instance = migration_class()

            if not fake:
                for _operation in migration_class_instance.operations:
                    if isinstance(_operation, MigrateData) and skip_data_migrations:
                        continue

                    backward_result = _operation.backward(self._executor)

                    if iscoroutine(backward_result):
                        await backward_result

                if not has_upapplied_migrations:
                    await self._executor.flush_buffer()

            await self._store.delete_migration(_migration)

            result.append(
                MigrationResult(
                    direction=MigrationDirection.BACKWARD,
                    migration=_migration,
                ),
            )

        for _migration in migrations:
            migration_class = self.get_migration_class(_migration)
            migration_class_instance = migration_class()

            if self._is_migration_applied(_migration):
                for _operation in migration_class_instance.operations:
                    _operation.forward_schema(self._executor)

                continue

            if not fake:
                for _operation in migration_class_instance.operations:
                    if isinstance(_operation, MigrateData):
                        await self._executor.flush_buffer()

                    if isinstance(_operation, MigrateData) and skip_data_migrations:
                        continue

                    forward_result = _operation.forward(self._executor)

                    if iscoroutine(forward_result):
                        await forward_result

                await self._executor.flush_buffer()

            await self._store.save_migration(_migration)

            result.append(
                MigrationResult(
                    direction=MigrationDirection.FORWARD,
                    migration=_migration,
                ),
            )

        await self._register_schemas(self._executor)

        return result

    async def _init_state_from_applied_migrations(self, migrations: list[MigrationFile]) -> None:
        for _migration in migrations:
            migration_class = self.get_migration_class(_migration)
            migration_class_instance = migration_class()

            if self._is_migration_applied(_migration):
                state_executor = AsyncStateMigrationExecutor(
                    self._executor.schemas,
                    do_fetch_latest_version=True,
                )

                for _operation in migration_class_instance.operations:
                    if isinstance(_operation, MigrateData):
                        await state_executor.flush_buffer()
                        continue

                    _operation.forward(state_executor)

                await state_executor.flush_buffer()

    @staticmethod
    async def _register_schemas(executor: BaseMigrationExecutor) -> None:
        if hasattr(executor, 'register_schemas'):
            await executor.register_schemas()


class AsyncFileMigrationExecutorManager:
    """
    Manager class for executing file migrations.

    Attributes:
        migration_address (Address): The address associated with the migration.
        core_loader (MigrationsLoader): Loader for core migrations.
        contrib_loaders (list[MigrationsLoader]): List of loaders for contributed migrations.
        app_loader (MigrationsLoader): Loader for application migrations.
        executor (BaseMigrationExecutor): The executor responsible for running migrations.
        store (BaseMigrationStore): The store for managing migration files.
    """

    migration_address: Address = Address.from_string('resource#Migration')

    def __init__(
        self,
        core_migrations_path: Path,
        app_migrations_loader: MigrationsLoader,
        executor: AsyncBaseMigrationExecutor,
        store: AsyncBaseMigrationStore | None = None,
        contrib: list[str] | None = None,
        contrib_migrations_directory_name: str = 'migrations',
    ) -> None:
        self.core_loader = MigrationsLoader(
            migrations_dir=core_migrations_path,
            module_type=ModuleType.CORE,
            module_name=build_migrations_module_name(
                'amsdal',
                '__migrations__',
            ),
        )
        self.contrib_loaders = self._get_contrib_loaders(contrib or [], contrib_migrations_directory_name)
        self.app_loader = app_migrations_loader
        self.executor = executor
        self._applied_migration_files: list[MigrationFile] = []
        self._core_executor_manager: AsyncSimpleFileMigrationExecutorManager | None = None
        self._contrib_executor_managers: list[AsyncSimpleFileMigrationExecutorManager] = []
        self._app_executor_manager: AsyncSimpleFileMigrationExecutorManager | None = None

        self.store = store or AsyncFileMigrationStore(app_migrations_loader.migrations_dir)

    @property
    def app_executor_manager(self) -> AsyncSimpleFileMigrationExecutorManager:
        if self._app_executor_manager is None:
            msg = 'App executor manager is not initialized.'
            raise ValueError(msg)
        return self._app_executor_manager

    @property
    def core_executor_manager(self) -> AsyncSimpleFileMigrationExecutorManager:
        if self._core_executor_manager is None:
            msg = 'Core executor manager is not initialized.'
            raise ValueError(msg)
        return self._core_executor_manager

    async def execute(
        self,
        migration_number: int | None = None,
        module_type: ModuleType | None = None,
        *,
        fake: bool = False,
        skip_data_migrations: bool = False,
    ) -> list[MigrationResult]:
        """
        Executes the migrations.

        Args:
            migration_number (int | None): The migration number to execute up to. Defaults to None.
            module_type (ModuleTypes | None): The type of module to migrate. Defaults to None.
            fake (bool): If True, simulates the migration without applying changes. Defaults to False.
            skip_data_migrations (bool): If True, skips data migrations. Defaults to False.

        Returns:
            list[MigrationResult]: List of results from the migration execution.
        """
        await self.store.init_migration_table()
        self._applied_migration_files = await self.store.fetch_migrations()
        self._core_executor_manager = AsyncSimpleFileMigrationExecutorManager(
            migrations_loader=self.core_loader,
            executor=self.executor,
            module_type=ModuleType.CORE,
            applied_migrations=[
                _migration for _migration in self._applied_migration_files if _migration.type == ModuleType.CORE
            ],
            store=self.store,
        )

        for _loader in self.contrib_loaders:
            self._contrib_executor_managers.append(
                AsyncSimpleFileMigrationExecutorManager(
                    migrations_loader=_loader,
                    executor=self.executor,
                    module_type=ModuleType.CONTRIB,
                    applied_migrations=[
                        _migration
                        for _migration in self._applied_migration_files
                        if _migration.type == ModuleType.CONTRIB and _migration.module == _loader._module_name
                    ],
                    store=self.store,
                ),
            )

        self._app_executor_manager = AsyncSimpleFileMigrationExecutorManager(
            migrations_loader=self.app_loader,
            executor=self.executor,
            module_type=ModuleType.USER,
            applied_migrations=[
                _migration for _migration in self._applied_migration_files if _migration.type == ModuleType.USER
            ],
            store=self.store,
        )

        return await self._apply(  # type: ignore[call-arg]
            migration_number=migration_number,
            module_type=module_type,
            fake=fake,
            skip_data_migrations=skip_data_migrations,
        )

    @staticmethod
    def _get_contrib_loaders(contrib: list[str], contrib_migrations_directory_name: str) -> list[MigrationsLoader]:
        _loaders: list[MigrationsLoader] = []

        for _contrib_name in contrib:
            contrib_root_path = contrib_to_module_root_path(_contrib_name)

            _loaders.append(
                MigrationsLoader(
                    migrations_dir=contrib_root_path / contrib_migrations_directory_name,
                    module_type=ModuleType.CONTRIB,
                    module_name=build_migrations_module_name(
                        '.'.join(_contrib_name.split('.')[:-2]),
                        contrib_migrations_directory_name,
                    ),
                ),
            )

        return _loaders

    @async_transaction
    async def _apply(
        self,
        migration_number: int | None = None,
        module_type: ModuleType | None = None,
        *,
        fake: bool = False,
        skip_data_migrations: bool = False,
    ) -> list[MigrationResult]:
        _migrations: list[MigrationResult] = []

        if module_type == ModuleType.CORE:
            return await self.core_executor_manager.execute(
                migration_number=migration_number,
                fake=fake,
                skip_data_migrations=skip_data_migrations,
            )
        else:
            _migrations.extend(
                await self.core_executor_manager.execute(
                    skip_data_migrations=skip_data_migrations,
                ),
            )

        if module_type == ModuleType.CONTRIB:
            for _manager in self._contrib_executor_managers:
                _migrations.extend(
                    await _manager.execute(
                        migration_number=migration_number,
                        fake=fake,
                        skip_data_migrations=skip_data_migrations,
                    ),
                )

            return _migrations
        else:
            for _manager in self._contrib_executor_managers:
                _migrations.extend(
                    await _manager.execute(
                        skip_data_migrations=skip_data_migrations,
                    ),
                )

        _migrations.extend(
            await self.app_executor_manager.execute(
                migration_number=migration_number,
                fake=fake,
                skip_data_migrations=skip_data_migrations,
            ),
        )

        return _migrations
