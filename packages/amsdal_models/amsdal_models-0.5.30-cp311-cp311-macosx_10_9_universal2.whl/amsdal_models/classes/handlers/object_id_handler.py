import logging
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from amsdal_data.connections.constants import PRIMARY_PARTITION_KEY
from amsdal_utils.models.data_models.address import ObjectIDType
from amsdal_utils.utils.identifier import get_identifier
from pydantic import PrivateAttr

from amsdal_models.classes.decorators.private_property import PrivateProperty
from amsdal_models.classes.handlers.metadata_handler import MetadataHandler
from amsdal_models.classes.relationships.constants import PRIMARY_KEY
from amsdal_models.classes.relationships.constants import PRIMARY_KEY_FIELDS
from amsdal_models.classes.utils import is_partial_model

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class PrimaryKeyItem:
    instance: Any
    field_name: str

    @property
    def value(self) -> Any:
        return getattr(self.instance, self.field_name)

    @value.setter
    def value(self, value: Any) -> None:
        setattr(self.instance, self.field_name, value)


@dataclass(kw_only=True)
class PrimaryKeyInfo:
    items: list[PrimaryKeyItem]

    @property
    def is_single_key(self) -> bool:
        return len(self.items) == 1

    @property
    def single_key(self) -> PrimaryKeyItem:
        if self.is_single_key:
            return self.items[0]

        msg = 'Multiple primary keys found.'
        raise ValueError(msg)

    @property
    def value(self) -> Any:
        if self.is_single_key:
            return self.single_key.value

        return [item.value for item in self.items]

    def is_equal_by_index(self, pk_index: int, value: Any) -> bool:
        return self.items[pk_index].value == value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PrimaryKeyInfo):
            return False

        return self.value == other.value

    def __neq__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(tuple([item.value for item in self.items]))


class ObjectIdHandler(MetadataHandler):
    _object_id: ObjectIDType = PrivateAttr()  # type: ignore[assignment]
    _is_new_object: bool = PrivateAttr(default=True)

    def __init__(self, **kwargs: Any):
        _object_id = None
        _is_new_object = True
        _pk_fields = getattr(self.__class__, PRIMARY_KEY_FIELDS, None) or {}
        _is_custom_pk = len(_pk_fields) != 1 or PRIMARY_PARTITION_KEY not in _pk_fields

        if _is_custom_pk:
            _object_id = [kwargs.get(pk) for pk in _pk_fields]
            _is_new_object = any(_val is None for _val in _object_id)

            if _is_new_object:
                _object_id = [kwargs.get(pk) for pk in (getattr(self.__class__, PRIMARY_KEY, None) or [])]
                _is_new_object = any(_val is None for _val in _object_id)

            if len(_object_id) == 1:
                _object_id = _object_id[0]
        else:
            _object_id = kwargs.pop('_object_id', None)

        super().__init__(**kwargs)

        self._is_new_object = _is_new_object

        if not _is_custom_pk:
            self._is_new_object = _object_id is None

            if _object_id is None:
                self._object_id = get_identifier()
            else:
                self._object_id = _object_id

    @PrivateProperty
    def _table_name(self) -> str:
        if self.__table_name__:
            return self.__table_name__

        if is_partial_model(self._entity):
            return self.__class__.__name__[: -len('Partial')]
        return self.__class__.__name__

    @PrivateProperty
    def pk(self) -> PrimaryKeyInfo:
        pks = list(getattr(self, PRIMARY_KEY_FIELDS, {}).keys())

        if pks == [PRIMARY_PARTITION_KEY]:
            pks = ['_object_id']

        return PrimaryKeyInfo(
            items=[
                PrimaryKeyItem(
                    instance=self,
                    field_name=pk,
                )
                for pk in pks
            ],
        )

    @PrivateProperty
    def object_id(self) -> ObjectIDType:
        """
        Object identifier. This is a unique identifier for the record. This is a UUID.

        Returns:
            str: UUID string of the object ID.
        """
        return self.pk.value

    @classmethod
    def _pk_fields(cls) -> list[str]:
        return list(getattr(cls, PRIMARY_KEY_FIELDS, {}).keys())

    @object_id.setter  # type: ignore[no-redef]
    def object_id(self, object_id: ObjectIDType) -> None:
        """
        Set the object ID.

        Args:
            object_id (ObjectIDType): Object identifier.
        """
        pks = self._pk_fields()

        if pks == [PRIMARY_PARTITION_KEY]:
            pks = ['_object_id']

        if not isinstance(object_id, Iterable) or isinstance(object_id, str):
            object_id = [object_id]

        if len(object_id) != len(pks):
            msg = (
                f'Primary key fields count does not match the object ID count. '
                f'Expected {len(pks)} but got {len(object_id)}'
            )

            raise ValueError(msg)

        for pk, value in zip(pks, object_id, strict=False):
            setattr(self, f'_{pk}', value)

    @PrivateProperty
    def is_new_object(self) -> bool:
        """
        Returns True if the object is new and has not been saved to the database.

        Returns:
            bool: Boolean flag indicating if the object is new.
        """
        return self._is_new_object

    def __getattribute__(self, name: str) -> Any:
        try:
            return super().__getattribute__(name)
        except AttributeError as e:
            if name.startswith('_'):
                raise

            pks = self._pk_fields()

            if name not in pks:
                raise e

            try:
                return getattr(self, f'_{name}')
            except AttributeError:
                raise e  # noqa: B904
