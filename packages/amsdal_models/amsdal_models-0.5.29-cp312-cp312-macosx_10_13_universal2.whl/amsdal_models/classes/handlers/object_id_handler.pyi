from _typeshed import Incomplete
from amsdal_models.classes.decorators.private_property import PrivateProperty as PrivateProperty
from amsdal_models.classes.handlers.metadata_handler import MetadataHandler as MetadataHandler
from amsdal_models.classes.relationships.constants import PRIMARY_KEY as PRIMARY_KEY, PRIMARY_KEY_FIELDS as PRIMARY_KEY_FIELDS
from amsdal_models.classes.utils import is_partial_model as is_partial_model
from amsdal_utils.models.data_models.address import ObjectIDType as ObjectIDType
from dataclasses import dataclass
from typing import Any

logger: Incomplete

@dataclass(kw_only=True)
class PrimaryKeyItem:
    instance: Any
    field_name: str
    @property
    def value(self) -> Any: ...
    @value.setter
    def value(self, value: Any) -> None: ...

@dataclass(kw_only=True)
class PrimaryKeyInfo:
    items: list[PrimaryKeyItem]
    @property
    def is_single_key(self) -> bool: ...
    @property
    def single_key(self) -> PrimaryKeyItem: ...
    @property
    def value(self) -> Any: ...
    def is_equal_by_index(self, pk_index: int, value: Any) -> bool: ...
    def __eq__(self, other: Any) -> bool: ...
    def __neq__(self, other: Any) -> bool: ...
    def __hash__(self) -> int: ...

class ObjectIdHandler(MetadataHandler):
    
    
    def __init__(self, **kwargs: Any) -> None: ...
    @PrivateProperty
    def _table_name(self) -> str: ...
    @PrivateProperty
    def pk(self) -> PrimaryKeyInfo: ...
    @PrivateProperty
    def object_id(self) -> ObjectIDType:
        """
        Object identifier. This is a unique identifier for the record. This is a UUID.

        Returns:
            str: UUID string of the object ID.
        """
    @classmethod
    def _pk_fields(cls) -> list[str]: ...
    @object_id.setter
    def object_id(self, object_id: ObjectIDType) -> None:
        """
        Set the object ID.

        Args:
            object_id (ObjectIDType): Object identifier.
        """
    @PrivateProperty
    def is_new_object(self) -> bool:
        """
        Returns True if the object is new and has not been saved to the database.

        Returns:
            bool: Boolean flag indicating if the object is new.
        """
    def __getattribute__(self, name: str) -> Any: ...
