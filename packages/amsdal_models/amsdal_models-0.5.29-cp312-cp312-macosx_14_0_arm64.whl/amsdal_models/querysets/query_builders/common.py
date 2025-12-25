from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any
from typing import TypeVar

import amsdal_glue as glue
from amsdal_data.connections.historical.data_query_transform import DEFAULT_PKS
from amsdal_utils.query.data_models.order_by import OrderBy
from amsdal_utils.query.data_models.paginator import NumberPaginator
from amsdal_utils.query.enums import Lookup
from amsdal_utils.query.utils import Q

from amsdal_models.classes.relationships.constants import FOREIGN_KEYS
from amsdal_models.classes.relationships.constants import PRIMARY_KEY_FIELDS
from amsdal_models.classes.relationships.meta.common import resolve_model_type
from amsdal_models.classes.relationships.meta.references import build_fk_db_fields
from amsdal_models.classes.utils import is_partial_model

if TYPE_CHECKING:
    from amsdal_models.classes.model import Model
    from amsdal_models.querysets.base_queryset import QuerySetBase

ModelType = TypeVar('ModelType', bound='Model')


class BaseQueryBuilder:
    qs_table_name: str
    qs_model: type['ModelType']  # type: ignore[valid-type]
    qs_select_related: dict[tuple[str, type['ModelType'], str], Any] | None  # type: ignore[valid-type]
    qs_only: list[str] | None
    qs_conditions: Q | None
    qs_order_by: list[OrderBy]
    qs_limit: NumberPaginator

    def __init__(self, queryset: 'QuerySetBase') -> None:  # type: ignore[type-arg]
        self._queryset = queryset

        self.qs_table_name = self._queryset.table_name
        self.qs_model = self._queryset.entity
        self.qs_select_related = self._extract_select_related()
        self.qs_only = self._queryset.get_query_specifier().only if self._queryset.get_query_specifier() else None
        self.qs_conditions = self._queryset.get_conditions()
        self.qs_order_by = self._queryset.get_order_by()
        self.qs_limit = self._queryset.get_paginator()

    def build_limit(self) -> glue.LimitQuery | None:
        if not self.qs_limit or not self.qs_limit.limit:
            return None

        return glue.LimitQuery(
            limit=self.qs_limit.limit,
            offset=self.qs_limit.offset or 0,
        )

    @staticmethod
    def build_field(field_name: str) -> glue.Field:
        if '__' in field_name:
            _parent_name, *_rest_names = field_name.split('__')
            field = glue.Field(name=_parent_name)
            _root = field

            for _name in _rest_names:
                _child = glue.Field(name=_name, parent=_root)
                _root.child = _child
                _root = _child
        else:
            field = glue.Field(name=field_name)
        return field

    @staticmethod
    def build_table_name(model: type['ModelType']) -> str:
        if model.__table_name__:
            return model.__table_name__
        if is_partial_model(model):
            return model.__name__[: -len('Partial')]
        return model.__name__

    def normalize_primary_key(self, pk: str) -> str | list[str]:
        from amsdal_models.querysets.executor import ADDRESS_FIELD

        if '__ref__' in pk:
            return pk

        if '__' in pk:
            rest, pk_field = pk.rsplit('__', 1)
        else:
            rest, pk_field = '', pk

        pk_aliases = {
            'pk',
            '_object_id',
            'object_id',
        }
        _model = self.qs_model
        _db_fields = getattr(_model, PRIMARY_KEY_FIELDS, None) or DEFAULT_PKS

        if rest == ADDRESS_FIELD:
            rest = ''

        for fk in rest.split('__'):
            if not fk or fk not in _model.model_fields:  # type: ignore[attr-defined]
                continue

            _field_info = _model.model_fields[fk]  # type: ignore[attr-defined]
            _model, _db_fields, _ = build_fk_db_fields(fk, _field_info)  # type: ignore[assignment]

        if pk_field not in _model.model_fields and pk_field in pk_aliases:  # type: ignore[attr-defined]
            result = ['__'.join(filter(None, [rest, db_field])) for db_field in _db_fields]
            return result[0] if len(result) == 1 else result
        return pk

    def _build_field_reference(
        self,
        prop_name: str,
        model: type['ModelType'],
        table_name: str | None = None,
    ) -> list[glue.FieldReference]:
        model_fks = getattr(model, FOREIGN_KEYS, [])
        _table_name = table_name or self.build_table_name(model)

        if prop_name in model_fks:
            field_info = model.model_fields[prop_name]
            _, db_fields, _ = build_fk_db_fields(prop_name, field_info)

            return [
                glue.FieldReference(
                    field=self.build_field(_db_field),
                    table_name=_table_name,
                )
                for _db_field in db_fields
            ]
        else:
            return [
                glue.FieldReference(
                    field=self.build_field(prop_name),
                    table_name=_table_name,
                ),
            ]

    def build_field_references_from_pks(self, model: type['ModelType']) -> list[glue.FieldReference]:
        pks = getattr(model, PRIMARY_KEY_FIELDS).keys()
        return [
            glue.FieldReference(
                field=self.build_field(pk_field),
                table_name=self.build_table_name(model),
            )
            for pk_field in pks
        ]

    def _build_field_references_from_model(self, model: type['ModelType']) -> list[glue.FieldReference]:
        result = []

        for prop_name in model.model_fields:
            _fields = self._build_field_reference(prop_name, model)

            for _field in _fields:
                if _field not in result:
                    result.append(_field)

        return result

    def _extract_select_related(self) -> dict[tuple[str, type['ModelType'], str], Any] | None:
        _unprocessed_select_related = self._queryset.get_select_related()

        if not isinstance(_unprocessed_select_related, dict):
            return None

        return self._process_select_related(
            select_related=_unprocessed_select_related,
            model=self.qs_model,
        )

    def _process_select_related(
        self,
        select_related: dict[str, Any],
        model: type['ModelType'],
        alias_index: int = 0,
    ) -> dict[tuple[str, type['ModelType'], str], Any] | None:
        _select_related = {}
        _fk_fields = getattr(model, FOREIGN_KEYS, [])

        for key, value in select_related.items():
            if key not in _fk_fields:
                msg = f'Select related field "{key}" must be a Model type (a Foreign Key).'
                raise ValueError(msg)

            alias_index += 1
            fk_type, _ = resolve_model_type(model.model_fields[key].annotation)
            _related = self._process_select_related(value, fk_type, alias_index=alias_index)  # type: ignore[arg-type]

            _select_related[
                (
                    key,
                    fk_type,
                    f'sr_{alias_index}',
                )
            ] = _related

        return _select_related if _select_related else None  # type: ignore[return-value]

    @staticmethod
    def _to_glue_lookup(lookup: Lookup) -> glue.FieldLookup:
        return (
            {
                Lookup.EQ: glue.FieldLookup.EQ,
                Lookup.NEQ: glue.FieldLookup.NEQ,
                Lookup.GT: glue.FieldLookup.GT,
                Lookup.GTE: glue.FieldLookup.GTE,
                Lookup.LT: glue.FieldLookup.LT,
                Lookup.LTE: glue.FieldLookup.LTE,
                Lookup.IN: glue.FieldLookup.IN,
                Lookup.CONTAINS: glue.FieldLookup.CONTAINS,
                Lookup.ICONTAINS: glue.FieldLookup.ICONTAINS,
                Lookup.STARTSWITH: glue.FieldLookup.STARTSWITH,
                Lookup.ISTARTSWITH: glue.FieldLookup.ISTARTSWITH,
                Lookup.ENDSWITH: glue.FieldLookup.ENDSWITH,
                Lookup.IENDSWITH: glue.FieldLookup.IENDSWITH,
                Lookup.ISNULL: glue.FieldLookup.ISNULL,
                Lookup.REGEX: glue.FieldLookup.REGEX,
                Lookup.IREGEX: glue.FieldLookup.IREGEX,
            }
        )[lookup]

    @classmethod
    def _process_nested_rest(
        cls,
        rest: str,
        select_related: dict[tuple[str, type['ModelType'], str], Any] | None = None,
    ) -> str:
        if not select_related or '__' not in rest:
            return rest

        [_field_name, _rest] = rest.split('__', 1)

        for (field, _, alias), nested_select_related in select_related.items():
            if field == _field_name:
                return f'{alias}__{cls._process_nested_rest(_rest, nested_select_related)}'
        return rest


class QueryBuilder(BaseQueryBuilder, ABC):
    @abstractmethod
    def transform(self) -> glue.QueryStatement: ...

    @abstractmethod
    def transform_count(self) -> glue.QueryStatement: ...

    @classmethod
    @abstractmethod
    def _build_nested_only(
        cls,
        select_related: dict[tuple[str, type['ModelType'], str], Any],
    ) -> list[glue.FieldReferenceAliased]: ...

    def build_only(
        self,
        model: type['ModelType'],
        only: list[str] | None = None,
        select_related: dict[tuple[str, type['ModelType'], str], Any] | None = None,
    ) -> list[glue.FieldReference | glue.FieldReferenceAliased] | None:
        if not only and not select_related and not self._queryset._annotations:
            return None

        _only = self.build_field_references_from_pks(model)
        pk_names = list(getattr(model, PRIMARY_KEY_FIELDS).keys())

        if only:
            for _only_field in only:
                normalized_item = self.normalize_primary_key(_only_field)

                if isinstance(normalized_item, list) or normalized_item in pk_names:
                    # the field was specified as PK, skip we have already added them
                    continue
                else:
                    _only.extend(self._build_field_reference(normalized_item, model))

            return _only

        # process select_related
        for _field in self._build_field_references_from_model(model):
            if _field not in _only:
                _only.append(_field)

        if select_related:
            _only.extend(self._build_nested_only(select_related))

        return _only


class AsyncQueryBuilder(BaseQueryBuilder, ABC):
    @abstractmethod
    async def transform(self) -> glue.QueryStatement: ...

    @abstractmethod
    async def transform_count(self) -> glue.QueryStatement: ...

    @abstractmethod
    async def _build_nested_only(
        self,
        select_related: dict[tuple[str, type['ModelType'], str], Any],
    ) -> list[glue.FieldReferenceAliased]: ...

    async def build_only(
        self,
        model: type['ModelType'],
        only: list[str] | None = None,
        select_related: dict[tuple[str, type['ModelType'], str], Any] | None = None,
    ) -> list[glue.FieldReference | glue.FieldReferenceAliased] | None:
        if not only and not select_related:
            return None

        _only = self.build_field_references_from_pks(model)
        pk_names = list(getattr(model, PRIMARY_KEY_FIELDS).keys())

        if only:
            for _only_field in only:
                normalized_item = self.normalize_primary_key(_only_field)

                if isinstance(normalized_item, list) or normalized_item in pk_names:
                    # the field was specified as PK, skip we have already added them
                    continue
                else:
                    _only.extend(self._build_field_reference(normalized_item, model))

            return _only

        # process select_related
        for _field in self._build_field_references_from_model(model):
            if _field not in _only:
                _only.append(_field)

        if select_related:
            _only.extend(await self._build_nested_only(select_related))

        return _only
