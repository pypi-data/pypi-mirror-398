from collections.abc import Iterator
from pathlib import Path

from amsdal_utils.models.enums import ModuleType

from amsdal_models.migration.data_classes import MigrationFile


class MigrationsLoader:
    """
    Loads and manages migration files from a specified directory.
    """

    migrations_dir: Path

    def __init__(
        self,
        migrations_dir: Path,
        module_type: ModuleType,
        module_name: str | None = None,
    ) -> None:
        self.migrations_dir = migrations_dir
        self._module_type = module_type
        self._module_name = module_name
        self._migrations_files: list[MigrationFile] = []
        self._load_migration_files()

    @property
    def has_initial_migration(self) -> bool:
        """
        Checks if there is an initial migration file.

        Returns:
            bool: True if there is an initial migration file, False otherwise.
        """
        return bool([True for _migration_file in self._migrations_files if _migration_file.is_initial])

    @property
    def last_migration_number(self) -> int:
        """
        Gets the number of the last migration file.

        Returns:
            int: The number of the last migration file, or -1 if there are no migration files.
        """
        try:
            return self._migrations_files[-1].number
        except IndexError:
            return -1

    def __iter__(self) -> Iterator[MigrationFile]:
        return iter(self._migrations_files)

    def _load_migration_files(self) -> None:
        if not self.migrations_dir.exists():
            return

        for _file in self.migrations_dir.iterdir():
            if not _file.is_file():
                continue

            if not _file.suffix.lower() == '.py':
                continue

            self._migrations_files.append(
                MigrationFile(
                    path=_file,
                    type=self._module_type,
                    module=self._module_name,
                    number=int(_file.stem.split('_', 1)[0]),
                ),
            )

        self._migrations_files.sort(key=lambda _migration: _migration.number)
