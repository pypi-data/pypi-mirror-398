"""
External QuerySet for executing queries against external databases.

This module provides a queryset implementation that translates AMSDAL
queries to execute against external database connections.
"""

import inspect
from typing import TYPE_CHECKING
from typing import Any
from typing import Generic
from typing import TypeVar

from amsdal_utils.config.manager import AmsdalConfigManager
from amsdal_utils.query.utils import Q

from amsdal_models.querysets.errors import MultipleObjectsReturnedError
from amsdal_models.querysets.errors import ObjectDoesNotExistError

if TYPE_CHECKING:
    from amsdal_models.classes.external_model import ExternalModel

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

    def __init__(self, model: type[ModelType]):
        self.model = model
        self._filters: list[tuple[list[Q], dict[str, Any]]] = []
        self._excludes: list[tuple[list[Q], dict[str, Any]]] = []
        self._order_by: list[str] = []
        self._limit: int | None = None
        self._offset: int | None = None
        self._query_type: str = 'select'  # 'select', 'count', 'exists', 'get', 'first'

    def _clone(self) -> 'ExternalQuerySet[ModelType]':
        """Create a copy of this queryset."""
        qs = ExternalQuerySet(model=self.model)
        qs._filters = self._filters.copy()
        qs._excludes = self._excludes.copy()
        qs._order_by = self._order_by.copy()
        qs._limit = self._limit
        qs._offset = self._offset
        qs._query_type = self._query_type
        return qs

    def filter(self, *args: Q, **kwargs: Any) -> 'ExternalQuerySet[ModelType]':
        """
        Filter records by conditions.

        Args:
            *args: Q objects for complex queries
            **kwargs: Field lookups (field__lookup=value)

        Returns:
            ExternalQuerySet: New queryset with additional filters
        """
        qs = self._clone()
        qs._filters.append((list(args), kwargs))
        return qs

    def exclude(self, *args: Q, **kwargs: Any) -> 'ExternalQuerySet[ModelType]':
        """
        Exclude records matching conditions.

        Args:
            *args: Q objects for complex queries
            **kwargs: Field lookups (field__lookup=value)

        Returns:
            ExternalQuerySet: New queryset with additional exclusions
        """
        qs = self._clone()
        qs._excludes.append((list(args), kwargs))
        return qs

    def get(self, *args: Q, **kwargs: Any) -> 'ExternalQuerySet[ModelType]':
        """
        Get a single record.

        Args:
            *args: Q objects for complex queries
            **kwargs: Field lookups (field__lookup=value)

        Returns:
            ExternalQuerySet: Queryset configured for get operation
        """
        qs = self._clone()
        qs._filters.append((list(args), kwargs))
        qs._query_type = 'get'
        return qs

    def first(self, *args: Q, **kwargs: Any) -> 'ExternalQuerySet[ModelType]':
        """
        Get the first record.

        Args:
            *args: Q objects for complex queries
            **kwargs: Field lookups (field__lookup=value)

        Returns:
            ExternalQuerySet: Queryset configured for first operation
        """
        qs = self._clone()
        if args or kwargs:
            qs._filters.append((list(args), kwargs))
        qs._query_type = 'first'
        qs._limit = 1
        return qs

    def count(self) -> 'ExternalQuerySet[ModelType]':
        """
        Count records.

        Returns:
            ExternalQuerySet: Queryset configured for count operation
        """
        qs = self._clone()
        qs._query_type = 'count'
        return qs

    def exists(self) -> 'ExternalQuerySet[ModelType]':
        """
        Check if any records exist.

        Returns:
            ExternalQuerySet: Queryset configured for exists operation
        """
        qs = self._clone()
        qs._query_type = 'exists'
        return qs

    def order_by(self, *fields: str) -> 'ExternalQuerySet[ModelType]':
        """
        Order records by fields.

        Args:
            *fields: Field names (prefix with '-' for descending)

        Returns:
            ExternalQuerySet: New queryset with ordering
        """
        qs = self._clone()
        qs._order_by = list(fields)
        return qs

    def limit(self, limit: int) -> 'ExternalQuerySet[ModelType]':
        """
        Limit the number of records.

        Args:
            limit: Maximum number of records

        Returns:
            ExternalQuerySet: New queryset with limit
        """
        qs = self._clone()
        qs._limit = limit
        return qs

    def offset(self, offset: int) -> 'ExternalQuerySet[ModelType]':
        """
        Skip a number of records.

        Args:
            offset: Number of records to skip

        Returns:
            ExternalQuerySet: New queryset with offset
        """
        qs = self._clone()
        qs._offset = offset
        return qs

    def _build_where_clause(self, placeholder: str = '?') -> tuple[str, list[Any]]:
        """
        Build WHERE clause from filters and excludes.

        Args:
            placeholder: SQL placeholder style ('?' for SQLite, '%s' for PostgreSQL)

        Returns:
            tuple[str, list[Any]]: WHERE clause and parameters
        """
        conditions = []
        parameters = []

        # Process filters
        for _q_objects, field_lookups in self._filters:
            for field, value in field_lookups.items():
                if '__' in field:
                    field_name, lookup = field.rsplit('__', 1)
                else:
                    field_name, lookup = field, 'exact'

                if lookup == 'exact':
                    conditions.append(f'{field_name} = {placeholder}')
                    parameters.append(value)
                elif lookup == 'gt':
                    conditions.append(f'{field_name} > {placeholder}')
                    parameters.append(value)
                elif lookup == 'gte':
                    conditions.append(f'{field_name} >= {placeholder}')
                    parameters.append(value)
                elif lookup == 'lt':
                    conditions.append(f'{field_name} < {placeholder}')
                    parameters.append(value)
                elif lookup == 'lte':
                    conditions.append(f'{field_name} <= {placeholder}')
                    parameters.append(value)
                elif lookup == 'in':
                    placeholders = ', '.join(placeholder * len(value))
                    conditions.append(f'{field_name} IN ({placeholders})')
                    parameters.extend(value)
                elif lookup == 'isnull':
                    if value:
                        conditions.append(f'{field_name} IS NULL')
                    else:
                        conditions.append(f'{field_name} IS NOT NULL')
                elif lookup == 'contains':
                    conditions.append(f'{field_name} LIKE {placeholder}')
                    parameters.append(f'%{value}%')
                elif lookup == 'icontains':
                    conditions.append(f'{field_name} LIKE {placeholder} COLLATE NOCASE')
                    parameters.append(f'%{value}%')
                elif lookup == 'startswith':
                    conditions.append(f'{field_name} LIKE {placeholder}')
                    parameters.append(f'{value}%')
                elif lookup == 'endswith':
                    conditions.append(f'{field_name} LIKE {placeholder}')
                    parameters.append(f'%{value}')
                else:
                    msg = f'Unsupported lookup: {lookup}'
                    raise ValueError(msg)

        # Process excludes
        for _q_objects, field_lookups in self._excludes:
            for field, value in field_lookups.items():
                if '__' in field:
                    field_name, lookup = field.rsplit('__', 1)
                else:
                    field_name, lookup = field, 'exact'

                if lookup == 'exact':
                    conditions.append(f'NOT ({field_name} = {placeholder})')
                    parameters.append(value)
                else:
                    msg = f'Unsupported exclude lookup: {lookup}'
                    raise ValueError(msg)

        if conditions:
            where_clause = ' AND '.join(conditions)
            return where_clause, parameters

        return '', []

    def _build_sql(self, connection: Any = None) -> tuple[str, list[Any]]:
        """
        Build SQL query.

        Args:
            connection: External database connection (optional, used to detect SQL dialect)

        Returns:
            tuple[str, list[Any]]: SQL query and parameters
        """
        # Get placeholder style from connection
        placeholder = '?'  # Default
        supports_limit_minus_one = True  # Default
        if connection:
            placeholder = getattr(connection, 'sql_placeholder', '?')
            supports_limit_minus_one = getattr(connection, 'supports_limit_minus_one', True)

        table_name = self.model.get_table_name()
        where_clause, parameters = self._build_where_clause(placeholder)

        if self._query_type == 'count':
            query = f'SELECT COUNT(*) as count FROM {table_name}'  # noqa: S608
        elif self._query_type == 'exists':
            query = f'SELECT 1 FROM {table_name}'  # noqa: S608
        else:
            query = f'SELECT * FROM {table_name}'  # noqa: S608

        if where_clause:
            query += f' WHERE {where_clause}'

        if self._order_by:
            order_parts = []
            for field in self._order_by:
                if field.startswith('-'):
                    order_parts.append(f'{field[1:]} DESC')
                else:
                    order_parts.append(f'{field} ASC')
            query += ' ORDER BY ' + ', '.join(order_parts)

        if self._limit is not None:
            query += f' LIMIT {self._limit}'
        elif self._offset is not None:
            # Handle databases that don't support LIMIT -1
            if supports_limit_minus_one:
                # SQLite accepts LIMIT -1 to mean "no limit"
                query += ' LIMIT -1'
            else:
                # PostgreSQL and others: use a very large number or omit LIMIT
                # For PostgreSQL, we can use LIMIT ALL or a large number
                query += ' LIMIT ALL'

        if self._offset is not None:
            query += f' OFFSET {self._offset}'

        return query, parameters

    def execute(self) -> Any:
        """
        Execute the query and return results.

        Returns:
            Any: Query results (list[ModelType], ModelType, int, or bool depending on query type)

        Raises:
            ObjectDoesNotExistError: If get() finds no records
            MultipleObjectsReturnedError: If get() finds multiple records
        """
        from amsdal_data.application import AsyncDataApplication
        from amsdal_data.application import DataApplication

        # Get the external connection
        connection_name = self.model.get_connection_name()

        app: DataApplication | AsyncDataApplication
        if AmsdalConfigManager().get_config().async_mode:
            app = AsyncDataApplication()
        else:
            app = DataApplication()

        connection = app.get_external_service_connection(connection_name)

        # Build and execute query (pass connection for dialect detection)
        query, parameters = self._build_sql(connection)

        if self._query_type == 'count':
            result = connection.fetch_one(query, tuple(parameters) if parameters else None)
            return result['count'] if result else 0

        if self._query_type == 'exists':
            result = connection.fetch_one(query, tuple(parameters) if parameters else None)
            return result is not None

        if self._query_type in ('get', 'first'):
            result = connection.fetch_one(query, tuple(parameters) if parameters else None)

            if self._query_type == 'get' and result is None:
                msg = f'{self.model.__name__} matching query does not exist'
                raise ObjectDoesNotExistError(msg)

            if self._query_type == 'first' and result is None:
                return None

            # Check if get() returned multiple results
            if self._query_type == 'get':
                # Execute query with limit 2 to check for multiple results
                check_query = query + ' LIMIT 2'
                check_results = connection.fetch_all(check_query, tuple(parameters) if parameters else None)
                if len(check_results) > 1:
                    msg = f'get() returned more than one {self.model.__name__}'
                    raise MultipleObjectsReturnedError(msg)

            # Convert row to model instance
            return self.model(**dict(result))

        # Default: select query returning list
        results = connection.fetch_all(query, tuple(parameters) if parameters else None)
        return [self.model(**dict(row)) for row in results]

    async def aexecute(self) -> Any:
        """
        Execute the query and return results.

        Returns:
            Any: Query results (list[ModelType], ModelType, int, or bool depending on query type)

        Raises:
            ObjectDoesNotExistError: If get() finds no records
            MultipleObjectsReturnedError: If get() finds multiple records
        """
        from amsdal_data.application import AsyncDataApplication
        from amsdal_data.application import DataApplication

        # Get the external connection
        connection_name = self.model.get_connection_name()

        app: DataApplication | AsyncDataApplication
        if AmsdalConfigManager().get_config().async_mode:
            app = AsyncDataApplication()
        else:
            app = DataApplication()

        connection = app.get_external_service_connection(connection_name)

        # Build and execute query (pass connection for dialect detection)
        query, parameters = self._build_sql(connection)

        if self._query_type == 'count':
            result = connection.fetch_one(query, tuple(parameters) if parameters else None)
            if inspect.isawaitable(result):
                result = await result
            return result['count'] if result else 0

        if self._query_type == 'exists':
            result = connection.fetch_one(query, tuple(parameters) if parameters else None)
            if inspect.isawaitable(result):
                result = await result
            return result is not None

        if self._query_type in ('get', 'first'):
            result = connection.fetch_one(query, tuple(parameters) if parameters else None)
            if inspect.isawaitable(result):
                result = await result

            if self._query_type == 'get' and result is None:
                msg = f'{self.model.__name__} matching query does not exist'
                raise ObjectDoesNotExistError(msg)

            if self._query_type == 'first' and result is None:
                return None

            # Check if get() returned multiple results
            if self._query_type == 'get':
                # Execute query with limit 2 to check for multiple results
                check_query = query + ' LIMIT 2'
                check_results = connection.fetch_all(check_query, tuple(parameters) if parameters else None)
                if inspect.isawaitable(check_results):
                    check_results = await check_results
                if len(check_results) > 1:
                    msg = f'get() returned more than one {self.model.__name__}'
                    raise MultipleObjectsReturnedError(msg)

            # Convert row to model instance
            return self.model(**dict(result))

        # Default: select query returning list
        results = connection.fetch_all(query, tuple(parameters) if parameters else None)
        if inspect.isawaitable(results):
            results = await results
        return [self.model(**dict(row)) for row in results]

    def __repr__(self) -> str:
        """String representation of the queryset."""
        return f'<ExternalQuerySet: {self.model.__name__}>'
