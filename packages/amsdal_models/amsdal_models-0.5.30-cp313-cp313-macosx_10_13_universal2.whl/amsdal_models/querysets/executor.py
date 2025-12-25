import logging
from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any
from typing import Generic
from typing import TypeVar

import amsdal_glue as glue
from amsdal_data.connections.constants import PRIMARY_PARTITION_KEY
from amsdal_data.connections.constants import SECONDARY_PARTITION_KEY
from amsdal_data.connections.historical.schema_version_manager import AsyncHistoricalSchemaVersionManager
from amsdal_data.connections.historical.schema_version_manager import HistoricalSchemaVersionManager
from amsdal_data.services.operation_manager import AsyncOperationManager
from amsdal_data.services.operation_manager import OperationManager
from amsdal_utils.config.manager import AmsdalConfigManager
from amsdal_utils.errors import AmsdalError
from amsdal_utils.models.data_models.address import Address

from amsdal_models.querysets.errors import AmsdalQuerySetError
from amsdal_models.querysets.query_builders.historical_builder import AsyncHistoricalQueryBuilder
from amsdal_models.querysets.query_builders.historical_builder import HistoricalQueryBuilder
from amsdal_models.querysets.query_builders.state_builder import StateQueryBuilder

if TYPE_CHECKING:
    from amsdal_models.classes.model import Model
    from amsdal_models.querysets.base_queryset import QuerySetBase

logger = logging.getLogger(__name__)

DEFAULT_DB_ALIAS = 'default'
LAKEHOUSE_DB_ALIAS = 'lakehouse'
OBJECT_ID_FIELD = 'object_id'
OBJECT_VERSION_FIELD = 'object_version'
CLASS_VERSION_FIELD = 'class_version'
ADDRESS_FIELD = '_address'
METADATA_FIELD = '_metadata'

ModelType = TypeVar('ModelType', bound='Model')


class ExecutorBase(Generic[ModelType], ABC):
    """
    Abstract base class for query executors.

    This class provides the base functionality for executing queries and counting
    results. It defines the interface that all concrete executor classes must implement.

    Attributes:
        queryset (QuerySetBase): The query set to be executed.
    """

    queryset: 'QuerySetBase[ModelType]'

    def __init__(self, queryset: 'QuerySetBase[ModelType]') -> None:
        self.queryset = queryset

    @property
    def operation_manager(self) -> OperationManager:
        from amsdal_data.application import DataApplication

        return DataApplication().operation_manager

    @property
    def is_using_lakehouse(self) -> bool:
        from amsdal_data.application import DataApplication

        return self.queryset.get_using() == LAKEHOUSE_DB_ALIAS or DataApplication().is_lakehouse_only

    @abstractmethod
    def query(self) -> list[glue.Data]: ...

    @abstractmethod
    def count(self) -> int: ...


class AsyncExecutorBase(Generic[ModelType], ABC):
    """
    Abstract base class for query executors.

    This class provides the base functionality for executing queries and counting
    results. It defines the interface that all concrete executor classes must implement.

    Attributes:
        queryset (QuerySetBase): The query set to be executed.
    """

    queryset: 'QuerySetBase[ModelType]'

    def __init__(self, queryset: 'QuerySetBase[ModelType]') -> None:
        self.queryset = queryset

    @property
    def operation_manager(self) -> AsyncOperationManager:
        from amsdal_data.application import AsyncDataApplication

        return AsyncDataApplication().operation_manager

    @property
    def is_using_lakehouse(self) -> bool:
        from amsdal_data.application import AsyncDataApplication

        return self.queryset.get_using() == LAKEHOUSE_DB_ALIAS or AsyncDataApplication().is_lakehouse_only

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

    def _address(self) -> Address:
        return Address(
            resource='',
            class_name=self.queryset.entity_name,
            class_version=HistoricalSchemaVersionManager().get_latest_schema_version(self.queryset.entity_name),
            object_id='',
            object_version='',
        )

    def query(self) -> list[glue.Data]:
        """
        Execute the query and return the results.

        This method uses the connection object to execute the query based on the
        query set's specifier, conditions, pagination, and order by attributes.

        Returns:
            list[dict[str, Any]]: The query results as a list of dictionaries.
        """
        if AmsdalConfigManager().get_config().async_mode:
            msg = 'Async mode is enabled. Use AsyncExecutor instead.'
            raise AmsdalError(msg)

        if self.is_using_lakehouse:
            hist_query_builder = HistoricalQueryBuilder(self.queryset)
            _select_related = hist_query_builder.qs_select_related
            result = self.operation_manager.query_lakehouse(hist_query_builder.transform())
        else:
            query_builder = StateQueryBuilder(self.queryset)
            _select_related = query_builder.qs_select_related
            result = self.operation_manager.query(query_builder.transform())

        if not result.success:
            msg = f'Error while executing query: {result.message}'
            raise AmsdalQuerySetError(msg) from result.exception
        res = [self._process_data(item, _select_related) for item in (result.data or [])]
        return res

    def count(self) -> int:
        """
        Execute the query and return the count of results.

        This method uses the connection object to execute the query and return
        the count of model instances that match the query conditions.

        Returns:
            int: The count of matching results.
        """
        if AmsdalConfigManager().get_config().async_mode:
            msg = 'Async mode is enabled. Use AsyncExecutor instead.'
            raise AmsdalError(msg)

        if self.is_using_lakehouse:
            hist_query_builder = HistoricalQueryBuilder(self.queryset)
            result = self.operation_manager.query_lakehouse(hist_query_builder.transform_count())
        else:
            query_builder = StateQueryBuilder(self.queryset)
            result = self.operation_manager.query(query_builder.transform_count())

        if not result.success:
            msg = 'Error while executing query'
            raise Exception(msg) from result.exception

        return (result.data or [])[0].data['total_count']

    def _process_data(
        self,
        data: glue.Data,
        select_related: dict[tuple[str, type['ModelType'], str], Any] | None = None,
    ) -> glue.Data:
        _data = data.data

        if select_related:
            for (field, fk_type, alias), nested_select_related in select_related.items():
                _nested_data = {}
                prefix = f'{alias}__'

                if self.is_using_lakehouse:
                    for version, _ in (
                        HistoricalSchemaVersionManager()
                        .get_all_schema_properties(
                            fk_type.__name__,
                        )
                        .items()
                    ):
                        prefix += f'{version[:8]}__'

                        if any(True for field_name in _data.keys() if field_name.startswith(prefix)):
                            break

                for data_field, value in _data.items():
                    if data_field.startswith(prefix):
                        _nested_data[data_field[slice(len(prefix), None)]] = value

                for key in _nested_data.keys():
                    _prefixed_key = f'{prefix}{key}'

                    _data.pop(_prefixed_key, None)

                nested_data = self._process_data(glue.Data(data=_nested_data), nested_select_related)

                if nested_data and any(v is not None for v in nested_data.data.values()):
                    _data[field] = nested_data.data

        if PRIMARY_PARTITION_KEY in _data:
            _data['_object_id'] = _data.pop(PRIMARY_PARTITION_KEY)
        if SECONDARY_PARTITION_KEY in _data:
            # we take object_version from metadata
            _data.pop(SECONDARY_PARTITION_KEY)
        return glue.Data(data=_data, metadata=data.metadata)


class AsyncExecutor(AsyncExecutorBase['ModelType']):
    """
    Concrete executor class for executing queries and counting results.

    This class extends the `ExecutorBase` and provides the implementation for
    executing queries and counting results using the specified query set.
    """

    async def _address(self) -> Address:
        return Address(
            resource='',
            class_name=self.queryset.entity_name,
            class_version=await AsyncHistoricalSchemaVersionManager().get_latest_schema_version(
                self.queryset.entity_name
            ),
            object_id='',
            object_version='',
        )

    async def query(self) -> list[glue.Data]:
        """
        Execute the query and return the results.

        This method uses the connection object to execute the query based on the
        query set's specifier, conditions, pagination, and order by attributes.

        Returns:
            list[dict[str, Any]]: The query results as a list of dictionaries.
        """
        if not AmsdalConfigManager().get_config().async_mode:
            msg = 'Async mode is disabled. Use Executor instead.'
            raise AmsdalError(msg)

        if self.is_using_lakehouse:
            async_query_builder = AsyncHistoricalQueryBuilder(self.queryset)
            _select_related = async_query_builder.qs_select_related
            result = await self.operation_manager.query_lakehouse(await async_query_builder.transform())
        else:
            query_builder = StateQueryBuilder(self.queryset)
            _select_related = query_builder.qs_select_related
            result = await self.operation_manager.query(query_builder.transform())

        if not result.success:
            msg = f'Error while executing query: {result.message}'
            raise AmsdalQuerySetError(msg) from result.exception

        return [await self._process_data(item, _select_related) for item in (result.data or [])]

    async def count(self) -> int:
        """
        Execute the query and return the count of results.

        This method uses the connection object to execute the query and return
        the count of model instances that match the query conditions.

        Returns:
            int: The count of matching results.
        """
        if not AmsdalConfigManager().get_config().async_mode:
            msg = 'Async mode is disabled. Use Executor instead.'
            raise AmsdalError(msg)

        if self.is_using_lakehouse:
            async_query_builder = AsyncHistoricalQueryBuilder(self.queryset)
            result = await self.operation_manager.query_lakehouse(await async_query_builder.transform_count())
        else:
            query_builder = StateQueryBuilder(self.queryset)
            result = await self.operation_manager.query(query_builder.transform_count())

        if not result.success:
            msg = 'Error while executing query'
            raise Exception(msg) from result.exception

        return (result.data or [])[0].data['total_count']

    async def _process_data(
        self,
        data: glue.Data,
        select_related: dict[tuple[str, type['ModelType'], str], Any] | None = None,
    ) -> glue.Data:
        _data = data.data

        if select_related:
            for (field, fk_type, alias), nested_select_related in select_related.items():
                _nested_data = {}
                prefix = f'{alias}__'

                if self.is_using_lakehouse:
                    for version, _ in (
                        await AsyncHistoricalSchemaVersionManager().get_all_schema_properties(
                            fk_type.__name__,
                        )
                    ).items():
                        prefix += f'{version[:8]}__'

                        if any(True for field_name in _data.keys() if field_name.startswith(prefix)):
                            break

                for data_field, value in _data.items():
                    if data_field.startswith(prefix):
                        _nested_data[data_field[slice(len(prefix), None)]] = value

                for key in _nested_data.keys():
                    _prefixed_key = f'{prefix}{key}'

                    _data.pop(_prefixed_key, None)

                nested_data = await self._process_data(glue.Data(data=_nested_data), nested_select_related)

                if nested_data and any(v is not None for v in nested_data.data.values()):
                    _data[field] = nested_data.data

        if PRIMARY_PARTITION_KEY in _data:
            _data['_object_id'] = _data.pop(PRIMARY_PARTITION_KEY)
        if SECONDARY_PARTITION_KEY in _data:
            # we take object_version from metadata
            _data.pop(SECONDARY_PARTITION_KEY)
        return glue.Data(data=_data, metadata=data.metadata)
