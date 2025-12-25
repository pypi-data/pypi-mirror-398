from _typeshed import Incomplete
from amsdal_models.classes.base import BaseModel as BaseModel
from amsdal_models.classes.constants import PARTIAL_CLASS_NAME_SUFFIX as PARTIAL_CLASS_NAME_SUFFIX
from amsdal_models.classes.decorators.private_property import PrivateProperty as PrivateProperty
from amsdal_models.classes.relationships.constants import FOREIGN_KEYS as FOREIGN_KEYS, PRIMARY_KEY as PRIMARY_KEY
from amsdal_models.classes.utils import build_class_meta_schema_reference as build_class_meta_schema_reference, build_class_schema_reference as build_class_schema_reference, is_partial_model as is_partial_model
from amsdal_utils.models.data_models.metadata import Metadata
from amsdal_utils.utils.lazy_object import LazyObject
from typing import Any, ClassVar

logger: Incomplete
OBJECT_ID_FIELD: str

class MetadataHandler(BaseModel):
    _class_address: ClassVar[str]
    
    
    
    def __init__(self, **kwargs: Any) -> None: ...
    @PrivateProperty
    def _metadata(self) -> Metadata: ...
    @PrivateProperty
    def is_latest(self) -> bool: ...
    @PrivateProperty
    def is_from_lakehouse(self) -> bool: ...
    def build_metadata(self, metadata: dict[str, Any] | Metadata | None) -> Metadata:
        """
        Builds the metadata object for this record.

        Returns:
            Metadata: The metadata object for this record.
        """
    def get_metadata(self) -> Metadata:
        """
        Returns the metadata object for this record.

        Returns:
            Metadata: The metadata object for this record.
        """
    async def aget_metadata(self) -> Metadata:
        """
        Returns the metadata object for this record.

        Returns:
            Metadata: The metadata object for this record.
        """
    def _invalidate_metadata(self) -> None: ...
