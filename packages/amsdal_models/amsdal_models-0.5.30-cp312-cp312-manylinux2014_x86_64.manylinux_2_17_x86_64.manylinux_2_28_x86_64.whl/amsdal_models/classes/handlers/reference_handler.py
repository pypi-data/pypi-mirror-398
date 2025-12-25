import asyncio
import json
from datetime import date
from datetime import datetime
from enum import Enum
from inspect import iscoroutine
from typing import Any
from typing import Literal

import typing_extensions
from amsdal_utils.config.manager import AmsdalConfigManager
from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.models.enums import Versions
from amsdal_utils.models.utils.reference_builders import build_reference
from pydantic import model_serializer
from pydantic_core.core_schema import SerializationInfo
from pydantic_core.core_schema import SerializerFunctionWrapHandler

from amsdal_models.classes.handlers.object_id_handler import ObjectIdHandler
from amsdal_models.classes.relationships.constants import FOREIGN_KEYS
from amsdal_models.classes.relationships.constants import MANY_TO_MANY_FIELDS
from amsdal_models.classes.utils import object_id_to_internal
from amsdal_models.errors import AmsdalTypeError

# should be `set[int] | set[str] | dict[int, IncEx] | dict[str, IncEx] | None`, but mypy can't cope
IncEx: typing_extensions.TypeAlias = 'set[int] | set[str] | dict[int, Any] | dict[str, Any] | None'

SERIALIZE_WITH_REFS_FLAG = 'serialize_with_refs'
EXCLUDE_M2M_FIELDS_FLAG = 'exclude_m2m_fields'
STACK_CONTEXT_FLAG = 'stack_context'


def _serialize_type_model_field_value(
    field_value: Any,
    field_name: str,
) -> Any:
    if isinstance(field_value, datetime) or isinstance(field_value, date):
        return field_value.isoformat()

    if isinstance(field_value, Enum):
        return field_value.value

    if isinstance(field_value, bytes):
        return field_value.decode('utf-8')

    try:
        json.dumps(field_value)
    except TypeError as e:
        msg = f'{field_name} field value is not JSON serializable: {field_value}'
        raise AmsdalTypeError(msg) from e

    return field_value


class ReferenceHandler(ObjectIdHandler):
    def build_reference(self, *, is_frozen: bool = False) -> Reference:
        """
        Reference of the object/record. It's always referenced to latest object version.

        Returns:
            Reference: The reference of the object/record.
        """
        from amsdal_utils.config.manager import AmsdalConfigManager

        if not is_frozen:
            return build_reference(
                resource=AmsdalConfigManager().get_connection_name_by_model_name(
                    self.__class__.__name__,
                ),
                class_name=self.__class__.__name__,
                class_version=Versions.LATEST,
                object_id=object_id_to_internal([item.value for item in self.pk.items]),
                object_version=Versions.LATEST,
            )

        metadata = self.get_metadata()
        reference_address = metadata.address

        if reference_address.object_version == Versions.LATEST:
            msg = (
                'Cannot freeze the latest version of the object. Make sure you have saved the object first and '
                'you are using lakehouse connection.'
            )
            raise ValueError(msg)

        return build_reference(
            resource=reference_address.resource,
            class_name=reference_address.class_name,
            object_id=object_id_to_internal(reference_address.object_id),
            class_version=reference_address.class_version,
            object_version=reference_address.object_version,
        )

    async def abuild_reference(self, *, is_frozen: bool = False) -> Reference:
        """
        Reference of the object/record. It's always referenced to latest object version.

        Returns:
            Reference: The reference of the object/record.
        """
        from amsdal_utils.config.manager import AmsdalConfigManager

        if not is_frozen:
            return build_reference(
                resource=AmsdalConfigManager().get_connection_name_by_model_name(
                    self.__class__.__name__,
                ),
                class_name=self.__class__.__name__,
                class_version=Versions.LATEST,
                object_id=object_id_to_internal([item.value for item in self.pk.items]),
                object_version=Versions.LATEST,
            )

        metadata = await self.aget_metadata()
        reference_address = metadata.address

        if reference_address.object_version == Versions.LATEST:
            msg = (
                'Cannot freeze the latest version of the object. Make sure you have saved the object first and '
                'you are using lakehouse connection.'
            )
            raise ValueError(msg)

        return build_reference(
            resource=reference_address.resource,
            class_name=reference_address.class_name,
            object_id=object_id_to_internal(reference_address.object_id),
            class_version=reference_address.class_version,
            object_version=reference_address.object_version,
        )

    @model_serializer(mode='wrap')
    def ser_model(self, nxt: SerializerFunctionWrapHandler, info: SerializationInfo) -> dict[str, Any]:
        """
        Serializes the model.

        Returns:
            dict[str, Any]: The serialized model as a dictionary.
        """
        from amsdal_models.classes.helpers.reference_loader import ReferenceLoader
        from amsdal_models.classes.model import Model
        from amsdal_models.classes.model import TypeModel

        if not isinstance(self, Model):
            return nxt(self)

        _context = info.context or {}
        _is_serializing_with_refs = (
            _context.get(SERIALIZE_WITH_REFS_FLAG, False) or AmsdalConfigManager().get_config().async_mode
        )
        _stack_context = _context.setdefault(STACK_CONTEXT_FLAG, {})

        obj_id = id(self)
        obj_hash = hash(self)

        if obj_id in _stack_context:
            data = _stack_context[obj_id][1]
        elif obj_hash in _stack_context:
            data = _stack_context[obj_hash][1]
        else:
            data: dict[str, Any] = {}  # type: ignore[no-redef]

        _stack_context[id(self)] = (self, data)
        _stack_context[hash(self)] = (self, data)

        def _serialize_value(_value: Any) -> Any:
            value_id = id(_value)

            if value_id in _stack_context:
                return _stack_context[value_id][1]

            try:
                value_hash = hash(_value)
            except TypeError:
                value_hash = None
            else:
                if value_hash in _stack_context:
                    return _stack_context[value_hash][1]

            if isinstance(_value, Reference):
                if _is_serializing_with_refs:
                    return _value.model_dump(exclude_none=info.exclude_none)

                _obj = ReferenceLoader(_value).load_reference()
                return _serialize_value(_obj)

            if isinstance(_value, Enum):
                return _value.value

            if isinstance(_value, TypeModel) and not isinstance(_value, Model):
                _data = _value.model_dump(exclude_none=info.exclude_none, context=_context)
                _data = {
                    field_name: _serialize_type_model_field_value(field_value, field_name)
                    for field_name, field_value in _data.items()
                }
                _stack_context[value_id] = _value, _data

                if value_hash is not None:
                    _stack_context[value_hash] = _value, _data

                return _data

            if isinstance(_value, Model):
                if _is_serializing_with_refs:
                    _data = _value.build_reference().model_dump(exclude_none=info.exclude_none, context=_context)
                else:
                    _data = {}

                    _stack_context[value_id] = _value, _data
                    _stack_context[value_hash] = _value, _data
                    _value.model_dump(exclude_none=info.exclude_none, context=_context)

                return _data
            return _value

        fks = getattr(self.__class__, FOREIGN_KEYS, None) or []
        m2m_fields = getattr(self.__class__, MANY_TO_MANY_FIELDS, None) or {}

        for field_name in self.__class__.model_fields:
            if field_name in fks:
                if _is_serializing_with_refs:
                    data[field_name] = getattr(self, f'{field_name}_reference')
                    continue

            value = getattr(self, field_name)

            if isinstance(value, list):
                data[field_name] = [_serialize_value(item) for item in value]

                if all(isinstance(item, bytes) for item in value):
                    data[field_name] = [item.decode('utf-8') for item in value]

                if all(isinstance(item, date) for item in value) or all(isinstance(item, datetime) for item in value):
                    data[field_name] = [item.isoformat() for item in value]

            elif isinstance(value, dict):
                data[field_name] = {key: _serialize_value(item) for key, item in value.items()}
            elif value is None:
                if not info.exclude_none:
                    data[field_name] = None
            else:
                data[field_name] = _serialize_value(value)

        if self.__pydantic_extra__:
            for field_name, value in self.__pydantic_extra__.items():
                data[field_name] = value

        if _context.get(EXCLUDE_M2M_FIELDS_FLAG, False):
            return data

        for m2m in m2m_fields:
            if _is_serializing_with_refs:
                data[m2m] = getattr(self, f'{m2m}_references')
            else:
                data[m2m] = [_serialize_value(item) for item in getattr(self, m2m)]
        return data

    def model_dump_refs(
        self,
        *,
        mode: Literal['json', 'python'] | str = 'python',
        include: IncEx = None,
        exclude: IncEx = None,
        by_alias: bool = False,
        context: Any | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
        serialize_as_any: bool = False,
    ) -> dict[str, Any]:
        """
        Dumps the model with references.

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
            dict[str, Any]: The serialized model as a dictionary.
        """
        context = context or {}
        context[SERIALIZE_WITH_REFS_FLAG] = True

        return super(ObjectIdHandler, self).model_dump(
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

    async def amodel_dump_refs(self, **kwargs) -> dict[str, Any]:  # type: ignore[no-untyped-def]
        return {
            key: await value if asyncio.iscoroutine(value) else value
            for key, value in self.model_dump_refs(**kwargs).items()
        }

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
        Dumps the model.

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
            dict[str, Any]: The serialized model as a dictionary.
        """
        return super(ObjectIdHandler, self).model_dump(
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

    async def amodel_dump(
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
        data = self.model_dump(
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

        return await self._async_model_dump(data)

    @classmethod
    async def _async_model_dump(cls, obj: Any) -> Any:
        from amsdal_utils.models.data_models.reference import Reference

        if isinstance(obj, Reference):
            return await cls._async_model_dump((await obj).model_dump())

        if isinstance(obj, ReferenceHandler):
            return await cls._async_model_dump(obj.model_dump())

        if isinstance(obj, list):
            return [await cls._async_model_dump(item) for item in obj]

        if isinstance(obj, dict):
            data = {}
            for key, value in obj.items():
                if iscoroutine(value):
                    data[key] = await cls._async_model_dump(await value)
                else:
                    data[key] = await cls._async_model_dump(value)
            return data

        return obj

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
        Dumps the model as a JSON string with references.

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
            str: The serialized model as a JSON string.
        """
        context = context or {}
        context[SERIALIZE_WITH_REFS_FLAG] = True

        return super(ObjectIdHandler, self).model_dump_json(
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
        Dumps the model as a JSON string.

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
            str: The serialized model as a JSON string.
        """
        context = context or {}
        context[SERIALIZE_WITH_REFS_FLAG] = True

        return super(ObjectIdHandler, self).model_dump_json(
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
