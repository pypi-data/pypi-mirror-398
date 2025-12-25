from _typeshed import Incomplete
from amsdal_data.transactions.decorators import async_transaction, transaction
from amsdal_glue_core.common.operations.mutations.data import DataMutation as DataMutation
from amsdal_models.classes.glue_utils import model_to_data as model_to_data
from amsdal_models.classes.relationships.helpers.build_pk_query import build_pk_query as build_pk_query
from amsdal_models.classes.relationships.meta.primary_key import build_metadata_primary_key as build_metadata_primary_key
from amsdal_models.classes.relationships.meta.references import build_metadata_foreign_keys as build_metadata_foreign_keys
from amsdal_models.managers.base_manager import BaseManager as BaseManager
from amsdal_models.querysets.base_queryset import ModelType as ModelType
from amsdal_models.querysets.errors import BulkOperationError as BulkOperationError
from amsdal_models.querysets.executor import LAKEHOUSE_DB_ALIAS as LAKEHOUSE_DB_ALIAS
from amsdal_utils.utils.decorators import async_mode_only, sync_mode_only

logger: Incomplete

class Manager(BaseManager):
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
    @sync_mode_only
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
    @async_mode_only
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
    @async_transaction
    async def bulk_acreate(self, objs: list[ModelType], using: str | None = None, *, force_insert: bool = False) -> None:
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
