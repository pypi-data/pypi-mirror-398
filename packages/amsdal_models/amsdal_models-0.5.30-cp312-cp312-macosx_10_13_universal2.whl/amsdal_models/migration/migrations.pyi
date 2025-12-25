import abc
from _typeshed import Incomplete
from abc import ABC, abstractmethod
from amsdal_models.migration.base_migration_schemas import BaseMigrationSchemas as BaseMigrationSchemas, DefaultMigrationSchemas as DefaultMigrationSchemas
from amsdal_models.migration.executors.base import BaseMigrationExecutor as BaseMigrationExecutor
from amsdal_utils.models.enums import ModuleType as ModuleType
from collections.abc import Callable as Callable
from typing import Any

class Operation(ABC, metaclass=abc.ABCMeta):
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
    def forward_schema(self, executor: BaseMigrationExecutor) -> None:
        """
        Executes the forward schema operation.

        Args:
            executor (BaseMigrationExecutor): The executor responsible for running migrations.

        Returns:
            None
        """
    def backward(self, executor: BaseMigrationExecutor) -> None:
        """
        Executes the backward operation.

        Args:
            executor (BaseMigrationExecutor): The executor responsible for running migrations.

        Returns:
            None
        """

class CreateClass(SchemaOperation):
    """
    Represents an operation to create a class schema.

    Attributes:
        forward_method_name (str): The name of the method to call for the forward operation.
        backward_method_name (str): The name of the method to call for the backward operation.
        forward_args (list[Any]): Arguments for the forward operation.
        backward_args (list[Any]): Arguments for the backward operation.
    """
    forward_method_name: str
    backward_method_name: str
    forward_args: Incomplete
    backward_args: Incomplete
    def __init__(self, class_name: str, new_schema: dict[str, Any], module_type: ModuleType) -> None: ...

class UpdateClass(SchemaOperation):
    """
    Represents an operation to update a class schema.

    Attributes:
        forward_method_name (str): The name of the method to call for the forward operation.
        backward_method_name (str): The name of the method to call for the backward operation.
        forward_args (list[Any]): Arguments for the forward operation.
        backward_args (list[Any]): Arguments for the backward operation.
    """
    forward_method_name: str
    backward_method_name: str
    forward_args: Incomplete
    backward_args: Incomplete
    def __init__(self, class_name: str, old_schema: dict[str, Any], new_schema: dict[str, Any], module_type: ModuleType) -> None: ...
    @staticmethod
    def _build_execution_context(from_schema: dict[str, Any]) -> dict[str, Any]: ...

class DeleteClass(SchemaOperation):
    """
    Represents an operation to delete a class schema.

    Attributes:
        forward_method_name (str): The name of the method to call for the forward operation.
        backward_method_name (str): The name of the method to call for the backward operation.
        forward_args (list[Any]): Arguments for the forward operation.
        backward_args (list[Any]): Arguments for the backward operation.
    """
    forward_method_name: str
    backward_method_name: str
    forward_args: Incomplete
    backward_args: Incomplete
    def __init__(self, class_name: str, old_schema: dict[str, Any], module_type: ModuleType) -> None: ...

class MigrationSchemas(DefaultMigrationSchemas): ...

class MigrateData(Operation):
    """
    Represents a data migration operation.

    Attributes:
        forward_migration (Callable[[MigrationSchemas \\| BaseMigrationSchemas], None]): The function to call for
            the forward migration.
        backward_migration (Callable[[MigrationSchemas \\| BaseMigrationSchemas], None]): The function to call for
            the backward migration.
    """
    @staticmethod
    def noop(schemas: MigrationSchemas) -> None: ...
    forward_migration: Incomplete
    backward_migration: Incomplete
    def __init__(self, forward_migration: Callable[[MigrationSchemas | BaseMigrationSchemas], None], backward_migration: Callable[[MigrationSchemas | BaseMigrationSchemas], None]) -> None: ...
    def forward(self, executor: BaseMigrationExecutor) -> Any:
        """
        Executes the forward data migration.

        Args:
            executor (BaseMigrationExecutor): The executor responsible for running migrations.

        Returns:
            Any
        """
    def backward(self, executor: BaseMigrationExecutor) -> Any:
        """
        Executes the backward data migration.

        Args:
            executor (BaseMigrationExecutor): The executor responsible for running migrations.

        Returns:
            Any
        """
    def forward_schema(self, executor: BaseMigrationExecutor) -> None:
        """
        No-op for forward schema in data migration.

        Args:
            executor (BaseMigrationExecutor): The executor responsible for running migrations.

        Returns:
            None
        """

class Migration:
    """
    Represents a collection of migration operations.

    Attributes:
        operations (list[Operation]): The list of migration operations.
    """
    operations: list[Operation]
