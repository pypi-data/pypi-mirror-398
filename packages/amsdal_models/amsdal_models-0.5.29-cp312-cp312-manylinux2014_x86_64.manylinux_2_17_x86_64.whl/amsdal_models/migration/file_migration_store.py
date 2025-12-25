import json
import time
from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import Any
from typing import ClassVar

import amsdal_glue as glue
from amsdal_data.aliases.using import LAKEHOUSE_DB_ALIAS
from amsdal_data.application import AsyncDataApplication
from amsdal_data.application import DataApplication
from amsdal_data.connections.constants import METADATA_KEY
from amsdal_data.connections.constants import PRIMARY_PARTITION_KEY
from amsdal_data.connections.constants import SECONDARY_PARTITION_KEY
from amsdal_data.connections.historical.data_query_transform import METADATA_TABLE_ALIAS
from amsdal_data.connections.historical.data_query_transform import NEXT_VERSION_FIELD
from amsdal_data.connections.historical.schema_version_manager import AsyncHistoricalSchemaVersionManager
from amsdal_data.connections.historical.schema_version_manager import HistoricalSchemaVersionManager
from amsdal_data.errors import CommandError
from amsdal_data.errors import QueryError
from amsdal_data.services.table_schema_manager import AsyncTableSchemasManager
from amsdal_data.services.table_schema_manager import TableSchemasManager
from amsdal_data.transactions.manager import AmsdalAsyncTransactionManager
from amsdal_data.transactions.manager import AmsdalTransactionManager
from amsdal_utils.models.data_models.address import Address
from amsdal_utils.models.data_models.metadata import Metadata
from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.models.data_models.reference import ReferenceData
from amsdal_utils.models.enums import ModuleType
from amsdal_utils.models.enums import Versions
from amsdal_utils.utils.identifier import get_identifier

from amsdal_models.migration.data_classes import MigrationFile
from amsdal_models.migration.utils import module_name_to_migrations_path
from amsdal_models.querysets.query_builders.historical_builder import AsyncHistoricalQueryBuilder
from amsdal_models.querysets.query_builders.historical_builder import HistoricalQueryBuilder


class BaseMigrationStore(ABC):
    def init_migration_table(self) -> None: ...

    @abstractmethod
    def fetch_migrations(self) -> list[MigrationFile]: ...

    @abstractmethod
    def save_migration(self, migration: MigrationFile) -> None: ...

    @abstractmethod
    def delete_migration(self, migration: MigrationFile) -> None: ...


class AsyncBaseMigrationStore(ABC):
    async def init_migration_table(self) -> None: ...

    @abstractmethod
    async def fetch_migrations(self) -> list[MigrationFile]: ...

    @abstractmethod
    async def save_migration(self, migration: MigrationFile) -> None: ...

    @abstractmethod
    async def delete_migration(self, migration: MigrationFile) -> None: ...


class FileMigrationStore(BaseMigrationStore):
    """
    Manages the storage and retrieval of migration files.

    Attributes:
        migration_address (Address): The address associated with the migration.
    """

    MIGRATION_TABLE: ClassVar[str] = 'Migration'
    migration_address: Address = Address.from_string('resource#Migration')

    def __init__(self, app_migrations_path: Path) -> None:
        self._app_migrations_path = app_migrations_path
        self._operation_manager = DataApplication().operation_manager

    def init_migration_table(self) -> None:
        self._init_migration_table()

    def fetch_migrations(self) -> list[MigrationFile]:
        """
        Fetches the list of applied migrations.

        Returns:
            list[MigrationFile]: List of applied migration files.
        """
        query = HistoricalQueryBuilder.build_query_statement_with_metadata(
            table=glue.SchemaReference(name=self.MIGRATION_TABLE, version=glue.Version.LATEST),
            where=glue.Conditions(
                glue.Condition(
                    left=glue.FieldReferenceExpression(
                        field_reference=glue.FieldReference(
                            field=glue.Field(name='is_deleted'),
                            table_name=METADATA_TABLE_ALIAS,
                        ),
                    ),
                    lookup=glue.FieldLookup.EQ,
                    right=glue.Value(False),
                ),
                glue.Conditions(
                    glue.Condition(
                        left=glue.FieldReferenceExpression(
                            field_reference=glue.FieldReference(
                                field=glue.Field(name=NEXT_VERSION_FIELD),
                                table_name=METADATA_TABLE_ALIAS,
                            ),
                        ),
                        lookup=glue.FieldLookup.ISNULL,
                        right=glue.Value(value=True),
                    ),
                    glue.Condition(
                        left=glue.FieldReferenceExpression(
                            field_reference=glue.FieldReference(
                                field=glue.Field(name=NEXT_VERSION_FIELD),
                                table_name=METADATA_TABLE_ALIAS,
                            ),
                        ),
                        lookup=glue.FieldLookup.EQ,
                        right=glue.Value(value=''),
                    ),
                    connector=glue.FilterConnector.OR,
                ),
            ),
        )
        result = self._operation_manager.query_lakehouse(query)

        if not result.success:
            msg = f'Failed to fetch migrations: {result.message}'
            raise QueryError(msg) from result.exception

        _result: list[MigrationFile] = []

        for _migration_data in result.data or []:
            _migration = _migration_data.data

            if _migration['module_name']:
                _path_module = module_name_to_migrations_path(_migration['module_name'])
            else:
                _path_module = self._app_migrations_path

            _metadata = Metadata(**_migration['_metadata'])
            _result.append(
                MigrationFile(
                    number=_migration['number'],
                    path=_path_module / _migration['migration_name'],
                    type=ModuleType(_migration['module_type']),
                    module=_migration['module_name'],
                    applied_at=_migration['applied_at'],
                    stored_address=_metadata.address,
                )
            )

        return _result

    def save_migration(self, migration: MigrationFile) -> None:
        """
        Saves a migration file.

        Args:
            migration (MigrationFile): The migration file to save.

        Returns:
            None
        """
        migration.applied_at = time.time()
        _migration_data = self._build_migration_data(migration)
        _address, _metadata = self._build_migration_metadata(migration)

        self._save_historical_data(
            address=_address,
            data=_migration_data,
            metadata=_metadata,
        )

    def delete_migration(self, migration: MigrationFile) -> None:
        """
        Deletes a migration file.

        Args:
            migration (MigrationFile): The migration file to delete.

        Returns:
            None
        """
        address = migration.stored_address

        if not address:
            return

        _object_id = address.object_id

        if isinstance(_object_id, list):
            _object_id = _object_id[0]
        else:
            try:
                _object_id = json.loads(_object_id)[0]  # type: ignore[arg-type]
            except json.JSONDecodeError:
                pass

        result = self._operation_manager.perform_data_command_lakehouse(
            command=glue.DataCommand(
                root_transaction_id=AmsdalTransactionManager().get_root_transaction_id(),
                transaction_id=AmsdalTransactionManager().transaction_id,
                mutations=[
                    glue.DeleteData(
                        schema=glue.SchemaReference(name=address.class_name, version=glue.Version.LATEST),
                        query=glue.Conditions(
                            glue.Condition(
                                left=glue.FieldReferenceExpression(
                                    field_reference=glue.FieldReference(
                                        field=glue.Field(name=PRIMARY_PARTITION_KEY),
                                        table_name=address.class_name,
                                    ),
                                ),
                                lookup=glue.FieldLookup.EQ,
                                right=glue.Value(value=_object_id),
                            )
                        ),
                    ),
                ],
            ),
        )

        if not result.success:
            msg = f'Failed to delete migration in DB: {result.message}'
            raise CommandError(msg) from result.exception

    def _save_historical_data(self, address: Address, data: dict[str, Any], metadata: dict[str, Any]) -> None:
        data[METADATA_KEY] = metadata
        data[PRIMARY_PARTITION_KEY] = address.object_id

        result = self._operation_manager.perform_data_command_lakehouse(
            command=glue.DataCommand(
                root_transaction_id=AmsdalTransactionManager().get_root_transaction_id(),
                transaction_id=AmsdalTransactionManager().transaction_id,
                mutations=[
                    glue.InsertData(
                        schema=glue.SchemaReference(name=address.class_name, version=glue.Version.LATEST),
                        data=[glue.Data(data=data)],
                    ),
                ],
            ),
        )

        if not result.success:
            msg = f'Failed to save migration into DB: {result.message}'
            raise CommandError(msg) from result.exception

    @staticmethod
    def _build_migration_data(migration: MigrationFile) -> dict[str, Any]:
        return {
            'number': migration.number,
            'migration_name': migration.path.name,
            'module_type': migration.type.value,
            'module_name': migration.module,
            'applied_at': migration.applied_at,
        }

    @classmethod
    def _build_migration_metadata(
        cls,
        migration: MigrationFile,  # noqa: ARG003
        object_id: str | None = None,
    ) -> tuple[Address, dict[str, Any]]:
        _address = cls.migration_address.model_copy(
            update={
                'object_id': object_id or get_identifier(),
            },
        )
        _transaction_manager = AmsdalTransactionManager()
        _transaction_ref = None

        if _transaction_manager.transaction_object:
            _transaction_ref = Reference(
                ref=ReferenceData(
                    **_transaction_manager.transaction_object.address.model_dump(),
                ),
            )

        return (
            _address,
            json.loads(
                Metadata(
                    object_id=_address.object_id,
                    object_version=_address.object_version,
                    class_schema_reference=Reference(
                        ref=ReferenceData(
                            **cls.migration_address.model_copy(
                                update={
                                    'class_version': Versions.LATEST,
                                }
                            ).model_dump(),
                        ),
                    ),
                    transaction=_transaction_ref,
                ).model_dump_json(),
            ),
        )

    def _init_migration_table(self) -> None:
        migration_schema = glue.Schema(
            name=self.MIGRATION_TABLE,
            version='',
            properties=[
                glue.PropertySchema(
                    name=PRIMARY_PARTITION_KEY,
                    type=str,
                    required=True,
                ),
                glue.PropertySchema(
                    name=SECONDARY_PARTITION_KEY,
                    type=str,
                    required=True,
                ),
                glue.PropertySchema(
                    name='number',
                    type=int,
                    required=True,
                ),
                glue.PropertySchema(
                    name='migration_name',
                    type=str,
                    required=True,
                ),
                glue.PropertySchema(
                    name='module_type',
                    type=str,
                    required=True,
                ),
                glue.PropertySchema(
                    name='module_name',
                    type=str,
                    required=False,
                    default=None,
                ),
                glue.PropertySchema(
                    name='applied_at',
                    type=float,
                    required=False,
                    default=None,
                ),
            ],
            constraints=[
                glue.PrimaryKeyConstraint(
                    name=f'pk_{self.MIGRATION_TABLE.lower()}',
                    fields=[PRIMARY_PARTITION_KEY, SECONDARY_PARTITION_KEY],
                ),
            ],
        )

        table_schema_manager = TableSchemasManager()
        table_schema_manager.register_table(migration_schema, using=LAKEHOUSE_DB_ALIAS)

        # we need to register the last version of the schema
        schema_version_manager = HistoricalSchemaVersionManager()
        schema_version_manager.register_last_version(self.MIGRATION_TABLE, '')


class AsyncFileMigrationStore(AsyncBaseMigrationStore):
    """
    Manages the storage and retrieval of migration files.

    Attributes:
        migration_address (Address): The address associated with the migration.
    """

    MIGRATION_TABLE: ClassVar[str] = 'Migration'
    migration_address: Address = Address.from_string('resource#Migration')

    def __init__(self, app_migrations_path: Path) -> None:
        self._app_migrations_path = app_migrations_path
        self._operation_manager = AsyncDataApplication().operation_manager

    async def init_migration_table(self) -> None:
        await self._init_migration_table()

    async def fetch_migrations(self) -> list[MigrationFile]:
        """
        Fetches the list of applied migrations.

        Returns:
            list[MigrationFile]: List of applied migration files.
        """
        query = await AsyncHistoricalQueryBuilder.build_query_statement_with_metadata(
            table=glue.SchemaReference(name=self.MIGRATION_TABLE, version=glue.Version.LATEST),
            where=glue.Conditions(
                glue.Condition(
                    left=glue.FieldReferenceExpression(
                        field_reference=glue.FieldReference(
                            field=glue.Field(name='is_deleted'),
                            table_name=METADATA_TABLE_ALIAS,
                        ),
                    ),
                    lookup=glue.FieldLookup.EQ,
                    right=glue.Value(False),
                ),
                glue.Conditions(
                    glue.Condition(
                        left=glue.FieldReferenceExpression(
                            field_reference=glue.FieldReference(
                                field=glue.Field(name=NEXT_VERSION_FIELD),
                                table_name=METADATA_TABLE_ALIAS,
                            ),
                        ),
                        lookup=glue.FieldLookup.ISNULL,
                        right=glue.Value(value=True),
                    ),
                    glue.Condition(
                        left=glue.FieldReferenceExpression(
                            field_reference=glue.FieldReference(
                                field=glue.Field(name=NEXT_VERSION_FIELD),
                                table_name=METADATA_TABLE_ALIAS,
                            ),
                        ),
                        lookup=glue.FieldLookup.EQ,
                        right=glue.Value(value=''),
                    ),
                    connector=glue.FilterConnector.OR,
                ),
            ),
        )

        result = await self._operation_manager.query_lakehouse(query)

        if not result.success:
            msg = f'Failed to fetch migrations: {result.message}'
            raise QueryError(msg) from result.exception

        _result: list[MigrationFile] = []

        for _migration_data in result.data or []:
            _migration = _migration_data.data

            if _migration['module_name']:
                _path_module = module_name_to_migrations_path(_migration['module_name'])
            else:
                _path_module = self._app_migrations_path

            _metadata = Metadata(**_migration['_metadata'])
            _result.append(
                MigrationFile(
                    number=_migration['number'],
                    path=_path_module / _migration['migration_name'],
                    type=ModuleType(_migration['module_type']),
                    module=_migration['module_name'],
                    applied_at=_migration['applied_at'],
                    stored_address=_metadata.address,
                )
            )

        return _result

    async def save_migration(self, migration: MigrationFile) -> None:
        """
        Saves a migration file.

        Args:
            migration (MigrationFile): The migration file to save.

        Returns:
            None
        """
        migration.applied_at = time.time()
        _migration_data = self._build_migration_data(migration)
        _address, _metadata = self._build_migration_metadata(migration)

        await self._save_historical_data(
            address=_address,
            data=_migration_data,
            metadata=_metadata,
        )

    async def delete_migration(self, migration: MigrationFile) -> None:
        """
        Deletes a migration file.

        Args:
            migration (MigrationFile): The migration file to delete.

        Returns:
            None
        """
        address = migration.stored_address

        if not address:
            return

        _object_id = address.object_id

        if isinstance(_object_id, list):
            _object_id = _object_id[0]
        else:
            try:
                _object_id = json.loads(_object_id)[0]  # type: ignore[arg-type]
            except json.JSONDecodeError:
                pass

        result = await self._operation_manager.perform_data_command_lakehouse(
            command=glue.DataCommand(
                root_transaction_id=AmsdalAsyncTransactionManager().get_root_transaction_id(),
                transaction_id=AmsdalAsyncTransactionManager().transaction_id,
                mutations=[
                    glue.DeleteData(
                        schema=glue.SchemaReference(name=address.class_name, version=glue.Version.LATEST),
                        query=glue.Conditions(
                            glue.Condition(
                                left=glue.FieldReferenceExpression(
                                    field_reference=glue.FieldReference(
                                        field=glue.Field(name=PRIMARY_PARTITION_KEY),
                                        table_name=address.class_name,
                                    ),
                                ),
                                lookup=glue.FieldLookup.EQ,
                                right=glue.Value(value=_object_id),
                            )
                        ),
                    ),
                ],
            ),
        )

        if not result.success:
            msg = f'Failed to delete migration in DB: {result.message}'
            raise CommandError(msg) from result.exception

    async def _save_historical_data(self, address: Address, data: dict[str, Any], metadata: dict[str, Any]) -> None:
        data[METADATA_KEY] = metadata
        data[PRIMARY_PARTITION_KEY] = address.object_id

        result = await self._operation_manager.perform_data_command_lakehouse(
            command=glue.DataCommand(
                root_transaction_id=AmsdalAsyncTransactionManager().get_root_transaction_id(),
                transaction_id=AmsdalAsyncTransactionManager().transaction_id,
                mutations=[
                    glue.InsertData(
                        schema=glue.SchemaReference(name=address.class_name, version=glue.Version.LATEST),
                        data=[glue.Data(data=data)],
                    ),
                ],
            ),
        )

        if not result.success:
            msg = f'Failed to save historical data: {result.message}'
            raise CommandError(msg) from result.exception

    @staticmethod
    def _build_migration_data(migration: MigrationFile) -> dict[str, Any]:
        return {
            'number': migration.number,
            'migration_name': migration.path.name,
            'module_type': migration.type.value,
            'module_name': migration.module,
            'applied_at': migration.applied_at,
        }

    @classmethod
    def _build_migration_metadata(
        cls,
        migration: MigrationFile,  # noqa: ARG003
        object_id: str | None = None,
    ) -> tuple[Address, dict[str, Any]]:
        _address = cls.migration_address.model_copy(
            update={
                'object_id': object_id or get_identifier(),
            },
        )
        _transaction_manager = AmsdalAsyncTransactionManager()
        _transaction_ref = None

        if _transaction_manager.transaction_object:
            _transaction_ref = Reference(
                ref=ReferenceData(
                    **_transaction_manager.transaction_object.address.model_dump(),
                ),
            )

        return (
            _address,
            json.loads(
                Metadata(
                    object_id=_address.object_id,
                    object_version=_address.object_version,
                    class_schema_reference=Reference(
                        ref=ReferenceData(
                            **cls.migration_address.model_copy(
                                update={
                                    'class_version': Versions.LATEST,
                                }
                            ).model_dump(),
                        ),
                    ),
                    transaction=_transaction_ref,
                ).model_dump_json(),
            ),
        )

    async def _init_migration_table(self) -> None:
        migration_schema = glue.Schema(
            name=self.MIGRATION_TABLE,
            version='',
            properties=[
                glue.PropertySchema(
                    name=PRIMARY_PARTITION_KEY,
                    type=str,
                    required=True,
                ),
                glue.PropertySchema(
                    name=SECONDARY_PARTITION_KEY,
                    type=str,
                    required=True,
                ),
                glue.PropertySchema(
                    name='number',
                    type=int,
                    required=True,
                ),
                glue.PropertySchema(
                    name='migration_name',
                    type=str,
                    required=True,
                ),
                glue.PropertySchema(
                    name='module_type',
                    type=str,
                    required=True,
                ),
                glue.PropertySchema(
                    name='module_name',
                    type=str,
                    required=False,
                    default=None,
                ),
                glue.PropertySchema(
                    name='applied_at',
                    type=float,
                    required=False,
                    default=None,
                ),
            ],
            constraints=[
                glue.PrimaryKeyConstraint(
                    name=f'pk_{self.MIGRATION_TABLE.lower()}',
                    fields=[PRIMARY_PARTITION_KEY, SECONDARY_PARTITION_KEY],
                ),
            ],
        )

        table_schema_manager = AsyncTableSchemasManager()
        await table_schema_manager.register_table(migration_schema, using=LAKEHOUSE_DB_ALIAS)

        # we need to register the last version of the schema
        schema_version_manager = AsyncHistoricalSchemaVersionManager()
        schema_version_manager.register_last_version(self.MIGRATION_TABLE, '')
