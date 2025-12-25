import contextlib
import inspect
import json
import logging
from collections.abc import Generator
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from typing import Literal
from typing import Optional
from typing import Self

import typing_extensions
from amsdal_data.connections.historical.data_query_transform import DEFAULT_PKS
from amsdal_data.transactions.decorators import async_transaction
from amsdal_data.transactions.decorators import transaction
from amsdal_utils.config.manager import AmsdalConfigManager
from amsdal_utils.errors import AmsdalError
from amsdal_utils.models.data_models.address import Address
from amsdal_utils.models.enums import ModuleType
from amsdal_utils.models.enums import Versions
from amsdal_utils.query.utils import Q
from amsdal_utils.utils.decorators import async_mode_only
from amsdal_utils.utils.decorators import sync_mode_only
from pydantic import ConfigDict
from pydantic import Field as PydanticModelField
from pydantic import PrivateAttr
from pydantic import model_validator
from pydantic._internal._model_construction import ModelMetaclass
from pydantic._internal._model_construction import NoInitField
from pydantic.errors import PydanticUserError
from typing_extensions import dataclass_transform

from amsdal_models.classes.base import BaseModel
from amsdal_models.classes.constants import REFERENCE_FIELD_SUFFIX
from amsdal_models.classes.data_models.constraints import UniqueConstraint
from amsdal_models.classes.errors import AmsdalRecursionError
from amsdal_models.classes.errors import AmsdalUniquenessError
from amsdal_models.classes.errors import ObjectAlreadyExistsError
from amsdal_models.classes.handlers.reference_handler import ReferenceHandler
from amsdal_models.classes.mixins.model_hooks_mixin import ModelHooksMixin
from amsdal_models.classes.relationships.constants import FOREIGN_KEYS
from amsdal_models.classes.relationships.constants import MANY_TO_MANY_FIELDS
from amsdal_models.classes.relationships.meta.common import convert_models_in_dict_to_references
from amsdal_models.classes.relationships.meta.many_to_many import DeferredModel
from amsdal_models.classes.utils import is_partial_model
from amsdal_models.managers.model_manager import Manager
from amsdal_models.querysets.errors import ObjectDoesNotExistError
from amsdal_models.querysets.executor import DEFAULT_DB_ALIAS
from amsdal_models.querysets.executor import LAKEHOUSE_DB_ALIAS
from amsdal_models.storage.base import Storage

if TYPE_CHECKING:
    from amsdal_utils.models.data_models.reference import Reference

# should be `set[int] | set[str] | dict[int, IncEx] | dict[str, IncEx] | None`, but mypy can't cope
IncEx: typing_extensions.TypeAlias = 'set[int] | set[str] | dict[int, Any] | dict[str, Any] | None'

logger = logging.getLogger(__name__)


class TypeModel(
    ModelHooksMixin,
    ReferenceHandler,
    BaseModel,
):
    model_config = ConfigDict(validate_assignment=True)

    __module_type__: ClassVar[ModuleType] = ModuleType.USER
    __table_name__: ClassVar[str | None] = None
    __primary_key__: ClassVar[list[str] | None] = None
    __primary_key_fields__: ClassVar[dict[str, Any] | None] = None
    __foreign_keys__: ClassVar[list[str] | None] = None
    __many_to_many_fields__: ClassVar[dict[str, tuple[Any, Any, tuple[str, str] | None]] | None] = None

    @model_validator(mode='before')
    @classmethod
    def convert_string_to_dict(cls, data: Any) -> Any:
        """
        Converts a string to a dictionary if possible.

        Args:
            data (Any): The data to convert.

        Returns:
            Any: The converted data.
        """
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                pass

        return data


@dataclass_transform(kw_only_default=True, field_specifiers=(PydanticModelField, PrivateAttr, NoInitField))
class AmsdalModelMetaclass(ModelMetaclass):
    if not TYPE_CHECKING:

        def __new__(
            mcs,
            cls_name: str,
            bases: tuple[type[Any], ...],
            namespace: dict[str, Any],
            *args: Any,
            **kwargs: Any,
        ) -> type:
            from amsdal_models.classes.relationships.meta.many_to_many import generate_m2m_properties
            from amsdal_models.classes.relationships.meta.primary_key import process_primary_keys
            from amsdal_models.classes.relationships.meta.primary_key import resolve_primary_keys
            from amsdal_models.classes.relationships.meta.references import extract_references
            from amsdal_models.classes.relationships.meta.references import generate_fk_properties
            from amsdal_models.classes.relationships.validators.foreign_keys import model_foreign_keys_validator

            if cls_name not in {'Model', 'LegacyModel'}:
                process_primary_keys(resolve_primary_keys(bases, namespace), bases, namespace)
                base_field_names, _, _ = mcs._collect_bases_data(bases)

                fks, many2many = extract_references(base_field_names, bases, namespace)

                if FOREIGN_KEYS not in namespace:
                    namespace[FOREIGN_KEYS] = []

                for fk, fk_annotation in fks.items():
                    generate_fk_properties(fk, fk_annotation, namespace)

                for m2m, m2m_annotation in many2many.items():
                    generate_m2m_properties(m2m, m2m_annotation, namespace)

                namespace['_foreign_keys_validator'] = model_validator(mode='wrap')(
                    classmethod(model_foreign_keys_validator),  # type: ignore[arg-type]
                )

                convert_models_in_dict_to_references(namespace)

            cls = super().__new__(mcs, cls_name, bases, namespace, *args, **kwargs)

            # Handle the default 'objects' manager
            if 'objects' in namespace:
                namespace['objects'].model = cls
            else:
                for base in bases:
                    if hasattr(base, 'objects'):
                        cls.objects = base.objects.copy(cls=cls)  # type: ignore[attr-defined]
                        break

            # Handle all other custom managers in the namespace
            from amsdal_models.managers.base_manager import BaseManager

            for attr_name, attr_value in namespace.items():
                if attr_name != 'objects' and isinstance(attr_value, BaseManager):
                    # Bind the manager to the model class
                    attr_value.model = cls

            return cls

        def __call__(cls, *args: Any, **kwds: Any) -> Any:  # noqa: N805
            from amsdal_models.classes.relationships.constants import DEFERRED_FOREIGN_KEYS
            from amsdal_models.classes.relationships.constants import DEFERRED_M2M_FIELDS
            from amsdal_models.classes.relationships.constants import DEFERRED_PRIMARY_KEYS
            from amsdal_models.classes.relationships.helpers.deferred_foreign_keys import complete_deferred_foreign_keys
            from amsdal_models.classes.relationships.helpers.deferred_many_to_many import complete_deferred_many_to_many
            from amsdal_models.classes.relationships.helpers.deferred_primary_keys import complete_deferred_primary_keys

            if getattr(cls, DEFERRED_PRIMARY_KEYS, None):
                complete_deferred_primary_keys(cls)

            if getattr(cls, DEFERRED_FOREIGN_KEYS, None):
                complete_deferred_foreign_keys(cls)

            if getattr(cls, DEFERRED_M2M_FIELDS, None):
                complete_deferred_many_to_many(cls)

            return super().__call__(*args, **kwds)


class Model(TypeModel, metaclass=AmsdalModelMetaclass):
    """
    Base class for all model classes.

    Attributes:
        model_config (ConfigDict): Configuration for the model.
        objects (ClassVar[Manager[Self]]): Manager for the Model class.
    """

    _is_inside_save: bool = PrivateAttr(default=False)
    model_config = ConfigDict(validate_assignment=True)

    objects: ClassVar[Manager] = Manager()

    def __init__(self, **kwargs: Any) -> None:
        is_new_object = not kwargs.get('_object_id', None)

        self.pre_init(is_new_object=is_new_object, kwargs=kwargs)
        super().__init__(**kwargs)

        m2m_fields = getattr(self.__class__, MANY_TO_MANY_FIELDS, {}) or {}

        for _property, _property_value in kwargs.items():
            if _property in m2m_fields and _property_value:
                _, _, _, _ = m2m_fields[_property]
                setattr(self, _property, _property_value)

        self.post_init(is_new_object=is_new_object, kwargs=kwargs)
        self._is_inside_save = False

    @sync_mode_only
    @transaction
    def save(self, *, force_insert: bool = False, using: str | None = None, skip_hooks: bool = False) -> Self:
        """
        Saves the record of the Model object into the database.

        By default, the object will be updated in the database if it already exists.
        If `force_insert` is set to True, the object will be inserted into the database even if it already exists,
        which may result in an `ObjectAlreadyExistsError`.

        The method first checks if `force_insert` is True, and if the object already exists in the database.
        If it does, it raises an `ObjectAlreadyExistsError`.

        Then, depending on the object existence, the method either creates a new record in the database or updates
        the existing record. It also triggers the corresponding `pre_create()`, `post_create()`, `pre_update()`, and
        `post_update()` hooks.

        Finally, the method returns the saved Model object.

        Args:
            force_insert (bool): Indicates whether to force insert the object into the database,
            even if it already exists.
            using (str | None): The name of the database to use.
            skip_hooks (bool): Indicates whether to skip the hooks.

        Returns:
            Model: The saved Model object.
        """
        from amsdal_models.classes.relationships.meta.many_to_many import build_m2m_value_property

        if is_partial_model(self.__class__):
            msg = 'Partial models cannot be saved!'
            raise AmsdalError(msg)

        if self._is_inside_save:
            msg = 'Trying to save an object that is already being saved'
            raise AmsdalRecursionError(msg)

        self._is_inside_save = True

        try:
            if force_insert:
                _using = using or DEFAULT_DB_ALIAS
                qs = self.objects.using(_using).filter(_address__object_id=self.object_id)

                if _using == LAKEHOUSE_DB_ALIAS:
                    qs = qs.latest()

                if qs.count().execute():
                    if _using == LAKEHOUSE_DB_ALIAS:
                        _address = self.get_metadata().address
                    else:
                        _address = Address(
                            resource=AmsdalConfigManager().get_connection_name_by_model_name(
                                self.__class__.__name__,
                            ),
                            object_id=self.object_id,
                            object_version=Versions.LATEST,
                            class_name=self.__class__.__name__,
                            class_version=Versions.LATEST,
                        )
                    raise ObjectAlreadyExistsError(address=_address)

                self._is_new_object = True

            _is_new_object = self._is_new_object
            _old_m2m_records = {}
            _m2m_fields = getattr(self.__class__, MANY_TO_MANY_FIELDS, None) or {}
            _has_m2m_fields = bool(_m2m_fields)

            if _is_new_object:
                self._create(using=using, skip_hooks=skip_hooks)
            else:
                _old_m2m_records = self._get_old_m2m_records(using=using)
                self._update(using=using, skip_hooks=skip_hooks)

            if _has_m2m_fields:
                _instance = self.refetch_from_db(latest=True)

                for m2m in _m2m_fields:
                    _value_property = build_m2m_value_property(m2m)

                    if hasattr(self, _value_property):
                        setattr(_instance, _value_property, getattr(self, _value_property))
            else:
                _instance = self

            self._process_m2m_fields(
                instance=_instance,
                old_m2m_records=_old_m2m_records,
                using=using,
            )
        finally:
            self._is_inside_save = False

        # invalidate metadata
        self._invalidate_metadata()

        return self

    @async_mode_only
    @async_transaction
    async def asave(self, *, force_insert: bool = False, using: str | None = None, skip_hooks: bool = False) -> Self:
        """
        Saves the record of the Model object into the database.

        By default, the object will be updated in the database if it already exists.
        If `force_insert` is set to True, the object will be inserted into the database even if it already exists,
        which may result in an `ObjectAlreadyExistsError`.

        The method first checks if `force_insert` is True, and if the object already exists in the database.
        If it does, it raises an `ObjectAlreadyExistsError`.

        Then, depending on the object existence, the method either creates a new record in the database or updates
        the existing record. It also triggers the corresponding `pre_create()`, `post_create()`, `pre_update()`, and
        `post_update()` hooks.

        Finally, the method returns the saved Model object.

        Args:
            force_insert (bool): Indicates whether to force insert the object into the database,
            even if it already exists.
            using (str | None): The name of the database to use.
            skip_hooks (bool): Indicates whether to skip the hooks.

        Returns:
            Model: The saved Model object.
        """
        from amsdal_models.classes.relationships.meta.many_to_many import build_m2m_value_property

        if is_partial_model(self.__class__):
            msg = 'Partial models cannot be saved!'
            raise AmsdalError(msg)

        if self._is_inside_save:
            msg = 'Trying to save an object that is already being saved'
            raise AmsdalRecursionError(msg)

        self._is_inside_save = True

        try:
            if force_insert:
                _using = using or DEFAULT_DB_ALIAS
                qs = self.objects.using(_using).filter(_address__object_id=self.object_id)

                if _using == LAKEHOUSE_DB_ALIAS:
                    qs = qs.latest()

                if await qs.count().aexecute():
                    if _using == LAKEHOUSE_DB_ALIAS:
                        _address = (await self.aget_metadata()).address
                    else:
                        _address = Address(
                            resource=AmsdalConfigManager().get_connection_name_by_model_name(
                                self.__class__.__name__,
                            ),
                            object_id=self.object_id,
                            object_version=Versions.LATEST,
                            class_name=self.__class__.__name__,
                            class_version=Versions.LATEST,
                        )
                    raise ObjectAlreadyExistsError(address=_address)

                self._is_new_object = True

            _is_new_object = self._is_new_object
            _old_m2m_records = {}
            _m2m_fields = getattr(self.__class__, MANY_TO_MANY_FIELDS, None) or {}
            _has_m2m_fields = bool(_m2m_fields)

            if _is_new_object:
                await self._acreate(using=using, skip_hooks=skip_hooks)
            else:
                _old_m2m_records = await self._aget_old_m2m_records(using=using)
                await self._aupdate(using=using, skip_hooks=skip_hooks)

            if _has_m2m_fields:
                _instance = await self.arefetch_from_db(latest=True)

                for m2m in _m2m_fields:
                    _value_property = build_m2m_value_property(m2m)

                    if hasattr(self, _value_property):
                        setattr(_instance, _value_property, getattr(self, _value_property))
            else:
                _instance = self

            await self._aprocess_m2m_fields(
                instance=_instance,
                old_m2m_records=_old_m2m_records,
                using=using,
            )
        finally:
            self._is_inside_save = False

        # invalidate metadata
        self._invalidate_metadata()

        return self

    @sync_mode_only
    @transaction
    def delete(self, using: str | None = None, *, skip_hooks: bool = False) -> None:
        """
        Deletes the existing record of the Model object from the database.

        This method first calls the `pre_delete()` method, then deletes the record from the database by calling
            the `_delete()` method, and finally calls the `post_delete()` method.
        It changes the flag `is_deleted` to True in the metadata of the record.

        Args:
            using (str | None): The name of the database to use.
            skip_hooks (bool): Indicates whether to skip the `pre_delete()` and `post_delete()` hooks.

        Returns:
            None
        """
        if is_partial_model(self.__class__):
            msg = 'Partial models cannot be deleted!'
            raise AmsdalError(msg)

        if self._is_inside_save:
            msg = 'Trying to delete an object that is already being saved'
            raise AmsdalRecursionError(msg)

        self._is_inside_save = True

        try:
            if not skip_hooks:
                self.pre_delete()

            if not self._metadata.is_latest:
                msg = 'Error! Trying to make a new version of an object that is not the latest version!'
                raise ValueError(msg)

            self.objects.bulk_delete([self], using=using)  # type: ignore[arg-type,call-arg]

            if not skip_hooks:
                self.post_delete()

        finally:
            self._is_inside_save = False

        # invalidate metadata
        self._invalidate_metadata()

    @async_mode_only
    @async_transaction
    async def adelete(self, using: str | None = None, *, skip_hooks: bool = False) -> None:
        """
        Deletes the existing record of the Model object from the database.

        This method first calls the `pre_delete()` method, then deletes the record from the database by calling
            the `_delete()` method, and finally calls the `post_delete()` method.
        It changes the flag `is_deleted` to True in the metadata of the record.

        Args:
            using (str | None): The name of the database to use.
            skip_hooks (bool): Indicates whether to skip the `pre_delete()` and `post_delete()` hooks.

        Returns:
            None
        """
        if is_partial_model(self.__class__):
            msg = 'Partial models cannot be deleted!'
            raise AmsdalError(msg)

        if self._is_inside_save:
            msg = 'Trying to delete an object that is already being saved'
            raise AmsdalRecursionError(msg)

        self._is_inside_save = True

        try:
            if not skip_hooks:
                await self.apre_delete()

            if not self._metadata.is_latest:
                msg = 'Error! Trying to make a new version of an object that is not the latest version!'
                raise ValueError(msg)

            await self.objects.bulk_adelete([self], using=using)  # type: ignore[arg-type,call-arg]

            if not skip_hooks:
                await self.apost_delete()

        finally:
            self._is_inside_save = False

        # invalidate metadata
        self._invalidate_metadata()

    @property
    def display_name(self) -> str:
        """
        Gets the display name of the Model object.

        This method returns the string representation of the object's address.

        Returns:
            str: The display name of the Model object.
        """
        if self.is_from_lakehouse and not AmsdalConfigManager().get_config().async_mode:
            _address = self.get_metadata().address
        else:
            _class_name = self.__class__.__name__
            _address = Address(
                resource=AmsdalConfigManager().get_connection_name_by_model_name(_class_name),
                class_name=_class_name,
                class_version=Versions.LATEST,
                object_id=self.object_id,
                object_version=Versions.LATEST,
            )

        return str(_address)

    def _check_unique(self, using: str | None) -> None:
        from amsdal_data.application import DataApplication

        if self.__class__.__name__ in ['ClassObject', 'ClassObjectMeta', 'Object']:
            return

        unique = [
            constraint.fields
            for constraint in getattr(self, '__constraints__', [])
            if isinstance(constraint, UniqueConstraint)
        ]

        if unique:
            qs = self.objects.using(using or DEFAULT_DB_ALIAS).latest()

            if using == LAKEHOUSE_DB_ALIAS or DataApplication().is_lakehouse_only:
                qs = qs.filter(_metadata__is_deleted=False)

            if not self._is_new_object:
                qs = qs.exclude(_address__object_id=self.object_id)

            _q: Q | None = None

            for unique_properties in unique:
                _sub_q = Q(**{_property: getattr(self, _property) for _property in unique_properties})
                _q = _sub_q if _q is None else _q | _sub_q

            if qs.filter(_q).count().execute():  # type: ignore[arg-type]
                msg = f'Object with these unique properties {unique} already exists'
                raise AmsdalUniquenessError(msg)

    async def _acheck_unique(self, using: str | None) -> None:
        from amsdal_data.application import AsyncDataApplication

        if self.__class__.__name__ in ['ClassObject', 'ClassObjectMeta', 'Object']:
            return

        unique = [
            constraint.fields
            for constraint in getattr(self, '__constraints__', [])
            if isinstance(constraint, UniqueConstraint)
        ]

        if unique:
            qs = self.objects.latest()

            if using == LAKEHOUSE_DB_ALIAS or AsyncDataApplication().is_lakehouse_only:
                qs = qs.filter(_metadata__is_deleted=False)

            if not self._is_new_object:
                qs = qs.exclude(_address__object_id=self._object_id)

            _q: Q | None = None

            for unique_properties in unique:
                _sub_q = Q(**{_property: getattr(self, _property) for _property in unique_properties})
                _q = _sub_q if _q is None else _q | _sub_q

            if await qs.filter(_q).count().aexecute():  # type: ignore[arg-type]
                msg = f'Object with these unique properties {unique} already exists'
                raise AmsdalUniquenessError(msg)

    def _create(self, using: str | None, *, skip_hooks: bool = False) -> None:
        if not skip_hooks:
            self.pre_create()

        self._process_nested_objects()
        self._check_unique(using=using)
        self.objects.bulk_create([self], using=using)  # type: ignore[arg-type,call-arg]

        try:
            self._is_new_object = False

            if not skip_hooks:
                self.post_create()
        except Exception:
            self._is_new_object = True
            raise

    async def _acreate(self, using: str | None, *, skip_hooks: bool = False) -> None:
        if not skip_hooks:
            await self.apre_create()

        await self._async_process_nested_objects()
        await self._acheck_unique(using=using)
        await self.objects.bulk_acreate([self], using=using)  # type: ignore[arg-type,call-arg]

        try:
            self._is_new_object = False

            if not skip_hooks:
                await self.apost_create()
        except Exception:
            self._is_new_object = True
            raise

    def _update(self, using: str | None, *, skip_hooks: bool = False) -> None:
        if not skip_hooks:
            self.pre_update()

        if not self._metadata.is_latest:
            msg = 'Error! Trying to make a new version of an object that is not the latest version!'
            raise ValueError(msg)

        self._process_nested_objects()
        self._check_unique(using=using)
        self.objects.bulk_update([self], using=using)  # type: ignore[arg-type,call-arg]

        if not skip_hooks:
            self.post_update()

    async def _aupdate(self, using: str | None, *, skip_hooks: bool = False) -> None:
        if not skip_hooks:
            await self.apre_update()

        if not self._metadata.is_latest:
            msg = 'Error! Trying to make a new version of an object that is not the latest version!'
            raise ValueError(msg)

        await self._async_process_nested_objects()
        await self._acheck_unique(using=using)
        await self.objects.bulk_aupdate([self], using=using)  # type: ignore[arg-type,call-arg]

        if not skip_hooks:
            await self.apost_update()

    def _get_old_m2m_records(self, using: str | None) -> dict[str, list['Model']]:
        records = {}
        using = using or DEFAULT_DB_ALIAS
        _m2m_fields = getattr(self.__class__, MANY_TO_MANY_FIELDS, {}) or {}

        for m2m, (m2m_ref, m2m_model, through_fields, _) in _m2m_fields.items():
            _m2m_model = m2m_model(self.__class__) if isinstance(m2m_model, DeferredModel) else m2m_model

            source_field, target_field = (
                through_fields
                if through_fields
                else (
                    self.__class__.__name__.lower(),
                    m2m_ref.__name__.lower(),
                )
            )
            m2m_records = (
                _m2m_model.objects.using(using)
                .select_related(target_field)
                .filter(
                    **{source_field: self.build_reference(is_frozen=True)},
                )
                .execute()
            )
            records[m2m] = m2m_records

        return records

    async def _aget_old_m2m_records(self, using: str | None) -> dict[str, list['Model']]:
        records = {}
        using = using or DEFAULT_DB_ALIAS
        _m2m_fields = getattr(self.__class__, MANY_TO_MANY_FIELDS, {}) or {}

        for m2m, (m2m_ref, m2m_model, through_fields, _) in _m2m_fields.items():
            _m2m_model = m2m_model(self.__class__) if isinstance(m2m_model, DeferredModel) else m2m_model

            source_field, target_field = (
                through_fields
                if through_fields
                else (
                    self.__class__.__name__.lower(),
                    m2m_ref.__name__.lower(),
                )
            )
            m2m_records = await (
                _m2m_model.objects.using(using)
                .select_related(target_field)
                .filter(
                    **{source_field: await self.abuild_reference(is_frozen=True)},
                )
                .aexecute()
            )
            records[m2m] = m2m_records

        return records

    @classmethod
    def _process_m2m_fields(
        cls,
        instance: 'Model',
        old_m2m_records: dict[str, list['Model']],
        *,
        using: str | None,
    ) -> None:
        from amsdal_models.classes.relationships.meta.many_to_many import build_m2m_value_property

        using = using or DEFAULT_DB_ALIAS
        _m2m_fields = getattr(cls, MANY_TO_MANY_FIELDS, {}) or {}

        for m2m, (m2m_ref, m2m_model, through_fields, _) in _m2m_fields.items():
            _m2m_model = m2m_model(cls) if isinstance(m2m_model, DeferredModel) else m2m_model

            _value_property = build_m2m_value_property(m2m)
            _has_changed_m2m_values = hasattr(instance, _value_property)

            source_field, target_field = (
                through_fields
                if through_fields
                else (
                    cls.__name__.lower(),
                    m2m_ref.__name__.lower(),
                )
            )

            new_values: list[Model] = []
            _values = old_m2m_records.get(m2m, [])
            old_values = {getattr(_value, target_field): _value for _value in _values}

            if not _has_changed_m2m_values and not old_values:
                continue

            if _has_changed_m2m_values:
                unchanged_values = []

                new_values = []
                for item in getattr(instance, _value_property) or []:
                    if item in old_values:
                        unchanged_values.append(old_values.pop(item))
                    else:
                        new_values.append(
                            _m2m_model(
                                **{
                                    source_field: instance.build_reference(is_frozen=True),
                                    target_field: item,
                                },
                            ),
                        )
            else:
                unchanged_values = list(old_values.values())
                old_values.clear()

            if old_values:
                _m2m_model.objects.bulk_delete(list(old_values.values()), using=using)  # type: ignore[arg-type,call-arg]
            if new_values:
                _m2m_model.objects.bulk_create(new_values, using=using, force_insert=True)  # type: ignore[arg-type,call-arg]
            if unchanged_values:
                # unchanged values are important only for lakehouse
                _items = []

                for _item in unchanged_values:
                    _data = _item.model_dump_refs()
                    _data[source_field] = instance.build_reference(is_frozen=True)
                    _items.append(_m2m_model(**_data))

                _m2m_model.objects.bulk_create(_items, using=LAKEHOUSE_DB_ALIAS, force_insert=True)  # type: ignore[arg-type,call-arg]

    @classmethod
    async def _aprocess_m2m_fields(
        cls,
        instance: 'Model',
        old_m2m_records: dict[str, list['Model']],
        *,
        using: str | None,
    ) -> None:
        from amsdal_models.classes.relationships.meta.many_to_many import build_m2m_value_property

        using = using or DEFAULT_DB_ALIAS
        _m2m_fields = getattr(cls, MANY_TO_MANY_FIELDS, {}) or {}

        for m2m, (m2m_ref, m2m_model, through_fields, _) in _m2m_fields.items():
            _m2m_model = m2m_model(cls) if isinstance(m2m_model, DeferredModel) else m2m_model

            _value_property = build_m2m_value_property(m2m)
            _has_changed_m2m_values = hasattr(instance, _value_property)

            source_field, target_field = (
                through_fields
                if through_fields
                else (
                    cls.__name__.lower(),
                    m2m_ref.__name__.lower(),
                )
            )

            new_values: list[Model] = []
            _values = old_m2m_records.get(m2m, [])
            old_values = {getattr(_value, target_field): _value for _value in _values}

            if not _has_changed_m2m_values and not old_values:
                continue

            if _has_changed_m2m_values:
                unchanged_values = []

                new_values = []
                _items = getattr(instance, _value_property) or []
                if inspect.iscoroutine(_items):
                    _items = await _items

                for item in _items:
                    if item in old_values:
                        unchanged_values.append(old_values.pop(item))
                    else:
                        new_values.append(
                            _m2m_model(
                                **{
                                    source_field: await instance.abuild_reference(is_frozen=True),
                                    target_field: item,
                                },
                            ),
                        )
            else:
                unchanged_values = list(old_values.values())
                old_values.clear()

            if old_values:
                await _m2m_model.objects.bulk_adelete(list(old_values.values()), using=using)  # type: ignore[arg-type,call-arg]
            if new_values:
                await _m2m_model.objects.bulk_acreate(new_values, using=using, force_insert=True)  # type: ignore[arg-type,call-arg]
            if unchanged_values:
                # unchanged values are important only for lakehouse
                _items = []

                for _item in unchanged_values:
                    _data = _item.model_dump_refs()
                    _data[source_field] = await instance.abuild_reference(is_frozen=True)
                    _items.append(_m2m_model(**_data))

                await _m2m_model.objects.bulk_acreate(_items, using=LAKEHOUSE_DB_ALIAS, force_insert=True)  # type: ignore[arg-type,call-arg]

    def _process_nested_objects(self) -> None:
        for field in sorted(self.model_fields_set):
            setattr(self, field, self._process_nested_field(getattr(self, field)))

    def _process_nested_field(self, field_value: Any) -> Any:
        if isinstance(field_value, LegacyModel):
            return field_value.build_reference()
        if isinstance(field_value, Model):
            if field_value.is_new_object:
                field_value.save()
            return field_value.build_reference()
        elif isinstance(field_value, (list, set, tuple)):
            return [self._process_nested_field(item) for item in field_value]
        elif isinstance(field_value, dict):
            return {
                self._process_nested_field(key): self._process_nested_field(value) for key, value in field_value.items()
            }
        return field_value

    async def _async_process_nested_objects(self) -> None:
        for field in sorted(self.model_fields_set):
            _v = getattr(self, field)
            if inspect.iscoroutine(_v):
                _v = await _v
            _value = await self._async_process_nested_field(_v)
            setattr(self, field, _value)

    async def _async_process_nested_field(self, field_value: Any) -> Any:
        if isinstance(field_value, LegacyModel):
            return await field_value.abuild_reference()
        if isinstance(field_value, Model):
            if field_value.is_new_object:
                await field_value.asave()
            return await field_value.abuild_reference()
        elif isinstance(field_value, (list, set, tuple)):
            return [await self._async_process_nested_field(item) for item in field_value]
        elif isinstance(field_value, dict):
            return {
                await self._async_process_nested_field(key): await self._async_process_nested_field(value)
                for key, value in field_value.items()
            }
        return field_value

    @model_validator(mode='after')
    def _bind_file_storages(self) -> 'Model':
        for name, field_info in self.__class__.model_fields.items():
            extra = getattr(field_info, 'json_schema_extra', None) or {}

            if 'storage_class' not in extra:
                continue

            storage = Storage.from_storage_spec(extra)
            value = getattr(self, name, None)
            self._attach_storage(value, storage)

        return self

    @staticmethod
    def _attach_storage(value: Any, storage: Storage) -> None:
        from collections.abc import Iterable
        from collections.abc import Mapping

        if value is None:
            return

        looks_like_file = (
            hasattr(value, 'filename')
            and hasattr(value, 'data')
            and hasattr(value, 'size')
            and hasattr(value, 'storage_address')
            and hasattr(value, '_storage')
        )

        if looks_like_file and value._storage is None:
            value._storage = storage
            return

        if isinstance(value, Mapping):
            for v in value.values():
                Model._attach_storage(v, storage)
        elif isinstance(value, Iterable) and not isinstance(value, str | bytes | bytearray):
            for v in value:
                Model._attach_storage(v, storage)

    def __setattr__(self, name: str, value: Any) -> None:
        # If it's a declared field, let Pydantic validate it
        if name in self.__class__.model_fields:
            field_info = self.__class__.model_fields.get(name)
            extra = getattr(field_info, 'json_schema_extra', None)

            if isinstance(extra, dict) and 'storage_class' in extra:
                storage = Storage.from_storage_spec(extra)
                self._attach_storage(value, storage)

            super().__setattr__(name, value)
        else:
            # Otherwise, bypass Pydantic entirely
            object.__setattr__(self, name, value)

    def model_dump_refs(
        self,
        *,
        mode: Literal['json', 'python'] | str = 'python',
        include: IncEx = None,
        exclude: IncEx = None,
        context: Any | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
        serialize_as_any: bool = False,
    ) -> dict[str, Any]:
        """
        Dumps the record and its references into a dictionary of data.

        Args:
            mode (Literal['json', 'python'] | str, optional): The mode of serialization. Defaults to 'python'.
            include (IncEx, optional): Fields to include in the serialization. Defaults to None.
            exclude (IncEx, optional): Fields to exclude from the serialization. Defaults to None.
            context (Any | None, optional): The context of the serialization. Defaults to None.
            by_alias (bool, optional): Whether to use field aliases. Defaults to False.
            exclude_unset (bool, optional): Whether to exclude unset fields. Defaults to False.
            exclude_defaults (bool, optional): Whether to exclude fields with default values. Defaults to False.
            exclude_none (bool, optional): Whether to exclude fields with None values. Defaults to False.
            round_trip (bool, optional): Whether to ensure round-trip serialization. Defaults to False.
            warnings (bool, optional): Whether to show warnings. Defaults to True.
            serialize_as_any (bool, optional): Whether to serialize as Any. Defaults to False.

        Returns:
            dict[str, Any]: A dictionary representation of the model.
        """
        return super().model_dump_refs(
            mode=mode,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
        )

    def model_dump(  # type: ignore[override]
        self,
        *,
        mode: Literal['json', 'python'] | str = 'python',
        include: IncEx = None,
        exclude: IncEx = None,
        context: Any | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
        serialize_as_any: bool = False,
    ) -> dict[str, Any]:
        """
        This method is used to dump the record dictionary of data, although the referenced objects will be represented
        in reference format. Here is an example of reference format:

            {
              "$ref": {
                "resource": "sqlite",
                "class_name": "Person",
                "class_version": "1234",
                "object_id": "4567",
                "object_version": "8901"
              }
            }

        Args:
            mode (Literal['json', 'python'] | str, optional): The mode of serialization. Defaults to 'python'.
            include (IncEx, optional): Fields to include in the serialization. Defaults to None.
            exclude (IncEx, optional): Fields to exclude from the serialization. Defaults to None.
            context (Any | None, optional): The context of the serialization. Defaults to None.
            by_alias (bool, optional): Whether to use field aliases. Defaults to False.
            exclude_unset (bool, optional): Whether to exclude unset fields. Defaults to False.
            exclude_defaults (bool, optional): Whether to exclude fields with default values. Defaults to False.
            exclude_none (bool, optional): Whether to exclude fields with None values. Defaults to False.
            round_trip (bool, optional): Whether to ensure round-trip serialization. Defaults to False.
            warnings (bool, optional): Whether to show warnings. Defaults to True.
            serialize_as_any (bool, optional): Whether to serialize as Any. Defaults to False.

        Returns:
            dict[str, Any]: A dictionary representation of the model.
        """
        return super().model_dump(
            mode=mode,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
        )

    def model_dump_json_refs(
        self,
        *,
        indent: int | None = None,
        include: IncEx = None,
        exclude: IncEx = None,
        context: Any | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
        serialize_as_any: bool = False,
    ) -> str:
        """
        Similar to `model_dump_refs`, but returns a JSON string instead of a dictionary.

        Args:
            indent (int | None, optional): The indentation of the JSON string. Defaults to None.
            include (IncEx, optional): Fields to include in the serialization. Defaults to None.
            exclude (IncEx, optional): Fields to exclude from the serialization. Defaults to None.
            context (Any | None, optional): The context of the serialization. Defaults to None.
            by_alias (bool, optional): Whether to use field aliases. Defaults to False.
            exclude_unset (bool, optional): Whether to exclude unset fields. Defaults to False.
            exclude_defaults (bool, optional): Whether to exclude fields with default values. Defaults to False.
            exclude_none (bool, optional): Whether to exclude fields with None values. Defaults to False.
            round_trip (bool, optional): Whether to ensure round-trip serialization. Defaults to False.
            warnings (bool, optional): Whether to show warnings. Defaults to True.
            serialize_as_any (bool, optional): Whether to serialize as Any. Defaults to False.

        Returns:
            str: A JSON string representation of the model.
        """

        return super().model_dump_json_refs(
            indent=indent,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
        )

    def model_dump_json(  # type: ignore[override]
        self,
        *,
        indent: int | None = None,
        include: IncEx = None,
        exclude: IncEx = None,
        context: Any | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
        serialize_as_any: bool = False,
    ) -> str:
        """
        Similar to `model_dump`, but returns a JSON string instead of a dictionary.

        Args:
            mode (Literal['json', 'python'] | str, optional): The mode of serialization. Defaults to 'python'.
            include (IncEx, optional): Fields to include in the serialization. Defaults to None.
            exclude (IncEx, optional): Fields to exclude from the serialization. Defaults to None.
            context (Any | None, optional): The context of the serialization. Defaults to None.
            by_alias (bool, optional): Whether to use field aliases. Defaults to False.
            exclude_unset (bool, optional): Whether to exclude unset fields. Defaults to False.
            exclude_defaults (bool, optional): Whether to exclude fields with default values. Defaults to False.
            exclude_none (bool, optional): Whether to exclude fields with None values. Defaults to False.
            round_trip (bool, optional): Whether to ensure round-trip serialization. Defaults to False.
            warnings (bool, optional): Whether to show warnings. Defaults to True.
            serialize_as_any (bool, optional): Whether to serialize as Any. Defaults to False.

        Returns:
            str: A JSON string representation of the model.
        """

        return super().model_dump_json(
            indent=indent,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
        )

    @sync_mode_only
    def previous_version(self) -> Self | None:
        """
        Gets the previous version of the Model object from the database.

        This method returns the Model object that is the previous version of the current object, if it exists.
            Otherwise, it returns None.

        Returns:
            Self | None: The previous version of the Model object.
        """
        return self.objects.previous_version(obj=self)

    @async_mode_only
    async def aprevious_version(self) -> Self | None:
        """
        Gets the previous version of the Model object from the database.

        This method returns the Model object that is the previous version of the current object, if it exists.
            Otherwise, it returns None.

        Returns:
            Self | None: The previous version of the Model object.
        """
        return await self.objects.aprevious_version(obj=self)

    @sync_mode_only
    def next_version(self) -> Self | None:
        """
        Gets the next version of the Model object from the database.

        This method returns the Model object that is the next version of the current object, if it exists. Otherwise,
            it returns None.

        Returns:
            Self | None: The next version of the Model object.
        """
        return self.objects.next_version(obj=self)

    @async_mode_only
    async def anext_version(self) -> Self | None:
        """
        Gets the next version of the Model object from the database.

        This method returns the Model object that is the next version of the current object, if it exists. Otherwise,
            it returns None.

        Returns:
            Self | None: The next version of the Model object.
        """
        return await self.objects.anext_version(obj=self)

    @sync_mode_only
    def refetch_from_db(self, *, latest: bool = False) -> Self:
        """
        Gets the object with the current version from the database.

        Returns:
            Self: The object with the current version from the database.
        """
        if latest:
            _object_version = Versions.LATEST
        else:
            _object_version = self.get_metadata().object_version if self.is_from_lakehouse else Versions.LATEST  # type: ignore[assignment]

        try:
            refetched_object = self.objects.get_specific_version(
                object_id=self.object_id,
                object_version=_object_version,
            )
        except ObjectDoesNotExistError as exc:
            msg = f'Object with id {self.object_id} and version {_object_version} does not exist'
            raise AmsdalError(msg) from exc

        if refetched_object is None:
            msg = f'Object with id {self.object_id} and version {_object_version} does not exist'
            raise AmsdalError(msg)

        return refetched_object

    @async_mode_only
    async def arefetch_from_db(self, *, latest: bool = False) -> Self:
        """
        Gets the object with the current version from the database.

        Returns:
            Self: The object with the current version from the database.
        """
        if latest:
            _object_version = Versions.LATEST
        else:
            _object_version = (await self.aget_metadata()).object_version if self.is_from_lakehouse else Versions.LATEST  # type: ignore[assignment]

        try:
            refetched_object = await self.objects.aget_specific_version(  # type: ignore[func-returns-value]
                object_id=self.object_id,
                object_version=_object_version,
            )
        except ObjectDoesNotExistError as exc:
            msg = f'Object with id {self.object_id} and version {_object_version} does not exist'
            raise AmsdalError(msg) from exc

        if refetched_object is None:
            msg = f'Object with id {self.object_id} and version {_object_version} does not exist'
            raise AmsdalError(msg)

        return refetched_object

    def __getattribute__(self, name: str) -> Any:
        from amsdal_utils.models.data_models.reference import Reference

        from amsdal_models.classes.helpers.reference_loader import ReferenceLoader

        if name.endswith(REFERENCE_FIELD_SUFFIX):
            res = super().__getattribute__(name[: -len(REFERENCE_FIELD_SUFFIX)])

            if isinstance(res, Model):
                res = res.build_reference()
            return res

        res = super().__getattribute__(name)

        is_reference_field = False
        if not name.startswith('__'):
            _model_fields = self.__class__.model_fields
            if name in _model_fields and (_annotation := _model_fields[name].annotation):
                if _annotation is Reference or _annotation == Optional[Reference]:
                    is_reference_field = True

        if isinstance(res, Reference) and not is_reference_field:
            if not AmsdalConfigManager().get_config().async_mode:
                with contextlib.suppress(PydanticUserError, AmsdalError):
                    res = ReferenceLoader(res).load_reference()
            else:

                async def _load_reference() -> Any:
                    with contextlib.suppress(PydanticUserError, AmsdalError):
                        return await ReferenceLoader(res).aload_reference()

                return _load_reference()

        return res

    @staticmethod
    async def _async_load_reference(ref: 'Reference') -> Any:
        from amsdal_models.classes.helpers.reference_loader import ReferenceLoader

        with contextlib.suppress(PydanticUserError, AmsdalError):
            return await ReferenceLoader(ref).aload_reference()

        return ref

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False

        if self.pk != other.pk:
            return False

        if not (self.is_from_lakehouse or other.is_from_lakehouse) or AmsdalConfigManager().get_config().async_mode:
            return True

        return self.get_metadata().object_version == other.get_metadata().object_version

    def __neq__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.pk)

    def __await__(self) -> Generator[None, None, Self]:
        async def _self() -> Self:
            return self

        return _self().__await__()


class LegacyModel(TypeModel, metaclass=AmsdalModelMetaclass):
    """
    LegacyModel class that inherits from TypeModel and uses AmsdalModelMetaclass as its metaclass.

    Attributes:
        model_config (ConfigDict): Configuration for the model.
    """

    __primary_key__: ClassVar[list[str]] = ['_object_id']
    __primary_key_fields__: ClassVar[dict[str, Any]] = DEFAULT_PKS
    model_config = ConfigDict(extra='allow')
