import inspect
import pkgutil
import sys
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

from amsdal_models.classes.relationships.constants import DEFERRED_M2M_FIELDS
from amsdal_models.classes.relationships.constants import MANY_TO_MANY_FIELDS
from amsdal_models.classes.relationships.helpers.deferred_many_to_many import complete_deferred_many_to_many
from amsdal_models.classes.relationships.meta.many_to_many import DeferredModel

if TYPE_CHECKING:
    from amsdal_models.classes.model import Model


class ModelClassLoader:
    def __init__(self, module_path: str) -> None:
        self._module_path = module_path

    def load(self, *, unload_module: bool = False) -> set[type['Model']]:
        if unload_module:
            for _module in list(sys.modules.keys()):
                if _module.startswith(self._module_path):
                    sys.modules.pop(_module, None)

        loaded_module = import_module(self._module_path)
        module_path = Path(loaded_module.__file__)  # type: ignore[arg-type]

        if module_path.is_file() and module_path.name == '__init__.py':
            module_path = module_path.parent

        if module_path.is_dir():
            return self._load_package_classes(self._module_path)

        return self._load_module_classes(self._module_path)

    def _load_module_classes(self, module_name: str) -> set[type['Model']]:
        from amsdal_models.classes.model import Model
        from amsdal_models.classes.model import TypeModel

        module = import_module(module_name)
        found_classes = {}

        for _, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, (Model, TypeModel)) and cls not in (Model, TypeModel):
                found_classes[cls.__name__] = cls

        for cls in list(found_classes.values()):
            if getattr(cls, DEFERRED_M2M_FIELDS, None):
                if not complete_deferred_many_to_many(cls, _types_namespace=found_classes):  # type: ignore[arg-type]
                    msg = f'Unable to resolve all deferred many-to-many fields on {cls.__name__}.'
                    raise RuntimeError(msg)

            m2m_fields = getattr(cls, MANY_TO_MANY_FIELDS, None) or {}

            if m2m_fields:
                for m2m, (m2m_ref, m2m_model, through_fields, field_info) in m2m_fields.items():
                    if isinstance(m2m_model, DeferredModel):
                        _m2m_model = m2m_model(cls)  # type: ignore[type-var]
                        m2m_fields[m2m] = (m2m_ref, _m2m_model, through_fields, field_info)
                    else:
                        _m2m_model = m2m_model

                    found_classes[_m2m_model.__name__] = _m2m_model
                setattr(cls, MANY_TO_MANY_FIELDS, m2m_fields)
        return list(found_classes.values())  # type: ignore[return-value]

    def _load_package_classes(self, package_name: str) -> set[type['Model']]:
        package = import_module(package_name)
        package_path = Path(package.__file__).parent  # type: ignore[arg-type]
        model_classes = set()

        for _, name, is_pkg in pkgutil.walk_packages([str(package_path)]):
            full_name = f'{package_name}.{name}'
            model_classes.update(self._load_module_classes(full_name))

            if is_pkg:
                model_classes.update(self._load_package_classes(full_name))

        return model_classes
