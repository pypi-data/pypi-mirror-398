import abc
from _typeshed import Incomplete
from abc import ABC, abstractmethod
from amsdal_models.migration.data_classes import MigrationFile as MigrationFile
from amsdal_models.migration.utils import module_name_to_migrations_path as module_name_to_migrations_path
from amsdal_models.querysets.query_builders.historical_builder import AsyncHistoricalQueryBuilder as AsyncHistoricalQueryBuilder, HistoricalQueryBuilder as HistoricalQueryBuilder
from amsdal_utils.models.data_models.address import Address
from pathlib import Path
from typing import Any, ClassVar

class BaseMigrationStore(ABC, metaclass=abc.ABCMeta):
    def init_migration_table(self) -> None: ...
    @abstractmethod
    def fetch_migrations(self) -> list[MigrationFile]: ...
    @abstractmethod
    def save_migration(self, migration: MigrationFile) -> None: ...
    @abstractmethod
    def delete_migration(self, migration: MigrationFile) -> None: ...

class AsyncBaseMigrationStore(ABC, metaclass=abc.ABCMeta):
    async def init_migration_table(self) -> None: ...
    @abstractmethod
    async def fetch_migrations(self) -> list[MigrationFile]: ...
    @abstractmethod
    async def save_migration(self, migration: MigrationFile) -> None: ...
    @abstractmethod
    async def delete_migration(self, migration: MigrationFile) -> None: ...

class FileMigrationStore(BaseMigrationStore):
    """
    Manages the storage and retrieval of migration files.

    Attributes:
        migration_address (Address): The address associated with the migration.
    """
    MIGRATION_TABLE: ClassVar[str]
    migration_address: Address
    _app_migrations_path: Incomplete
    _operation_manager: Incomplete
    def __init__(self, app_migrations_path: Path) -> None: ...
    def init_migration_table(self) -> None: ...
    def fetch_migrations(self) -> list[MigrationFile]:
        """
        Fetches the list of applied migrations.

        Returns:
            list[MigrationFile]: List of applied migration files.
        """
    def save_migration(self, migration: MigrationFile) -> None:
        """
        Saves a migration file.

        Args:
            migration (MigrationFile): The migration file to save.

        Returns:
            None
        """
    def delete_migration(self, migration: MigrationFile) -> None:
        """
        Deletes a migration file.

        Args:
            migration (MigrationFile): The migration file to delete.

        Returns:
            None
        """
    def _save_historical_data(self, address: Address, data: dict[str, Any], metadata: dict[str, Any]) -> None: ...
    @staticmethod
    def _build_migration_data(migration: MigrationFile) -> dict[str, Any]: ...
    @classmethod
    def _build_migration_metadata(cls, migration: MigrationFile, object_id: str | None = None) -> tuple[Address, dict[str, Any]]: ...
    def _init_migration_table(self) -> None: ...

class AsyncFileMigrationStore(AsyncBaseMigrationStore):
    """
    Manages the storage and retrieval of migration files.

    Attributes:
        migration_address (Address): The address associated with the migration.
    """
    MIGRATION_TABLE: ClassVar[str]
    migration_address: Address
    _app_migrations_path: Incomplete
    _operation_manager: Incomplete
    def __init__(self, app_migrations_path: Path) -> None: ...
    async def init_migration_table(self) -> None: ...
    async def fetch_migrations(self) -> list[MigrationFile]:
        """
        Fetches the list of applied migrations.

        Returns:
            list[MigrationFile]: List of applied migration files.
        """
    async def save_migration(self, migration: MigrationFile) -> None:
        """
        Saves a migration file.

        Args:
            migration (MigrationFile): The migration file to save.

        Returns:
            None
        """
    async def delete_migration(self, migration: MigrationFile) -> None:
        """
        Deletes a migration file.

        Args:
            migration (MigrationFile): The migration file to delete.

        Returns:
            None
        """
    async def _save_historical_data(self, address: Address, data: dict[str, Any], metadata: dict[str, Any]) -> None: ...
    @staticmethod
    def _build_migration_data(migration: MigrationFile) -> dict[str, Any]: ...
    @classmethod
    def _build_migration_metadata(cls, migration: MigrationFile, object_id: str | None = None) -> tuple[Address, dict[str, Any]]: ...
    async def _init_migration_table(self) -> None: ...
