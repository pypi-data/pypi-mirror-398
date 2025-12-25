import logging
from collections.abc import Callable
from collections.abc import Iterable
from typing import Any

import amsdal_glue as glue
from amsdal_data.connections.historical.data_query_transform import DEFAULT_PKS
from amsdal_data.connections.historical.data_query_transform import META_CLASS_NAME
from amsdal_glue_core.common.data_models.vector import Vector
from amsdal_glue_core.common.expressions.vector import CosineDistanceExpression
from amsdal_glue_core.common.expressions.vector import InnerProductExpression
from amsdal_glue_core.common.expressions.vector import L1DistanceExpression
from amsdal_glue_core.common.expressions.vector import L2DistanceExpression
from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.models.data_models.reference import ReferenceData
from amsdal_utils.query.enums import Lookup
from amsdal_utils.query.enums import OrderDirection
from amsdal_utils.query.mixin import QueryableMixin
from amsdal_utils.query.mixin import ReferenceableMixin
from amsdal_utils.query.utils import ConnectorEnum
from amsdal_utils.query.utils import Q

from amsdal_models.classes.annotations import CosineDistance
from amsdal_models.classes.annotations import InnerProduct
from amsdal_models.classes.annotations import L1Distance
from amsdal_models.classes.annotations import L2Distance
from amsdal_models.classes.relationships.constants import FOREIGN_KEYS
from amsdal_models.classes.relationships.constants import PRIMARY_KEY
from amsdal_models.classes.relationships.constants import PRIMARY_KEY_FIELDS
from amsdal_models.classes.relationships.meta.primary_key import build_metadata_primary_key
from amsdal_models.classes.relationships.meta.references import build_fk_db_fields
from amsdal_models.querysets.query_builders.common import ModelType
from amsdal_models.querysets.query_builders.common import QueryBuilder

logger = logging.getLogger(__name__)


def _field_shortcut(field_name: str) -> glue.Field:
    return glue.Field(name=field_name)


def _separated_fields(alias: str, prop_name: str) -> Callable[[str], str]:
    def _inner(field_name: str) -> str:  # noqa: ARG001
        return f'{alias}__{prop_name}'

    return _inner


class StateQueryBuilder(QueryBuilder):
    def transform(self) -> glue.QueryStatement:
        _query = glue.QueryStatement(
            only=self.build_only(
                model=self.qs_model,
                only=self.qs_only,
                select_related=self.qs_select_related,
            ),
            aggregations=None,
            annotations=self.build_annotations(),
            table=glue.SchemaReference(
                name=self.build_table_name(self.qs_model),
                version=glue.Version.LATEST,
                metadata={
                    **build_metadata_primary_key(self.qs_model),
                    META_CLASS_NAME: self.qs_model.__name__,
                },
            ),
            joins=self.build_joins(
                parent_alias=self.qs_table_name,
                parent_model=self.qs_model,
                select_related=self.qs_select_related,
            ),
        )
        return glue.QueryStatement(
            # select all fields
            only=None,
            table=glue.SubQueryStatement(
                query=_query,
                alias=self.qs_table_name,
            ),
            where=self.build_where(
                model=self.qs_model,
                conditions=self.qs_conditions,
                select_related=self.qs_select_related,
                backpropagate_select_related=True,  # Subquery wrapper requires backpropagation
            ),
            order_by=self.build_order_by(),
            limit=self.build_limit(),
        )

    def build_annotations(self) -> list[glue.AnnotationQuery]:
        if not self._queryset._annotations:
            return []

        _annotations: list[glue.AnnotationQuery] = []

        for key, annotation in self._queryset._annotations.items():
            if isinstance(annotation, (L2Distance, L1Distance, CosineDistance, InnerProduct)):
                distance_expression = {
                    L2Distance: L2DistanceExpression,
                    L1Distance: L1DistanceExpression,
                    CosineDistance: CosineDistanceExpression,
                    InnerProduct: InnerProductExpression,
                }[annotation.__class__]

                _left = (
                    glue.FieldReferenceExpression(
                        field_reference=glue.FieldReference(
                            field=glue.Field(name=annotation.left), table_name=self.qs_table_name
                        )
                    )
                    if isinstance(annotation.left, str)
                    else glue.Value(value=Vector(values=annotation.left))
                )

                _right = (
                    glue.FieldReferenceExpression(
                        field_reference=glue.FieldReference(
                            field=glue.Field(name=annotation.right), table_name=self.qs_table_name
                        )
                    )
                    if isinstance(annotation.right, str)
                    else glue.Value(value=Vector(values=annotation.right))
                )

                _annotations.append(
                    glue.AnnotationQuery(
                        value=glue.ExpressionAnnotation(
                            alias=key,
                            expression=distance_expression(left=_left, right=_right),
                        ),
                    ),
                )
            else:
                msg = f'Unsupported annotation type: {type(annotation)}'
                raise ValueError(msg)

        return _annotations

    def transform_count(self, total_alias: str = 'total_count', count_field: str = '*') -> glue.QueryStatement:
        return glue.QueryStatement(
            only=None,
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
            table=glue.SchemaReference(
                name=self.build_table_name(self.qs_model),
                version=glue.Version.LATEST,
                metadata={
                    **build_metadata_primary_key(self.qs_model),
                    META_CLASS_NAME: self.qs_model.__name__,
                },
            ),
            joins=self.build_joins(
                parent_alias=self.qs_table_name,
                parent_model=self.qs_model,
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

    def build_joins(
        self,
        parent_alias: str,
        parent_model: type['ModelType'],
        select_related: dict[tuple[str, type['ModelType'], str], Any] | None,
    ) -> list[glue.JoinQuery] | None:
        if not select_related:
            return None

        joins = []

        for (field, fk_type, alias), nested_select_related in select_related.items():
            _query = glue.QueryStatement(
                table=glue.SchemaReference(
                    name=self.build_table_name(fk_type),
                    version=glue.Version.LATEST,
                ),
                only=self.build_only(fk_type, only=None, select_related=nested_select_related),
                joins=self.build_joins(self.build_table_name(fk_type), fk_type, nested_select_related),
            )
            field_info = parent_model.model_fields[field]
            _, db_fields, _ = build_fk_db_fields(field, field_info)
            fk_pks = getattr(fk_type, PRIMARY_KEY_FIELDS, None) or DEFAULT_PKS
            _on_conditions = glue.Conditions(
                *[
                    glue.Condition(
                        left=glue.FieldReferenceExpression(
                            field_reference=glue.FieldReference(
                                field=glue.Field(name=_db_field),
                                table_name=parent_alias,
                            ),
                        ),
                        lookup=glue.FieldLookup.EQ,
                        right=glue.FieldReferenceExpression(
                            field_reference=glue.FieldReference(
                                field=glue.Field(name=_fk_field),
                                table_name=alias,
                            ),
                        ),
                    )
                    for _db_field, _fk_field in zip(db_fields, fk_pks.keys(), strict=False)
                ]
            )

            joins.append(
                glue.JoinQuery(
                    table=glue.SubQueryStatement(
                        query=_query,
                        alias=alias,
                    ),
                    on=_on_conditions,
                    join_type=glue.JoinType.LEFT,
                ),
            )

        return joins if joins else None

    def build_where(
        self,
        model: type['ModelType'],
        conditions: Q | None,
        select_related: dict[tuple[str, type['ModelType'], str], Any] | None = None,
        *,
        backpropagate_select_related: bool = False,
    ) -> glue.Conditions | None:
        from amsdal_models.querysets.executor import ADDRESS_FIELD
        from amsdal_models.querysets.executor import METADATA_FIELD
        from amsdal_models.querysets.executor import OBJECT_ID_FIELD

        if not conditions:
            return None

        fk_fields = getattr(model, FOREIGN_KEYS, [])
        _conditions: list[glue.Conditions | glue.Condition] = []

        for child in conditions.children:
            if isinstance(child, Q):
                if _cond := self.build_where(
                    model,
                    child,
                    select_related,
                    backpropagate_select_related=backpropagate_select_related,
                ):
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

            if not _rest and _field_name in fk_fields:
                if isinstance(_value, str):
                    try:
                        _ref_data = ReferenceData.from_string(_value)
                        _value = Reference(ref=_ref_data)
                    except Exception as e:
                        msg = f'Failed to parse reference string for field {_field_name}: {_value}'
                        raise ValueError(msg) from e

                if not isinstance(_value, ReferenceableMixin):
                    msg = f'Value for {_field_name} must be a ReferenceableMixin'
                    raise TypeError(msg)

                field_info = model.model_fields[_field_name]
                _model, _db_fields, _ = build_fk_db_fields(_field_name, field_info)
                _object_id = _value.to_reference().ref.object_id

                if isinstance(_object_id, str) or not isinstance(_object_id, Iterable):
                    _object_id = [_object_id]

                _conditions.append(
                    glue.Conditions(
                        *[
                            glue.Condition(
                                left=glue.FieldReferenceExpression(
                                    field_reference=glue.FieldReference(
                                        field=self.build_field(_db_field),
                                        table_name=self.qs_table_name,
                                    ),
                                ),
                                lookup=self._to_glue_lookup(child.lookup),
                                right=glue.Value(value=_fk_value),
                            )
                            for _db_field, _fk_value in zip(_db_fields, _object_id, strict=False)
                        ],
                    ),
                )

                continue

            if isinstance(_value, QueryableMixin):
                new_q = _value.to_query(prefix=f'{child.field_name}__')

                if child.lookup == Lookup.NEQ:
                    new_q = ~new_q

                if _cond := self.build_where(new_q, _select_related, backpropagate_select_related):  # type: ignore[arg-type]
                    _conditions.append(_cond)

                continue

            if _field_name == ADDRESS_FIELD and _rest != OBJECT_ID_FIELD:
                continue

            if _field_name == METADATA_FIELD:
                continue

            if _select_related_key:
                field_name = self._process_nested_rest(_rest, _select_related)
                table_name = _select_related_key[2]
                _build_field = _field_shortcut
            else:
                field_name = child.field_name
                table_name = self.qs_table_name
                _build_field = self.build_field

            normalized_field = self.normalize_primary_key(field_name)

            if isinstance(normalized_field, str):
                if isinstance(_value, list) and len(_value) == 1 and child.lookup != Lookup.IN:
                    _value = _value[0]
                field_value = [(normalized_field, _value)]
            else:
                field_value = zip(normalized_field, _value, strict=False)  # type: ignore[assignment]

            _conditions.extend(
                [
                    glue.Condition(
                        left=glue.FieldReferenceExpression(
                            field_reference=glue.FieldReference(
                                field=_build_field(_db_field),
                                table_name=table_name,
                            ),
                        ),
                        lookup=self._to_glue_lookup(child.lookup),
                        right=glue.Value(value=_pk_value),
                    )
                    for _db_field, _pk_value in field_value
                ]
            )

        if _conditions:
            return glue.Conditions(
                *self._backpropagate_conditions(_conditions, backpropagate_select_related=backpropagate_select_related),
                connector=(
                    {
                        ConnectorEnum.AND: glue.FilterConnector.AND,
                        ConnectorEnum.OR: glue.FilterConnector.OR,
                    }
                )[conditions.connector],
                negated=conditions.negated,
            )

        return None

    def _backpropagate_conditions(
        self,
        conditions: list[glue.Condition | glue.Conditions],
        *,
        backpropagate_select_related: bool = False,
    ) -> list[glue.Condition | glue.Conditions]:
        return [
            self._backpropagate_condition(cond, backpropagate_select_related=backpropagate_select_related)
            for cond in conditions
        ]

    def _backpropagate_condition(
        self,
        condition: glue.Condition | glue.Conditions,
        *,
        backpropagate_select_related: bool = False,
    ) -> glue.Condition | glue.Conditions:
        if isinstance(condition, glue.Conditions):
            return glue.Conditions(
                *self._backpropagate_conditions(
                    condition.children,
                    backpropagate_select_related=backpropagate_select_related,
                ),
                connector=condition.connector,
                negated=condition.negated,
            )

        # Only backpropagate if table is different from main queryset table
        if (
            isinstance(condition.left, glue.FieldReferenceExpression)
            and condition.left.field_reference.table_name != self.qs_table_name
        ):
            _field_reference = condition.left.field_reference
            # For select_related aliases with subquery wrapper, transform field name to match subquery alias
            if backpropagate_select_related and _field_reference.table_name.startswith('sr_'):
                _field_reference.field.name = f'{_field_reference.table_name}__{_field_reference.field.name}'
                _field_reference.table_name = self.qs_table_name
            # For non-select_related or count queries, always backpropagate table name
            elif not _field_reference.table_name.startswith('sr_'):
                _field_reference.table_name = self.qs_table_name
        if (
            isinstance(condition.right, glue.FieldReferenceExpression)
            and condition.right.field_reference.table_name != self.qs_table_name
        ):
            _field_reference = condition.right.field_reference
            # For select_related aliases with subquery wrapper, transform field name to match subquery alias
            if backpropagate_select_related and _field_reference.table_name.startswith('sr_'):
                _field_reference.field.name = f'{_field_reference.table_name}__{_field_reference.field.name}'
                _field_reference.table_name = self.qs_table_name
            # For non-select_related or count queries, always backpropagate table name
            elif not _field_reference.table_name.startswith('sr_'):
                _field_reference.table_name = self.qs_table_name

        return condition

    def build_order_by(self) -> list[glue.OrderByQuery] | None:
        from amsdal_models.querysets.executor import ADDRESS_FIELD
        from amsdal_models.querysets.executor import METADATA_FIELD
        from amsdal_models.querysets.executor import OBJECT_ID_FIELD

        if not self.qs_order_by:
            return None

        order_by = []

        for item in self.qs_order_by:
            field_name = item.field_name

            if '__' in field_name:
                [_field_name, _rest] = field_name.split('__', 1)
            else:
                [_field_name, _rest] = field_name, ''

            if _field_name == ADDRESS_FIELD and _rest != OBJECT_ID_FIELD:
                # Ignore address field in non-lakehouse queries
                logger.warning(
                    'State database supports only ordering by _address__object_id field.  It will be ignored.',
                )
                continue

            if _field_name == METADATA_FIELD:
                logger.warning(
                    'The "_metadata" field is not supported in non-lakehouse queries. It will be ignored.',
                )
                continue

            fields = self.normalize_primary_key(field_name)

            if not isinstance(fields, list):
                fields = [fields]

            order_by.extend(
                [
                    glue.OrderByQuery(
                        field=glue.FieldReference(
                            field=self.build_field(_field),
                            table_name=self.qs_table_name,
                        ),
                        direction=(
                            {
                                OrderDirection.ASC: glue.OrderDirection.ASC,
                                OrderDirection.DESC: glue.OrderDirection.DESC,
                            }
                        )[item.direction],
                    )
                    for _field in fields
                ]
            )
        return order_by

    @classmethod
    def _build_aliased_field_reference(
        cls,
        prop_name: str,
        model: type['ModelType'],
        alias: Callable[[str], str],
        table_name: str | None = None,
    ) -> list[glue.FieldReferenceAliased]:
        model_fks = getattr(model, FOREIGN_KEYS, [])
        _table_name = table_name or cls.build_table_name(model)

        if prop_name in model_fks:
            field_info = model.model_fields[prop_name]
            _, db_fields, _ = build_fk_db_fields(prop_name, field_info)
            _alias, _ = alias('').rsplit('__', 1)

            return [
                glue.FieldReferenceAliased(
                    field=cls.build_field(_db_field),
                    table_name=_table_name,
                    alias=f'{_alias}__{_db_field}',
                )
                for _db_field in db_fields
            ]
        else:
            return [
                glue.FieldReferenceAliased(
                    field=cls.build_field(prop_name),
                    table_name=_table_name,
                    alias=alias(prop_name),
                ),
            ]

    @classmethod
    def _build_nested_only(
        cls,
        select_related: dict[tuple[str, type['ModelType'], str], Any],
    ) -> list[glue.FieldReferenceAliased]:
        only: list[glue.FieldReferenceAliased] = []
        fk_type: type[ModelType]

        for (_, fk_type, alias), nested_select_related in select_related.items():
            _pks = getattr(fk_type, PRIMARY_KEY, None) or list(DEFAULT_PKS.keys())
            _used_fields: list[str] = list(_pks)

            for _pk in _pks:
                only.extend(
                    cls._build_aliased_field_reference(
                        prop_name=_pk,
                        model=fk_type,
                        alias=_separated_fields(alias, _pk),
                        table_name=alias,
                    )
                )

            for prop_name in fk_type.model_fields:
                if prop_name in _used_fields:
                    continue

                _used_fields.append(prop_name)
                _fields = cls._build_aliased_field_reference(
                    prop_name=prop_name,
                    model=fk_type,
                    alias=_separated_fields(alias, prop_name),
                    table_name=alias,
                )

                for _field in _fields:
                    if _field not in only:
                        only.append(_field)

            if nested_select_related:
                for sub_field in cls._build_nested_only(nested_select_related):
                    only.append(
                        glue.FieldReferenceAliased(
                            field=glue.Field(name=sub_field.alias),
                            table_name=alias,
                            alias=f'{alias}__{sub_field.alias}',
                        ),
                    )

        return only
