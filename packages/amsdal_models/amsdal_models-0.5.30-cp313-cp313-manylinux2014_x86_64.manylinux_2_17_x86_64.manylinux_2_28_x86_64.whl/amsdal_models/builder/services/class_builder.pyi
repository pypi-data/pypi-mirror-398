from amsdal_models.builder.class_source_builder import ClassSourceBuilder as ClassSourceBuilder
from amsdal_models.builder.utils import ModelModuleInfo as ModelModuleInfo
from amsdal_models.classes.model import Model as Model, TypeModel as TypeModel
from amsdal_utils.models.enums import ModuleType as ModuleType
from amsdal_utils.schemas.schema import ObjectSchema as ObjectSchema
from pathlib import Path
from typing import TypeAlias

ModulePathType: TypeAlias = str
ClassNameType: TypeAlias = str

class ClassBuilder:
    def build(self, models_package_path: Path, models_module_path: ModulePathType, object_schema: ObjectSchema, module_type: ModuleType, dependencies: ModelModuleInfo, indent_width: str = ...) -> None: ...
    @staticmethod
    def _check_models_path_is_package(models_package_path: Path) -> Path: ...
    @staticmethod
    def _resolve_base_class_for_schema(schema: ObjectSchema) -> type[Model | TypeModel]:
        """
        Resolves the base class for the given schema.

        Args:
            schema (ObjectSchema): The schema to resolve the base class for.

        Returns:
            type[Union['Model', 'TypeModel']]: The resolved base class.

        Raises:
            ValueError: If the schema's meta class is invalid.
        """
    @staticmethod
    def _write_model(module_path: Path, class_source_builder: ClassSourceBuilder) -> None: ...
