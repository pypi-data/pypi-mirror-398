import ast
import sys
from datetime import date
from datetime import datetime
from functools import partial
from typing import ClassVar
from typing import TypeAlias

import astor  # type: ignore[import-untyped]
import black
import isort
from amsdal_utils.models.enums import ModuleType
from amsdal_utils.schemas.schema import PropertyData
from astor.source_repr import split_lines  # type: ignore[import-untyped]
from astor.string_repr import pretty_string  # type: ignore[import-untyped]

from amsdal_models.builder.ast_generator.data_models import CallAst
from amsdal_models.builder.ast_generator.data_models import CustomCodeAst
from amsdal_models.builder.ast_generator.data_models import NestedPropertyTypeAst
from amsdal_models.builder.ast_generator.data_models import PropertyAst
from amsdal_models.builder.ast_generator.data_models import PropertyListValueAst
from amsdal_models.builder.ast_generator.data_models import PropertyValueAst
from amsdal_models.builder.ast_generator.dependency_generator import AstDependencyGenerator
from amsdal_models.builder.ast_generator.helpers.build_assign_node import build_assign_node
from amsdal_models.builder.ast_generator.helpers.build_validator_node import build_validator_node
from amsdal_models.builder.utils import ModelModuleInfo
from amsdal_models.builder.validator_resolver import ValidatorResolver
from amsdal_models.classes.constants import BASE_OBJECT_TYPE
from amsdal_models.classes.data_models.constraints import UniqueConstraint
from amsdal_models.classes.data_models.indexes import IndexInfo
from amsdal_models.classes.model import Model
from amsdal_models.classes.model import TypeModel

ModulePathType: TypeAlias = str


class AstClassGenerator:
    def __init__(
        self,
        module_type: ModuleType,
        module_path: ModulePathType,
        base_class: type[Model | TypeModel] | str,
        model_module_info: ModelModuleInfo,
        indent_width: str,
    ) -> None:
        self._base_class = base_class
        self._indent_width = indent_width

        if sys.version_info >= (3, 12):
            self._class_definition: ast.ClassDef = ast.ClassDef(
                name='',
                bases=[],
                keywords=[],
                body=[],
                decorator_list=[],
                type_params=[],
            )
        else:
            self._class_definition: ast.ClassDef = ast.ClassDef(
                name='',
                bases=[],
                keywords=[],
                body=[],
                decorator_list=[],
            )

        self._ast_dependency_generator = AstDependencyGenerator(
            module_type=module_type,
            module_path=module_path,
            model_module_info=model_module_info,
        )

    def register_class(self, class_name: str, extend_type: str) -> None:
        """
        Registers a class with the given name and extend type.

        Args:
            class_name (str): The name of the class to register.
            extend_type (str): The type to extend for the class.

        Returns:
            None
        """
        self._ast_dependency_generator.add_ignore_type_name(class_name)

        if extend_type == BASE_OBJECT_TYPE:
            base_name = self._base_class if isinstance(self._base_class, str) else self._base_class.__name__
            self._ast_dependency_generator.add_python_type_dependency(self._base_class)
        else:
            base_name = extend_type
            self._ast_dependency_generator.add_model_type_dependency(extend_type)

        self._class_definition.name = class_name
        self._class_definition.bases.append(ast.Name(id=base_name, ctx=ast.Load()))

    def add_class_data(
        self,
        table_name: str | None,
        primary_key: list[str] | None,
        module_type: ModuleType,
        indexed: list[str],
        unique: list[list[str]],
    ) -> None:
        """
        Adds class data to the AST class definition.

        Args:
            table_name (str): The name of the table.
            primary_key (list[str]): The primary key fields.
            module_type (ModuleType): The schema type of the class.
            indexed (list[str]): List of fields that are indexed.
            unique (list[list[str]]): The fields that are unique.
        """
        self._ast_dependency_generator.add_python_type_dependency(ModuleType)
        self._ast_dependency_generator.add_python_type_dependency(ClassVar)
        self._ast_dependency_generator.add_python_type_dependency(date)
        self._ast_dependency_generator.add_python_type_dependency(datetime)

        if table_name:
            self._class_definition.body.append(
                PropertyAst(
                    name='__table_name__',
                    types=[
                        NestedPropertyTypeAst(
                            root=PropertyValueAst(
                                name=ClassVar.__name__,  # type: ignore[attr-defined]
                            ),
                            child=[PropertyValueAst(name='str')],
                        ),
                    ],
                    value=PropertyValueAst(
                        constant=table_name,
                    ),
                ).ast,
            )

        if primary_key:
            self._class_definition.body.append(
                PropertyAst(
                    name='__primary_key__',
                    types=[
                        NestedPropertyTypeAst(
                            root=PropertyValueAst(
                                name=ClassVar.__name__,  # type: ignore[attr-defined]
                            ),
                            child=[
                                NestedPropertyTypeAst(
                                    root=PropertyValueAst(name=list.__name__),
                                    child=[PropertyValueAst(name='str')],
                                ),
                            ],
                        ),
                    ],
                    value=PropertyListValueAst(
                        elements=[PropertyValueAst(constant=_pk) for _pk in primary_key],
                    ),
                ).ast,
            )

        self._class_definition.body.append(
            PropertyAst(
                name='__module_type__',
                types=[
                    NestedPropertyTypeAst(
                        root=PropertyValueAst(
                            name=ClassVar.__name__,  # type: ignore[attr-defined]
                        ),
                        child=[PropertyValueAst(name='ModuleType')],
                    ),
                ],
                value=PropertyValueAst(
                    attr=('ModuleType', module_type.name),
                ),
            ).ast,
        )

        if indexed:
            self._ast_dependency_generator.add_python_type_dependency(IndexInfo)
            self._class_definition.body.append(
                PropertyAst(
                    name='__indexes__',
                    types=[
                        NestedPropertyTypeAst(
                            root=PropertyValueAst(
                                name=ClassVar.__name__,  # type: ignore[attr-defined]
                            ),
                            child=[
                                NestedPropertyTypeAst(
                                    root=PropertyValueAst(name=list.__name__),
                                    child=[PropertyValueAst(name=IndexInfo.__name__)],
                                ),
                            ],
                        ),
                    ],
                    value=PropertyListValueAst(
                        elements=[
                            CallAst(
                                func_name=IndexInfo.__name__,
                                kwargs={
                                    'name': PropertyValueAst(
                                        constant=f'idx_{self._class_definition.name}_{_idx}'.lower(),
                                    ),
                                    'field': PropertyValueAst(constant=_idx),
                                },
                            )
                            for _idx in indexed
                        ],
                    ),
                ).ast,
            )

        if unique:
            self._ast_dependency_generator.add_python_type_dependency(UniqueConstraint)
            self._class_definition.body.append(
                PropertyAst(
                    name='__constraints__',
                    types=[
                        NestedPropertyTypeAst(
                            root=PropertyValueAst(
                                name=ClassVar.__name__,  # type: ignore[attr-defined]
                            ),
                            child=[
                                NestedPropertyTypeAst(
                                    root=PropertyValueAst(name=list.__name__),
                                    child=[PropertyValueAst(name=UniqueConstraint.__name__)],
                                ),
                            ],
                        ),
                    ],
                    value=PropertyListValueAst(
                        elements=[
                            CallAst(
                                func_name=UniqueConstraint.__name__,
                                kwargs={
                                    'name': PropertyValueAst(
                                        constant=f'unq_{self._class_definition.name}_{"_".join(_unique_fields)}'.lower(),
                                    ),
                                    'fields': PropertyValueAst(constant=_unique_fields),
                                },
                            )
                            for _unique_fields in unique
                        ],
                    ),
                ).ast,
            )

    def add_class_property(
        self,
        property_name: str,
        property_config: PropertyData,
        *,
        is_required: bool,
    ) -> None:
        """
        Adds a property to the AST class definition.

        Args:
            property_name (str): The name of the property to add.
            property_config (PropertyData): The configuration of the property.
            is_required (bool): Whether the property is required.

        Returns:
            None
        """
        property_node = build_assign_node(
            class_name=self._class_definition.name,
            target_name=property_name,
            type_data=property_config,
            ast_dependency_generator=self._ast_dependency_generator,
            is_required=is_required,
            value=property_config.default,
            title=property_config.title,
            db_field=getattr(property_config, 'db_field', None),
            extra=property_config.model_dump(
                include={
                    'storage_class',
                    'storage_kwargs',
                }
            ),
        )

        self._class_definition.body.append(property_node)

    def add_properties_validators(
        self,
        property_name: str,
        property_config: PropertyData,
    ) -> None:
        """
        Adds validators for the given property to the AST class definition.

        Args:
            property_name (str): The name of the property to validate.
            property_config (PropertyData): The configuration of the property.

        Returns:
            None
        """
        for (
            _method_name,
            _validator,
            _values,
        ) in sorted(ValidatorResolver.process_property(property_name, property_config)):
            self._class_definition.body.append(
                build_validator_node(
                    prop_name=property_name,
                    validator_name=_method_name,
                    validator=_validator,
                    options=_values,
                    ast_dependency_generator=self._ast_dependency_generator,
                ),
            )

    def add_class_custom_code(self, custom_code: str) -> None:
        """
        Adds custom code to the AST class definition.

        Args:
            custom_code (str): The custom code to add.

        Returns:
            None
        """
        custom_code_ast = CustomCodeAst(custom_code=custom_code)

        for node in custom_code_ast.ast_imports:
            self._ast_dependency_generator.add_ast_import_node(node)

        for node in sorted(custom_code_ast.ast, key=lambda _node: getattr(_node, 'name', '')):
            self._class_definition.body.append(node)

    @property
    def model_source(self) -> str:
        """
        Generates the source code for the model.

        Returns:
            str: The formatted source code of the model.
        """
        source = astor.to_source(
            self._class_definition,
            indent_with=self._indent_width,
            pretty_string=partial(pretty_string, max_line=120),
            pretty_source=lambda _source: ''.join(split_lines(_source, maxline=120)),
        )

        # black formats the code
        return black.format_str(
            source,
            mode=black.FileMode(
                string_normalization=False,
                target_versions={black.TargetVersion.PY310},  # type: ignore[attr-defined]
                line_length=120,
            ),
        )

    @property
    def enums_source(self) -> str:
        """
        Generates the source code for the enums.
        Returns:
            str: The formatted source code of the enums.
        """
        source = astor.to_source(
            self._ast_dependency_generator.ast_enums,
            pretty_string=partial(pretty_string, max_line=120),
            pretty_source=lambda _source: ''.join(split_lines(_source, maxline=120)),
        )

        return isort.code(
            source,
            force_single_line=True,
            profile='black',
            line_length=120,
            order_by_type=True,
            known_third_party=[
                'amsdal_utils',
                'amsdal_data',
                'amsdal_models',
                'amsdal',
            ],
            known_first_party=[
                'models',
            ],
        )

    @property
    def dependencies_source(self) -> str:
        """
        Generates the source code for the dependencies.

        Returns:
            str: The formatted source code of the dependencies.
        """
        source = astor.to_source(
            self._ast_dependency_generator.ast_module,
            pretty_string=partial(pretty_string, max_line=120),
            pretty_source=lambda _source: ''.join(split_lines(_source, maxline=120)),
        )

        return isort.code(
            source,
            force_single_line=True,
            profile='black',
            line_length=120,
            order_by_type=True,
            known_third_party=[
                'amsdal_utils',
                'amsdal_data',
                'amsdal_models',
                'amsdal',
            ],
            known_first_party=[
                'models',
            ],
        )
