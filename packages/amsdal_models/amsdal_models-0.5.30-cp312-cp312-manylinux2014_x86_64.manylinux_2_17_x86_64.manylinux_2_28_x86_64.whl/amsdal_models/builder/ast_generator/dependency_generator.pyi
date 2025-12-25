import ast
from _typeshed import Incomplete
from amsdal_models.builder.ast_generator.data_models import DependencyItem as DependencyItem
from amsdal_models.builder.utils import ModelModuleInfo as ModelModuleInfo
from amsdal_utils.models.data_models.core import OptionItemData as OptionItemData
from amsdal_utils.models.enums import ModuleType
from pydantic import BaseModel
from typing import Any, ClassVar, TypeAlias

ModulePathType: TypeAlias = str

class EnumToBuild(BaseModel):
    title: str
    options: list[OptionItemData]

class AstDependencyGenerator:
    _searching_module_ordering: ClassVar[list[ModuleType]]
    _module_type: Incomplete
    _ignore_type_names: set[str]
    _module_path: Incomplete
    _model_module_info: Incomplete
    _dependencies: set[DependencyItem]
    _enums_to_build: list[EnumToBuild]
    def __init__(self, module_type: ModuleType, module_path: ModulePathType, model_module_info: ModelModuleInfo) -> None: ...
    @property
    def ast_module(self) -> ast.Module:
        """
        Generates an AST module for the dependencies.

        Returns:
            ast.Module: The AST module containing the import statements for the dependencies.
        """
    def add_ignore_type_name(self, type_name: str) -> None:
        """
        Ignores some type names and does not add them to the dependencies,
        probably in the case of self-referencing types.

        Args:
            type_name (str): The type name to ignore.

        Returns:
            None
        """
    def add_python_type_dependency(self, python_type: Any, alias: str | None = None) -> None:
        """
        Adds a dependency for a given Python type.

        Args:
            python_type (Any): The Python type to add as a dependency.
            alias (str | None): The alias name for this type

        Returns:
            None
        """
    def add_model_type_dependency(self, model_type_name: str) -> None:
        """
        Adds a dependency for a given model type.

        Args:
            model_type_name (str): The model type to add as a dependency.

        Returns:
            None
        """
    def add_enums_to_build(self, title: str, options: list[OptionItemData]) -> None: ...
    @property
    def ast_enums(self) -> ast.Module:
        """
        Generates an AST module for the enums to build.

        Returns:
            ast.Module: The AST module containing the enum definitions.
        """
    def add_ast_import_node(self, node: ast.Import | ast.ImportFrom) -> None:
        """
        Adds an AST import node to the dependencies.

        Args:
            node (ast.Import | ast.ImportFrom): The AST import node to add.

        Returns:
            None
        """
    def _resolve_model_module_info(self, model_type_name: str) -> ModulePathType | None: ...
