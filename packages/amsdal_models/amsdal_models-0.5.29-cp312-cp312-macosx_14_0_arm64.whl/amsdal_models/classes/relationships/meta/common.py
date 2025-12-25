from contextlib import suppress
from types import GenericAlias
from types import NoneType
from types import UnionType
from typing import TYPE_CHECKING
from typing import Any
from typing import ForwardRef
from typing import Optional
from typing import Union
from typing import get_args
from typing import get_origin

from amsdal_utils.models.data_models.reference import Reference
from pydantic.fields import FieldInfo

from amsdal_models.classes.relationships.constants import ANNOTATIONS
from amsdal_models.classes.relationships.constants import PRIMARY_KEY_FIELDS
from amsdal_models.classes.relationships.reference_field import ReferenceFieldInfo

if TYPE_CHECKING:
    from amsdal_models.classes.model import Model


def get_type_for(
    prop: str,
    bases: tuple[type[Any], ...],
    namespace: dict[str, Any],
) -> type | str | ForwardRef:
    if prop in namespace[ANNOTATIONS]:
        return namespace[ANNOTATIONS][prop]

    if prop in namespace:
        prop_info: FieldInfo = namespace[prop]
        if prop_info.annotation:
            return prop_info.annotation

    for field, value in namespace.items():
        if isinstance(value, ReferenceFieldInfo):
            _db_fields = [value.db_field] if isinstance(value.db_field, str) else value.db_field

            if _db_fields and prop in _db_fields:  # type: ignore[operator]
                return get_type_for(field, bases, namespace)

    for base in bases:
        if prop in (getattr(base, PRIMARY_KEY_FIELDS, None) or {}):
            return getattr(base, PRIMARY_KEY_FIELDS)[prop]

    msg = f'Missing type annotation for field "{prop}"!'
    raise RuntimeError(msg)


def is_model_subclass(field_type: type) -> bool:
    from amsdal_models.classes.model import Model

    _is_model_subclass = False

    with suppress(TypeError):
        _is_model_subclass = issubclass(field_type, Model)

    return _is_model_subclass


def is_forward_ref(target: Any) -> bool:
    _is_forward_ref_instance = False
    _is_forward_ref_str = False

    with suppress(TypeError):
        _is_forward_ref_instance = isinstance(target, ForwardRef)

    with suppress(TypeError):
        _is_forward_ref_str = isinstance(target, str)

    return _is_forward_ref_instance or _is_forward_ref_str


def is_forward_ref_or_model(target: Any) -> bool:
    return is_forward_ref(target) or is_model_subclass(target)


def resolve_model_type(annotation: Any) -> tuple[type['Model'] | ForwardRef | str, bool]:
    """
    Resolves a model type annotation, returning a tuple of the resolved model type and a boolean
    indicating whether it is it required.

    Arguments:
        annotation (Any): the model's field type annotation
    """
    from amsdal_models.classes.model import LegacyModel

    if isinstance(annotation, str):
        return annotation, True

    _origin = get_origin(annotation)
    is_required = True

    if _origin is Union or _origin is UnionType:
        is_required = False
        _args = [_arg for _arg in get_args(annotation) if _arg not in (NoneType, Reference, LegacyModel)]
        (annotation,) = _args

        if isinstance(annotation, GenericAlias):
            _origin = get_origin(annotation)

    if _origin is list:
        return resolve_model_type(get_args(annotation)[0])
    else:
        _model = annotation

    if isinstance(_model, str):
        _model = ForwardRef(_model)

    return _model, is_required


def convert_models_in_dict_to_references(namespace: dict[str, Any]) -> None:
    annotations = namespace.get(ANNOTATIONS, {})

    for field, annotation in annotations.items():
        # process only dict annotations, list are handled as m2m, direct types - as a FK
        _origin = get_origin(annotation)

        if _origin in {Union, Optional, UnionType} or isinstance(_origin, UnionType):
            _args = []

            for _arg in get_args(annotation):
                _arg_origin = get_origin(_arg)

                if _arg_origin is dict:
                    _args.append(process_model_annotation(_arg))
                    continue

                _args.append(_arg)

            annotations[field] = Union[tuple(_args)]
            continue

        if _origin is not dict:
            continue

        annotations[field] = process_model_annotation(annotation)


def process_model_annotation(_annotation: Any) -> Any:
    from amsdal_models.classes.model import LegacyModel
    from amsdal_models.classes.model import Model

    _origin = get_origin(_annotation)

    if _origin is dict:
        key_type, value_type = get_args(_annotation)
        return dict[process_model_annotation(key_type), process_model_annotation(value_type)]  # type: ignore[misc]

    if _origin is tuple:
        # we are not supporting tuple with models
        return _annotation

    if _origin in {Union, Optional, UnionType} or isinstance(_origin, UnionType):
        return Union[tuple([process_model_annotation(_arg) for _arg in get_args(_annotation)])]

    if isinstance(_annotation, type):
        try:
            if issubclass(_annotation, Model):
                return Union[Reference, _annotation, LegacyModel]
        except TypeError:
            ...

    if isinstance(_annotation, str) or isinstance(_annotation, ForwardRef):
        return Union[Reference, _annotation, LegacyModel]

    return _annotation
