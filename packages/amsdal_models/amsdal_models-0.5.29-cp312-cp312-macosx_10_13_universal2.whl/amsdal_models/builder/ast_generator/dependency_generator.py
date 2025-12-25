import ast
import sys
from typing import Any
from typing import ClassVar
from typing import TypeAlias

from amsdal_utils.models.data_models.core import OptionItemData
from amsdal_utils.models.enums import ModuleType
from amsdal_utils.utils.text import to_snake_case
from pydantic import BaseModel

from amsdal_models.builder.ast_generator.data_models import DependencyItem
from amsdal_models.builder.utils import ModelModuleInfo

ModulePathType: TypeAlias = str


class EnumToBuild(BaseModel):
    title: str
    options: list[OptionItemData]


class AstDependencyGenerator:
    _searching_module_ordering: ClassVar[list[ModuleType]] = [
        ModuleType.USER,
        ModuleType.CONTRIB,
        ModuleType.CORE,
        ModuleType.TYPE,
    ]

    def __init__(
        self,
        module_type: ModuleType,
        module_path: ModulePathType,
        model_module_info: ModelModuleInfo,
    ) -> None:
        self._module_type = module_type
        self._ignore_type_names: set[str] = set()
        self._module_path = module_path
        self._model_module_info = model_module_info
        self._dependencies: set[DependencyItem] = set()
        self._enums_to_build: list[EnumToBuild] = []

    @property
    def ast_module(self) -> ast.Module:
        """
        Generates an AST module for the dependencies.

        Returns:
            ast.Module: The AST module containing the import statements for the dependencies.
        """
        module = ast.Module(body=[], type_ignores=[])

        for dependency in self._dependencies:
            _module, _name, _as_name = dependency.module

            if _module is None:
                module.body.append(
                    ast.Import(
                        names=[ast.alias(name=_name, asname=_as_name)],
                    ),
                )
            else:
                module.body.append(
                    ast.ImportFrom(
                        module=_module,
                        names=[ast.alias(name=_name, asname=_as_name)],
                        level=0,
                    ),
                )
        return module

    def add_ignore_type_name(self, type_name: str) -> None:
        """
        Ignores some type names and does not add them to the dependencies,
        probably in the case of self-referencing types.

        Args:
            type_name (str): The type name to ignore.

        Returns:
            None
        """
        self._ignore_type_names.add(type_name)

    def add_python_type_dependency(self, python_type: Any, alias: str | None = None) -> None:
        """
        Adds a dependency for a given Python type.

        Args:
            python_type (Any): The Python type to add as a dependency.
            alias (str | None): The alias name for this type

        Returns:
            None
        """
        if python_type.__module__ == 'builtins':
            # We do not need to import builtins
            return

        self._dependencies.add(
            DependencyItem(module=(python_type.__module__, python_type.__name__, alias)),
        )

    def add_model_type_dependency(self, model_type_name: str) -> None:
        """
        Adds a dependency for a given model type.

        Args:
            model_type_name (str): The model type to add as a dependency.

        Returns:
            None
        """
        if model_type_name in self._ignore_type_names:
            return

        model_module_path = self._resolve_model_module_info(model_type_name)

        if not model_module_path:
            return

        self._dependencies.add(
            DependencyItem(
                module=(
                    f'{model_module_path}.{to_snake_case(model_type_name)}',
                    '*',
                    None,
                )
            ),
        )

    def add_enums_to_build(self, title: str, options: list[OptionItemData]) -> None:
        if title in [enum.title for enum in self._enums_to_build]:
            return

        self._enums_to_build.append(EnumToBuild(title=title, options=options))

    @property
    def ast_enums(self) -> ast.Module:
        """
        Generates an AST module for the enums to build.

        Returns:
            ast.Module: The AST module containing the enum definitions.
        """
        module = ast.Module(body=[], type_ignores=[])
        _bases = ['Enum']
        if all(isinstance(option.value, str) for enum in self._enums_to_build for option in enum.options):
            _bases = ['str', 'Enum']

        for enum in self._enums_to_build:
            if sys.version_info >= (3, 12):
                _class_def = ast.ClassDef(
                    name=enum.title,
                    bases=_bases,  # type: ignore[arg-type]
                    keywords=[],
                    body=[
                        ast.Assign(
                            targets=[ast.Name(id=option.key, ctx=ast.Store())],
                            value=ast.Constant(value=option.value),
                        )
                        for option in enum.options
                    ],
                    decorator_list=[],
                    type_params=[],
                )
            else:
                _class_def = ast.ClassDef(
                    name=enum.title,
                    bases=_bases,  # type: ignore[arg-type]
                    keywords=[],
                    body=[
                        ast.Assign(
                            targets=[ast.Name(id=option.key, ctx=ast.Store())],
                            value=ast.Constant(value=option.value),
                        )
                        for option in enum.options
                    ],
                    decorator_list=[],
                )

            module.body.append(_class_def)

        return module

    def add_ast_import_node(self, node: ast.Import | ast.ImportFrom) -> None:
        """
        Adds an AST import node to the dependencies.

        Args:
            node (ast.Import | ast.ImportFrom): The AST import node to add.

        Returns:
            None
        """
        for import_name in node.names:
            self._dependencies.add(
                DependencyItem(
                    module=(
                        None if isinstance(node, ast.Import) else node.module,
                        import_name.name,
                        getattr(import_name, 'asname', None),
                    ),
                ),
            )

    def _resolve_model_module_info(self, model_type_name: str) -> ModulePathType | None:
        _start_index = self._searching_module_ordering.index(self._module_type)
        _searching_module_ordering = self._searching_module_ordering[_start_index:]

        for _searching_module_type in _searching_module_ordering:
            _models = self._model_module_info.get_by_type(_searching_module_type)

            if model_type_name in _models:
                return _models[model_type_name]

        return None
