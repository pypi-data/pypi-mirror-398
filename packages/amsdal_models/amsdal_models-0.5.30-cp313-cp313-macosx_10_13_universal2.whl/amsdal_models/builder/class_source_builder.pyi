from _typeshed import Incomplete
from amsdal_models.builder.ast_generator.class_generator import AstClassGenerator as AstClassGenerator
from amsdal_models.builder.utils import ModelModuleInfo as ModelModuleInfo
from amsdal_models.classes.model import Model as Model, TypeModel as TypeModel
from amsdal_utils.models.enums import ModuleType as ModuleType
from amsdal_utils.schemas.schema import ObjectSchema as ObjectSchema
from functools import cache, cached_property as cached_property
from typing import TypeAlias

ModulePathType: TypeAlias = str

class ClassSourceBuilder:
    ast_generator: AstClassGenerator
    _schema: Incomplete
    _module_type: Incomplete
    _base_class: Incomplete
    def __init__(self, module_path: ModulePathType, schema: ObjectSchema, module_type: ModuleType, base_class: type[Model | TypeModel] | str, dependencies: ModelModuleInfo, indent_width: str = ...) -> None: ...
    @cached_property
    def model_class_source(self) -> str:
        """
        Returns the source code for the model class.

        Returns:
            str: The source code for the model class.
        """
    @cached_property
    def dependencies_source(self) -> str:
        """
        Returns the source code for the dependencies.

        Returns:
            str: The source code for the dependencies.
        """
    @cached_property
    def enums_source(self) -> str:
        """
        Returns the source code for the enums.

        Returns:
            str: The source code for the enums.
        """
    @cache
    def _build_class_source(self) -> str: ...
