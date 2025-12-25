import amsdal_glue as glue
from _typeshed import Incomplete
from amsdal_models.classes.model import Model as Model
from amsdal_models.classes.utils import is_partial_model as is_partial_model
from amsdal_models.querysets.errors import BulkOperationError as BulkOperationError, MultipleObjectsReturnedError as MultipleObjectsReturnedError, ObjectDoesNotExistError as ObjectDoesNotExistError
from amsdal_models.querysets.executor import AsyncExecutor as AsyncExecutor, AsyncExecutorBase as AsyncExecutorBase, DEFAULT_DB_ALIAS as DEFAULT_DB_ALIAS, Executor as Executor, ExecutorBase as ExecutorBase
from amsdal_utils.query.data_models.order_by import OrderBy
from amsdal_utils.query.data_models.paginator import NumberPaginator
from amsdal_utils.query.data_models.query_specifier import QuerySpecifier
from amsdal_utils.query.utils import Q
from amsdal_utils.utils.decorators import async_mode_only, sync_mode_only
from typing import Any, Generic, Self, TypeVar

logger: Incomplete
ModelType = TypeVar('ModelType', bound='Model')

class QuerySetBase(Generic[ModelType]):
    """
    Base class for QuerySets.

    This class provides the base functionality for creating and manipulating
    query sets for model instances. It includes methods for filtering, ordering,
    and executing queries, as well as handling pagination and distinct results.

    """
    _entity: type[ModelType]
    _executor: Incomplete
    _async_executor: Incomplete
    _paginator: NumberPaginator
    _order_by: list[OrderBy]
    _query_specifier: QuerySpecifier
    _conditions: Q | None
    _using: str
    _select_related: bool | dict[str, Any]
    _annotations: dict[str, Any]
    _strict_class_version: Incomplete
    def __init__(self, entity: type[ModelType], executor: ExecutorBase[ModelType] | None = None, async_executor: AsyncExecutorBase[ModelType] | None = None, *, strict_class_version: bool = False) -> None: ...
    @property
    def entity_name(self) -> str:
        """
        Get the name of the entity associated with the query set.

        This property returns the name of the model class associated with the query set.

        Returns:
            str: The name of the model class.
        """
    @property
    def table_name(self) -> str: ...
    @property
    def entity(self) -> type[ModelType]:
        """
        Get the entity associated with the query set.

        This property returns the model class associated with the query set.

        Returns:
            type[ModelType]: The model class.
        """
    def get_conditions(self) -> Q | None:
        """
        Get the conditions of the query set.

        This property returns the conditions of the query set.

        Returns:
            Q | None: The conditions of the query set.
        """
    def get_select_related(self) -> bool | dict[str, Any]:
        """
        Get the related objects to include in the query results.

        This property returns the related objects to include in the query results.

        Returns:
            bool | dict[str, Any]: The related objects to include in the query results.
        """
    def get_query_specifier(self) -> QuerySpecifier:
        """
        Get the query specifier of the query set.

        This property returns the query specifier of the query set.

        Returns:
            QuerySpecifier: The query specifier of the query set.
        """
    def get_order_by(self) -> list[OrderBy]:
        """
        Get the order by fields of the query set.

        This property returns the order by fields of the query set.

        Returns:
            list[OrderBy]: The order by fields of the query set.
        """
    def get_using(self) -> str:
        """
        Get the database alias used for the query.

        This property returns the database alias used for the query.

        Returns:
            str: The database alias used for the query.
        """
    def get_paginator(self) -> NumberPaginator:
        """
        Get the paginator of the query set.

        This property returns the paginator of the query set.

        Returns:
            NumberPaginator: The paginator of the query set.
        """
    def using(self, value: str) -> Self:
        """
        Set the database alias to be used for the query.

        This method creates a copy of the current query set and sets the `_using`
        attribute to the specified database alias.

        Args:
            value (str): The database alias to be used for the query.

        Returns:
            Self: A new instance of the query set with the specified database alias.
        """
    def annotate(self, **kwargs: Any) -> Self: ...
    @classmethod
    def _from_queryset(cls, queryset: QuerySetBase[ModelType]) -> Self: ...
    def _copy(self) -> Self: ...
    def __copy__(self) -> Self: ...
    def only(self, fields: list[str]) -> Self:
        """
        Limit the number of fields to be returned.

        This method creates a copy of the current query set and sets the `only`
        attribute to the specified fields, limiting the fields to be returned
        in the query results.

        Args:
            fields (list[str]): The fields to be returned.

        Returns:
            Self: A new instance of the query set with the specified fields.
        """
    def distinct(self, fields: list[str]) -> Self:
        """
        Return only distinct (different) values.

        This method creates a copy of the current query set and sets the `distinct`
        attribute to the specified fields, ensuring that only distinct values are
        returned in the query results.

        Args:
            fields (list[str]): The fields to be distinct.

        Returns:
            Self: A new instance of the query set with the specified distinct fields.
        """
    def filter(self, *args: Q, **kwargs: Any) -> Self:
        """
        Apply filters to the query. The filters are combined with AND.

        Args:
            args (Q): The filters to be applied.
            kwargs (Any): The filters to be applied.

        Returns:
            Self: A new instance of the query set with the applied filters.
        """
    def exclude(self, *args: Q, **kwargs: Any) -> Self:
        """
        Exclude filters from the query. The filters are combined with AND.

        Args:
            args (Q): The filters to be applied.
            kwargs (Any): The filters to be applied.

        Returns:
            Self: A new instance of the query set with the applied filters.
        """
    @sync_mode_only
    def _execute_query(self) -> list[glue.Data]: ...
    @sync_mode_only
    def _execute_count(self) -> int: ...
    @async_mode_only
    async def _aexecute_query(self) -> list[glue.Data]: ...
    @async_mode_only
    async def _aexecute_count(self) -> int: ...
    def _filter(self, *args: Q, negated: bool = False, **kwargs: Any) -> Self: ...
    def order_by(self, *args: str) -> Self:
        """
        Order the query by the given fields.

        Args:
            args (str): The fields to order by.

        Returns:
            Self: A new instance of the query set with the specified order.
        """
    def __getitem__(self, index: slice | int) -> Self: ...
    def _create_instance(self, *, _is_partial: bool, data: glue.Data) -> ModelType: ...
    async def _acreate_instance(self, *, _is_partial: bool, data: glue.Data) -> ModelType: ...
    def latest(self) -> Self:
        """
        Filter the query set to include only the latest version of the model instances.

        This method creates a copy of the current query set and applies a filter to
        include only the latest version of the model instances.

        Returns:
            Self: A new instance of the query set with the filter applied to include
            only the latest version of the model instances.
        """
    def _check_type(self, obj: ModelType) -> None: ...
    def select_related(self, *fields: str) -> Self:
        """
        Include related objects in the query results.

        Args:
            *fields (str): The related objects to include in the query results.

        Returns:
            Self: A new instance of the query set with the specified related objects.
        """

class QuerySet(QuerySetBase[ModelType], Generic[ModelType]):
    """
    Interface to access the database.

    This class provides methods to create and manipulate query sets for model instances.
    It includes methods for filtering, ordering, and executing queries, as well as handling
    pagination and distinct results.
    """
    def get(self, *args: Q, **kwargs: Any) -> QuerySetOneRequired[ModelType]:
        """
        Change the QuerySet to a QuerySetOneRequired. Query execution will return a single item or raise an error.

        Args:
            args (Q): The filters to be applied.
            kwargs (Any): The filters to be applied.

        Returns:
            QuerySetOneRequired: A new instance of the QuerySetOneRequired with the applied filters.
        """
    def get_or_none(self, *args: Q, **kwargs: Any) -> QuerySetOne[ModelType]:
        """
        Change the QuerySet to a QuerySetOne. Query execution will return a single item or None.

        Args:
            args (Q): The filters to be applied.
            kwargs (Any): The filters to be applied.

        Returns:
            QuerySetOne: A new instance of the QuerySetOne with the applied filters.
        """
    def select_related(self, *fields: str) -> Self:
        """
        Include related objects in the query results.

        This method creates a copy of the current query set and sets the `select_related`
        attribute to the specified fields, including related objects in the query results.

        Args:
            *fields (str): The related objects to include in the query results.

        Returns:
            Self: A new instance of the query set with the specified related objects.
        """
    def first(self, *args: Q, **kwargs: Any) -> QuerySetOne[ModelType]:
        """
        Change the QuerySet to a QuerySetOne. Query execution will return the first item or None.

        Args:
            args (Q): The filters to be applied.
            kwargs (Any): The filters to be applied.

        Returns:
            QuerySetOneRequired: A new instance of the QuerySetOneRequired with the applied filters.
        """
    def count(self) -> QuerySetCount[ModelType]:
        """
        Change the QuerySet to a QuerySetCount. Query execution will return the count of items.

        Returns:
            QuerySetCount: A new instance of the QuerySetCount.
        """
    @sync_mode_only
    def execute(self) -> list[ModelType]:
        """
        Return the list of items.

        This method executes the query and returns a list of model instances.
        If the `only` attribute is set, partial model instances are created.

        Returns:
            list[ModelType]: A list of model instances.
        """
    @async_mode_only
    async def aexecute(self) -> list[ModelType]:
        """
        Return the list of items.

        This method executes the query and returns a list of model instances.
        If the `only` attribute is set, partial model instances are created.

        Returns:
            list[ModelType]: A list of model instances.
        """
    def only(self, fields: list[str]) -> Self:
        """
        Limit the number of fields to be returned.

        This method creates a copy of the current query set and sets the `only`
        attribute to the specified fields, limiting the fields to be returned
        in the query results.

        Args:
            fields (list[str]): The fields to be returned.

        Returns:
            Self: A new instance of the query set with the specified fields.
        """
    def distinct(self, fields: list[str]) -> Self:
        """
        Return only distinct (different) values.

        This method creates a copy of the current query set and sets the `distinct`
        attribute to the specified fields, ensuring that only distinct values are
        returned in the query results.

        Args:
            fields (list[str]): The fields to be distinct.

        Returns:
            Self: A new instance of the query set with the specified distinct fields.
        """
    def filter(self, *args: Q, **kwargs: Any) -> Self:
        """
        Apply filters to the query. The filters are combined with AND.

        This method creates a copy of the current query set and applies the specified
        filters to it. The filters can be provided as positional arguments or keyword
        arguments, and they are combined using the AND operator.

        Args:
            *args (Q): The filters to be applied as positional arguments.
            **kwargs (Any): The filters to be applied as keyword arguments.

        Returns:
            Self: A new instance of the query set with the applied filters.
        """
    def exclude(self, *args: Q, **kwargs: Any) -> Self:
        """
        Exclude filters from the query. The filters are combined with AND.

        This method creates a copy of the current query set and applies the specified
        filters to exclude certain results. The filters can be provided as positional
        arguments or keyword arguments, and they are combined using the AND operator.

        Args:
            *args (Q): The filters to be applied as positional arguments.
            **kwargs (Any): The filters to be applied as keyword arguments.

        Returns:
            Self: A new instance of the query set with the applied exclusion filters.
        """
    def order_by(self, *args: str) -> Self:
        """
        Order the query by the given fields.

        This method creates a copy of the current query set and sets the `order_by`
        attribute to the specified fields, determining the order of the query results.

        Args:
            *args (str): The fields to order by.

        Returns:
            Self: A new instance of the query set with the specified order.
        """

class QuerySetOne(QuerySetBase[ModelType], Generic[ModelType]):
    """
    QuerySet class for models. QuerySet is executed to a single model object or None.

    This class provides methods to create and manipulate query sets for model instances.
    It includes methods for filtering, ordering, and executing queries, as well as handling
    pagination and distinct results. The query execution will return a single item or None.
    """
    _raise_on_multiple: bool
    def __init__(self, entity: type[ModelType]) -> None: ...
    def only(self, fields: list[str]) -> Self:
        """
        Limit the number of fields to be returned.

        This method creates a copy of the current query set and sets the `only`
        attribute to the specified fields, limiting the fields to be returned
        in the query results.

        Args:
            fields (list[str]): The fields to be returned.

        Returns:
            Self: A new instance of the query set with the specified fields.
        """
    def distinct(self, fields: list[str]) -> Self:
        """
        Return only distinct (different) values.

        This method creates a copy of the current query set and sets the `distinct`
        attribute to the specified fields, ensuring that only distinct values are
        returned in the query results.

        Args:
            fields (list[str]): The fields to be distinct.

        Returns:
            Self: A new instance of the query set with the specified distinct fields.
        """
    def filter(self, *args: Q, **kwargs: Any) -> Self:
        """
        Apply filters to the query. The filters are combined with AND.

        This method creates a copy of the current query set and applies the specified
        filters to it. The filters can be provided as positional arguments or keyword
        arguments, and they are combined using the AND operator.

        Args:
            *args (Q): The filters to be applied as positional arguments.
            **kwargs (Any): The filters to be applied as keyword arguments.

        Returns:
            Self: A new instance of the query set with the applied filters.
        """
    def exclude(self, *args: Q, **kwargs: Any) -> Self:
        """
        Exclude filters from the query. The filters are combined with AND.

        This method creates a copy of the current query set and applies the specified
        filters to exclude certain results. The filters can be provided as positional
        arguments or keyword arguments, and they are combined using the AND operator.

        Args:
            *args (Q): The filters to be applied as positional arguments.
            **kwargs (Any): The filters to be applied as keyword arguments.

        Returns:
            Self: A new instance of the query set with the applied exclusion filters.
        """
    def order_by(self, *args: str) -> Self:
        """
        Order the query by the given fields.

        This method creates a copy of the current query set and sets the `order_by`
        attribute to the specified fields, determining the order of the query results.

        Args:
            *args (str): The fields to order by.

        Returns:
            Self: A new instance of the query set with the specified order.
        """
    @sync_mode_only
    def execute(self) -> ModelType | None:
        """
        Query the database and return the single item or None.

        This method executes the query and returns a single model instance or None.
        If multiple items are found, a `MultipleObjectsReturnedError` is raised.

        Raises:
            MultipleObjectsReturnedError: If multiple items are found.

        Returns:
            ModelType | None: The single model instance or None if no items are found.
        """
    @async_mode_only
    async def aexecute(self) -> ModelType | None:
        """
        Query the database and return the single item or None.

        This method executes the query and returns a single model instance or None.
        If multiple items are found, a `MultipleObjectsReturnedError` is raised.

        Raises:
            MultipleObjectsReturnedError: If multiple items are found.

        Returns:
            ModelType | None: The single model instance or None if no items are found.
        """

class QuerySetOneRequired(QuerySetOne[ModelType], Generic[ModelType]):
    """
    QuerySet class for models. QuerySet is executed to a single model object or raises an error.

    This class provides methods to create and manipulate query sets for model instances.
    It includes methods for filtering, ordering, and executing queries, as well as handling
    pagination and distinct results. The query execution will return a single item or raise
    an error if no items are found.
    """
    def only(self, fields: list[str]) -> Self:
        """
        Limit the number of fields to be returned.

        This method creates a copy of the current query set and sets the `only`
        attribute to the specified fields, limiting the fields to be returned
        in the query results.

        Args:
            fields (list[str]): The fields to be returned.

        Returns:
            Self: A new instance of the query set with the specified fields.
        """
    def distinct(self, fields: list[str]) -> Self:
        """
        Return only distinct (different) values.

        This method creates a copy of the current query set and sets the `distinct`
        attribute to the specified fields, ensuring that only distinct values are
        returned in the query results.

        Args:
            fields (list[str]): The fields to be distinct.

        Returns:
            Self: A new instance of the query set with the specified distinct fields.
        """
    def filter(self, *args: Q, **kwargs: Any) -> Self:
        """
        Apply filters to the query. The filters are combined with AND.

        This method creates a copy of the current query set and applies the specified
        filters to it. The filters can be provided as positional arguments or keyword
        arguments, and they are combined using the AND operator.

        Args:
            *args (Q): The filters to be applied as positional arguments.
            **kwargs (Any): The filters to be applied as keyword arguments.

        Returns:
            Self: A new instance of the query set with the applied filters.
        """
    def exclude(self, *args: Q, **kwargs: Any) -> Self:
        """
        Exclude filters from the query. The filters are combined with AND.

        This method creates a copy of the current query set and applies the specified
        filters to exclude certain results. The filters can be provided as positional
        arguments or keyword arguments, and they are combined using the AND operator.

        Args:
            *args (Q): The filters to be applied as positional arguments.
            **kwargs (Any): The filters to be applied as keyword arguments.

        Returns:
            Self: A new instance of the query set with the applied exclusion filters.
        """
    def order_by(self, *args: str) -> Self:
        """
        Order the query by the given fields.

        This method creates a copy of the current query set and sets the `order_by`
        attribute to the specified fields, determining the order of the query results.

        Args:
            *args (str): The fields to order by.

        Returns:
            Self: A new instance of the query set with the specified order.
        """
    @sync_mode_only
    def execute(self) -> ModelType:
        """
        Return the single item.

        This method executes the query and returns a single model instance.
        If no items are found, an `ObjectDoesNotExistError` is raised.

        Raises:
            ObjectDoesNotExistError: If no items are found.

        Returns:
            ModelType: The single model instance.
        """
    @async_mode_only
    async def aexecute(self) -> ModelType:
        """
        Return the single item.

        This method executes the query and returns a single model instance.
        If no items are found, an `ObjectDoesNotExistError` is raised.

        Raises:
            ObjectDoesNotExistError: If no items are found.

        Returns:
            ModelType: The single model instance.
        """

class QuerySetCount(QuerySetBase[ModelType], Generic[ModelType]):
    """
    QuerySet class for models. QuerySet is executed to a count of items.

    This class provides methods to create and manipulate query sets for model instances.
    It includes methods for filtering, ordering, and executing queries, as well as handling
    pagination and distinct results. The query execution will return the count of items.

    """
    def only(self, fields: list[str]) -> Self:
        """
        Limit the number of fields to be returned.

        This method creates a copy of the current query set and sets the `only`
        attribute to the specified fields, limiting the fields to be returned
        in the query results.

        Args:
            fields (list[str]): The fields to be returned.

        Returns:
            Self: A new instance of the query set with the specified fields.
        """
    def distinct(self, fields: list[str]) -> Self:
        """
        Return only distinct (different) values.

        This method creates a copy of the current query set and sets the `distinct`
        attribute to the specified fields, ensuring that only distinct values are
        returned in the query results.

        Args:
            fields (list[str]): The fields to be distinct.

        Returns:
            Self: A new instance of the query set with the specified distinct fields.
        """
    def filter(self, *args: Q, **kwargs: Any) -> Self:
        """
        Apply filters to the query. The filters are combined with AND.

        This method creates a copy of the current query set and applies the specified
        filters to it. The filters can be provided as positional arguments or keyword
        arguments, and they are combined using the AND operator.

        Args:
            *args (Q): The filters to be applied as positional arguments.
            **kwargs (Any): The filters to be applied as keyword arguments.

        Returns:
            Self: A new instance of the query set with the applied filters.
        """
    def exclude(self, *args: Q, **kwargs: Any) -> Self:
        """
        Exclude filters from the query. The filters are combined with AND.

        This method creates a copy of the current query set and applies the specified
        filters to exclude certain results. The filters can be provided as positional
        arguments or keyword arguments, and they are combined using the AND operator.

        Args:
            *args (Q): The filters to be applied as positional arguments.
            **kwargs (Any): The filters to be applied as keyword arguments.

        Returns:
            Self: A new instance of the query set with the applied exclusion filters.
        """
    def order_by(self, *args: str) -> Self:
        """
        Order the query by the given fields.

        This method creates a copy of the current query set and sets the `order_by`
        attribute to the specified fields, determining the order of the query results.

        Args:
            *args (str): The fields to order by.

        Returns:
            Self: A new instance of the query set with the specified order.
        """
    @sync_mode_only
    def execute(self) -> int:
        """
        Return the count of items.

        This method executes the query and returns the count of model instances
        that match the query criteria.

        Returns:
            int: The count of model instances.
        """
    @async_mode_only
    async def aexecute(self) -> int:
        """
        Return the count of items.

        This method executes the query and returns the count of model instances
        that match the query criteria.

        Returns:
            int: The count of model instances.
        """
