from _typeshed import Incomplete
from amsdal_models.migration.data_classes import MigrationFile as MigrationFile
from amsdal_utils.models.enums import ModuleType as ModuleType
from collections.abc import Iterator
from pathlib import Path

class MigrationsLoader:
    """
    Loads and manages migration files from a specified directory.
    """
    migrations_dir: Path
    _module_type: Incomplete
    _module_name: Incomplete
    _migrations_files: list[MigrationFile]
    def __init__(self, migrations_dir: Path, module_type: ModuleType, module_name: str | None = None) -> None: ...
    @property
    def has_initial_migration(self) -> bool:
        """
        Checks if there is an initial migration file.

        Returns:
            bool: True if there is an initial migration file, False otherwise.
        """
    @property
    def last_migration_number(self) -> int:
        """
        Gets the number of the last migration file.

        Returns:
            int: The number of the last migration file, or -1 if there are no migration files.
        """
    def __iter__(self) -> Iterator[MigrationFile]: ...
    def _load_migration_files(self) -> None: ...
