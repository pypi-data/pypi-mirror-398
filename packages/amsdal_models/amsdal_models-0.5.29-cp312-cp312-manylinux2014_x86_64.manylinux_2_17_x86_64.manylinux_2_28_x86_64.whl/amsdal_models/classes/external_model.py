"""
External Model for accessing external databases without AMSDAL schema management.

This module provides a base class for models that represent tables in external databases.
Unlike regular AMSDAL models, ExternalModels:
- Do not require schema migrations
- Do not have metadata tracking (no object_id, versions, etc.)
- Are read-only by default (no save/delete methods)
- Map directly to existing database tables
"""

from typing import Any
from typing import ClassVar

from amsdal_utils.models.data_models.metadata import Metadata
from amsdal_utils.models.data_models.reference import Reference
from pydantic import ConfigDict

from amsdal_models.classes.base import BaseModel
from amsdal_models.managers.external_manager import ExternalManager


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

    model_config = ConfigDict(validate_assignment=True, extra='ignore')

    __table_name__: ClassVar[str | None] = None
    __connection__: ClassVar[str | None] = None
    __primary_key__: ClassVar[list[str]] = ['id']

    objects: ClassVar[ExternalManager[Any]] = ExternalManager()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Initialize subclass and set up the manager."""
        super().__init_subclass__(**kwargs)

        # Create a new manager instance for this model
        if 'objects' not in cls.__dict__:
            cls.objects = ExternalManager()

        # Bind the model to the manager
        cls.objects.model = cls

    @classmethod
    def get_connection_name(cls) -> str:
        """
        Get the external connection name for this model.

        Returns:
            str: The connection name

        Raises:
            ValueError: If __connection__ is not set
        """
        if cls.__connection__ is None:
            msg = f'{cls.__name__}.__connection__ must be set to the external connection name'
            raise ValueError(msg)
        return cls.__connection__

    @classmethod
    def get_table_name(cls) -> str:
        """
        Get the table name for this model.

        Returns:
            str: The table name (defaults to lowercase class name if not set)
        """
        if cls.__table_name__ is not None:
            return cls.__table_name__
        return cls.__name__.lower()

    @classmethod
    def get_primary_key(cls) -> list[str]:
        """
        Get the primary key field names.

        Returns:
            list[str]: List of primary key field names
        """
        return cls.__primary_key__

    def __eq__(self, other: Any) -> bool:
        """
        Compare two external model instances by primary key.

        Args:
            other: The other instance to compare with

        Returns:
            bool: True if instances have the same primary key values
        """
        if not isinstance(other, self.__class__):
            return False

        pk_fields = self.get_primary_key()
        for field in pk_fields:
            if getattr(self, field, None) != getattr(other, field, None):
                return False

        return True

    def __hash__(self) -> int:
        """
        Compute hash based on primary key values.

        Returns:
            int: Hash value
        """
        pk_fields = self.get_primary_key()
        pk_values = tuple(getattr(self, field, None) for field in pk_fields)
        return hash((self.__class__.__name__, pk_values))

    def __repr__(self) -> str:
        """
        String representation of the model instance.

        Returns:
            str: String representation showing class name and primary key
        """
        pk_fields = self.get_primary_key()
        pk_repr = ', '.join(f'{field}={getattr(self, field, None)!r}' for field in pk_fields)
        return f'{self.__class__.__name__}({pk_repr})'

    def build_reference(self, *, is_frozen: bool = False) -> Reference:
        """
        Build reference for external model (not supported).

        External models don't have metadata tracking, so references are not supported.

        Args:
            is_frozen: Ignored for external models

        Raises:
            NotImplementedError: Always raises since external models don't support references
        """
        msg = 'ExternalModel does not support references. Use primary key values directly.'
        raise NotImplementedError(msg)

    def get_metadata(self) -> Metadata:
        """
        Get metadata for external model (not supported).

        External models don't have metadata tracking.

        Raises:
            NotImplementedError: Always raises since external models don't have metadata
        """
        msg = 'ExternalModel does not support metadata tracking.'
        raise NotImplementedError(msg)
