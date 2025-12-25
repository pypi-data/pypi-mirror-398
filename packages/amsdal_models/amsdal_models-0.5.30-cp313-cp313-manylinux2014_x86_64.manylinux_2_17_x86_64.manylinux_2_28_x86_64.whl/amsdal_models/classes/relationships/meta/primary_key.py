from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from typing import ForwardRef

from amsdal_data.connections.constants import PRIMARY_PARTITION_KEY
from amsdal_data.connections.historical.data_query_transform import DEFAULT_PKS
from amsdal_data.connections.historical.data_query_transform import META_PRIMARY_KEY
from amsdal_data.connections.historical.data_query_transform import META_PRIMARY_KEY_FIELDS

from amsdal_models.classes.relationships.constants import ANNOTATIONS
from amsdal_models.classes.relationships.constants import DEFERRED_PRIMARY_KEYS
from amsdal_models.classes.relationships.constants import PRIMARY_KEY
from amsdal_models.classes.relationships.constants import PRIMARY_KEY_FIELDS
from amsdal_models.classes.relationships.meta.common import get_type_for
from amsdal_models.classes.relationships.meta.common import is_model_subclass

if TYPE_CHECKING:
    from amsdal_models.classes.model import Model


def resolve_primary_keys(
    bases: tuple[type[Any], ...],
    namespace: dict[str, Any],
) -> list[str]:
    if PRIMARY_KEY in namespace:
        return namespace[PRIMARY_KEY]

    for base in bases:
        if hasattr(base, PRIMARY_KEY) and getattr(base, PRIMARY_KEY):
            return getattr(base, PRIMARY_KEY)

    return []


def process_primary_keys(
    pks: list[str],
    bases: tuple[type[Any], ...],
    namespace: dict[str, Any],
) -> None:
    pk_fields: dict[str, Any] = {}

    if not pks:
        pk_fields = DEFAULT_PKS.copy()
        namespace[PRIMARY_KEY] = list(DEFAULT_PKS.keys())
    else:
        for pk in pks:
            if pk == PRIMARY_PARTITION_KEY:
                pk_fields[pk] = str
                continue

            field_type = get_type_for(pk, bases, namespace)

            if (
                isinstance(field_type, str)
                or isinstance(field_type, ForwardRef)
                or getattr(field_type, DEFERRED_PRIMARY_KEYS, None)
            ):
                _deferred_pks = namespace.setdefault(DEFERRED_PRIMARY_KEYS, {})
                _deferred_pks[pk] = ForwardRef(field_type) if isinstance(field_type, str) else field_type
                pk_fields[pk] = ForwardRef(field_type) if isinstance(field_type, str) else field_type
                continue

            if is_model_subclass(field_type):
                pk_fields.update(_build_pk_fields(field_type, prefix=pk))
            elif field_type in (list, dict):
                msg = 'Primary Key cannot be list or dict typed'
                raise RuntimeError(msg)
            else:
                pk_fields[pk] = field_type

    _annotations = namespace.setdefault(ANNOTATIONS, {})
    _annotations[PRIMARY_KEY_FIELDS] = ClassVar[dict[str, type]]
    namespace[PRIMARY_KEY_FIELDS] = pk_fields


def _build_pk_fields(model: type['Model'], prefix: str = '') -> dict[str, Any]:
    fields: dict[str, Any] = {}
    _pk_fields = getattr(model, PRIMARY_KEY_FIELDS)

    for _field, _field_type in _pk_fields.items():
        if is_model_subclass(_field_type):
            fields.update(_build_pk_fields(_field_type, prefix=f'{prefix}_{_field}'))
        else:
            fields[f'{prefix}_{_field}'] = _field_type
    return fields


def build_metadata_primary_key(model: type['Model']) -> dict[str, Any]:
    return {
        META_PRIMARY_KEY: getattr(model, PRIMARY_KEY, None) or [PRIMARY_PARTITION_KEY],
        META_PRIMARY_KEY_FIELDS: getattr(model, PRIMARY_KEY_FIELDS, None) or DEFAULT_PKS,
    }
