import contextlib
import json
import logging
from functools import partial
from typing import Any
from typing import ClassVar

import amsdal_glue as glue
from amsdal_data.application import AsyncDataApplication
from amsdal_data.application import DataApplication
from amsdal_data.connections.constants import PRIMARY_PARTITION_KEY
from amsdal_data.connections.historical.metadata_query import build_metadata_query
from amsdal_utils.models.data_models.metadata import Metadata
from amsdal_utils.models.enums import Versions
from amsdal_utils.utils.lazy_object import LazyObject
from pydantic import PrivateAttr

from amsdal_models.classes.base import BaseModel
from amsdal_models.classes.constants import PARTIAL_CLASS_NAME_SUFFIX
from amsdal_models.classes.decorators.private_property import PrivateProperty
from amsdal_models.classes.relationships.constants import FOREIGN_KEYS
from amsdal_models.classes.relationships.constants import PRIMARY_KEY
from amsdal_models.classes.utils import build_class_meta_schema_reference
from amsdal_models.classes.utils import build_class_schema_reference
from amsdal_models.classes.utils import is_partial_model

logger = logging.getLogger(__name__)

OBJECT_ID_FIELD = '_object_id'


class MetadataHandler(BaseModel):
    _class_address: ClassVar[str]

    _object_id: str = PrivateAttr()
    _is_from_lakehouse: bool = PrivateAttr(default=False)
    _metadata_lazy: LazyObject[Metadata] = PrivateAttr()

    def __init__(self, **kwargs: Any):
        metadata = kwargs.pop('_metadata', None)

        super().__init__(**kwargs)

        if metadata:
            if isinstance(metadata, Metadata):
                self._is_from_lakehouse = metadata.object_version != Versions.LATEST
            else:
                self._is_from_lakehouse = metadata.get('object_version') != Versions.LATEST

        self._metadata_lazy = LazyObject(partial(self.build_metadata, metadata=metadata))

    @PrivateProperty
    def _metadata(self) -> Metadata:
        return self._metadata_lazy.value

    @PrivateProperty
    def is_latest(self) -> bool:
        return self._metadata.is_latest

    @PrivateProperty
    def is_from_lakehouse(self) -> bool:
        return self._is_from_lakehouse

    def build_metadata(self, metadata: dict[str, Any] | Metadata | None) -> Metadata:
        """
        Builds the metadata object for this record.

        Returns:
            Metadata: The metadata object for this record.
        """
        if metadata:
            _metadata = metadata if isinstance(metadata, Metadata) else Metadata(**metadata)

            if (
                isinstance(_metadata.object_id, str)
                and len(_metadata.object_id) > 1
                and _metadata.object_id[0] == '['
                and _metadata.object_id[-1] == ']'
            ):
                with contextlib.suppress(json.JSONDecodeError):
                    _metadata.object_id = json.loads(_metadata.object_id)

            if isinstance(_metadata.object_id, list) and len(_metadata.object_id) == 1:
                _metadata.object_id = _metadata.object_id[0]

            if _metadata.object_version != Versions.LATEST:
                self._is_from_lakehouse = True

            return _metadata

        class_name = self.__class__.__name__

        if is_partial_model(self.__class__) and class_name.endswith(PARTIAL_CLASS_NAME_SUFFIX):
            class_name = class_name[slice(0, -len(PARTIAL_CLASS_NAME_SUFFIX))]

        return Metadata(
            object_id=self.object_id,  # type: ignore[attr-defined]
            object_version=Versions.LATEST,
            class_schema_reference=build_class_schema_reference(class_name, self.__class__),
            class_meta_schema_reference=build_class_meta_schema_reference(class_name, self.object_id),  # type: ignore[attr-defined]
        )

    def get_metadata(self) -> Metadata:
        """
        Returns the metadata object for this record.

        Returns:
            Metadata: The metadata object for this record.
        """
        if self._metadata.object_version == Versions.LATEST:
            pks = getattr(self, PRIMARY_KEY, None) or [OBJECT_ID_FIELD]
            fks = getattr(self, FOREIGN_KEYS, None) or []
            object_id = []

            if pks == [PRIMARY_PARTITION_KEY]:
                pks = [OBJECT_ID_FIELD]

            for pk in pks:
                if pk in fks:
                    object_id.append(getattr(self, f'{pk}_reference').model_dump())
                else:
                    object_id.append(getattr(self, pk))

            query = build_metadata_query(
                object_id=object_id,
                class_name=self.__class__.__name__,
            )
            query.limit = glue.LimitQuery(limit=1, offset=0)
            result = DataApplication().operation_manager.query_lakehouse(query)

            if not result.success:
                msg = f'Failed to retrieve metadata for object_id: {object_id}'
                raise ValueError(msg) from result.exception

            if not result.data:
                msg = f'No metadata found for object_id: {object_id}. Make sure the object was saved.'
                raise ValueError(msg) from None

            _metadata = Metadata(**result.data[0].data)

            if isinstance(_metadata.object_id, list) and len(_metadata.object_id) == 1:
                _metadata.object_id = _metadata.object_id[0]

            self._metadata_lazy = LazyObject(
                lambda: _metadata,
            )

        return self._metadata

    async def aget_metadata(self) -> Metadata:
        """
        Returns the metadata object for this record.

        Returns:
            Metadata: The metadata object for this record.
        """
        if self._metadata.object_version == Versions.LATEST:
            pks = getattr(self, PRIMARY_KEY, None) or [OBJECT_ID_FIELD]
            fks = getattr(self, FOREIGN_KEYS, None) or []
            object_id = []

            if pks == [PRIMARY_PARTITION_KEY]:
                pks = [OBJECT_ID_FIELD]

            for pk in pks:
                if pk in fks:
                    object_id.append(getattr(self, f'{pk}_reference').model_dump())
                else:
                    object_id.append(getattr(self, pk))

            query = build_metadata_query(
                object_id=object_id,
                class_name=self.__class__.__name__,
            )
            query.limit = glue.LimitQuery(limit=1, offset=0)
            result = await AsyncDataApplication().operation_manager.query_lakehouse(query)

            if not result.success:
                msg = f'Failed to retrieve metadata for object_id: {self.object_id}'  # type: ignore[attr-defined]
                raise ValueError(msg) from result.exception

            if not result.data:
                msg = f'No metadata found for object_id: {self.object_id}. Make sure the object was saved.'  # type: ignore[attr-defined]
                raise ValueError(msg) from None

            _metadata = Metadata(**result.data[0].data)

            if isinstance(_metadata.object_id, list) and len(_metadata.object_id) == 1:
                _metadata.object_id = _metadata.object_id[0]

            self._metadata_lazy = LazyObject(
                lambda: _metadata,
            )

        return self._metadata

    def _invalidate_metadata(self) -> None:
        self._metadata_lazy = LazyObject(partial(self.build_metadata, metadata=None))
