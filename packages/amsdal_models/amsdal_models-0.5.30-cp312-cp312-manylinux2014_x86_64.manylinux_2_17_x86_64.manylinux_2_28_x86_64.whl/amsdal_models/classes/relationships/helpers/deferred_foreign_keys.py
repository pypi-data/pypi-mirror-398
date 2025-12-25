from functools import partial
from typing import TYPE_CHECKING
from typing import Any
from typing import ForwardRef
from typing import Optional
from typing import Union

from amsdal_data.connections.historical.data_query_transform import DEFAULT_PKS
from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.models.utils.reference_builders import build_reference
from pydantic import Field
from pydantic.fields import FieldInfo

from amsdal_models.classes.decorators.private_property import PrivateProperty
from amsdal_models.classes.relationships.constants import DEFERRED_FOREIGN_KEYS
from amsdal_models.classes.relationships.constants import FOREIGN_KEYS
from amsdal_models.classes.relationships.constants import PRIMARY_KEY_FIELDS
from amsdal_models.classes.relationships.meta.common import is_forward_ref
from amsdal_models.classes.relationships.meta.common import is_model_subclass
from amsdal_models.classes.relationships.meta.common import resolve_model_type
from amsdal_models.classes.relationships.reference_field import ReferenceFieldInfo

if TYPE_CHECKING:
    from amsdal_models.classes.model import AmsdalModelMetaclass
    from amsdal_models.classes.model import Model


def complete_deferred_foreign_keys(cls: Union[type['Model'], 'AmsdalModelMetaclass']) -> None:
    from amsdal_models.classes.model import LegacyModel
    from amsdal_models.classes.model import Model

    do_rebuild_model = False
    deferred_fks: dict[str, ForwardRef] = getattr(cls, DEFERRED_FOREIGN_KEYS, {})

    if deferred_fks:
        cls.__deferred_foreign_keys__ = {}  # type: ignore[union-attr]

    for fk, deferred_fk_value in deferred_fks.items():
        _field_info = cls.model_fields[fk]  # type: ignore[union-attr]
        _annotation = _field_info.annotation
        fk_type, is_required = resolve_model_type(_annotation)

        if is_forward_ref(fk_type):
            cls.__deferred_foreign_keys__[fk] = deferred_fk_value  # type: ignore[union-attr]
            continue

        if not is_model_subclass(fk_type):  # type: ignore[arg-type]
            continue

        fks = getattr(cls, FOREIGN_KEYS) or []

        if fk not in fks:
            fks.append(fk)
            setattr(cls, FOREIGN_KEYS, fks)

        do_rebuild_model = True
        _field_annotation = Union[Reference, fk_type, LegacyModel]  # type: ignore[valid-type]

        if not is_required:
            _field_annotation = Optional[_field_annotation]  # type: ignore[misc]

        if isinstance(_field_info, ReferenceFieldInfo):
            _field_info = ReferenceFieldInfo.merge_field_infos(
                Field(union_mode='left_to_right'),
                _field_info,
                annotation=_field_annotation,
            )
        else:
            _field_info = FieldInfo.merge_field_infos(
                Field(union_mode='left_to_right'),
                _field_info,
                annotation=_field_annotation,
                default=_field_info.default,
            )
        cls.model_fields[fk] = _field_info  # type: ignore[union-attr]
        db_fields: dict[str, Any] | None = None

        if isinstance(_field_info, ReferenceFieldInfo):
            _db_field = _field_info.db_field(fk, fk_type) if callable(_field_info.db_field) else _field_info.db_field  # type: ignore[arg-type]

            if isinstance(_db_field, str):
                db_fields = {_db_field: fk_type}
            elif _db_field:
                db_fields = dict.fromkeys(_db_field, fk_type)

        if db_fields is None:
            db_fields = {
                f'{fk}_{_pk}': _pk_type
                for _pk, _pk_type in (getattr(fk_type, PRIMARY_KEY_FIELDS, None) or DEFAULT_PKS).items()
            }

        for _index, (_fk_field, _fk_field_type) in enumerate(db_fields.items()):
            _private_field = f'_{_fk_field}'

            def _getter(_field: str, obj: Model) -> Any:
                return getattr(obj, _field)

            def _setter(
                _index: int,
                _fk: str,
                _fk_type: Any,
                _field: str,
                _fk_field: str,
                _fk_field_type: Any,
                obj: Model,
                value: Any,
            ) -> None:
                if not isinstance(value, _fk_field_type):
                    msg = f'The {_fk_field} type must be {_fk_field_type.__name__} but is {type(value)}.'
                    raise ValueError(msg)

                setattr(obj, _field, value)
                ref = getattr(obj, _fk)

                if isinstance(ref, Model) and ref.pk.is_equal_by_index(_index, value):

                    return

                ref_pks = getattr(_fk_type, '__primary_key__', None) or list(DEFAULT_PKS.keys())

                if len(ref_pks) == 1:
                    _object_id = value
                else:
                    _object_id = [value if _idx == _index else None for _idx in range(len(ref_pks))]

                ref_obj = build_reference(
                    class_name=_fk_type.__name__,
                    object_id=_object_id,
                )
                setattr(obj, _fk, ref_obj)

            setattr(
                cls,
                _fk_field,
                PrivateProperty(
                    partial(_getter, _private_field),
                    partial(
                        _setter,
                        _index,
                        fk,
                        fk_type,
                        _private_field,
                        _fk_field,
                        _fk_field_type,
                    ),
                ),
            )

    if do_rebuild_model:
        cls.model_rebuild(force=True)  # type: ignore[union-attr]
