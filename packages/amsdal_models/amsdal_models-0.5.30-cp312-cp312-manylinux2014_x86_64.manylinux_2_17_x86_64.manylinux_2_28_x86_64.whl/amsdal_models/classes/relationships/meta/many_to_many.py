from collections.abc import Callable
from collections.abc import Coroutine
from contextlib import suppress
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from typing import ForwardRef
from typing import TypeVar
from typing import Union
from typing import get_args
from typing import get_origin

from amsdal_utils.config.manager import AmsdalConfigManager
from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.models.enums import ModuleType
from pydantic import TypeAdapter
from pydantic import ValidationError
from pydantic import create_model
from pydantic.fields import FieldInfo

from amsdal_models.classes.decorators.private_property import PrivateProperty
from amsdal_models.classes.relationships.constants import ANNOTATIONS
from amsdal_models.classes.relationships.constants import DEFERRED_M2M_FIELDS
from amsdal_models.classes.relationships.constants import MANY_TO_MANY_FIELDS
from amsdal_models.classes.relationships.many_reference_field import ManyList
from amsdal_models.classes.relationships.many_reference_field import ManyReferenceFieldInfo
from amsdal_models.classes.relationships.meta.common import is_forward_ref
from amsdal_models.classes.relationships.meta.common import resolve_model_type
from amsdal_models.errors import AmsdalModelError
from amsdal_models.managers.base_manager import BaseManager
from amsdal_models.querysets.executor import DEFAULT_DB_ALIAS
from amsdal_models.querysets.executor import LAKEHOUSE_DB_ALIAS

if TYPE_CHECKING:
    from amsdal_models.classes.model import AmsdalModelMetaclass
    from amsdal_models.classes.model import Model

ClassTypeT = TypeVar('ClassTypeT', bound=type['Model'])


def generate_m2m_properties(
    m2m: str,
    annotation: Any,
    namespace: dict[str, Any],
) -> None:
    m2m_ref, m2m_model, through_fields, field_info = resolve_m2m_ref(annotation)

    if is_forward_ref(m2m_ref):  # or namespace.get(DEFERRED_PRIMARY_KEYS):
        # deferred m2m relationship
        namespace.setdefault(DEFERRED_M2M_FIELDS, {})[m2m] = annotation
        return

    if isinstance(m2m_ref, list):
        msg = 'Many-to-many relation cannot have default value'
        raise AmsdalModelError(msg)

    if not m2m_model:
        m2m_model = DeferredModel(m2m_ref)  # type: ignore[assignment,type-var]

    namespace.setdefault(MANY_TO_MANY_FIELDS, {})[m2m] = m2m_ref, m2m_model, through_fields, field_info
    generate_dynamic_m2m_fields(m2m, m2m_ref, m2m_model, through_fields, namespace)  # type: ignore[arg-type]


class DeferredModel:
    def __init__(self, m2m_ref: ClassTypeT) -> None:
        self._build_model = lambda cls: build_m2m_model(cls, m2m_ref)

    def __call__(self, cls: ClassTypeT) -> ClassTypeT:
        return self._build_model(cls)  # type: ignore[return-value]


def generate_dynamic_m2m_fields(
    m2m: str,
    m2m_ref: type['Model'],
    m2m_model: DeferredModel | type['Model'],
    through_fields: tuple[str, str] | None,
    namespace: dict[str, Any] | type['Model'],
) -> None:
    def _ns_setter(field: str, value: Any) -> None:
        if isinstance(namespace, dict):
            namespace[field] = value
        else:
            setattr(namespace, field, value)

    def _ns_getter(field: str, default: Any = None) -> Any:
        if isinstance(namespace, dict):
            return namespace.get(field, default)
        return getattr(namespace, field, default)

    _getter = generate_m2m_getter(m2m, m2m_ref, through_fields)
    _setter = generate_m2m_setter(m2m, m2m_ref)
    _through_getter = generate_m2m_through_getter(m2m_model)
    _manager_getter = generate_m2m_manager_getter(m2m)
    _getter_references = generate_m2m_references_getter(m2m, m2m_ref, through_fields)

    _ns_setter(
        f'{m2m}_through',
        PrivateProperty(_through_getter),
    )
    _ns_setter(
        f'{m2m}_manager',
        PrivateProperty(_manager_getter),
    )
    _ns_setter(
        f'{m2m}_references',
        PrivateProperty(_getter_references),
    )
    _getter_prop = PrivateProperty(_getter)
    _ns_setter(m2m, _getter_prop)
    _ns_setter(m2m, _getter_prop.setter(_setter))

    # remove m2m field from annotations
    _annotations = _ns_getter(ANNOTATIONS, {})
    _annotations.pop(m2m, None)


def generate_m2m_getter(
    m2m: str, m2m_ref: type['Model'], through_fields: tuple[str, str] | None
) -> Callable[[Any], list[ManyList] | Coroutine[None, None, list[ManyList]]]:
    _, target_field = through_fields if through_fields else (None, m2m_ref.__name__.lower())

    def _getter(self: Any) -> list[ManyList] | Coroutine[Any, Any, list[ManyList]]:
        _value_property = build_m2m_value_property(m2m)
        _value_cached_property = f'_{m2m}_cached'

        if hasattr(self, _value_property):
            return getattr(self, _value_property)

        if hasattr(self, _value_cached_property):
            return getattr(self, _value_cached_property)

        through = getattr(self, f'{m2m}_through')
        m2m_fields = getattr(self.__class__, MANY_TO_MANY_FIELDS)
        _, _, _through_fields, _ = m2m_fields[m2m]
        source_field, _ = _through_fields if _through_fields else (self.__class__.__name__.lower(), None)
        using = LAKEHOUSE_DB_ALIAS if self.is_from_lakehouse else DEFAULT_DB_ALIAS

        if AmsdalConfigManager().get_config().async_mode:

            async def _async_getter() -> list[ManyList]:
                try:
                    self_reference = await self.abuild_reference(is_frozen=True)
                except ValueError as e:
                    if 'No metadata found' in str(e):
                        _value = ManyList(m2m, self, through.objects, [])
                        setattr(self, _value_cached_property, _value)
                        return _value
                    raise

                _result = await (
                    through.objects.select_related(target_field)
                    .using(using)
                    .filter(
                        **{source_field: self_reference},
                    )
                    .aexecute()
                )
                _value = ManyList(
                    m2m,
                    self,
                    through.objects,
                    [getattr(_item, target_field) for _item in _result],
                )
                setattr(self, _value_cached_property, _value)

                return _value

            return _async_getter()

        try:
            self_reference = self.build_reference(is_frozen=True)
        except ValueError as e:
            if 'No metadata found' in str(e):
                _value = ManyList(m2m, self, through.objects, [])
                setattr(self, _value_cached_property, _value)
                return _value
            raise

        result = (
            through.objects.select_related(target_field)
            .using(using)
            .filter(
                **{source_field: self_reference},
            )
            .execute()
        )
        value = ManyList(
            m2m,
            self,
            through.objects,
            [getattr(_item, target_field) for _item in result],
        )
        setattr(self, _value_cached_property, value)

        return value

    return _getter


def generate_m2m_setter(m2m: str, m2m_ref: type['Model']) -> Callable[[Any, list[type['Model']]], None]:
    def _setter(self: Any, value: list[type['Model']]) -> None:
        _values = []

        for _value in value or []:
            if isinstance(_value, dict):
                for _type in [Reference, m2m_ref]:
                    try:
                        _type_adapter = TypeAdapter(_type)
                        _value = _type_adapter.validate_python(_value)
                    except ValidationError:
                        if _type is m2m_ref:
                            raise
                        continue
                    else:
                        _values.append(_value)
                        break
            else:
                _values.append(_value)

        with suppress(AttributeError):
            delattr(self, f'_{m2m}_cached')

        if isinstance(_values, list):
            manager = getattr(self, f'{m2m}_manager')
            _values = ManyList(m2m, self, manager, _values)
        setattr(self, build_m2m_value_property(m2m), _values)

    return _setter


def generate_m2m_through_getter(m2m_model: type['Model'] | DeferredModel) -> Callable[[Any], type['Model']]:
    def _through_getter(self: Any) -> type['Model']:
        if isinstance(m2m_model, DeferredModel):
            _m2m_model = m2m_model(self.__class__)
        else:
            _m2m_model = m2m_model

        return _m2m_model

    return _through_getter


def generate_m2m_manager_getter(m2m: str) -> Callable[[Any], BaseManager[Any]]:
    def _manager_getter(self: Any) -> BaseManager[Any]:
        through = getattr(self, f'{m2m}_through')
        return through.objects

    return _manager_getter


def generate_m2m_references_getter(
    m2m: str,
    m2m_ref: type['Model'],
    through_fields: tuple[str, str] | None,
) -> Callable[[Any], list[Reference] | Coroutine[None, None, list[Reference]]]:
    _, target_field = through_fields if through_fields else (None, m2m_ref.__name__.lower())

    def _references_getter(self: Any) -> list[Reference] | Coroutine[None, None, list[Reference]]:
        through = getattr(self, f'{m2m}_through')
        m2m_fields = getattr(self.__class__, MANY_TO_MANY_FIELDS)
        _, _, _through_fields, _ = m2m_fields[m2m]
        source_field, _ = _through_fields if _through_fields else (self.__class__.__name__.lower(), None)
        using = LAKEHOUSE_DB_ALIAS if self.is_from_lakehouse else DEFAULT_DB_ALIAS

        if AmsdalConfigManager().get_config().async_mode:

            async def _async_references_getter() -> list[Reference]:
                _result = (
                    await through.objects.using(using)
                    .filter(
                        **{source_field: await self.abuild_reference(is_frozen=True)},
                    )
                    .aexecute()
                )
                return [getattr(_item, f'{target_field}_reference') for _item in _result]

            return _async_references_getter()

        result = (
            through.objects.using(using)
            .filter(
                **{source_field: self.build_reference(is_frozen=True)},
            )
            .execute()
        )
        return [getattr(_item, f'{target_field}_reference') for _item in result]

    return _references_getter


def build_m2m_value_property(m2m: str) -> str:
    return f'_{m2m}_value'


def resolve_m2m_ref(
    annotation: Any,
) -> tuple[
    type['Model'] | ForwardRef,
    type['Model'] | ForwardRef | None,
    tuple[str, str] | None,
    ManyReferenceFieldInfo | FieldInfo | None,
]:
    if isinstance(annotation, ManyReferenceFieldInfo) or isinstance(annotation, FieldInfo):
        m2m_ref, _ = resolve_model_type(annotation.annotation)
        field_info = annotation
    else:
        _origin = get_origin(annotation)
        field_info = None

        if _origin is list:
            _annotation = get_args(annotation)[0]
            m2m_ref, _ = resolve_model_type(_annotation)
        else:
            m2m_ref, _ = resolve_model_type(annotation)

    if isinstance(annotation, ManyReferenceFieldInfo):
        m2m_model = annotation.through
        through_fields = annotation.through_fields
    else:
        m2m_model = None
        through_fields = None

    if isinstance(m2m_ref, str):
        m2m_ref = ForwardRef(m2m_ref)

    return m2m_ref, m2m_model, through_fields, field_info  # type: ignore[return-value]


def build_m2m_model(
    cls: Union[type['Model'], 'AmsdalModelMetaclass'],
    to_model: type['Model'],
) -> type['Model']:
    from amsdal_models.classes.model import Model

    _model_fields: dict[str, Any] = {
        cls.__name__.lower(): (cls, ...),
        to_model.__name__.lower(): (to_model, ...),
    }

    return create_model(
        f'{cls.__name__}{to_model.__name__}',
        **_model_fields,
        __module_type__=(ClassVar[ModuleType], getattr(cls, '__module_type__', ModuleType.USER)),
        __primary_key__=(ClassVar[list[str]], list(_model_fields.keys())),
        __base__=Model,
    )
