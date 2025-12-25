import ast
from _typeshed import Incomplete
from amsdal_models.builder.ast_generator.data_models import CallAst as CallAst, CustomCodeAst as CustomCodeAst, NestedPropertyTypeAst as NestedPropertyTypeAst, PropertyAst as PropertyAst, PropertyListValueAst as PropertyListValueAst, PropertyValueAst as PropertyValueAst
from amsdal_models.builder.ast_generator.dependency_generator import AstDependencyGenerator as AstDependencyGenerator
from amsdal_models.builder.ast_generator.helpers.build_assign_node import build_assign_node as build_assign_node
from amsdal_models.builder.ast_generator.helpers.build_validator_node import build_validator_node as build_validator_node
from amsdal_models.builder.utils import ModelModuleInfo as ModelModuleInfo
from amsdal_models.builder.validator_resolver import ValidatorResolver as ValidatorResolver
from amsdal_models.classes.constants import BASE_OBJECT_TYPE as BASE_OBJECT_TYPE
from amsdal_models.classes.data_models.constraints import UniqueConstraint as UniqueConstraint
from amsdal_models.classes.data_models.indexes import IndexInfo as IndexInfo
from amsdal_models.classes.model import Model as Model, TypeModel as TypeModel
from amsdal_utils.models.enums import ModuleType
from amsdal_utils.schemas.schema import PropertyData as PropertyData
from typing import TypeAlias

ModulePathType: TypeAlias = str

class AstClassGenerator:
    _base_class: Incomplete
    _indent_width: Incomplete
    _class_definition: ast.ClassDef
    _ast_dependency_generator: Incomplete
    def __init__(self, module_type: ModuleType, module_path: ModulePathType, base_class: type[Model | TypeModel] | str, model_module_info: ModelModuleInfo, indent_width: str) -> None: ...
    def register_class(self, class_name: str, extend_type: str) -> None:
        """
        Registers a class with the given name and extend type.

        Args:
            class_name (str): The name of the class to register.
            extend_type (str): The type to extend for the class.

        Returns:
            None
        """
    def add_class_data(self, table_name: str | None, primary_key: list[str] | None, module_type: ModuleType, indexed: list[str], unique: list[list[str]]) -> None:
        """
        Adds class data to the AST class definition.

        Args:
            table_name (str): The name of the table.
            primary_key (list[str]): The primary key fields.
            module_type (ModuleType): The schema type of the class.
            indexed (list[str]): List of fields that are indexed.
            unique (list[list[str]]): The fields that are unique.
        """
    def add_class_property(self, property_name: str, property_config: PropertyData, *, is_required: bool) -> None:
        """
        Adds a property to the AST class definition.

        Args:
            property_name (str): The name of the property to add.
            property_config (PropertyData): The configuration of the property.
            is_required (bool): Whether the property is required.

        Returns:
            None
        """
    def add_properties_validators(self, property_name: str, property_config: PropertyData) -> None:
        """
        Adds validators for the given property to the AST class definition.

        Args:
            property_name (str): The name of the property to validate.
            property_config (PropertyData): The configuration of the property.

        Returns:
            None
        """
    def add_class_custom_code(self, custom_code: str) -> None:
        """
        Adds custom code to the AST class definition.

        Args:
            custom_code (str): The custom code to add.

        Returns:
            None
        """
    @property
    def model_source(self) -> str:
        """
        Generates the source code for the model.

        Returns:
            str: The formatted source code of the model.
        """
    @property
    def enums_source(self) -> str:
        """
        Generates the source code for the enums.
        Returns:
            str: The formatted source code of the enums.
        """
    @property
    def dependencies_source(self) -> str:
        """
        Generates the source code for the dependencies.

        Returns:
            str: The formatted source code of the dependencies.
        """
