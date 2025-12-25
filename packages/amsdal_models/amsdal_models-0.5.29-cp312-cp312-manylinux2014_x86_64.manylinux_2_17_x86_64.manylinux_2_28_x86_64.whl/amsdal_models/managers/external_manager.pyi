from amsdal_models.classes.external_model import ExternalModel as ExternalModel
from amsdal_models.querysets.external_queryset import ExternalQuerySet as ExternalQuerySet
from amsdal_utils.query.utils import Q as Q
from typing import Any, Generic, TypeVar

ModelType = TypeVar('ModelType', bound='ExternalModel')

class ExternalManager(Generic[ModelType]):
    """
    Manager for external models.

    Provides a Django-like query interface for accessing external databases:
    - filter() - Filter records by conditions
    - exclude() - Exclude records matching conditions
    - get() - Get a single record (raises error if not found or multiple found)
    - first() - Get the first record or None
    - all() - Get all records
    - count() - Count records
    - exists() - Check if any records match

    Example usage:
        class ExternalUser(ExternalModel):
            __table_name__ = 'users'
            __connection__ = 'external_users_db'
            id: int
            username: str

        # Query interface
        users = ExternalUser.objects.filter(active=True).execute()
        user = ExternalUser.objects.get(id=1).execute()
        count = ExternalUser.objects.count().execute()
        exists = ExternalUser.objects.filter(username='alice').exists().execute()
    """
    model: type[ModelType] | None
    def __init__(self) -> None: ...
    def copy(self, cls: type[ModelType]) -> ExternalManager[ModelType]:
        """
        Create a copy of this manager for a different model class.

        Args:
            cls: The model class to bind to

        Returns:
            ExternalManager: A new manager instance bound to the model
        """
    def get_queryset(self) -> ExternalQuerySet[ModelType]:
        """
        Get a new queryset for this manager.

        Returns:
            ExternalQuerySet: A new queryset instance

        Raises:
            ValueError: If manager is not bound to a model
        """
    def all(self) -> ExternalQuerySet[ModelType]:
        """
        Get a queryset for all records.

        Returns:
            ExternalQuerySet: Queryset for all records
        """
    def filter(self, *args: Q, **kwargs: Any) -> ExternalQuerySet[ModelType]:
        """
        Filter records by conditions.

        Args:
            *args: Q objects for complex queries
            **kwargs: Field lookups (field__lookup=value)

        Returns:
            ExternalQuerySet: Filtered queryset

        Example:
            users = ExternalUser.objects.filter(active=True).execute()
            users = ExternalUser.objects.filter(Q(age__gte=18) | Q(verified=True)).execute()
        """
    def exclude(self, *args: Q, **kwargs: Any) -> ExternalQuerySet[ModelType]:
        """
        Exclude records matching conditions.

        Args:
            *args: Q objects for complex queries
            **kwargs: Field lookups (field__lookup=value)

        Returns:
            ExternalQuerySet: Filtered queryset

        Example:
            users = ExternalUser.objects.exclude(active=False).execute()
        """
    def get(self, *args: Q, **kwargs: Any) -> ExternalQuerySet[ModelType]:
        """
        Get a single record matching the conditions.

        Args:
            *args: Q objects for complex queries
            **kwargs: Field lookups (field__lookup=value)

        Returns:
            ExternalQuerySet: Queryset that will return a single object

        Raises:
            ObjectDoesNotExistError: If no record is found
            MultipleObjectsReturnedError: If multiple records are found

        Example:
            user = ExternalUser.objects.get(id=1).execute()
        """
    def first(self, *args: Q, **kwargs: Any) -> ExternalQuerySet[ModelType]:
        """
        Get the first record matching the conditions.

        Args:
            *args: Q objects for complex queries
            **kwargs: Field lookups (field__lookup=value)

        Returns:
            ExternalQuerySet: Queryset that will return the first object or None

        Example:
            user = ExternalUser.objects.first(active=True).execute()
        """
    def count(self) -> ExternalQuerySet[ModelType]:
        """
        Count records.

        Returns:
            ExternalQuerySet: Queryset that will return the count

        Example:
            total = ExternalUser.objects.count().execute()
            active_count = ExternalUser.objects.filter(active=True).count().execute()
        """
    def exists(self) -> ExternalQuerySet[ModelType]:
        """
        Check if any records exist.

        Returns:
            ExternalQuerySet: Queryset that will return boolean

        Example:
            has_users = ExternalUser.objects.exists().execute()
            has_active = ExternalUser.objects.filter(active=True).exists().execute()
        """
    def order_by(self, *fields: str) -> ExternalQuerySet[ModelType]:
        """
        Order records by fields.

        Args:
            *fields: Field names (prefix with '-' for descending order)

        Returns:
            ExternalQuerySet: Ordered queryset

        Example:
            users = ExternalUser.objects.order_by('username').execute()
            users = ExternalUser.objects.order_by('-created_at', 'username').execute()
        """
    def limit(self, limit: int) -> ExternalQuerySet[ModelType]:
        """
        Limit the number of records returned.

        Args:
            limit: Maximum number of records

        Returns:
            ExternalQuerySet: Limited queryset

        Example:
            users = ExternalUser.objects.limit(10).execute()
        """
    def offset(self, offset: int) -> ExternalQuerySet[ModelType]:
        """
        Skip a number of records.

        Args:
            offset: Number of records to skip

        Returns:
            ExternalQuerySet: Queryset with offset

        Example:
            users = ExternalUser.objects.offset(10).limit(10).execute()
        """
