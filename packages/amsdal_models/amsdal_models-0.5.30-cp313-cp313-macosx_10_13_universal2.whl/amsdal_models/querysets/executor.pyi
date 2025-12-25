import abc
import amsdal_glue as glue
from _typeshed import Incomplete
from abc import ABC, abstractmethod
from amsdal_data.services.operation_manager import AsyncOperationManager, OperationManager
from amsdal_models.classes.model import Model as Model
from amsdal_models.querysets.base_queryset import QuerySetBase as QuerySetBase
from amsdal_models.querysets.errors import AmsdalQuerySetError as AmsdalQuerySetError
from amsdal_models.querysets.query_builders.historical_builder import AsyncHistoricalQueryBuilder as AsyncHistoricalQueryBuilder, HistoricalQueryBuilder as HistoricalQueryBuilder
from amsdal_models.querysets.query_builders.state_builder import StateQueryBuilder as StateQueryBuilder
from amsdal_utils.models.data_models.address import Address
from typing import Any, Generic, TypeVar

logger: Incomplete
DEFAULT_DB_ALIAS: str
LAKEHOUSE_DB_ALIAS: str
OBJECT_ID_FIELD: str
OBJECT_VERSION_FIELD: str
CLASS_VERSION_FIELD: str
ADDRESS_FIELD: str
METADATA_FIELD: str
ModelType = TypeVar('ModelType', bound='Model')

class ExecutorBase(ABC, Generic[ModelType], metaclass=abc.ABCMeta):
    """
    Abstract base class for query executors.

    This class provides the base functionality for executing queries and counting
    results. It defines the interface that all concrete executor classes must implement.

    Attributes:
        queryset (QuerySetBase): The query set to be executed.
    """
    queryset: QuerySetBase[ModelType]
    def __init__(self, queryset: QuerySetBase[ModelType]) -> None: ...
    @property
    def operation_manager(self) -> OperationManager: ...
    @property
    def is_using_lakehouse(self) -> bool: ...
    @abstractmethod
    def query(self) -> list[glue.Data]: ...
    @abstractmethod
    def count(self) -> int: ...

class AsyncExecutorBase(ABC, Generic[ModelType], metaclass=abc.ABCMeta):
    """
    Abstract base class for query executors.

    This class provides the base functionality for executing queries and counting
    results. It defines the interface that all concrete executor classes must implement.

    Attributes:
        queryset (QuerySetBase): The query set to be executed.
    """
    queryset: QuerySetBase[ModelType]
    def __init__(self, queryset: QuerySetBase[ModelType]) -> None: ...
    @property
    def operation_manager(self) -> AsyncOperationManager: ...
    @property
    def is_using_lakehouse(self) -> bool: ...
    @abstractmethod
    async def query(self) -> list[glue.Data]: ...
    @abstractmethod
    async def count(self) -> int: ...

class Executor(ExecutorBase['ModelType']):
    """
    Concrete executor class for executing queries and counting results.

    This class extends the `ExecutorBase` and provides the implementation for
    executing queries and counting results using the specified query set.
    """
    def _address(self) -> Address: ...
    def query(self) -> list[glue.Data]:
        """
        Execute the query and return the results.

        This method uses the connection object to execute the query based on the
        query set's specifier, conditions, pagination, and order by attributes.

        Returns:
            list[dict[str, Any]]: The query results as a list of dictionaries.
        """
    def count(self) -> int:
        """
        Execute the query and return the count of results.

        This method uses the connection object to execute the query and return
        the count of model instances that match the query conditions.

        Returns:
            int: The count of matching results.
        """
    def _process_data(self, data: glue.Data, select_related: dict[tuple[str, type['ModelType'], str], Any] | None = None) -> glue.Data: ...

class AsyncExecutor(AsyncExecutorBase['ModelType']):
    """
    Concrete executor class for executing queries and counting results.

    This class extends the `ExecutorBase` and provides the implementation for
    executing queries and counting results using the specified query set.
    """
    async def _address(self) -> Address: ...
    async def query(self) -> list[glue.Data]:
        """
        Execute the query and return the results.

        This method uses the connection object to execute the query based on the
        query set's specifier, conditions, pagination, and order by attributes.

        Returns:
            list[dict[str, Any]]: The query results as a list of dictionaries.
        """
    async def count(self) -> int:
        """
        Execute the query and return the count of results.

        This method uses the connection object to execute the query and return
        the count of model instances that match the query conditions.

        Returns:
            int: The count of matching results.
        """
    async def _process_data(self, data: glue.Data, select_related: dict[tuple[str, type['ModelType'], str], Any] | None = None) -> glue.Data: ...
