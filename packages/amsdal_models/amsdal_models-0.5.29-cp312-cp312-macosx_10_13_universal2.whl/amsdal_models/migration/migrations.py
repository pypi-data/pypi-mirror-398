from abc import ABC
from abc import abstractmethod
from collections.abc import Callable
from typing import Any

from amsdal_data.connections.historical.data_query_transform import META_SCHEMA_FOREIGN_KEYS
from amsdal_utils.models.enums import ModuleType
from amsdal_utils.schemas.schema import ObjectSchema

from amsdal_models.migration.base_migration_schemas import BaseMigrationSchemas
from amsdal_models.migration.base_migration_schemas import DefaultMigrationSchemas
from amsdal_models.migration.executors.base import BaseMigrationExecutor


class Operation(ABC):
    @abstractmethod
    def forward(self, executor: BaseMigrationExecutor) -> None: ...

    @abstractmethod
    def forward_schema(self, executor: BaseMigrationExecutor) -> None: ...

    @abstractmethod
    def backward(self, executor: BaseMigrationExecutor) -> None: ...


class SchemaOperation(Operation):
    """
    Base class for schema operations.

    Attributes:
        forward_args (list[Any]): Arguments for the forward operation.
        backward_args (list[Any]): Arguments for the backward operation.
        forward_method_name (str): Name of the method to call for the forward operation.
        backward_method_name (str): Name of the method to call for the backward operation.
    """

    forward_args: list[Any]
    backward_args: list[Any]
    forward_method_name: str
    backward_method_name: str

    def forward(self, executor: BaseMigrationExecutor) -> None:
        """
        Executes the forward operation.

        Args:
            executor (BaseMigrationExecutor): The executor responsible for running migrations.

        Returns:
            None
        """
        getattr(executor, self.forward_method_name)(
            executor.schemas,
            *self.forward_args,
        )

    def forward_schema(self, executor: BaseMigrationExecutor) -> None:
        """
        Executes the forward schema operation.

        Args:
            executor (BaseMigrationExecutor): The executor responsible for running migrations.

        Returns:
            None
        """
        executor.forward_schema(
            executor.schemas,
            *self.forward_args,
        )

    def backward(self, executor: BaseMigrationExecutor) -> None:
        """
        Executes the backward operation.

        Args:
            executor (BaseMigrationExecutor): The executor responsible for running migrations.

        Returns:
            None
        """
        getattr(executor, self.backward_method_name)(
            executor.schemas,
            *self.backward_args,
        )


class CreateClass(SchemaOperation):
    """
    Represents an operation to create a class schema.

    Attributes:
        forward_method_name (str): The name of the method to call for the forward operation.
        backward_method_name (str): The name of the method to call for the backward operation.
        forward_args (list[Any]): Arguments for the forward operation.
        backward_args (list[Any]): Arguments for the backward operation.
    """

    forward_method_name: str = 'create_class'
    backward_method_name: str = 'delete_class'

    def __init__(self, class_name: str, new_schema: dict[str, Any], module_type: ModuleType) -> None:
        self.forward_args = [class_name, ObjectSchema(**new_schema), module_type]
        self.backward_args = [class_name, module_type]


class UpdateClass(SchemaOperation):
    """
    Represents an operation to update a class schema.

    Attributes:
        forward_method_name (str): The name of the method to call for the forward operation.
        backward_method_name (str): The name of the method to call for the backward operation.
        forward_args (list[Any]): Arguments for the forward operation.
        backward_args (list[Any]): Arguments for the backward operation.
    """

    forward_method_name: str = 'update_class'
    backward_method_name: str = 'update_class'

    def __init__(
        self,
        class_name: str,
        old_schema: dict[str, Any],
        new_schema: dict[str, Any],
        module_type: ModuleType,
    ) -> None:
        new_context = self._build_execution_context(old_schema)
        old_context = self._build_execution_context(new_schema)

        self.forward_args = [class_name, ObjectSchema(**new_schema), module_type, new_context]
        self.backward_args = [class_name, ObjectSchema(**old_schema), module_type, old_context]

    @staticmethod
    def _build_execution_context(from_schema: dict[str, Any]) -> dict[str, Any]:
        execution_context = {}
        old_fk_metadata = from_schema.get('storage_metadata', {}).get('foreign_keys', {})

        if old_fk_metadata:
            execution_context[META_SCHEMA_FOREIGN_KEYS] = old_fk_metadata

        return execution_context


class DeleteClass(SchemaOperation):
    """
    Represents an operation to delete a class schema.

    Attributes:
        forward_method_name (str): The name of the method to call for the forward operation.
        backward_method_name (str): The name of the method to call for the backward operation.
        forward_args (list[Any]): Arguments for the forward operation.
        backward_args (list[Any]): Arguments for the backward operation.
    """

    forward_method_name: str = 'delete_class'
    backward_method_name: str = 'create_class'

    def __init__(self, class_name: str, old_schema: dict[str, Any], module_type: ModuleType) -> None:
        self.forward_args = [class_name, module_type]
        self.backward_args = [class_name, ObjectSchema(**old_schema), module_type]


class MigrationSchemas(DefaultMigrationSchemas): ...


class MigrateData(Operation):
    r"""
    Represents a data migration operation.

    Attributes:
        forward_migration (Callable[[MigrationSchemas \| BaseMigrationSchemas], None]): The function to call for
            the forward migration.
        backward_migration (Callable[[MigrationSchemas \| BaseMigrationSchemas], None]): The function to call for
            the backward migration.
    """

    @staticmethod
    def noop(schemas: MigrationSchemas) -> None: ...

    def __init__(
        self,
        forward_migration: Callable[[MigrationSchemas | BaseMigrationSchemas], None],
        backward_migration: Callable[[MigrationSchemas | BaseMigrationSchemas], None],
    ) -> None:
        self.forward_migration = forward_migration
        self.backward_migration = backward_migration

    def forward(self, executor: BaseMigrationExecutor) -> Any:
        """
        Executes the forward data migration.

        Args:
            executor (BaseMigrationExecutor): The executor responsible for running migrations.

        Returns:
            Any
        """
        return self.forward_migration(executor.schemas)

    def backward(self, executor: BaseMigrationExecutor) -> Any:
        """
        Executes the backward data migration.

        Args:
            executor (BaseMigrationExecutor): The executor responsible for running migrations.

        Returns:
            Any
        """
        return self.backward_migration(executor.schemas)

    def forward_schema(self, executor: BaseMigrationExecutor) -> None:
        """
        No-op for forward schema in data migration.

        Args:
            executor (BaseMigrationExecutor): The executor responsible for running migrations.

        Returns:
            None
        """
        pass


class Migration:
    """
    Represents a collection of migration operations.

    Attributes:
        operations (list[Operation]): The list of migration operations.
    """

    operations: list[Operation]
