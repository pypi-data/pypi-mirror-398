import logging
from typing import Any
from typing import Generic

from amsdal_data.transactions.manager import AmsdalTransactionManager
from amsdal_utils.query.utils import Q

from amsdal_models.querysets.base_queryset import ModelType
from amsdal_models.querysets.base_queryset import QuerySet
from amsdal_models.querysets.base_queryset import QuerySetOne
from amsdal_models.querysets.base_queryset import QuerySetOneRequired

logger = logging.getLogger(__name__)


class BaseManager(Generic[ModelType]):
    """
    Base manager for creating QuerySets for models.

    This class provides a base for managing models and creating query sets.
    It is generic and works with different model types defined by `ModelType`.

    Attributes:
        model (type[ModelType]): The model class associated with this manager.
        It defines the type of model this manager will handle.
    """

    model: type[ModelType]

    @property
    def table_name(self) -> str:
        return getattr(self.model, '__table_name__', None) or self.model.__name__

    @property
    def _transaction_manager(self) -> AmsdalTransactionManager:
        return AmsdalTransactionManager()

    def copy(self, cls: type[ModelType]) -> 'BaseManager[ModelType]':
        """
        Create a copy of the current manager for a specified model class.

        This method creates a new instance of the manager, assigning the provided
        model class to the `model` attribute of the new instance. It returns a
        new `BaseManager` instance associated with the given model class.

        Args:
            cls (type[ModelType]): The model class for which the new manager
            instance will be created.

        Returns:
            BaseManager: A new instance of `BaseManager` associated with the
            specified model class.
        """
        manager = self.__class__()
        manager.model = cls

        return manager

    def get_queryset(self) -> QuerySet[ModelType]:
        """
        Retrieve a new QuerySet instance for the associated model.

        This method creates and returns a new `QuerySet` instance that is
        associated with the model class defined in the `model` attribute
        of the manager.

        Returns:
            QuerySet[ModelType]: A new `QuerySet` instance for the associated model.
        """
        return QuerySet(self.model)

    def using(self, value: str) -> QuerySet[ModelType]:
        """
        Set the database alias for the QuerySet.

        This method sets the database alias to be used for the QuerySet operations.
        It returns a new QuerySet instance that will use the specified database alias.

        Args:
            value (str): The database alias to be used for the QuerySet.

        Returns:
            QuerySet[ModelType]: A new QuerySet instance using the specified database alias.
        """
        return self.get_queryset().using(value)

    def select_related(self, *fields: str) -> QuerySet[ModelType]:
        """
        Include related objects in the query results.

        Args:
            *fields (str): The related objects to include in the query results.

        Returns:
            QuerySet[ModelType]: A new instance of the query set with the specified related objects.
        """
        return self.get_queryset().select_related(*fields)

    def all(self) -> QuerySet[ModelType]:
        """
        Retrieve all instances of the associated model.

        This method returns a new `QuerySet` instance that includes all
        instances of the model class defined in the `model` attribute
        of the manager.

        Returns:
            QuerySet[ModelType]: A new `QuerySet` instance containing all instances of the associated model.
        """
        return self.get_queryset()

    def only(self, fields: list[str]) -> QuerySet[ModelType]:
        """
        Retrieve a QuerySet with only the specified fields.

        This method returns a new `QuerySet` instance that includes only the
        specified fields of the model class defined in the `model` attribute
        of the manager.

        Args:
            fields (list[str]): A list of field names to include in the QuerySet.

        Returns:
            QuerySet[ModelType]: A new `QuerySet` instance containing only the specified fields.
        """
        return self.get_queryset().only(fields=fields)

    def distinct(self, fields: list[str]) -> QuerySet[ModelType]:
        """
        Retrieve a QuerySet with distinct values for the specified fields.

        This method returns a new `QuerySet` instance that includes only distinct
        values for the specified fields of the model class defined in the `model`
        attribute of the manager.

        Args:
            fields (list[str]): A list of field names for which to retrieve distinct values.

        Returns:
            QuerySet[ModelType]: A new `QuerySet` instance containing distinct values for the specified fields.
        """
        return self.get_queryset().distinct(fields=fields)

    def filter(self, *args: Q, **kwargs: Any) -> QuerySet[ModelType]:
        """
        Filter the QuerySet based on the given conditions.

        This method returns a new `QuerySet` instance that includes only the
        instances of the model class defined in the `model` attribute of the
        manager that match the specified conditions.

        Args:
            *args (Q): Positional arguments representing query conditions.
            **kwargs (Any): Keyword arguments representing query conditions.

        Returns:
            QuerySet[ModelType]: A new `QuerySet` instance containing the filtered results.
        """
        return self.get_queryset().filter(*args, **kwargs)

    def exclude(self, *args: Q, **kwargs: Any) -> QuerySet[ModelType]:
        """
        Exclude instances from the QuerySet based on the given conditions.

        This method returns a new `QuerySet` instance that excludes the
        instances of the model class defined in the `model` attribute of the
        manager that match the specified conditions.

        Args:
            *args (Q): Positional arguments representing query conditions.
            **kwargs (Any): Keyword arguments representing query conditions.

        Returns:
            QuerySet[ModelType]: A new `QuerySet` instance excluding the specified results.
        """
        return self.get_queryset().exclude(*args, **kwargs)

    def get(self, *args: Q, **kwargs: Any) -> QuerySetOneRequired[ModelType]:
        """
        Retrieve a single instance of the model that matches the given conditions.

        This method returns a `QuerySetOneRequired` instance that includes the
        instance of the model class defined in the `model` attribute of the manager
        that matches the specified conditions. If no instance matches the conditions,
        an exception is raised.

        Args:
            *args (Q): Positional arguments representing query conditions.
            **kwargs (Any): Keyword arguments representing query conditions.

        Returns:
            QuerySetOneRequired[ModelType]: A `QuerySetOneRequired` instance containing the matched instance.
        """
        return self.get_queryset().get(*args, **kwargs)

    def get_or_none(self, *args: Q, **kwargs: Any) -> QuerySetOne[ModelType]:
        """
        Retrieve a single instance of the model that matches the given conditions or None.

        This method returns a `QuerySetOne` instance that includes the instance of the
        model class defined in the `model` attribute of the manager that matches the
        specified conditions. If no instance matches the conditions, None is returned.

        Args:
            *args (Q): Positional arguments representing query conditions.
            **kwargs (Any): Keyword arguments representing query conditions.

        Returns:
            QuerySetOne[ModelType]: A `QuerySetOne` instance containing the matched instance or None.
        """
        return self.get_queryset().get_or_none(*args, **kwargs)

    def first(self, *args: Q, **kwargs: Any) -> QuerySetOne[ModelType]:
        """
        Retrieve the first instance of the model that matches the given conditions.

        This method returns a `QuerySetOne` instance that includes the first instance
        of the model class defined in the `model` attribute of the manager that matches
        the specified conditions. If no instance matches the conditions, None is returned.

        Args:
            *args (Q): Positional arguments representing query conditions.
            **kwargs (Any): Keyword arguments representing query conditions.

        Returns:
            QuerySetOne[ModelType]: A `QuerySetOne` instance containing the first matched instance or None.
        """
        return self.get_queryset().first(*args, **kwargs)

    def latest(self) -> QuerySet[ModelType]:
        """
        Retrieve the latest instance of the model.

        This method returns a new `QuerySet` instance that includes the latest
        instance of the model class defined in the `model` attribute of the manager.

        Returns:
            QuerySet[ModelType]: A new `QuerySet` instance containing the latest instance of the associated model.
        """
        return self.get_queryset().latest()
