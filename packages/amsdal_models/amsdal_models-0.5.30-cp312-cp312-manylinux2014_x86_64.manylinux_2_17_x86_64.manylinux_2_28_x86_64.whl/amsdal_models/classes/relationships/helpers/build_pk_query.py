from collections.abc import Iterable
from typing import TYPE_CHECKING

import amsdal_glue as glue
from amsdal_data.connections.historical.data_query_transform import DEFAULT_PKS

from amsdal_models.classes.relationships.constants import PRIMARY_KEY_FIELDS

if TYPE_CHECKING:
    from amsdal_models.classes.model import Model


def build_pk_query(table_name: str, obj: 'Model') -> glue.Conditions:
    pks = getattr(obj.__class__, PRIMARY_KEY_FIELDS, None) or DEFAULT_PKS
    object_id = obj.object_id

    if isinstance(object_id, str) or not isinstance(object_id, Iterable):
        object_id = [object_id]

    return glue.Conditions(
        *[
            glue.Condition(
                left=glue.FieldReferenceExpression(
                    field_reference=glue.FieldReference(
                        field=glue.Field(name=_pk),
                        table_name=table_name,
                    ),
                ),
                lookup=glue.FieldLookup.EQ,
                right=glue.Value(value=_object_id),
            )
            for _pk, _object_id in zip(pks, object_id, strict=False)
        ]
    )
