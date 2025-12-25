from collections.abc import Callable
from typing import TYPE_CHECKING

from amsdal_utils.schemas.interfaces import BaseSchemaLoader
from amsdal_utils.schemas.interfaces import ModulePathType
from amsdal_utils.schemas.schema import ObjectSchema

from amsdal_models.classes.relationships.constants import FOREIGN_KEYS
from amsdal_models.classes.relationships.helpers.deferred_foreign_keys import complete_deferred_foreign_keys
from amsdal_models.classes.relationships.helpers.deferred_many_to_many import complete_deferred_many_to_many
from amsdal_models.classes.relationships.helpers.deferred_primary_keys import complete_deferred_primary_keys
from amsdal_models.classes.relationships.meta.references import build_fk_db_fields

if TYPE_CHECKING:
    from amsdal_models.classes.model import Model


class ClassSchemaLoader(BaseSchemaLoader):
    def __init__(
        self,
        module_path: ModulePathType,
        class_filter: Callable[[type['Model']], bool] | None = None,
    ) -> None:
        self._module_path = module_path
        self._class_filter = class_filter or (lambda cls: True)  # noqa: ARG005

    @property
    def schemas_per_module(self) -> dict[ModulePathType, list[ObjectSchema]]:
        return {self._module_path: self.load()}

    def load(self) -> list[ObjectSchema]:
        from amsdal_models.schemas.object_schema import model_to_object_schema

        return [model_to_object_schema(model_class) for model_class in self._load_classes()]

    def load_sorted(self) -> tuple[list[ObjectSchema], list[ObjectSchema]]:
        """
        Load object schemas sorted by dependencies.
        Returns: tuple of two elements, the first one is list of all sorted object schemas and the
                second one is list of schema that have cycle dependencies.
        """
        from amsdal_models.schemas.object_schema import model_to_object_schema

        _classes, _cycles = _sort_classes(self._load_classes())

        for model_class in _classes:
            _schema = model_to_object_schema(model_class)

            if model_class in _cycles:
                delattr(_schema, 'foreign_keys')

        return (
            [model_to_object_schema(model_class) for model_class in _classes],
            [model_to_object_schema(model_class) for model_class in _cycles],
        )

    def _load_classes(self) -> list[type['Model']]:
        from amsdal_models.classes.class_loader import ModelClassLoader

        model_class_loader = ModelClassLoader(self._module_path)
        return [_class for _class in model_class_loader.load(unload_module=True) if self._class_filter(_class)]


class ClassMultiDirectoryJsonLoader(BaseSchemaLoader):
    def __init__(
        self,
        module_paths: list[ModulePathType],
        class_filter: Callable[[type['Model']], bool] | None = None,
    ) -> None:
        self._module_paths = module_paths
        self._schemas_per_module: dict[ModulePathType, list[ObjectSchema]] = {}
        self._classes_per_module: dict[ModulePathType, list[type[Model]]] = {}
        self._class_filter = class_filter or (lambda cls: True)  # noqa: ARG005

    @property
    def schemas_per_module(self) -> dict[ModulePathType, list[ObjectSchema]]:
        return self._schemas_per_module

    def load(self) -> list[ObjectSchema]:
        from amsdal_models.schemas.object_schema import model_to_object_schema

        return [model_to_object_schema(model_class) for model_class in self._load_classes()]

    def load_sorted(self) -> tuple[list[ObjectSchema], list[ObjectSchema]]:
        from amsdal_models.schemas.object_schema import model_to_object_schema

        _classes, _cycles = _sort_classes(self._load_classes())

        for model_class in _classes:
            _schema = model_to_object_schema(model_class)

            if model_class in _cycles:
                delattr(_schema, 'foreign_keys')

        return (
            [model_to_object_schema(model_class) for model_class in _classes],
            [model_to_object_schema(model_class) for model_class in _cycles],
        )

    def _load_classes(self) -> list[type['Model']]:
        from amsdal_models.classes.class_loader import ModelClassLoader

        all_classes = []

        for _module_path in self._module_paths:
            model_class_loader = ModelClassLoader(_module_path)
            _classes = [_class for _class in model_class_loader.load(unload_module=True) if self._class_filter(_class)]
            all_classes.extend(_classes)
            self._classes_per_module[_module_path] = _classes
        return all_classes


def _sort_classes(
    classes: list[type['Model']],
) -> tuple[list[type['Model']], list[type['Model']]]:
    """
    Sorts model classes based on their dependencies and detects circular dependencies.
    Returns (sorted_models, models_in_cycles).
    """
    from typing import ForwardRef
    from typing import get_args
    from typing import get_args as get_args_ext
    from typing import get_origin
    from typing import get_origin as get_origin_ext

    from amsdal_models.classes.model import TypeModel

    # Build dependency graph
    graph: dict[str, set[str]] = {model.__name__: set() for model in classes}
    model_map = {model.__name__: model for model in classes}
    model_names = {model.__name__ for model in classes}

    def extract_model_refs(type_ann, visited=None):  # type: ignore[no-untyped-def]
        """Extract model references from a type annotation."""
        if visited is None:
            visited = set()

        if isinstance(type_ann, str):
            # Forward reference as string
            if type_ann in model_names:
                return {type_ann}
            return set()

        if isinstance(type_ann, ForwardRef):
            # Handle ForwardRef('ModelName')
            return extract_model_refs(type_ann.__forward_arg__, visited)

        if isinstance(type_ann, type) and issubclass(type_ann, TypeModel):
            # Direct model reference
            return {type_ann.__name__}

        # Handle Union/Optional types (including the | syntax)
        origin = get_origin(type_ann) or get_origin_ext(type_ann)

        if origin is not None:
            # Handle container types like list, dict, Union, Optional
            args = get_args(type_ann) or get_args_ext(type_ann)
            refs = set()
            for arg in args:
                if id(arg) not in visited:
                    visited.add(id(arg))
                    refs.update(extract_model_refs(arg, visited))
            return refs

        return set()

    def should_add_dependency(source_model, target_model_name):  # type: ignore[no-untyped-def]
        """Check if dependency should be added based on module type."""
        source_module_type = getattr(source_model, '__module_type__', None)
        target_model = model_map.get(target_model_name)

        if not target_model:
            return False

        target_module_type = getattr(target_model, '__module_type__', None)

        return source_module_type == target_module_type

    for model in classes:
        # Handle inheritance relationships
        for base in model.__bases__:
            if base.__name__ in model_names and base.__name__ != model.__name__:
                # Check module type before adding dependency
                if should_add_dependency(model, base.__name__):
                    # Child depends on parent, so parent should come first
                    graph[model.__name__].add(base.__name__)

        complete_deferred_primary_keys(model)
        complete_deferred_foreign_keys(model)
        complete_deferred_many_to_many(model)

        # Handle foreign keys
        fks = getattr(model, FOREIGN_KEYS, None) or []

        for fk in fks:
            field_info = model.model_fields[fk]
            fk_type, _, _ = build_fk_db_fields(fk, field_info)

            if not isinstance(fk_type, type):
                msg = f'Expected fk_type to be a type, got {type(fk_type)}'
                raise ValueError(msg)

            if fk_type.__name__ != model.__name__ and should_add_dependency(model, fk_type.__name__):
                graph[model.__name__].add(fk_type.__name__)

        # Handle all other field references, but skip M2M relationships
        for field_name, field_info in model.model_fields.items():
            # Skip fields that are already processed as FKs
            if field_name in fks:
                continue

            # Skip M2M fields (fields that are lists/collections of models)
            origin = get_origin(field_info.annotation) or get_origin_ext(field_info.annotation)
            if origin in (list, set, tuple):
                continue

            model_refs = extract_model_refs(field_info.annotation)
            for ref_name in model_refs:
                if ref_name in model_names and ref_name != model.__name__:
                    if should_add_dependency(model, ref_name):
                        graph[model.__name__].add(ref_name)

    # Cycle detection
    cycles: set[str] = set()
    visited = set()
    path: list[str] = []

    def dfs(node: str) -> None:
        if node not in graph:
            return

        if node in path:
            cycle_start = path.index(node)
            cycle = path[cycle_start:]

            if len(cycle) > 1:
                cycles.update(cycle)
            return

        if node in visited:
            return

        visited.add(node)
        path.append(node)

        for neighbor in list(graph[node]):
            dfs(neighbor)
        path.pop()

    # Detect cycles
    for node in list(graph.keys()):
        if node not in visited:
            dfs(node)

    # Create a reverse graph to track which nodes depend on each node
    reverse_graph: dict[str, set[str]] = {node: set() for node in graph}
    for node, deps in graph.items():
        for dep in deps:
            reverse_graph[dep].add(node)

    # Calculate in-degree for each node
    in_degree = {node: len(graph[node]) for node in graph}

    # Process nodes with no dependencies first
    queue = [node for node, degree in in_degree.items() if degree == 0]
    queue.sort()  # Sort alphabetically

    sorted_models = []
    visited = set()

    while queue:
        # Process next node with no dependencies
        node = queue.pop(0)
        visited.add(node)
        sorted_models.append(model_map[node])

        # Update in-degree for nodes that depend on this one
        next_nodes = []
        for dependent in reverse_graph[node]:
            if dependent not in visited:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    next_nodes.append(dependent)

        # Sort alphabetically and add to queue
        next_nodes.sort()
        queue.extend(next_nodes)

    # Handle any remaining nodes (part of cycles)
    remaining = [node for node in graph if node not in visited]
    remaining.sort()  # Sort alphabetically
    for node in remaining:
        if node not in visited:
            sorted_models.append(model_map[node])

    # Convert cycle model names back to model classes
    cyclic_models = [model_map[name] for name in cycles]

    return sorted_models, cyclic_models
