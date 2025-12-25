import json
from pathlib import Path
from typing import ClassVar

import black

from amsdal_models.migration.data_classes import MigrateOperation
from amsdal_models.migration.data_classes import OperationTypes


class FileMigrationWriter:
    """
    Handles the writing of migration files.

    Attributes:
        template_path (Path): The path to the migration template file.
        data_template_path (Path): The path to the data migration template file.
        operation_name_map (ClassVar[dict[OperationTypes, str]]): A mapping of operation types to their
            string representations.
    """

    template_path: Path = Path(__file__).parent / 'templates' / 'migration.tmpl'
    data_template_path: Path = Path(__file__).parent / 'templates' / 'data_migration.tmpl'
    operation_name_map: ClassVar[dict[OperationTypes, str]] = {
        OperationTypes.CREATE_CLASS: 'CreateClass',
        OperationTypes.UPDATE_CLASS: 'UpdateClass',
        OperationTypes.DELETE_CLASS: 'DeleteClass',
    }

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
        file_path.parent.mkdir(exist_ok=True, parents=True)
        file_path.write_text(
            cls.reformat(cls.render(operations)),
        )

    @classmethod
    def write_data_migration(cls, file_path: Path) -> None:
        """
        Writes a data migration to a file.

        Args:
            file_path (Path): The path to the data migration file.

        Returns:
            None
        """
        file_path.parent.mkdir(exist_ok=True, parents=True)
        file_path.write_text(
            cls.reformat(cls.data_template_path.read_text()),
        )

    @classmethod
    def render(cls, operations: list[MigrateOperation]) -> str:
        """
        Renders the migration operations into a string.

        Args:
            operations (list[MigrateOperation]): The list of migration operations to render.

        Returns:
            str: The rendered migration operations as a string.
        """
        _operations: list[str] = [cls.render_operation(operation) for operation in operations]

        template = cls.template_path.read_text()

        return template.replace('{{operations}}', ','.join(_operations) + (',' if _operations else ''))

    @classmethod
    def render_operation(cls, operation: MigrateOperation) -> str:
        """
        Renders a single migration operation into a string.

        Args:
            operation (MigrateOperation): The migration operation to render.

        Returns:
            str: The rendered migration operation as a string.
        """
        operation_name = cls.operation_name_map[operation.type]
        _args = [
            f'module_type=ModuleType.{operation.module_type.name}',
            f'class_name="{operation.class_name}"',
        ]

        if operation.old_schema:
            _schema = operation.old_schema.model_dump_json(exclude_defaults=True, exclude_unset=True)
            _args.append(f'old_schema={json.loads(_schema)!s}')

        if operation.new_schema:
            _schema = operation.new_schema.model_dump_json(exclude_defaults=True, exclude_unset=True)
            _args.append(f'new_schema={json.loads(_schema)!s}')

        operation_args = ', '.join(_args)

        return f'migrations.{operation_name}({operation_args})'

    @classmethod
    def reformat(cls, content: str) -> str:
        """
        Reformats the content using the Black formatter.

        Args:
            content (str): The content to reformat.

        Returns:
            str: The reformatted content.
        """
        return black.format_str(
            content,
            mode=black.FileMode(
                string_normalization=True,
                target_versions={black.TargetVersion.PY310},  # type: ignore[attr-defined]
                line_length=120,
            ),
        )
