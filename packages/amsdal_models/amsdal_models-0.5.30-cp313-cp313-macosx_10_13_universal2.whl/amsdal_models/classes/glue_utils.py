from typing import TYPE_CHECKING

import amsdal_glue as glue
from amsdal_data.connections.historical.data_query_transform import DEFAULT_PKS
from amsdal_data.connections.historical.data_query_transform import META_FOREIGN_KEYS
from amsdal_data.connections.historical.data_query_transform import META_PRIMARY_KEY_FIELDS
from amsdal_glue_core.common.data_models.vector import Vector

from amsdal_models.classes.handlers.reference_handler import EXCLUDE_M2M_FIELDS_FLAG
from amsdal_models.classes.relationships.constants import PRIMARY_KEY_FIELDS

if TYPE_CHECKING:
    from amsdal_models.classes.model import Model


def model_to_data(obj: 'Model', *, exclude_m2m: bool = True) -> glue.Data:
    """
    Convert a model object to a data dictionary.

    Args:
        obj (Model): The model object to convert.
        exclude_m2m (bool, optional): Whether to exclude many-to-many fields. Defaults to True.

    Returns:
        amsdal_glue.Data: The data.
    """
    from amsdal_models.schemas.object_schema import get_model_foreign_keys

    _class = obj.__class__
    primary_key_meta = getattr(obj.__class__, PRIMARY_KEY_FIELDS, {}) or DEFAULT_PKS
    data_dump = obj.model_dump_refs(by_alias=False, context={EXCLUDE_M2M_FIELDS_FLAG: exclude_m2m})

    _object_id = [_item.value for _item in obj.pk.items]

    for _pk_field, _val in zip(primary_key_meta, _object_id, strict=False):
        data_dump[_pk_field] = _val

    _fks = get_model_foreign_keys(obj.__class__)
    foreign_keys_meta = {}

    for _fk, (_db_fields, _, _) in _fks.items():
        _fk_ref = getattr(obj, f'{_fk}_reference')
        foreign_keys_meta[_fk] = (
            _fk_ref,
            list(_db_fields.keys()),
        )
        _ref = data_dump.pop(_fk, None)

        if not _ref:
            for _db_field in _db_fields:
                data_dump[_db_field] = None
            continue

        _object_ids = _fk_ref.ref.object_id
        if not isinstance(_object_ids, list):
            _object_ids = [_object_ids]

        for _index, _db_field in enumerate(_db_fields.keys()):
            data_dump[_db_field] = _object_ids[_index]

    for key, value in list(data_dump.items()):
        if (
            isinstance(value, list)
            and key in _class.model_fields
            and (prop := _class.model_fields[key]).json_schema_extra
            and prop.json_schema_extra.get('additional_type') == 'vector'  # type: ignore
        ):
            data_dump[key] = Vector(values=value)

    return glue.Data(
        data=data_dump,
        metadata={
            META_PRIMARY_KEY_FIELDS: primary_key_meta,
            META_FOREIGN_KEYS: foreign_keys_meta,
        },
    )
