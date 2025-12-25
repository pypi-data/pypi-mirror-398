import ast
from enum import Enum
from typing import Literal
from typing import Optional

from amsdal_utils.models.data_models.core import DictSchema
from amsdal_utils.models.data_models.core import LegacyDictSchema
from amsdal_utils.models.data_models.core import TypeData
from amsdal_utils.models.data_models.enums import CoreTypes

from amsdal_models.builder.ast_generator.dependency_generator import AstDependencyGenerator
from amsdal_models.classes.constants import BASIC_TYPES_MAP


def build_annotation_node(
    type_data: TypeData,
    ast_dependency_generator: AstDependencyGenerator,
    *,
    current_class_name: str = '',
    is_required: bool = True,
    can_be_a_reference: bool = True,
) -> ast.Subscript | ast.Constant | ast.Name | ast.BinOp:
    """
    Builds an AST node for type annotations.

    Args:
        type_data (TypeData): The type data for the annotation.
        current_class_name (str): The name of current class. Used to avoid importing the same class.
        is_required (bool, optional): Whether the type is required. Defaults to True.
        can_be_a_reference (bool, optional): Whether the type can be a reference. Defaults to True.
        ast_dependency_generator (AstDependencyGenerator): The AST dependency generator.

    Returns:
        ast.Subscript | ast.Constant | ast.Name | ast.BinOp: The AST node representing the type annotation.
    """
    _property_type = type_data.type.lower()

    if not is_required:
        ast_dependency_generator.add_python_type_dependency(Optional)

        return ast.Subscript(
            value=ast.Name(
                id=Optional.__name__,  # type: ignore[attr-defined]
                ctx=ast.Load(),
            ),
            slice=build_annotation_node(
                type_data,
                ast_dependency_generator=ast_dependency_generator,
                current_class_name=current_class_name,
                can_be_a_reference=can_be_a_reference,
                is_required=True,
            ),
            ctx=ast.Load(),
        )

    if _property_type == CoreTypes.ARRAY.value:
        if isinstance(type_data.items, TypeData):
            return ast.Subscript(
                value=ast.Name(id='list', ctx=ast.Load()),
                slice=build_annotation_node(
                    type_data.items,
                    ast_dependency_generator=ast_dependency_generator,
                    current_class_name=current_class_name,
                    can_be_a_reference=can_be_a_reference,
                ),
                ctx=ast.Load(),
            )

    if _property_type == CoreTypes.DICTIONARY.value:
        if isinstance(type_data.items, DictSchema):
            return ast.Subscript(
                value=ast.Name(id='dict', ctx=ast.Load()),
                slice=ast.Tuple(
                    elts=[
                        build_annotation_node(
                            type_data.items.key,
                            ast_dependency_generator=ast_dependency_generator,
                            current_class_name=current_class_name,
                            can_be_a_reference=can_be_a_reference,
                        ),
                        build_annotation_node(
                            type_data.items.value,
                            ast_dependency_generator=ast_dependency_generator,
                            current_class_name=current_class_name,
                            is_required=False,
                            can_be_a_reference=can_be_a_reference,
                        ),
                    ],
                    ctx=ast.Load(),
                ),
                ctx=ast.Load(),
            )
        elif isinstance(type_data.items, LegacyDictSchema):
            return ast.Subscript(
                value=ast.Name(id='dict', ctx=ast.Load()),
                slice=ast.Tuple(
                    elts=[
                        build_annotation_node(
                            TypeData(type=type_data.items.key_type),
                            ast_dependency_generator=ast_dependency_generator,
                            current_class_name=current_class_name,
                            can_be_a_reference=can_be_a_reference,
                        ),
                        build_annotation_node(
                            TypeData(type=type_data.items.value_type),
                            ast_dependency_generator=ast_dependency_generator,
                            current_class_name=current_class_name,
                            is_required=False,
                            can_be_a_reference=can_be_a_reference,
                        ),
                    ],
                    ctx=ast.Load(),
                ),
                ctx=ast.Load(),
            )
        else:
            msg = f'Unknown dictionary type: "{type_data.items.__class__.__name__}"'
            raise ValueError(msg)

    try:
        if CoreTypes(_property_type) in BASIC_TYPES_MAP:
            type_object = BASIC_TYPES_MAP[CoreTypes(_property_type)]
            ast_dependency_generator.add_python_type_dependency(type_object)

            if type_data.options:
                ast_dependency_generator.add_python_type_dependency(Literal)
                # literal
                return ast.Subscript(
                    value=ast.Name(id='Literal', ctx=ast.Load()),
                    slice=ast.Tuple(
                        elts=[ast.Constant(value=option.value) for option in type_data.options],
                        ctx=ast.Load(),
                    ),
                    ctx=ast.Load(),
                )

            return ast.Name(
                id=type_object.__name__,
                ctx=ast.Load(),
            )
    except ValueError:
        ...

    if current_class_name != type_data.type:
        if type_data.options and getattr(type_data, 'title', None):
            ast_dependency_generator.add_enums_to_build(
                title=type_data.title,  # type: ignore[attr-defined]
                options=type_data.options,
            )
            ast_dependency_generator.add_python_type_dependency(Enum)
        else:
            ast_dependency_generator.add_model_type_dependency(type_data.type)

    return ast.Constant(value=type_data.type)
