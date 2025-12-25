from _typeshed import Incomplete
from amsdal_models.classes.base import BaseModel as BaseModel
from amsdal_models.managers.external_manager import ExternalManager as ExternalManager
from amsdal_utils.models.data_models.metadata import Metadata as Metadata
from amsdal_utils.models.data_models.reference import Reference as Reference
from typing import Any, ClassVar

class ExternalModel(BaseModel):
    """
    Base class for models that access external databases.

    ExternalModels are designed to query existing tables in external databases
    without requiring AMSDAL to manage the schema. They are read-only by default
    and do not have versioning, metadata, or lifecycle management.

    Example usage:
        class ExternalUser(ExternalModel):
            __table_name__ = 'users'
            __connection__ = 'external_users_db'

            id: int
            username: str
            email: str
            active: bool

        # Query the external database
        users = ExternalUser.objects.filter(active=True).execute()
        user = ExternalUser.objects.get(id=1).execute()
        count = ExternalUser.objects.count().execute()

    Class Attributes:
        __table_name__: Name of the table in the external database
        __connection__: Name of the external connection (from config)
        __primary_key__: List of primary key field names (optional, defaults to ['id'])
        objects: Manager for querying the external database
    """
    
    __table_name__: ClassVar[str | None]
    __connection__: ClassVar[str | None]
    __primary_key__: ClassVar[list[str]]
    objects: ClassVar[ExternalManager[Any]]
    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Initialize subclass and set up the manager."""
    @classmethod
    def get_connection_name(cls) -> str:
        """
        Get the external connection name for this model.

        Returns:
            str: The connection name

        Raises:
            ValueError: If __connection__ is not set
        """
    @classmethod
    def get_table_name(cls) -> str:
        """
        Get the table name for this model.

        Returns:
            str: The table name (defaults to lowercase class name if not set)
        """
    @classmethod
    def get_primary_key(cls) -> list[str]:
        """
        Get the primary key field names.

        Returns:
            list[str]: List of primary key field names
        """
    def __eq__(self, other: Any) -> bool:
        """
        Compare two external model instances by primary key.

        Args:
            other: The other instance to compare with

        Returns:
            bool: True if instances have the same primary key values
        """
    def __hash__(self) -> int:
        """
        Compute hash based on primary key values.

        Returns:
            int: Hash value
        """
    def __repr__(self) -> str:
        """
        String representation of the model instance.

        Returns:
            str: String representation showing class name and primary key
        """
    def build_reference(self, *, is_frozen: bool = False) -> Reference:
        """
        Build reference for external model (not supported).

        External models don't have metadata tracking, so references are not supported.

        Args:
            is_frozen: Ignored for external models

        Raises:
            NotImplementedError: Always raises since external models don't support references
        """
    def get_metadata(self) -> Metadata:
        """
        Get metadata for external model (not supported).

        External models don't have metadata tracking.

        Raises:
            NotImplementedError: Always raises since external models don't have metadata
        """
