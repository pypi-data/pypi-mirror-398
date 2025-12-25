from functools import partial
from types import NoneType
from types import UnionType
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from typing import ForwardRef
from typing import Optional
from typing import Union
from typing import get_args
from typing import get_origin

from amsdal_data.connections.historical.data_query_transform import DEFAULT_PKS
from amsdal_data.connections.historical.data_query_transform import META_FOREIGN_KEYS
from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.models.utils.reference_builders import build_reference
from pydantic import Field
from pydantic.fields import FieldInfo

from amsdal_models.classes.decorators.private_property import PrivateProperty
from amsdal_models.classes.relationships.constants import ANNOTATIONS
from amsdal_models.classes.relationships.constants import DEFERRED_FOREIGN_KEYS
from amsdal_models.classes.relationships.constants import DEFERRED_PRIMARY_KEYS
from amsdal_models.classes.relationships.constants import FOREIGN_KEYS
from amsdal_models.classes.relationships.constants import PRIMARY_KEY_FIELDS
from amsdal_models.classes.relationships.helpers.deferred_primary_keys import complete_deferred_primary_keys
from amsdal_models.classes.relationships.meta.common import is_forward_ref_or_model
from amsdal_models.classes.relationships.meta.common import is_model_subclass
from amsdal_models.classes.relationships.meta.common import resolve_model_type
from amsdal_models.classes.relationships.reference_field import ReferenceFieldInfo

if TYPE_CHECKING:
    from amsdal_models.classes.model import Model


def extract_references(
    base_field_names: set[str],
    bases: tuple[type[Any], ...],
    namespace: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    from amsdal_models.classes.model import Model

    annotations = namespace.get(ANNOTATIONS, {})
    fk_references = {}
    many_to_may_references = {}
    items = list(annotations.items())

    for prop, annotation in items:
        target_for_child = annotation
        origin = get_origin(annotation)

        if origin:
            if origin is ClassVar:
                continue

            if origin is Union or origin is UnionType:
                _args = [_arg for _arg in get_args(annotation) if _arg is not NoneType]

                if len(_args) != 1:
                    continue

                origin = get_origin(_args[0])
                target_for_child = _args[0]

            if origin is list:
                (child,) = get_args(target_for_child)

                if is_forward_ref_or_model(child):
                    _value = namespace.get(prop, annotation)

                    if _value is None:
                        _value = FieldInfo(default=None)

                    if isinstance(_value, FieldInfo) and not _value.annotation:
                        _value.annotation = annotation

                    many_to_may_references[prop] = _value

                    if has_m2m_in_bases(prop, bases) or is_model_subclass(child):
                        annotations.pop(prop, None)

                        if is_model_subclass(child):
                            namespace.pop(prop, None)

                continue

        if is_forward_ref_or_model(target_for_child):
            _value = namespace.get(prop, annotation)

            if _value is None or _value is Ellipsis:
                _value = annotation
            elif isinstance(_value, FieldInfo) and not _value.annotation:
                _value.annotation = annotation

            fk_references[prop] = _value

            if is_model_subclass(target_for_child):
                annotations.pop(prop, None)
                namespace.pop(prop, None)

            continue

    for base_field_name in base_field_names:
        if base_field_name in namespace or base_field_name in namespace.get(ANNOTATIONS, {}):
            continue

        for base in bases:
            if issubclass(base, Model) and base is not Model:
                if base_field_name in base.model_fields:
                    _fks, _many2many = extract_references(
                        set(),
                        (),
                        {
                            ANNOTATIONS: {
                                field_name: field.annotation for field_name, field in base.model_fields.items()
                            },
                            **base.model_fields,
                        },
                    )

                    if base_field_name in _fks:
                        fk_references[base_field_name] = _fks[base_field_name]
                    elif base_field_name in _many2many:
                        many_to_may_references[base_field_name] = _many2many[base_field_name]

                    break

    return fk_references, many_to_may_references


def generate_fk_properties(fk: str, annotation: Any, namespace: dict[str, Any]) -> None:
    from amsdal_models.classes.model import LegacyModel

    _field_info = namespace.get(fk)

    if not isinstance(_field_info, FieldInfo):
        _field_info = annotation
    elif not _field_info.annotation:
        _field_info.annotation = annotation

    fk_type, db_fields, is_required = build_fk_db_fields(fk, _field_info)

    if isinstance(fk_type, ForwardRef):
        namespace.setdefault(DEFERRED_FOREIGN_KEYS, {})[fk] = fk_type
        return

    if not is_model_subclass(fk_type):
        return

    fks = namespace.get(FOREIGN_KEYS) or []

    if fk not in fks:
        fks.append(fk)
        namespace[FOREIGN_KEYS] = fks

    namespace[ANNOTATIONS][fk] = Union[Reference, fk_type, LegacyModel]
    _default = ...

    if not is_required:
        _default = None  # type: ignore[assignment]
        namespace[ANNOTATIONS][fk] = Optional[namespace[ANNOTATIONS][fk]]

    if fk not in namespace:
        namespace[fk] = Field(default=_default, union_mode='left_to_right')
        if isinstance(annotation, FieldInfo):
            namespace[fk] = namespace[fk].merge_field_infos(annotation)
    elif isinstance(namespace[fk], ReferenceFieldInfo):
        namespace[fk] = ReferenceFieldInfo.merge_field_infos(
            Field(union_mode='left_to_right'),
            namespace[fk],
            default=_default,
        )
    elif isinstance(namespace[fk], FieldInfo):
        namespace[fk] = FieldInfo.merge_field_infos(
            Field(union_mode='left_to_right'),
            namespace[fk],
        )
    else:
        namespace[fk] = Field(default=namespace[fk], union_mode='left_to_right')

    if db_fields:
        generate_dynamic_reference(fk, fk_type, db_fields, namespace, is_required=is_required)


def build_fk_db_fields(fk: str, annotation: Any) -> tuple[type['Model'] | ForwardRef, dict[str, type[Any]], bool]:
    if isinstance(annotation, ReferenceFieldInfo) or isinstance(annotation, FieldInfo):
        fk_type, is_required = resolve_model_type(annotation.annotation)
    else:
        fk_type, is_required = resolve_model_type(annotation)

    if isinstance(fk_type, str) or isinstance(fk_type, ForwardRef):
        return ForwardRef(fk_type) if isinstance(fk_type, str) else fk_type, {}, is_required

    if isinstance(annotation, ReferenceFieldInfo):
        _db_fields = annotation.db_field(fk, fk_type) if callable(annotation.db_field) else annotation.db_field
        fk_pks = getattr(fk_type, PRIMARY_KEY_FIELDS, {})

        if not fk_pks:
            msg = 'Foreign Key to model without PK is not allowed!'
            raise RuntimeError(msg)

        if isinstance(_db_fields, str):
            if len(fk_pks.keys()) > 1:
                msg = f'The "db_field" should be a list of fields due to compound PK for referenced model "{fk_type}"!'
                raise RuntimeError(msg)

            db_fields = {_db_fields: fk_pks[next(iter(fk_pks.keys()))]}
        else:
            if len(fk_pks.keys()) != len(list(_db_fields)):
                msg = (
                    'The number of "db_field" items are not equal '
                    f'to exact number of Primary Keys for referenced model "{fk_type}"!'
                )
                raise RuntimeError(msg)

            db_fields = dict(zip(_db_fields, fk_pks.values(), strict=False))
    else:
        if getattr(fk_type, DEFERRED_PRIMARY_KEYS, False):
            complete_deferred_primary_keys(fk_type)

        pks = getattr(fk_type, PRIMARY_KEY_FIELDS, None) or DEFAULT_PKS
        db_fields = {f'{fk}_{_pk}': _pk_type for _pk, _pk_type in pks.items()}

    return fk_type, db_fields, is_required


def generate_dynamic_reference(
    fk: str,
    fk_type: type['Model'],
    db_fields: dict[str, type],
    namespace: dict[str, Any],
    *,
    is_required: bool = True,
) -> None:
    from amsdal_models.classes.model import Model

    for _index, (_fk_field, _fk_type) in enumerate(db_fields.items()):
        _private_field = f'_{_fk_field}'
        _type = _fk_type if is_required else Optional[_fk_type]
        namespace[ANNOTATIONS][_private_field] = _type

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
            _internal_index = _index
            _internal_fk_type = _fk_field_type
            _internal_fk_field = _fk_field

            if not isinstance(value, _internal_fk_type):
                msg = f'The {_internal_fk_field} type must be {_internal_fk_type.__name__} but is {type(value)}.'
                raise ValueError(msg)

            setattr(obj, _field, value)
            ref = getattr(obj, _fk)

            if isinstance(ref, Model) and ref.pk.is_equal_by_index(_internal_index, value):
                return

            if isinstance(_fk_type, str):
                _fk_type, _ = resolve_model_type(obj.__class__.model_fields[_fk].annotation)

            ref_pks = _fk_type.__primary_key__ or list(DEFAULT_PKS.keys())

            if len(ref_pks) == 1:
                _object_id = value
            else:
                _object_id = [value if _idx == _internal_index else None for _idx in range(len(ref_pks))]

            ref_obj = build_reference(
                class_name=_fk_type.__name__,
                object_id=_object_id,
            )
            setattr(obj, _fk, ref_obj)

        namespace[_fk_field] = PrivateProperty(
            partial(_getter, _private_field),
            partial(
                _setter,
                _index,
                fk,
                fk_type,
                _private_field,
                _fk_field,
                _fk_type,
            ),
        )


def build_metadata_foreign_keys(obj: 'Model') -> dict[str, Any]:
    from amsdal_models.schemas.object_schema import get_model_foreign_keys

    foreign_keys_meta = {}
    _fks = get_model_foreign_keys(obj.__class__)

    for _fk, (_db_fields, _, _) in _fks.items():
        _fk_ref = getattr(obj, f'{_fk}_reference')
        foreign_keys_meta[_fk] = (
            _fk_ref,
            list(_db_fields.keys()),
        )

    return {
        META_FOREIGN_KEYS: foreign_keys_meta,
    }


def has_m2m_in_bases(
    field_name: str,
    bases: tuple[type[Any], ...],
) -> bool:
    from amsdal_models.classes.model import Model

    for base in bases:
        if issubclass(base, Model) and base is not Model:
            if field_name in base.model_computed_fields:
                return True

    return False
