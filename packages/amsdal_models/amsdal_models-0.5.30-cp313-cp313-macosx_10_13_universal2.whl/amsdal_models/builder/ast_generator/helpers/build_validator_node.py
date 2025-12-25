import ast
import sys
from collections.abc import Callable
from datetime import date
from datetime import datetime
from typing import Any

from pydantic import field_validator

from amsdal_models.builder.ast_generator.dependency_generator import AstDependencyGenerator


def build_validator_node(
    prop_name: str,
    validator_name: str,
    ast_dependency_generator: AstDependencyGenerator,
    validator: Callable[[type, Any], Any],
    options: list[Any] | None = None,
) -> ast.FunctionDef | ast.stmt:
    """
    Builds an AST node for a validator function.

    Args:
        prop_name (str): The name of the property to validate.
        validator_name (str): The name of the validator function.
        ast_dependency_generator (AstDependencyGenerator): The AST dependency generator.
        validator (Callable[[type, Any], Any]): The validator function.
        options (list[Any] | None, optional): Additional options for the validator. Defaults to None.

    Returns:
        ast.FunctionDef | ast.stmt: The AST node representing the validator function.
    """
    call_kwargs = []

    if options:
        call_kwargs.append(
            ast.keyword(
                arg='options',
                value=ast.List(
                    elts=[ast.Constant(value=option) for option in options],
                    ctx=ast.Load(),
                ),
            ),
        )

    ast_dependency_generator.add_python_type_dependency(date)
    ast_dependency_generator.add_python_type_dependency(datetime)
    ast_dependency_generator.add_python_type_dependency(Any)
    ast_dependency_generator.add_python_type_dependency(field_validator)
    ast_dependency_generator.add_python_type_dependency(validator)

    if sys.version_info >= (3, 12):
        return ast.FunctionDef(
            name=validator_name,
            args=ast.arguments(
                posonlyargs=[],
                args=[
                    ast.arg(arg='cls', annotation=ast.Name(id=type.__name__, ctx=ast.Load())),
                    ast.arg(
                        arg='value',
                        annotation=ast.Name(
                            id='Any',
                            ctx=ast.Load(),
                        ),
                    ),
                ],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
            ),
            body=[
                ast.Return(
                    value=ast.Call(
                        func=ast.Name(id=validator.__name__, ctx=ast.Load()),
                        args=[ast.Name(id='value', ctx=ast.Load())],
                        keywords=call_kwargs,
                    ),
                ),
            ],
            decorator_list=[
                ast.Call(
                    func=ast.Name(id=field_validator.__name__, ctx=ast.Load()),
                    args=[ast.Constant(value=prop_name)],
                    keywords=[],
                ),
                ast.Name(id=classmethod.__name__, ctx=ast.Load()),
            ],
            returns=ast.Name(
                id='Any',
                ctx=ast.Load(),
            ),
            type_params=[],
        )
    else:
        return ast.FunctionDef(
            name=validator_name,
            args=ast.arguments(
                posonlyargs=[],
                args=[
                    ast.arg(arg='cls', annotation=ast.Name(id=type.__name__, ctx=ast.Load())),
                    ast.arg(
                        arg='value',
                        annotation=ast.Name(
                            id='Any',
                            ctx=ast.Load(),
                        ),
                    ),
                ],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
            ),
            body=[
                ast.Return(
                    value=ast.Call(
                        func=ast.Name(id=validator.__name__, ctx=ast.Load()),
                        args=[ast.Name(id='value', ctx=ast.Load())],
                        keywords=call_kwargs,
                    ),
                ),
            ],
            decorator_list=[
                ast.Call(
                    func=ast.Name(id=field_validator.__name__, ctx=ast.Load()),
                    args=[ast.Constant(value=prop_name)],
                    keywords=[],
                ),
                ast.Name(id=classmethod.__name__, ctx=ast.Load()),
            ],
            returns=ast.Name(
                id='Any',
                ctx=ast.Load(),
            ),
        )
