from collections.abc import Callable
from collections.abc import Iterable
from copy import copy
from typing import TYPE_CHECKING
from typing import Any
from typing import Union
from warnings import warn

from pydantic.fields import FieldInfo
from pydantic.fields import _FromFieldInfoInputs
from pydantic.json_schema import PydanticJsonSchemaWarning
from pydantic_core import PydanticUndefined
from typing_extensions import Unpack

from amsdal_models.classes.relationships.constants import PRIMARY_KEY
from amsdal_models.classes.relationships.enum import ReferenceMode

if TYPE_CHECKING:
    from amsdal_models.classes.model import Model


def build_reference_db_field(field_name: str, suffix: str = '_id') -> str:
    return f'{field_name}{suffix}'


def default_db_field(field_name: str, field_type: type['Model']) -> str | Iterable[str]:
    pks = getattr(field_type, PRIMARY_KEY, [])
    pks_num = len(pks)

    if pks_num == 0:
        msg = 'Foreign Key to model without Primary Key is not allowed!'
        raise RuntimeError(msg)

    if pks_num == 1:
        return build_reference_db_field(field_name)

    return tuple(build_reference_db_field(pk) for pk in pks)


def ReferenceField(  # type: ignore[no-untyped-def] # noqa: N802
    *args,
    db_field: str | Iterable[str] | Callable[[str, type['Model']], str | Iterable[str]] = default_db_field,
    **kwargs,
) -> Any:
    return ReferenceFieldInfo.from_field(*args, db_field=db_field, **kwargs)


class _ReferenceFromFieldInfoInputs(_FromFieldInfoInputs):
    db_field: str | Iterable[str] | Callable[[str, type['Model']], str | Iterable[str]]
    on_delete: ReferenceMode | Callable[[Any], None]


class _ReferenceFieldInfoInputs(_ReferenceFromFieldInfoInputs, total=False):
    default: Any


class ReferenceFieldInfo(FieldInfo):  # type: ignore[misc]
    db_field: str | Iterable[str] | Callable[[str, type['Model']], str | Iterable[str]]
    __slots__ = (*FieldInfo.__slots__, 'db_field')

    def __init__(self, **kwargs: Unpack[_ReferenceFieldInfoInputs]) -> None:
        self.db_field = kwargs['db_field']

        super().__init__(**kwargs)  # type: ignore[misc]

    @staticmethod
    def from_field(default: Any = PydanticUndefined, **kwargs: Unpack[_ReferenceFromFieldInfoInputs]) -> FieldInfo:  # type: ignore[override]
        return ReferenceFieldInfo(default=default, **kwargs)

    @staticmethod
    def merge_field_infos(
        *field_infos: Union[FieldInfo, 'ReferenceFieldInfo'], **overrides: Any
    ) -> 'ReferenceFieldInfo':
        """Merge `FieldInfo | ReferenceFieldInfo` instances keeping only explicitly set attributes.

        Later `FieldInfo | ReferenceFieldInfo` instances override earlier ones.

        Returns:
            ReferenceFieldInfo: A merged FieldInfo | ReferenceFieldInfo instance.
        """
        if len(field_infos) == 1:
            # No merging necessary, but we still need to make a copy and apply the overrides
            field_info = copy(field_infos[0])
            field_info._attributes_set.update(overrides)

            default_override = overrides.pop('default', PydanticUndefined)
            if default_override is Ellipsis:
                default_override = PydanticUndefined
            if default_override is not PydanticUndefined:
                field_info.default = default_override

            for k, v in overrides.items():
                setattr(field_info, k, v)
            return field_info  # type: ignore

        merged_field_info_kwargs: dict[str, Any] = {}
        metadata = {}
        for field_info in field_infos:
            attributes_set = field_info._attributes_set.copy()

            try:
                json_schema_extra = attributes_set.pop('json_schema_extra')
                existing_json_schema_extra = merged_field_info_kwargs.get('json_schema_extra')

                if existing_json_schema_extra is None:
                    merged_field_info_kwargs['json_schema_extra'] = json_schema_extra
                if isinstance(existing_json_schema_extra, dict):
                    if isinstance(json_schema_extra, dict):
                        merged_field_info_kwargs['json_schema_extra'] = {
                            **existing_json_schema_extra,
                            **json_schema_extra,
                        }
                    if callable(json_schema_extra):
                        warn(
                            'Composing `dict` and `callable` type `json_schema_extra` is not supported.'
                            'The `callable` type is being ignored.'
                            "If you'd like support for this behavior, please open an issue on pydantic.",
                            PydanticJsonSchemaWarning,
                            stacklevel=2,
                        )
                elif callable(json_schema_extra):
                    # if ever there's a case of a callable, we'll just keep the last json schema extra spec
                    merged_field_info_kwargs['json_schema_extra'] = json_schema_extra
            except KeyError:
                pass

            # later FieldInfo instances override everything except json_schema_extra from earlier FieldInfo instances
            merged_field_info_kwargs.update(attributes_set)

            for x in field_info.metadata:
                if not isinstance(x, FieldInfo):
                    metadata[type(x)] = x

        merged_field_info_kwargs.update(overrides)
        field_info = ReferenceFieldInfo(**merged_field_info_kwargs)
        field_info.metadata = list(metadata.values())
        return field_info
