import ast
from _typeshed import Incomplete
from amsdal_models.builder.ast_generator.dependency_generator import AstDependencyGenerator as AstDependencyGenerator
from amsdal_models.builder.ast_generator.helpers.build_annotation_node import build_annotation_node as build_annotation_node
from amsdal_models.classes.relationships.reference_field import ReferenceField as ReferenceField
from amsdal_utils.models.data_models.core import TypeData
from collections.abc import Iterable
from typing import Any

class UNSET: ...

_EXPECTED_KEYWORDS: Incomplete
_JSON_SCHEMA_EXTRA_KEYWORDS: Incomplete
_KEYWORDS_MAPPING: Incomplete

def build_assign_node(class_name: str, target_name: str, type_data: TypeData, ast_dependency_generator: AstDependencyGenerator, value: Any = ..., *, is_required: bool = True, can_be_a_reference: bool = True, title: str | None = None, db_field: str | Iterable[str] | None, extra: dict[str, Any] | None = None) -> ast.AnnAssign | ast.stmt:
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
def cast_property_value(type_data: TypeData, property_value: Any) -> Any:
    """
    Casts a property value to its corresponding AST node based on the type data.

    Args:
        type_data (TypeData): The type data for the property.
        property_value (Any): The value to cast.

    Returns:
        Any: The AST node representing the casted property value.
    """
def cast_number_value(property_value: Any) -> int | float:
    """
    Casts a property value to an integer or float.

    Args:
        property_value (Any): The value to cast.

    Returns:
        int | float: The casted number value.

    Raises:
        ValueError: If the property value cannot be casted to a number.
    """
def cast_integer_value(property_value: Any) -> int:
    """
    Casts a property value to an integer.

    Args:
        property_value (Any): The value to cast.

    Returns:
        int: The casted integer value.

    Raises:
        ValueError: If the property value cannot be casted to an integer.
    """
