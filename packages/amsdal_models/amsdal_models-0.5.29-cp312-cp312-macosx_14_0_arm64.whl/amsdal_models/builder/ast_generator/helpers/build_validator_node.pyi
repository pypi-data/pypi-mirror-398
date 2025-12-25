import ast
from amsdal_models.builder.ast_generator.dependency_generator import AstDependencyGenerator as AstDependencyGenerator
from collections.abc import Callable as Callable
from typing import Any

def build_validator_node(prop_name: str, validator_name: str, ast_dependency_generator: AstDependencyGenerator, validator: Callable[[type, Any], Any], options: list[Any] | None = None) -> ast.FunctionDef | ast.stmt:
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
