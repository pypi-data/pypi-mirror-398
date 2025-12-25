import ast
from collections.abc import Iterable
from typing import Any

from amsdal_utils.models.data_models.core import DictSchema
from amsdal_utils.models.data_models.core import LegacyDictSchema
from amsdal_utils.models.data_models.core import TypeData
from amsdal_utils.models.data_models.enums import CoreTypes
from amsdal_utils.models.data_models.reference import Reference
from pydantic import Field

from amsdal_models.builder.ast_generator.dependency_generator import AstDependencyGenerator
from amsdal_models.builder.ast_generator.helpers.build_annotation_node import build_annotation_node
from amsdal_models.classes.relationships.reference_field import ReferenceField


class UNSET: ...


_EXPECTED_KEYWORDS = [
    'minimum',
    'maximum',
    'exclusive_minimum',
    'exclusive_maximum',
    'multiple_of',
    'min_length',
    'max_length',
    'pattern',
]

_JSON_SCHEMA_EXTRA_KEYWORDS = [
    'to_lower',
    'to_upper',
]


_KEYWORDS_MAPPING = {
    'minimum': 'ge',
    'maximum': 'le',
    'exclusive_minimum': 'gt',
    'exclusive_maximum': 'lt',
}


def build_assign_node(
    class_name: str,
    target_name: str,
    type_data: TypeData,
    ast_dependency_generator: AstDependencyGenerator,
    value: Any = UNSET,
    *,
    is_required: bool = True,
    can_be_a_reference: bool = True,
    title: str | None = None,
    db_field: str | Iterable[str] | None,
    extra: dict[str, Any] | None = None,
) -> ast.AnnAssign | ast.stmt:
    """
    Builds an AST node for an assignment with type annotations.

    Args:
        class_name (str): The name of current class. Used to avoid importing the same class.
        target_name (str): The name of the target variable.
        type_data (TypeData): The type data for the annotation.
        value (Any, optional): The value to assign. Defaults to UNSET.
        is_required (bool, optional): Whether the type is required. Defaults to True.
        can_be_a_reference (bool, optional): Whether the type can be a reference. Defaults to True.
        ast_dependency_generator (AstDependencyGenerator): The AST dependency generator.
        title (str | None, optional): The title of the field. Defaults to None.
        db_field (str | Iterable[str] | None, optional): The name of the database field. Defaults to None.
        extra (dict[str, Any] | None, optional): Additional properties. Defaults to None.

    Returns:
        ast.AnnAssign | ast.stmt: The AST node representing the assignment.
    """
    props: dict[str, Any] = {
        'target': ast.Name(id=target_name, ctx=ast.Store()),
        'annotation': build_annotation_node(
            type_data,
            ast_dependency_generator=ast_dependency_generator,
            current_class_name=class_name,
            is_required=is_required,
            can_be_a_reference=can_be_a_reference,
        ),
        'simple': 1,
    }

    if value != UNSET and (value is not None or not is_required):
        props['value'] = cast_property_value(
            type_data,
            value,
        )

    title = title or target_name

    ast_dependency_generator.add_python_type_dependency(Reference)
    ast_dependency_generator.add_python_type_dependency(Field)

    if 'value' in props:
        _args = [props['value']]
    else:
        _args = []

    keywords = [ast.keyword(arg='title', value=ast.Constant(value=title))]

    for keyword in _EXPECTED_KEYWORDS:
        if hasattr(type_data, keyword):
            keywords.append(
                ast.keyword(
                    arg=_KEYWORDS_MAPPING.get(keyword, keyword),
                    value=ast.Constant(value=getattr(type_data, keyword)),
                )
            )

    _json_schema_extra_keywords = {**(extra or {})}

    for keyword in _JSON_SCHEMA_EXTRA_KEYWORDS:
        if hasattr(type_data, keyword):
            _json_schema_extra_keywords[keyword] = getattr(type_data, keyword)

    if _json_schema_extra_keywords:
        keywords.append(
            ast.keyword(
                arg='json_schema_extra',
                value=ast.Constant(value=_json_schema_extra_keywords),  # type: ignore[arg-type]
            ),
        )

    if db_field:
        if isinstance(db_field, str):
            _value = ast.Constant(value=db_field)
        else:
            _value = ast.List(  # type: ignore[assignment]
                elts=[ast.Constant(value=value) for value in db_field],
            )
        keywords.append(ast.keyword(arg='db_field', value=_value))
        props['value'] = ast.Call(
            func=ast.Name(id=ReferenceField.__name__, ctx=ast.Load()),
            args=_args,
            keywords=keywords,
        )
        ast_dependency_generator.add_python_type_dependency(ReferenceField)
    else:
        props['value'] = ast.Call(
            func=ast.Name(id=Field.__name__, ctx=ast.Load()),
            args=_args,
            keywords=keywords,
        )

    return ast.AnnAssign(**props)


def cast_property_value(
    type_data: TypeData,
    property_value: Any,
) -> Any:
    """
    Casts a property value to its corresponding AST node based on the type data.

    Args:
        type_data (TypeData): The type data for the property.
        property_value (Any): The value to cast.

    Returns:
        Any: The AST node representing the casted property value.
    """
    property_type = type_data.type.lower()

    if property_value is None:
        return ast.Constant(value=property_value)

    if property_type == CoreTypes.STRING.value:
        return ast.Constant(value=property_value)
    elif property_type == CoreTypes.NUMBER.value:
        return ast.Constant(value=cast_number_value(property_value))
    elif property_type == CoreTypes.INTEGER.value:
        return ast.Constant(value=cast_integer_value(property_value))
    elif property_type == CoreTypes.BOOLEAN.value:
        return ast.Constant(value=bool(property_value))
    elif property_type == CoreTypes.BINARY.value:
        return ast.Constant(value=bytes(property_value))
    elif property_type == CoreTypes.ARRAY.value and type_data.items is not None:
        if isinstance(type_data.items, TypeData):
            return ast.List(
                elts=[
                    cast_property_value(
                        type_data.items,
                        value,
                    )
                    for value in property_value
                ],
            )
    elif property_type == CoreTypes.DICTIONARY.value and type_data.items is not None:
        if isinstance(type_data.items, LegacyDictSchema):
            return ast.Dict(
                keys=[
                    cast_property_value(
                        TypeData(type=type_data.items.key_type),
                        key,
                    )
                    for key in property_value
                ],
                values=[
                    cast_property_value(
                        TypeData(type=type_data.items.value_type),
                        val,
                    )
                    for val in property_value.values()
                ],
            )
        elif isinstance(type_data.items, DictSchema):
            return ast.Dict(
                keys=[
                    cast_property_value(
                        TypeData(type=type_data.items.key.type),
                        key,
                    )
                    for key in property_value
                ],
                values=[
                    cast_property_value(
                        TypeData(type=type_data.items.value.type),
                        val,
                    )
                    for val in property_value.values()
                ],
            )
        else:
            return ast.Name(id=property_value, ctx=ast.Load())


def cast_number_value(
    property_value: Any,
) -> int | float:
    """
    Casts a property value to an integer or float.

    Args:
        property_value (Any): The value to cast.

    Returns:
        int | float: The casted number value.

    Raises:
        ValueError: If the property value cannot be casted to a number.
    """
    error_msg = f'Cannot cast {property_value} to a number'

    if isinstance(property_value, int):
        return property_value
    elif isinstance(property_value, float):
        return property_value
    elif isinstance(property_value, str):
        try:
            if '.' in property_value:
                return float(property_value)
            return int(property_value)
        except ValueError as err:
            raise ValueError(error_msg) from err
    else:
        raise ValueError(error_msg)


def cast_integer_value(
    property_value: Any,
) -> int:
    """
    Casts a property value to an integer.

    Args:
        property_value (Any): The value to cast.

    Returns:
        int: The casted integer value.

    Raises:
        ValueError: If the property value cannot be casted to an integer.
    """
    error_msg = f'Cannot cast {property_value} to an integer'

    if isinstance(property_value, int):
        return property_value
    elif isinstance(property_value, str):
        try:
            return int(property_value)
        except ValueError as err:
            raise ValueError(error_msg) from err
    else:
        raise ValueError(error_msg)
