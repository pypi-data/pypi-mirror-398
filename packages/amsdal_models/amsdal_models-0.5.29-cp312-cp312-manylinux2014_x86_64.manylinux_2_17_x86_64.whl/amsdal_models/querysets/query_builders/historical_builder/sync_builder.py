import logging
import uuid
from typing import Any

import amsdal_glue as glue
from amsdal_data.connections.constants import PRIMARY_PARTITION_KEY
from amsdal_data.connections.constants import SECONDARY_PARTITION_KEY
from amsdal_data.connections.historical.data_query_transform import META_CLASS_NAME
from amsdal_data.connections.historical.data_query_transform import METADATA_FIELD
from amsdal_data.connections.historical.data_query_transform import METADATA_TABLE_ALIAS
from amsdal_data.connections.historical.data_query_transform import NEXT_VERSION_FIELD
from amsdal_data.connections.historical.data_query_transform import PK_FIELD_ALIAS_FOR_METADATA
from amsdal_data.connections.historical.data_query_transform import build_simple_query_statement_with_metadata
from amsdal_data.connections.historical.schema_version_manager import HistoricalSchemaVersionManager
from amsdal_glue_core.common.expressions.expression import Expression
from amsdal_glue_core.common.expressions.jsonb_array import JsonbArrayExpression
from amsdal_utils.models.data_models.enums import CoreTypes
from amsdal_utils.models.enums import Versions
from amsdal_utils.query.enums import Lookup
from amsdal_utils.query.mixin import QueryableMixin
from amsdal_utils.query.utils import ConnectorEnum
from amsdal_utils.query.utils import Q

from amsdal_models.classes.relationships.constants import FOREIGN_KEYS
from amsdal_models.classes.relationships.constants import PRIMARY_KEY
from amsdal_models.classes.relationships.meta.primary_key import build_metadata_primary_key
from amsdal_models.querysets.query_builders.common import ModelType
from amsdal_models.querysets.query_builders.common import QueryBuilder
from amsdal_models.querysets.query_builders.historical_builder.base import BaseHistoricalQueryBuilder
from amsdal_models.querysets.query_builders.historical_builder.base import _field_shortcut

logger = logging.getLogger(__name__)


class HistoricalQueryBuilder(BaseHistoricalQueryBuilder, QueryBuilder):
    def transform(self) -> glue.QueryStatement:
        return self.build_query_statement_with_metadata(
            table=glue.SchemaReference(
                name=self.build_table_name(self.qs_model),
                version=HistoricalSchemaVersionManager().get_latest_schema_version(self.qs_model.__name__),
                metadata={
                    **build_metadata_primary_key(self.qs_model),
                    META_CLASS_NAME: self.qs_model.__name__,
                },
            ),
            select_related=self.qs_select_related,
            only=self.build_only(
                model=self.qs_model,
                only=self.qs_only,
                select_related=self.qs_select_related,
            ),
            where=self.build_where(
                model=self.qs_model,
                conditions=self.qs_conditions,
                select_related=self.qs_select_related,
            ),
            order_by=self.build_order_by(),
            limit=self.build_limit(),
        )

    def transform_count(self, total_alias: str = 'total_count', count_field: str = '*') -> glue.QueryStatement:
        return self.build_query_statement_with_metadata(
            table=glue.SchemaReference(
                name=self.build_table_name(self.qs_model),
                version=HistoricalSchemaVersionManager().get_latest_schema_version(self.qs_model.__name__),
                metadata={
                    **build_metadata_primary_key(self.qs_model),
                    META_CLASS_NAME: self.qs_model.__name__,
                },
            ),
            select_related=self.qs_select_related,
            aggregations=[
                glue.AggregationQuery(
                    expression=glue.Count(
                        field=glue.FieldReference(
                            field=glue.Field(name=count_field),
                            table_name=self.qs_table_name,
                        )
                    ),
                    alias=total_alias,
                ),
            ],
            where=self.build_where(
                model=self.qs_model,
                conditions=self.qs_conditions,
                select_related=self.qs_select_related,
            ),
            limit=self.build_limit(),
        )

    def build_only(
        self,
        model: type['ModelType'],
        only: list[str] | None = None,
        select_related: dict[tuple[str, type['ModelType'], str], Any] | None = None,
    ) -> list[glue.FieldReference | glue.FieldReferenceAliased] | None:
        if not only:
            return None

        return super().build_only(model, only, select_related)

    @classmethod
    def build_query_statement_with_metadata(
        cls,
        table: glue.SchemaReference,
        select_related: dict[tuple[str, type['ModelType'], str], Any] | None = None,
        only: list[glue.FieldReference | glue.FieldReferenceAliased] | None = None,
        annotations: list[glue.AnnotationQuery] | None = None,
        aggregations: list[glue.AggregationQuery] | None = None,
        joins: list[glue.JoinQuery] | None = None,
        where: glue.Conditions | None = None,
        group_by: list[glue.GroupByQuery] | None = None,
        order_by: list[glue.OrderByQuery] | None = None,
        limit: glue.LimitQuery | None = None,
    ) -> glue.QueryStatement:
        if aggregations:
            _only_aggr = []
            _only_query = []
            _aggr_fields = [aggr.alias for aggr in aggregations]

            for _only in only or []:
                if _only.field.name in _aggr_fields:
                    _only_aggr.append(_only)
                else:
                    _only_query.append(_only)

            return glue.QueryStatement(
                aggregations=aggregations,
                table=glue.SubQueryStatement(
                    query=cls.build_query_statement_with_metadata(
                        table=table,
                        select_related=select_related,
                        only=_only_query or None,
                        annotations=annotations,
                        joins=joins,
                        where=where,
                    ),
                    alias=table.name,
                ),
                group_by=group_by,
                order_by=_only_aggr or None,  # type: ignore[arg-type]
                limit=limit,
            )

        query = build_simple_query_statement_with_metadata(
            table=table,
            only=only,
            annotations=annotations,
            joins=joins,
            where=where,
            order_by=order_by,
            limit=limit,
        )

        if not select_related:
            return query

        if not only:
            # if only was not specified explicitly, we need extend it with all select_related model's fields
            extra_only = cls._build_nested_only(select_related)
            query.only = query.only or []
            query.only.extend(extra_only)
            query.group_by = query.group_by or []
            query.group_by.extend(
                [
                    glue.GroupByQuery(
                        field=glue.FieldReference(
                            field=_item.field,
                            table_name=_item.table_name,
                        ),
                    )
                    for _item in extra_only
                ]
            )

        query.joins = query.joins or []
        query.joins.extend(
            cls._build_select_related_joins(
                parent_alias=table.alias or table.name,
                select_related=select_related,
            ),
        )

        return query

    def build_where(
        self,
        model: type['ModelType'],
        conditions: Q | None,
        select_related: dict[tuple[str, type['ModelType'], str], Any] | None = None,
    ) -> glue.Conditions | None:
        from amsdal_models.querysets.executor import ADDRESS_FIELD
        from amsdal_models.querysets.executor import OBJECT_VERSION_FIELD

        if not conditions:
            return None

        _fk_to_db_fields_map = self._fk_to_db_fields_for(model)
        _conditions: list[glue.Conditions | glue.Condition] = []

        for child in conditions.children:
            if isinstance(child, Q):
                if _cond := self.build_where(model, child, select_related):
                    _conditions.append(_cond)
                continue

            if '__' in child.field_name:
                [_field_name, _rest] = child.field_name.split('__', 1)
            else:
                [_field_name, _rest] = child.field_name, ''

            if select_related:
                _select_related_key: tuple[str, type[ModelType], str] | None = next(
                    (key for key in select_related if key[0] == _field_name), None
                )
                _select_related = select_related.get(_select_related_key)  # type: ignore[arg-type]
            else:
                _select_related_key = None
                _select_related = None

            _value = child.value

            if not _rest and _field_name in _fk_to_db_fields_map:
                _field_name = _fk_to_db_fields_map[_field_name]

            if isinstance(_value, QueryableMixin):
                new_q = _value.to_query(prefix=f'{_field_name}__')

                if child.lookup == Lookup.NEQ:
                    new_q = ~new_q

                if _cond := self.build_where(model, new_q, _select_related):
                    _conditions.append(_cond)
                continue

            if _field_name == ADDRESS_FIELD and _rest == OBJECT_VERSION_FIELD:
                _field = glue.Field(name=SECONDARY_PARTITION_KEY)

                if _value in (glue.Version.LATEST, Versions.LATEST, '', 'LATEST'):
                    _conditions.append(
                        glue.Conditions(
                            glue.Condition(
                                left=glue.FieldReferenceExpression(
                                    field_reference=glue.FieldReference(
                                        field=glue.Field(name=NEXT_VERSION_FIELD),
                                        table_name=METADATA_TABLE_ALIAS,
                                    ),
                                ),
                                lookup=glue.FieldLookup.ISNULL,
                                right=glue.Value(value=True),
                            ),
                            glue.Condition(
                                left=glue.FieldReferenceExpression(
                                    field_reference=glue.FieldReference(
                                        field=glue.Field(name=NEXT_VERSION_FIELD),
                                        table_name=METADATA_TABLE_ALIAS,
                                    ),
                                ),
                                lookup=glue.FieldLookup.EQ,
                                right=glue.Value(value=''),
                            ),
                            connector=glue.FilterConnector.OR,
                        ),
                    )
                    continue
                elif _value in (glue.Version.ALL, Versions.ALL, 'ALL'):
                    _conditions.append(
                        glue.Condition(
                            left=glue.FieldReferenceExpression(
                                field_reference=glue.FieldReference(
                                    field=_field,
                                    table_name=self.qs_table_name,
                                ),
                            ),
                            lookup=glue.FieldLookup.NEQ,
                            right=glue.Value('_empty-'),
                        )
                    )
                    continue

                _conditions.append(
                    glue.Condition(
                        left=glue.FieldReferenceExpression(
                            field_reference=glue.FieldReference(
                                field=_field,
                                table_name=self.qs_table_name,
                            ),
                        ),
                        lookup=glue.FieldLookup.EQ,
                        right=glue.Value(_value),
                    )
                )
                continue

            if _field_name == METADATA_FIELD:
                _conditions.append(
                    glue.Condition(
                        left=glue.FieldReferenceExpression(
                            field_reference=glue.FieldReference(
                                field=glue.Field(name=_rest),
                                table_name=METADATA_TABLE_ALIAS,
                            ),
                        ),
                        lookup=glue.FieldLookup.EQ,
                        right=glue.Value(_value),
                    )
                )
                continue

            if _select_related_key:
                field_names = self._process_nested_lakehouse_rest(_rest, _select_related)
                table_name = _select_related_key[2]
                _build_field = _field_shortcut
                _output_type = None
                versions = list(
                    HistoricalSchemaVersionManager()
                    .get_all_schema_properties(
                        _select_related_key[1].__name__,
                    )
                    .keys()
                )
            else:
                field_names = [child.field_name]
                table_name = self.qs_table_name
                _build_field = self.build_field
                _output_type = str if '__' in child.field_name else None
                versions = [glue.Version.LATEST]

            for _field_name in field_names:
                normalized_field = self.normalize_primary_key(_field_name)

                field_value: zip[tuple[str, Any]] | list[tuple[str, Any]]
                if isinstance(normalized_field, str):
                    if normalized_field in _fk_to_db_fields_map:
                        normalized_field = f'{_fk_to_db_fields_map[normalized_field]}__ref__object_id'

                    if isinstance(_value, list) and len(_value) == 1 and child.lookup != Lookup.IN:
                        _current_value = _value[0]
                    else:
                        _current_value = _value

                    field_value = [(normalized_field, _current_value)]
                else:
                    _normalized_field = []
                    for _field in normalized_field:  # type: ignore[assignment]
                        if _field in _fk_to_db_fields_map:
                            _normalized_field.append(f'{_fk_to_db_fields_map[_field]}__ref__object_id')  # type: ignore[index]
                        else:
                            _normalized_field.append(_field)  # type: ignore[arg-type]

                    field_value = zip(_normalized_field, _value, strict=False)

                _conditions.append(
                    glue.Conditions(
                        *(
                            glue.Conditions(
                                *(
                                    glue.Condition(
                                        left=glue.FieldReferenceExpression(
                                            field_reference=glue.FieldReference(
                                                field=_build_field(_db_field),
                                                table_name=(
                                                    table_name
                                                    if version == glue.Version.LATEST
                                                    else f'{table_name}__{version[:8]}'
                                                ),
                                            ),
                                            output_type=_output_type,
                                        ),
                                        lookup=self._to_glue_lookup(child.lookup),
                                        right=glue.Value(value=_pk_value, output_type=_output_type),
                                    )
                                    for _db_field, _pk_value in field_value
                                ),
                                connector=glue.FilterConnector.AND,
                            )
                            for version in versions
                        ),
                        connector=glue.FilterConnector.OR,
                    )
                )

        if _conditions:
            return glue.Conditions(
                *_conditions,
                connector=(
                    {
                        ConnectorEnum.AND: glue.FilterConnector.AND,
                        ConnectorEnum.OR: glue.FilterConnector.OR,
                    }
                )[conditions.connector],
                negated=conditions.negated,
            )

        return None

    @classmethod
    def _build_nested_only(
        cls,
        select_related: dict[tuple[str, type['ModelType'], str], Any],
    ) -> list[glue.FieldReferenceAliased]:
        only: list[glue.FieldReferenceAliased] = []
        fk_type: type[ModelType]

        for (_, fk_type, alias), nested_select_related in select_related.items():
            for version, properties in (
                HistoricalSchemaVersionManager()
                .get_all_schema_properties(
                    fk_type.__name__,
                )
                .items()
            ):
                _alias = f'{alias}__{version[:8]}'
                property_names = list(properties.keys())
                property_names.append(SECONDARY_PARTITION_KEY)

                for prop_name in property_names:
                    if properties.get(prop_name) == CoreTypes.ARRAY.value:
                        # exclude array fields coz it can be m2m field
                        continue

                    only.append(
                        glue.FieldReferenceAliased(
                            field=glue.Field(name=prop_name),
                            table_name=_alias,
                            alias=f'{_alias}__{prop_name}',
                        )
                    )

                if nested_select_related:
                    for sub_field in cls._build_nested_only(nested_select_related):
                        only.append(
                            glue.FieldReferenceAliased(
                                field=glue.Field(name=sub_field.alias),
                                table_name=_alias,
                                alias=f'{_alias}__{sub_field.alias}',
                            )
                        )
        return only

    @classmethod
    def _build_select_related_joins(
        cls,
        parent_alias: str,
        select_related: dict[tuple[str, type['ModelType'], str], Any],
        parent_properties: list[str] | None = None,
    ) -> list[glue.JoinQuery]:
        joins = []

        for (field, fk_type, alias), nested_select_related in select_related.items():
            if parent_properties and field not in parent_properties:
                logger.info(f'Field {field} not in parent "{parent_alias}" properties: {parent_properties}.')
                continue

            reference_field = glue.Field(name=field)
            ref_field = glue.Field(name='ref', parent=reference_field)
            object_id = glue.Field(name='object_id', parent=ref_field)
            reference_field.child = ref_field
            ref_field.child = object_id

            for version in (
                HistoricalSchemaVersionManager()
                .get_all_schema_properties(
                    fk_type.__name__,
                )
                .keys()
            ):
                fk_table_name = getattr(fk_type, '__table_name__', None) or fk_type.__name__
                join_query = cls.build_query_statement_with_metadata(
                    table=glue.SchemaReference(
                        name=fk_table_name,
                        version=version,
                        metadata={
                            **build_metadata_primary_key(fk_type),
                        },
                    ),
                    select_related=nested_select_related,
                )

                _alias = f'{alias}__{version[:8]}'
                _pk_metadata_alias = f'{PK_FIELD_ALIAS_FOR_METADATA}_{uuid.uuid4().hex[:8]}'
                _pks = getattr(fk_type, PRIMARY_KEY, None) or [PRIMARY_PARTITION_KEY]
                _fks = getattr(fk_type, FOREIGN_KEYS, None) or []
                _fields = []
                _is_compound_pk = len(_pks) > 1

                for _pk in _pks:
                    _pk_is_fk = _pk in _fks
                    _field = glue.Field(name=_pk)

                    if _pk_is_fk:
                        _ref_field = glue.Field(name='ref', parent=_field)
                        _object_id = glue.Field(name='object_id', parent=_ref_field)
                        _field.child = _ref_field
                        _ref_field.child = _object_id

                    _fields.append(
                        glue.FieldReference(
                            field=_field,
                            table_name=_alias,
                        ),
                    )

                if _is_compound_pk:
                    _output_type = None
                    _value: Expression = JsonbArrayExpression(
                        items=[glue.FieldReferenceExpression(field_reference=_field) for _field in _fields],
                    )
                else:
                    _output_type = str
                    _value = glue.FieldReferenceExpression(
                        field_reference=_fields[0],
                        output_type=_output_type,
                    )

                joins.append(
                    glue.JoinQuery(
                        table=glue.SubQueryStatement(
                            query=join_query,
                            alias=_alias,
                        ),
                        on=glue.Conditions(
                            glue.Condition(
                                left=glue.FieldReferenceExpression(
                                    field_reference=glue.FieldReference(
                                        field=reference_field,
                                        table_name=parent_alias,
                                    ),
                                    output_type=_output_type,
                                ),
                                lookup=glue.FieldLookup.EQ,
                                right=_value,
                            )
                        ),
                        join_type=glue.JoinType.LEFT,
                    )
                )

        return joins

    def _process_nested_lakehouse_rest(
        self,
        rest: str,
        select_related: dict[tuple[str, type['ModelType'], str], Any] | None = None,
    ) -> list[str]:
        if not select_related or '__' not in rest:
            return [rest]

        [_field_name, _rest] = rest.split('__', 1)
        _fields = []

        for (field, fk_type, alias), nested_select_related in select_related.items():
            if field == _field_name:
                versions = list(
                    HistoricalSchemaVersionManager()
                    .get_all_schema_properties(
                        fk_type.__name__,
                    )
                    .keys()
                )
                _fields.extend(
                    [
                        f'{alias}__{version[:8]}__{sub_field}'
                        for version in versions
                        for sub_field in self._process_nested_lakehouse_rest(_rest, nested_select_related)
                    ]
                )
        return _fields
