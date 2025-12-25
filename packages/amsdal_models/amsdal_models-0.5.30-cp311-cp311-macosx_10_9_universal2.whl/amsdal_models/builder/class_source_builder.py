from functools import cache
from functools import cached_property
from typing import TypeAlias

from amsdal_utils.models.enums import ModuleType
from amsdal_utils.schemas.schema import ObjectSchema

from amsdal_models.builder.ast_generator.class_generator import AstClassGenerator
from amsdal_models.builder.utils import ModelModuleInfo
from amsdal_models.classes.model import Model
from amsdal_models.classes.model import TypeModel

ModulePathType: TypeAlias = str


class ClassSourceBuilder:
    ast_generator: AstClassGenerator

    def __init__(
        self,
        module_path: ModulePathType,
        schema: ObjectSchema,
        module_type: ModuleType,
        base_class: type[Model | TypeModel] | str,
        dependencies: ModelModuleInfo,
        indent_width: str = ' ' * 4,
    ) -> None:
        self._schema = schema
        self._module_type = module_type
        self._base_class = base_class
        self.ast_generator = AstClassGenerator(
            module_type,
            module_path,
            base_class,
            dependencies,
            indent_width=indent_width,
        )

    @cached_property
    def model_class_source(self) -> str:
        """
        Returns the source code for the model class.

        Returns:
            str: The source code for the model class.
        """
        return self._build_class_source()

    @cached_property
    def dependencies_source(self) -> str:
        """
        Returns the source code for the dependencies.

        Returns:
            str: The source code for the dependencies.
        """
        self._build_class_source()
        return self.ast_generator.dependencies_source

    @cached_property
    def enums_source(self) -> str:
        """
        Returns the source code for the enums.

        Returns:
            str: The source code for the enums.
        """
        self._build_class_source()
        return self.ast_generator.enums_source

    @cache  # noqa: B019
    def _build_class_source(self) -> str:
        self.ast_generator.register_class(self._schema.title, extend_type=self._schema.type)
        self.ast_generator.add_class_data(
            table_name=getattr(self._schema, 'table_name', None),
            primary_key=getattr(self._schema, 'primary_key', None),
            module_type=self._module_type,
            indexed=getattr(self._schema, 'indexed', []),
            unique=getattr(self._schema, 'unique', []),
        )

        for _property_name, _property_config in self._schema.properties.items() if self._schema.properties else []:
            self.ast_generator.add_class_property(
                property_name=_property_name,
                property_config=_property_config,
                is_required=_property_name in self._schema.required,
            )

        for _property_name, _property_config in self._schema.properties.items() if self._schema.properties else []:
            self.ast_generator.add_properties_validators(
                property_name=_property_name,
                property_config=_property_config,
            )

        if self._schema.custom_code:
            self.ast_generator.add_class_custom_code(self._schema.custom_code)

        return self.ast_generator.model_source
