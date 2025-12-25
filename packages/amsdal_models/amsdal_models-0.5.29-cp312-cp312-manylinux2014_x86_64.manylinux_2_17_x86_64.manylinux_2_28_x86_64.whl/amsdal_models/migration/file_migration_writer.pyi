from amsdal_models.migration.data_classes import MigrateOperation as MigrateOperation, OperationTypes as OperationTypes
from pathlib import Path
from typing import ClassVar

class FileMigrationWriter:
    """
    Handles the writing of migration files.

    Attributes:
        template_path (Path): The path to the migration template file.
        data_template_path (Path): The path to the data migration template file.
        operation_name_map (ClassVar[dict[OperationTypes, str]]): A mapping of operation types to their
            string representations.
    """
    template_path: Path
    data_template_path: Path
    operation_name_map: ClassVar[dict[OperationTypes, str]]
    @classmethod
    def write(cls, file_path: Path, operations: list[MigrateOperation]) -> None:
        """
        Writes the migration operations to a file.

        Args:
            file_path (Path): The path to the migration file.
            operations (list[MigrateOperation]): The list of migration operations to write.

        Returns:
            None
        """
    @classmethod
    def write_data_migration(cls, file_path: Path) -> None:
        """
        Writes a data migration to a file.

        Args:
            file_path (Path): The path to the data migration file.

        Returns:
            None
        """
    @classmethod
    def render(cls, operations: list[MigrateOperation]) -> str:
        """
        Renders the migration operations into a string.

        Args:
            operations (list[MigrateOperation]): The list of migration operations to render.

        Returns:
            str: The rendered migration operations as a string.
        """
    @classmethod
    def render_operation(cls, operation: MigrateOperation) -> str:
        """
        Renders a single migration operation into a string.

        Args:
            operation (MigrateOperation): The migration operation to render.

        Returns:
            str: The rendered migration operation as a string.
        """
    @classmethod
    def reformat(cls, content: str) -> str:
        """
        Reformats the content using the Black formatter.

        Args:
            content (str): The content to reformat.

        Returns:
            str: The reformatted content.
        """
