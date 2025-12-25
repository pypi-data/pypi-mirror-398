import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from typing import TypeAlias
from typing import Union

from amsdal_utils.models.data_models.enums import MetaClasses
from amsdal_utils.models.enums import ModuleType
from amsdal_utils.schemas.schema import ObjectSchema
from amsdal_utils.utils.text import to_snake_case

from amsdal_models.builder.class_source_builder import ClassSourceBuilder
from amsdal_models.builder.utils import ModelModuleInfo

if TYPE_CHECKING:
    from amsdal_models.classes.model import Model
    from amsdal_models.classes.model import TypeModel

ModulePathType: TypeAlias = str
ClassNameType: TypeAlias = str


class ClassBuilder:
    def build(
        self,
        models_package_path: Path,
        models_module_path: ModulePathType,
        object_schema: ObjectSchema,
        module_type: ModuleType,
        dependencies: ModelModuleInfo,
        indent_width: str = ' ' * 4,
    ) -> None:
        package_dir: Path = self._check_models_path_is_package(models_package_path)

        class_source_builder = ClassSourceBuilder(
            module_path=models_module_path,
            schema=object_schema,
            module_type=module_type,
            base_class=self._resolve_base_class_for_schema(object_schema),
            dependencies=dependencies,
            indent_width=indent_width,
        )
        self._write_model(
            module_path=package_dir / f'{to_snake_case(object_schema.title)}.py',
            class_source_builder=class_source_builder,
        )

    @staticmethod
    def _check_models_path_is_package(models_package_path: Path) -> Path:
        if not models_package_path.exists():
            msg = f'The {models_package_path} either does not exist'
            raise RuntimeError(msg)

        if models_package_path.is_file():
            msg = f'The {models_package_path} should be python package instead of module/file.'
            raise RuntimeError(msg)

        if not (models_package_path / '__init__.py').exists():
            msg = f'The {models_package_path} should be python package and should contain __init__.py'
            raise RuntimeError(msg)

        return models_package_path

    @staticmethod
    def _resolve_base_class_for_schema(schema: ObjectSchema) -> type[Union['Model', 'TypeModel']]:
        """
        Resolves the base class for the given schema.

        Args:
            schema (ObjectSchema): The schema to resolve the base class for.

        Returns:
            type[Union['Model', 'TypeModel']]: The resolved base class.

        Raises:
            ValueError: If the schema's meta class is invalid.
        """
        if schema.meta_class == MetaClasses.CLASS_OBJECT.value:
            from amsdal_models.classes.model import Model

            return Model
        else:
            from amsdal_models.classes.model import TypeModel

            return TypeModel

    @staticmethod
    def _write_model(module_path: Path, class_source_builder: ClassSourceBuilder) -> None:
        source = (
            f'{class_source_builder.dependencies_source}\n\n'
            f'{class_source_builder.enums_source}\n\n'
            f'{class_source_builder.model_class_source}'
        )
        module_path.write_text(source)

        subprocess.run(  # noqa: S603
            [  # noqa: S607
                'ruff',
                'check',
                '--fix',
                '--select',
                'F401',
                '--fixable',
                'F401',
                '-s',
                str(module_path.absolute()),
            ],
            check=False,
        )
