from _typeshed import Incomplete
from amsdal_models.classes.model import Model as Model
from amsdal_models.classes.relationships.constants import FOREIGN_KEYS as FOREIGN_KEYS
from amsdal_models.classes.relationships.helpers.deferred_foreign_keys import complete_deferred_foreign_keys as complete_deferred_foreign_keys
from amsdal_models.classes.relationships.helpers.deferred_many_to_many import complete_deferred_many_to_many as complete_deferred_many_to_many
from amsdal_models.classes.relationships.helpers.deferred_primary_keys import complete_deferred_primary_keys as complete_deferred_primary_keys
from amsdal_models.classes.relationships.meta.references import build_fk_db_fields as build_fk_db_fields
from amsdal_utils.schemas.interfaces import BaseSchemaLoader, ModulePathType as ModulePathType
from amsdal_utils.schemas.schema import ObjectSchema as ObjectSchema
from collections.abc import Callable as Callable

class ClassSchemaLoader(BaseSchemaLoader):
    _module_path: Incomplete
    _class_filter: Incomplete
    def __init__(self, module_path: ModulePathType, class_filter: Callable[[type['Model']], bool] | None = None) -> None: ...
    @property
    def schemas_per_module(self) -> dict[ModulePathType, list[ObjectSchema]]: ...
    def load(self) -> list[ObjectSchema]: ...
    def load_sorted(self) -> tuple[list[ObjectSchema], list[ObjectSchema]]:
        """
        Load object schemas sorted by dependencies.
        Returns: tuple of two elements, the first one is list of all sorted object schemas and the
                second one is list of schema that have cycle dependencies.
        """
    def _load_classes(self) -> list[type['Model']]: ...

class ClassMultiDirectoryJsonLoader(BaseSchemaLoader):
    _module_paths: Incomplete
    _schemas_per_module: dict[ModulePathType, list[ObjectSchema]]
    _classes_per_module: dict[ModulePathType, list[type[Model]]]
    _class_filter: Incomplete
    def __init__(self, module_paths: list[ModulePathType], class_filter: Callable[[type['Model']], bool] | None = None) -> None: ...
    @property
    def schemas_per_module(self) -> dict[ModulePathType, list[ObjectSchema]]: ...
    def load(self) -> list[ObjectSchema]: ...
    def load_sorted(self) -> tuple[list[ObjectSchema], list[ObjectSchema]]: ...
    def _load_classes(self) -> list[type['Model']]: ...

def _sort_classes(classes: list[type['Model']]) -> tuple[list[type['Model']], list[type['Model']]]:
    """
    Sorts model classes based on their dependencies and detects circular dependencies.
    Returns (sorted_models, models_in_cycles).
    """
