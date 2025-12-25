from _typeshed import Incomplete
from amsdal_models.classes.external_model import ExternalModel as ExternalModel
from amsdal_models.querysets.errors import MultipleObjectsReturnedError as MultipleObjectsReturnedError, ObjectDoesNotExistError as ObjectDoesNotExistError
from amsdal_utils.query.utils import Q as Q
from typing import Any, Generic, TypeVar

ModelType = TypeVar('ModelType', bound='ExternalModel')

class ExternalQuerySet(Generic[ModelType]):
    """
    QuerySet for external models.

    Provides a chainable query interface similar to Django's QuerySet,
    but executes queries against external database connections.

    Example usage:
        qs = ExternalUser.objects.filter(active=True).order_by('-created_at')
        users = qs.execute()  # Returns list[ExternalUser]

        count = ExternalUser.objects.filter(active=True).count().execute()  # Returns int
    """
    model: Incomplete
    _filters: list[tuple[list[Q], dict[str, Any]]]
    _excludes: list[tuple[list[Q], dict[str, Any]]]
    _order_by: list[str]
    _limit: int | None
    _offset: int | None
    _query_type: str
    def __init__(self, model: type[ModelType]) -> None: ...
    def _clone(self) -> ExternalQuerySet[ModelType]:
        """Create a copy of this queryset."""
    def filter(self, *args: Q, **kwargs: Any) -> ExternalQuerySet[ModelType]:
        """
        Filter records by conditions.

        Args:
            *args: Q objects for complex queries
            **kwargs: Field lookups (field__lookup=value)

        Returns:
            ExternalQuerySet: New queryset with additional filters
        """
    def exclude(self, *args: Q, **kwargs: Any) -> ExternalQuerySet[ModelType]:
        """
        Exclude records matching conditions.

        Args:
            *args: Q objects for complex queries
            **kwargs: Field lookups (field__lookup=value)

        Returns:
            ExternalQuerySet: New queryset with additional exclusions
        """
    def get(self, *args: Q, **kwargs: Any) -> ExternalQuerySet[ModelType]:
        """
        Get a single record.

        Args:
            *args: Q objects for complex queries
            **kwargs: Field lookups (field__lookup=value)

        Returns:
            ExternalQuerySet: Queryset configured for get operation
        """
    def first(self, *args: Q, **kwargs: Any) -> ExternalQuerySet[ModelType]:
        """
        Get the first record.

        Args:
            *args: Q objects for complex queries
            **kwargs: Field lookups (field__lookup=value)

        Returns:
            ExternalQuerySet: Queryset configured for first operation
        """
    def count(self) -> ExternalQuerySet[ModelType]:
        """
        Count records.

        Returns:
            ExternalQuerySet: Queryset configured for count operation
        """
    def exists(self) -> ExternalQuerySet[ModelType]:
        """
        Check if any records exist.

        Returns:
            ExternalQuerySet: Queryset configured for exists operation
        """
    def order_by(self, *fields: str) -> ExternalQuerySet[ModelType]:
        """
        Order records by fields.

        Args:
            *fields: Field names (prefix with '-' for descending)

        Returns:
            ExternalQuerySet: New queryset with ordering
        """
    def limit(self, limit: int) -> ExternalQuerySet[ModelType]:
        """
        Limit the number of records.

        Args:
            limit: Maximum number of records

        Returns:
            ExternalQuerySet: New queryset with limit
        """
    def offset(self, offset: int) -> ExternalQuerySet[ModelType]:
        """
        Skip a number of records.

        Args:
            offset: Number of records to skip

        Returns:
            ExternalQuerySet: New queryset with offset
        """
    def _build_where_clause(self, placeholder: str = '?') -> tuple[str, list[Any]]:
        """
        Build WHERE clause from filters and excludes.

        Args:
            placeholder: SQL placeholder style ('?' for SQLite, '%s' for PostgreSQL)

        Returns:
            tuple[str, list[Any]]: WHERE clause and parameters
        """
    def _build_sql(self, connection: Any = None) -> tuple[str, list[Any]]:
        """
        Build SQL query.

        Args:
            connection: External database connection (optional, used to detect SQL dialect)

        Returns:
            tuple[str, list[Any]]: SQL query and parameters
        """
    def execute(self) -> Any:
        """
        Execute the query and return results.

        Returns:
            Any: Query results (list[ModelType], ModelType, int, or bool depending on query type)

        Raises:
            ObjectDoesNotExistError: If get() finds no records
            MultipleObjectsReturnedError: If get() finds multiple records
        """
    async def aexecute(self) -> Any:
        """
        Execute the query and return results.

        Returns:
            Any: Query results (list[ModelType], ModelType, int, or bool depending on query type)

        Raises:
            ObjectDoesNotExistError: If get() finds no records
            MultipleObjectsReturnedError: If get() finds multiple records
        """
    def __repr__(self) -> str:
        """String representation of the queryset."""
