from copy import deepcopy
from typing import TYPE_CHECKING
from typing import ForwardRef
from typing import Union

from amsdal_models.classes.relationships.constants import DEFERRED_PRIMARY_KEYS
from amsdal_models.classes.relationships.constants import PRIMARY_KEY_FIELDS
from amsdal_models.classes.relationships.meta.common import is_forward_ref
from amsdal_models.classes.relationships.meta.common import resolve_model_type

if TYPE_CHECKING:
    from amsdal_models.classes.model import AmsdalModelMetaclass
    from amsdal_models.classes.model import Model


def complete_deferred_primary_keys(cls: Union[type['Model'], 'AmsdalModelMetaclass']) -> None:
    from amsdal_models.classes.relationships.meta.references import build_fk_db_fields

    deferred_pks: dict[str, ForwardRef] = getattr(cls, DEFERRED_PRIMARY_KEYS, {})

    if deferred_pks:
        cls.__deferred_primary_keys__ = {}  # type: ignore[union-attr]

        for pk, deferred_pk in deferred_pks.items():
            _field_info = cls.model_fields[pk]  # type: ignore[union-attr]
            _annotation = _field_info.annotation
            pk_type, _ = resolve_model_type(_annotation)

            if is_forward_ref(pk_type):
                cls.__deferred_primary_keys__[pk] = deferred_pk  # type: ignore[union-attr]
                continue

            _, _fk_fields, _ = build_fk_db_fields(pk, _field_info)
            _new_pks = {}
            pks = deepcopy(getattr(cls, PRIMARY_KEY_FIELDS, None) or {})

            for _pk_field in pks:
                if _pk_field == pk:
                    _new_pks.update(_fk_fields)
                else:
                    _new_pks[_pk_field] = pks[_pk_field]
            setattr(cls, PRIMARY_KEY_FIELDS, _new_pks)

        cls.model_rebuild(force=True)  # type: ignore[union-attr]
