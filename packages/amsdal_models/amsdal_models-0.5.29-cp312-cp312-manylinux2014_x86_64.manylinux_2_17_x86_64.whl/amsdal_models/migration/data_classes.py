from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from amsdal_utils.models.data_models.address import Address
from amsdal_utils.models.enums import ModuleType
from amsdal_utils.schemas.schema import ObjectSchema
from amsdal_utils.schemas.schema import PropertyData

from amsdal_models.classes.model import Model


class Action(str, Enum):
    """
    Enumeration for different types of actions.

    Attributes:
        CREATE (str): Represents a created action.
        UPDATE (str): Represents an updated action.
        NO_ACTION (str): Represents no action.
    """

    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    NO_ACTION = 'NO_ACTION'


@dataclass
class ClassSaveResult:
    """
    Data class representing the result of a class save operation.

    Attributes:
        action (Action): The action performed during the save operation.
        instance (Model): The instance of the model that was saved.
    """

    action: Action
    instance: Model


@dataclass
class ClassUpdateResult:
    """
    Data class representing the result of a class update operation.

    Attributes:
        is_updated (bool): Indicates whether the class was updated.
        class_instance (Model): The instance of the model that was updated.
    """

    is_updated: bool
    class_instance: Model


@dataclass
class MigrateResult:
    """
    Data class representing the result of a migration operation.

    Attributes:
        class_instance (Model): The instance of the model that was migrated.
        is_table_created (bool): Indicates whether the table was created during the migration.
        is_data_migrated (bool): Indicates whether the data was migrated.
    """

    class_instance: Model
    is_table_created: bool
    is_data_migrated: bool


@dataclass
class MigrationFile:
    """
    Data class representing a migration file.

    Attributes:
        path (Path): The file path of the migration.
        type (ModuleType): The type of module the migration belongs to.
        number (int): The migration number.
        module (str | None): The module name, if applicable.
        applied_at (float | None): The timestamp when the migration was applied.
        stored_address (Address | None): The stored address associated with the migration.
    """

    path: Path
    type: ModuleType
    number: int
    module: str | None = None
    applied_at: float | None = None
    stored_address: Address | None = None

    @property
    def is_initial(self) -> bool:
        """
        Indicates whether this migration is the initial migration.

        Returns:
            bool: True if this is the initial migration, False otherwise.
        """
        return self.number == 0


@dataclass
class ClassSchema:
    """
    Data class representing a class schema.

    Attributes:
        object_schema (ObjectSchema): The object schema associated with the class.
        type (ModuleType): The type of module the class belongs to.
    """

    object_schema: ObjectSchema
    type: ModuleType


class OperationTypes(str, Enum):
    """
    Enumeration for different types of operations.

    Attributes:
        CREATE_CLASS (str): Represents the operation to create a class.
        UPDATE_CLASS (str): Represents the operation to update a class.
        DELETE_CLASS (str): Represents the operation to delete a class.
    """

    CREATE_CLASS = 'CREATE_CLASS'
    UPDATE_CLASS = 'UPDATE_CLASS'
    DELETE_CLASS = 'DELETE_CLASS'


@dataclass
class MigrateOperation:
    """
    Data class representing a migration operation.

    Attributes:
        type (OperationTypes): The type of operation being performed.
        class_name (str): The name of the class involved in the migration.
        module_type (ModuleType): The type of schema associated with the migration.
        old_schema (ObjectSchema | PropertyData | None): The old schema before the migration, if applicable.
        new_schema (ObjectSchema | PropertyData | None): The new schema after the migration, if applicable.
    """

    type: OperationTypes
    class_name: str
    module_type: ModuleType
    old_schema: ObjectSchema | PropertyData | None = None
    new_schema: ObjectSchema | PropertyData | None = None


class MigrationDirection(str, Enum):
    """
    Enumeration for the direction of a migration.

    Attributes:
        FORWARD (str): Represents a forward migration.
        BACKWARD (str): Represents a backward migration.
    """

    FORWARD = 'forward'
    BACKWARD = 'backward'


@dataclass
class MigrationResult:
    """
    Data class representing the result of a migration.

    Attributes:
        direction (MigrationDirection): The direction of the migration.
        migration (MigrationFile): The migration file associated with the migration.
    """

    direction: MigrationDirection
    migration: MigrationFile
