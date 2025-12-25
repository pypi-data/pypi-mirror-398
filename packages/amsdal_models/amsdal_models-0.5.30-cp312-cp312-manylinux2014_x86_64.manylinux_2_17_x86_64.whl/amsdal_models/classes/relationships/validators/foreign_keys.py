from collections.abc import Iterable
from typing import Any
from typing import Self

from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.models.utils.reference_builders import build_reference
from pydantic.functional_validators import ModelWrapValidatorHandler

from amsdal_models.classes.relationships.constants import FOREIGN_KEYS
from amsdal_models.classes.relationships.meta.references import build_fk_db_fields


def model_foreign_keys_validator(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:  # type: ignore[no-untyped-def,misc]
    from amsdal_models.classes.model import Model
    from amsdal_models.classes.model import TypeModel

    fks = getattr(cls, FOREIGN_KEYS, [])

    if isinstance(data, dict):
        for fk in fks:
            if fk in data:
                continue

            field_info = cls.model_fields[fk]
            fk_type, db_fields, _ = build_fk_db_fields(fk, field_info)

            object_id = [data.get(_db_field, None) for _db_field in db_fields]

            if not bool(list(filter(None, object_id))):
                continue

            ref_obj = build_reference(
                class_name=fk_type.__name__,  # type: ignore[union-attr]
                object_id=object_id,
            )

            data[fk] = ref_obj

    instance = handler(data)

    for fk in fks:
        if not hasattr(instance, f'{fk}_reference'):
            # TODO: should we have it? it happens when reference was set but it cannot get it from DB...
            continue

        field_info = cls.model_fields[fk]
        fk_annotation = cls.model_fields[fk].annotation
        fk_type, db_fields, _ = build_fk_db_fields(fk, field_info)

        try:
            if issubclass(fk_annotation, TypeModel) and not issubclass(fk_annotation, Model):
                return instance
        except TypeError:
            ...

        value = getattr(instance, f'{fk}_reference')

        if value is None:
            for db_field in db_fields:
                setattr(instance, f'_{db_field}', None)
            return instance

        if isinstance(value, Reference):
            _class_name = value.ref.class_name

            if _class_name != fk_type.__name__:  # type: ignore[union-attr]
                msg = f'Reference should be of type {fk_type}, not {_class_name}'
                raise ValueError(msg)

            _object_id = value.ref.object_id

            if not isinstance(_object_id, Iterable) or isinstance(_object_id, str):
                _object_id = [_object_id]

            for db_field, _value in zip(db_fields, _object_id, strict=False):
                if getattr(instance, f'_{db_field}', None) != _value:
                    setattr(instance, f'_{db_field}', _value)

    return instance
