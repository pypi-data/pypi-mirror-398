import logging

import amsdal_glue as glue
from amsdal_data.connections.constants import SECONDARY_PARTITION_KEY
from amsdal_data.connections.historical.data_query_transform import META_CLASS_NAME
from amsdal_data.connections.historical.data_query_transform import METADATA_TABLE_ALIAS
from amsdal_data.connections.historical.data_query_transform import NEXT_VERSION_FIELD
from amsdal_data.connections.historical.schema_version_manager import AsyncHistoricalSchemaVersionManager
from amsdal_data.connections.historical.schema_version_manager import HistoricalSchemaVersionManager
from amsdal_data.transactions.decorators import async_transaction
from amsdal_data.transactions.decorators import transaction
from amsdal_data.transactions.manager import AmsdalAsyncTransactionManager
from amsdal_glue_core.common.operations.mutations.data import DataMutation
from amsdal_utils.models.enums import Versions
from amsdal_utils.query.utils import Q
from amsdal_utils.utils.decorators import async_mode_only
from amsdal_utils.utils.decorators import sync_mode_only

from amsdal_models.classes.glue_utils import model_to_data
from amsdal_models.classes.relationships.helpers.build_pk_query import build_pk_query
from amsdal_models.classes.relationships.meta.primary_key import build_metadata_primary_key
from amsdal_models.classes.relationships.meta.references import build_metadata_foreign_keys
from amsdal_models.managers.base_manager import BaseManager
from amsdal_models.querysets.base_queryset import ModelType
from amsdal_models.querysets.errors import BulkOperationError
from amsdal_models.querysets.executor import LAKEHOUSE_DB_ALIAS

logger = logging.getLogger(__name__)


class Manager(BaseManager):  # type: ignore[type-arg]
    @sync_mode_only
    def previous_version(self, obj: ModelType) -> ModelType | None:
        """
        Retrieve the previous version of the given model instance.

        This method returns the previous version of the specified model instance
        by querying the database for the instance with the prior version number.
        If no prior version exists, None is returned.

        Args:
            obj (ModelType): The model instance for which to retrieve the previous version.

        Returns:
            ModelType | None: The previous version of the model instance, or None if no prior version exists.
        """
        object_id = obj.object_id
        object_version = obj.get_metadata().prior_version

        if not object_version:
            return None

        q = Q(_address__object_version=object_version)

        return self.get_queryset().using(LAKEHOUSE_DB_ALIAS).first(q, _address__object_id=object_id).execute()

    @async_mode_only
    async def aprevious_version(self, obj: ModelType) -> ModelType | None:
        """
        Retrieve the previous version of the given model instance.

        This method returns the previous version of the specified model instance
        by querying the database for the instance with the prior version number.
        If no prior version exists, None is returned.

        Args:
            obj (ModelType): The model instance for which to retrieve the previous version.

        Returns:
            ModelType | None: The previous version of the model instance, or None if no prior version exists.
        """
        object_id = obj.object_id
        object_version = (await obj.aget_metadata()).prior_version

        if not object_version:
            return None

        q = Q(_address__object_version=object_version)

        return await self.get_queryset().using(LAKEHOUSE_DB_ALIAS).first(q, _address__object_id=object_id).aexecute()

    @sync_mode_only
    def next_version(self, obj: ModelType) -> ModelType | None:
        """
        Retrieve the next version of the given model instance.

        This method returns the next version of the specified model instance
        by querying the database for the instance with the next version number.
        If no next version exists, None is returned.

        Args:
            obj (ModelType): The model instance for which to retrieve the next version.

        Returns:
            ModelType | None: The next version of the model instance, or None if no next version exists.
        """
        object_id = obj.object_id
        object_version = obj.get_metadata().next_version

        return self.get_specific_version(object_id, object_version)

    @async_mode_only
    async def anext_version(self, obj: ModelType) -> ModelType | None:
        """
        Retrieve the next version of the given model instance.

        This method returns the next version of the specified model instance
        by querying the database for the instance with the next version number.
        If no next version exists, None is returned.

        Args:
            obj (ModelType): The model instance for which to retrieve the next version.

        Returns:
            ModelType | None: The next version of the model instance, or None if no next version exists.
        """
        object_id = obj.object_id
        object_version = (await obj.aget_metadata()).next_version

        return await self.aget_specific_version(object_id, object_version)  # type: ignore[func-returns-value]

    @sync_mode_only  # type: ignore[arg-type]
    def get_specific_version(self, object_id: str, object_version: str | None) -> ModelType | None:
        """
        Retrieve a specific version of the model instance.

        This method returns a specific version of the model instance identified by
        the given `object_id` and `object_version`. If the `object_version` is not
        provided, None is returned. The method queries the database using the
        `LAKEHOUSE_DB_ALIAS` to find the instance with the specified version.

        Args:
            object_id (str): The unique identifier of the model instance.
            object_version (str | None): The version number of the model instance.

        Returns:
            ModelType | None: The model instance with the specified version, or None if
            the `object_version` is not provided or no matching instance is found.
        """
        if not object_version:
            return None

        return (
            self.get_queryset()
            .using(LAKEHOUSE_DB_ALIAS)
            .get(
                _address__class_version=Versions.ALL,
                _address__object_id=object_id,
                _address__object_version=object_version,
            )
            .execute()
        )

    @async_mode_only  # type: ignore[arg-type]
    async def aget_specific_version(self, object_id: str, object_version: str | None) -> ModelType | None:
        """
        Retrieve a specific version of the model instance.

        This method returns a specific version of the model instance identified by
        the given `object_id` and `object_version`. If the `object_version` is not
        provided, None is returned. The method queries the database using the
        `LAKEHOUSE_DB_ALIAS` to find the instance with the specified version.

        Args:
            object_id (str): The unique identifier of the model instance.
            object_version (str | None): The version number of the model instance.

        Returns:
            ModelType | None: The model instance with the specified version, or None if
            the `object_version` is not provided or no matching instance is found.
        """
        if not object_version:
            return None

        return await (
            self.get_queryset()
            .using(LAKEHOUSE_DB_ALIAS)
            .get(
                _address__class_version=Versions.ALL,
                _address__object_id=object_id,
                _address__object_version=object_version,
            )
            .aexecute()
        )

    @transaction
    def bulk_create(self, objs: list[ModelType], using: str | None = None, *, force_insert: bool = False) -> None:
        """
        Perform a bulk update on the given list of model instances.

        This method updates multiple instances of the model class defined in the
        `model` attribute of the manager in a single query. The `using` parameter
        allows specifying a database alias for the operation.

        Args:
            objs (list[ModelType]): A list of model instances to be updated.
            using (str | None): The database alias to be used for the bulk update operation.
            If None, the default database alias is used.

        Returns:
            None
        """
        from amsdal_data.application import DataApplication

        for obj in objs:
            if not obj.is_new_object and not force_insert:
                msg = 'Cannot create some objects: some are already saved'
                raise BulkOperationError(msg)

            if not isinstance(obj, self.model):
                msg = 'Cannot apply a bulk operation on objects of different types'
                raise BulkOperationError(msg)

        operation_manager = DataApplication().operation_manager

        command = glue.DataCommand(
            root_transaction_id=self._transaction_manager.get_root_transaction_id(),
            transaction_id=self._transaction_manager.transaction_id,
            mutations=[
                glue.InsertData(
                    schema=glue.SchemaReference(
                        name=self.table_name,
                        version=(HistoricalSchemaVersionManager().get_latest_schema_version(self.model.__name__)),
                        metadata={
                            **build_metadata_primary_key(self.model),
                            META_CLASS_NAME: self.model.__name__,
                        },
                    ),
                    data=[model_to_data(obj) for obj in objs],
                ),
            ],
        )

        if using == LAKEHOUSE_DB_ALIAS:
            result = operation_manager.perform_data_command_lakehouse(command)
        else:
            result = operation_manager.perform_data_command(command)

        if not result.success:
            msg = f'Bulk create operation failed: {result.message}'
            raise BulkOperationError(msg) from result.exception

    @async_transaction
    async def bulk_acreate(
        self,
        objs: list[ModelType],
        using: str | None = None,
        *,
        force_insert: bool = False,
    ) -> None:
        """
        Perform a bulk update on the given list of model instances.

        This method updates multiple instances of the model class defined in the
        `model` attribute of the manager in a single query. The `using` parameter
        allows specifying a database alias for the operation.

        Args:
            objs (list[ModelType]): A list of model instances to be updated.
            using (str | None): The database alias to be used for the bulk update operation.
            If None, the default database alias is used.

        Returns:
            None
        """
        from amsdal_data.application import AsyncDataApplication

        for obj in objs:
            if not obj.is_new_object and not force_insert:
                msg = 'Cannot create some objects: some are already saved'
                raise BulkOperationError(msg)

            if not isinstance(obj, self.model):
                msg = 'Cannot apply a bulk operation on objects of different types'
                raise BulkOperationError(msg)

        operation_manager = AsyncDataApplication().operation_manager

        command = glue.DataCommand(
            root_transaction_id=AmsdalAsyncTransactionManager().get_root_transaction_id(),
            transaction_id=AmsdalAsyncTransactionManager().transaction_id,
            mutations=[
                glue.InsertData(
                    schema=glue.SchemaReference(
                        name=self.table_name,
                        version=(
                            await AsyncHistoricalSchemaVersionManager().get_latest_schema_version(self.model.__name__)
                        ),
                        metadata={
                            **build_metadata_primary_key(self.model),
                            META_CLASS_NAME: self.model.__name__,
                        },
                    ),
                    data=[model_to_data(obj) for obj in objs],
                ),
            ],
        )

        if using == LAKEHOUSE_DB_ALIAS:
            result = await operation_manager.perform_data_command_lakehouse(command)
        else:
            result = await operation_manager.perform_data_command(command)

        if not result.success:
            msg = f'Bulk create operation failed: {result.message}'
            raise BulkOperationError(msg) from result.exception

    @transaction
    def bulk_update(self, objs: list[ModelType], using: str | None = None) -> None:
        """
        Perform a bulk creation of the given list of model instances.

        This method creates multiple instances of the model class defined in the
        `model` attribute of the manager in a single query. The `using` parameter
        allows specifying a database alias for the operation.

        Args:
            objs (list[ModelType]): A list of model instances to be created.
            using (str | None): The database alias to be used for the bulk creation operation.
            If None, the default database alias is used.

        Returns:
            None
        """
        from amsdal_data.application import DataApplication

        for obj in objs:
            if obj.is_new_object:
                msg = 'Cannot update a new object'
                raise BulkOperationError(msg)

            if not obj.is_latest:
                msg = 'Cannot update an object that is not the latest version'
                raise BulkOperationError(msg)

            if not isinstance(obj, self.model):
                msg = 'Cannot apply a bulk operation on objects of different types'
                raise BulkOperationError(msg)

        operation_manager = DataApplication().operation_manager
        mutations: list[DataMutation] = []
        for obj in objs:
            query = build_pk_query(self.table_name, obj)

            if using == LAKEHOUSE_DB_ALIAS:
                query.children.append(
                    glue.Condition(
                        left=glue.FieldReferenceExpression(
                            field_reference=glue.FieldReference(
                                field=glue.Field(name=SECONDARY_PARTITION_KEY),
                                table_name=self.table_name,
                            ),
                        ),
                        lookup=glue.FieldLookup.EQ,
                        right=glue.Value(value=obj.get_metadata().object_version),
                    ),
                )

            mutations.append(
                glue.UpdateData(
                    schema=glue.SchemaReference(
                        name=self.table_name,
                        version=(HistoricalSchemaVersionManager().get_latest_schema_version(self.model.__name__)),
                        metadata={
                            **build_metadata_primary_key(self.model),
                            **build_metadata_foreign_keys(obj),
                            META_CLASS_NAME: self.model.__name__,
                        },
                    ),
                    data=model_to_data(obj),
                    query=query,
                )
            )

        command = glue.DataCommand(
            root_transaction_id=self._transaction_manager.get_root_transaction_id(),
            transaction_id=self._transaction_manager.transaction_id,
            mutations=mutations,
        )

        if using == LAKEHOUSE_DB_ALIAS:
            result = operation_manager.perform_data_command_lakehouse(command)
        else:
            result = operation_manager.perform_data_command(command)

        if not result.success:
            msg = 'Bulk update operation failed'
            raise BulkOperationError(msg) from result.exception

    @async_transaction
    async def bulk_aupdate(self, objs: list[ModelType], using: str | None = None) -> None:
        """
        Perform a bulk creation of the given list of model instances.

        This method creates multiple instances of the model class defined in the
        `model` attribute of the manager in a single query. The `using` parameter
        allows specifying a database alias for the operation.

        Args:
            objs (list[ModelType]): A list of model instances to be created.
            using (str | None): The database alias to be used for the bulk creation operation.
            If None, the default database alias is used.

        Returns:
            None
        """
        from amsdal_data.application import AsyncDataApplication

        for obj in objs:
            if obj.is_new_object:
                msg = 'Cannot update a new object'
                raise BulkOperationError(msg)

            if not obj.is_latest:
                msg = 'Cannot update an object that is not the latest version'
                raise BulkOperationError(msg)

            if not isinstance(obj, self.model):
                msg = 'Cannot apply a bulk operation on objects of different types'
                raise BulkOperationError(msg)

        operation_manager = AsyncDataApplication().operation_manager
        mutations: list[DataMutation] = []
        locked_objects = []

        for obj in objs:
            query = build_pk_query(self.table_name, obj)

            if using == LAKEHOUSE_DB_ALIAS:
                query.children.append(
                    glue.Condition(
                        left=glue.FieldReferenceExpression(
                            field_reference=glue.FieldReference(
                                field=glue.Field(name=SECONDARY_PARTITION_KEY),
                                table_name=self.table_name,
                            ),
                        ),
                        lookup=glue.FieldLookup.EQ,
                        right=glue.Value(value=(await obj.aget_metadata()).address.object_version),
                    ),
                )

            mutations.append(
                glue.UpdateData(
                    schema=glue.SchemaReference(
                        name=self.table_name,
                        version=(
                            await AsyncHistoricalSchemaVersionManager().get_latest_schema_version(self.model.__name__)
                        ),
                        metadata={
                            **build_metadata_primary_key(self.model),
                            **build_metadata_foreign_keys(obj),
                            META_CLASS_NAME: self.model.__name__,
                        },
                    ),
                    data=model_to_data(obj),
                    query=query,
                )
            )
            locked_objects.append(
                glue.LockSchemaReference(
                    query=build_pk_query(self.table_name, obj),
                    schema=glue.SchemaReference(
                        name=self.table_name,
                        version=(
                            await AsyncHistoricalSchemaVersionManager().get_latest_schema_version(self.model.__name__)
                        ),
                        metadata={
                            **build_metadata_primary_key(self.model),
                            **build_metadata_foreign_keys(obj),
                            META_CLASS_NAME: self.model.__name__,
                        },
                    ),
                ),
            )

        lock_id = None
        root_transaction_id = AmsdalAsyncTransactionManager().get_root_transaction_id()
        transaction_id = AmsdalAsyncTransactionManager().transaction_id

        lock_command = glue.LockCommand(
            lock_id=lock_id,
            root_transaction_id=root_transaction_id,
            transaction_id=transaction_id,
            action=glue.LockAction.ACQUIRE,
            mode=glue.LockMode.EXCLUSIVE,
            parameter=glue.LockParameter.WAIT,
            locked_objects=locked_objects,
        )
        command = glue.DataCommand(
            lock_id=lock_id,
            root_transaction_id=root_transaction_id,
            transaction_id=transaction_id,
            mutations=mutations,
        )
        release_command = glue.LockCommand(
            lock_id=lock_id,
            root_transaction_id=root_transaction_id,
            transaction_id=transaction_id,
            action=glue.LockAction.RELEASE,
            mode=glue.LockMode.EXCLUSIVE,
            parameter=glue.LockParameter.WAIT,
            locked_objects=locked_objects,
        )

        if using == LAKEHOUSE_DB_ALIAS:
            perform_data_command = operation_manager.perform_data_command_lakehouse
            perform_lock_command = operation_manager.perform_lock_command_lakehouse
        else:
            perform_data_command = operation_manager.perform_data_command
            perform_lock_command = operation_manager.perform_lock_command

        lock_result = await perform_lock_command(lock_command)

        if not lock_result.success:
            msg = 'Bulk update operation failed'
            raise BulkOperationError(msg) from lock_result.exception

        result = await perform_data_command(command)
        await perform_lock_command(release_command)

        if not result.success:
            msg = 'Bulk update operation failed'
            raise BulkOperationError(msg) from result.exception

    @transaction
    def bulk_delete(self, objs: list[ModelType], using: str | None = None) -> None:
        """
        Perform a bulk deletion of the given list of model instances.

        This method deletes multiple instances of the model class defined in the
        `model` attribute of the manager in a single query. The `using` parameter
        allows specifying a database alias for the operation.

        Args:
            objs (list[ModelType]): A list of model instances to be deleted.
            using (str | None): The database alias to be used for the bulk deletion operation.
            If None, the default database alias is used.

        Returns:
            None
        """
        from amsdal_data.application import DataApplication

        for obj in objs:
            if obj.is_new_object:
                msg = 'Cannot delete a new object'
                raise BulkOperationError(msg)

            if not obj.is_latest:
                msg = 'Cannot delete an object that is not the latest version'
                raise BulkOperationError(msg)

            if not isinstance(obj, self.model):
                msg = 'Cannot apply a bulk operation on objects of different types'
                raise BulkOperationError(msg)

        operation_manager = DataApplication().operation_manager

        mutations: list[DataMutation] = []

        for obj in objs:
            mutation = glue.DeleteData(
                schema=glue.SchemaReference(
                    name=self.table_name,
                    version=(HistoricalSchemaVersionManager().get_latest_schema_version(self.model.__name__)),
                    metadata={
                        **build_metadata_primary_key(self.model),
                        **build_metadata_foreign_keys(obj),
                        META_CLASS_NAME: self.model.__name__,
                    },
                ),
                query=build_pk_query(self.table_name, obj),
            )

            mutations.append(mutation)

            if using != LAKEHOUSE_DB_ALIAS and not DataApplication().is_lakehouse_only:
                continue

            if obj.get_metadata().is_latest:
                if mutation.query:
                    _next_version_field = glue.FieldReference(
                        field=glue.Field(name=NEXT_VERSION_FIELD),
                        table_name=METADATA_TABLE_ALIAS,
                    )
                    mutation.query &= glue.Conditions(
                        glue.Condition(
                            left=glue.FieldReferenceExpression(field_reference=_next_version_field),
                            lookup=glue.FieldLookup.ISNULL,
                            right=glue.Value(value=True),
                        ),
                        glue.Condition(
                            left=glue.FieldReferenceExpression(field_reference=_next_version_field),
                            lookup=glue.FieldLookup.EQ,
                            right=glue.Value(value=''),
                        ),
                        connector=glue.FilterConnector.OR,
                    )
            else:
                _object_version = obj.get_metadata().object_version
                msg = f'Invalid object version: {_object_version}. Delete not latest version is not allowed'
                raise BulkOperationError(msg)

        command = glue.DataCommand(
            mutations=mutations,
            root_transaction_id=self._transaction_manager.get_root_transaction_id(),
            transaction_id=self._transaction_manager.transaction_id,
        )

        if using == LAKEHOUSE_DB_ALIAS:
            result = operation_manager.perform_data_command_lakehouse(command)
        else:
            result = operation_manager.perform_data_command(command)

        if not result.success:
            msg = 'Bulk delete operation failed'
            raise BulkOperationError(msg) from result.exception

    @async_transaction
    async def bulk_adelete(self, objs: list[ModelType], using: str | None = None) -> None:
        """
        Perform a bulk deletion of the given list of model instances.

        This method deletes multiple instances of the model class defined in the
        `model` attribute of the manager in a single query. The `using` parameter
        allows specifying a database alias for the operation.

        Args:
            objs (list[ModelType]): A list of model instances to be deleted.
            using (str | None): The database alias to be used for the bulk deletion operation.
            If None, the default database alias is used.

        Returns:
            None
        """
        from amsdal_data.application import AsyncDataApplication

        for obj in objs:
            if obj.is_new_object:
                msg = 'Cannot delete a new object'
                raise BulkOperationError(msg)

            if not obj.is_latest:
                msg = 'Cannot delete an object that is not the latest version'
                raise BulkOperationError(msg)

            if not isinstance(obj, self.model):
                msg = 'Cannot apply a bulk operation on objects of different types'
                raise BulkOperationError(msg)

        operation_manager = AsyncDataApplication().operation_manager

        mutations: list[DataMutation] = []
        locked_objects = []

        for obj in objs:
            mutation = glue.DeleteData(
                schema=glue.SchemaReference(
                    name=self.table_name,
                    version=(
                        await AsyncHistoricalSchemaVersionManager().get_latest_schema_version(self.model.__name__)
                    ),
                    metadata={
                        **build_metadata_primary_key(self.model),
                        **build_metadata_foreign_keys(obj),
                        META_CLASS_NAME: self.model.__name__,
                    },
                ),
                query=build_pk_query(self.table_name, obj),
            )
            mutations.append(mutation)

            locked_objects.append(
                glue.LockSchemaReference(
                    query=build_pk_query(self.table_name, obj),
                    schema=glue.SchemaReference(
                        name=self.table_name,
                        version=(
                            await AsyncHistoricalSchemaVersionManager().get_latest_schema_version(self.model.__name__)
                        ),
                        metadata={
                            **build_metadata_primary_key(self.model),
                            **build_metadata_foreign_keys(obj),
                            META_CLASS_NAME: self.model.__name__,
                        },
                    ),
                )
            )

            if using != LAKEHOUSE_DB_ALIAS and not AsyncDataApplication().is_lakehouse_only:
                continue

            if (await obj.aget_metadata()).is_latest:
                if mutation.query:
                    _next_version_field = glue.FieldReference(
                        field=glue.Field(name=NEXT_VERSION_FIELD),
                        table_name=METADATA_TABLE_ALIAS,
                    )
                    _cond = glue.Conditions(
                        glue.Condition(
                            left=glue.FieldReferenceExpression(field_reference=_next_version_field),
                            lookup=glue.FieldLookup.ISNULL,
                            right=glue.Value(value=True),
                        ),
                        glue.Condition(
                            left=glue.FieldReferenceExpression(field_reference=_next_version_field),
                            lookup=glue.FieldLookup.EQ,
                            right=glue.Value(value=''),
                        ),
                        connector=glue.FilterConnector.OR,
                    )
                    mutation.query &= _cond
            else:
                _object_version = (await obj.aget_metadata()).object_version
                msg = f'Invalid object version: {_object_version}. Delete not latest version is not allowed'
                raise BulkOperationError(msg)

        lock_id = None
        root_transaction_id = AmsdalAsyncTransactionManager().get_root_transaction_id()
        transaction_id = AmsdalAsyncTransactionManager().transaction_id
        lock_command = glue.LockCommand(
            lock_id=lock_id,
            root_transaction_id=root_transaction_id,
            transaction_id=transaction_id,
            action=glue.LockAction.ACQUIRE,
            mode=glue.LockMode.EXCLUSIVE,
            parameter=glue.LockParameter.WAIT,
            locked_objects=locked_objects,
        )
        command = glue.DataCommand(
            mutations=mutations,
            lock_id=lock_id,
            root_transaction_id=root_transaction_id,
            transaction_id=transaction_id,
        )
        release_command = glue.LockCommand(
            lock_id=lock_id,
            root_transaction_id=root_transaction_id,
            transaction_id=transaction_id,
            action=glue.LockAction.RELEASE,
            mode=glue.LockMode.EXCLUSIVE,
            parameter=glue.LockParameter.WAIT,
            locked_objects=locked_objects,
        )

        if using == LAKEHOUSE_DB_ALIAS:
            perform_data_command = operation_manager.perform_data_command_lakehouse
            perform_lock_command = operation_manager.perform_lock_command_lakehouse
        else:
            perform_data_command = operation_manager.perform_data_command
            perform_lock_command = operation_manager.perform_lock_command

        lock_result = await perform_lock_command(lock_command)
        if not lock_result.success:
            msg = 'Bulk update operation failed'
            raise BulkOperationError(msg) from lock_result.exception

        result = await perform_data_command(command)
        await perform_lock_command(release_command)

        if not result.success:
            msg = 'Bulk delete operation failed'
            raise BulkOperationError(msg) from result.exception
