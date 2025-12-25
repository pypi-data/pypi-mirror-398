import sys
from collections import defaultdict
from typing import TypeAlias

from amsdal_utils.models.enums import ModuleType
from amsdal_utils.utils.singleton import Singleton

from amsdal_models.classes.class_loader import ModelClassLoader
from amsdal_models.classes.model import Model
from amsdal_models.classes.relationships.constants import MANY_TO_MANY_FIELDS

ModulePathType: TypeAlias = str
ClassNameType: TypeAlias = str
LoadedClassesType: TypeAlias = dict[ModuleType, dict[ClassNameType, tuple[type[Model], ModulePathType]]]


class ClassManager(metaclass=Singleton):
    def __init__(self) -> None:
        self._models_modules: list[tuple[ModulePathType, ModuleType]] = []
        self._loaded_classes: LoadedClassesType = defaultdict(dict)

    @property
    def has_models_modules(self) -> bool:
        return bool(self._models_modules)

    @property
    def user_models_count(self) -> int:
        if not self.has_models_modules:
            return 0

        raise NotImplementedError

    def register_models_modules(
        self,
        modules: list[tuple[ModulePathType, ModuleType]],
        *,
        clear_previously_registered: bool = False,
    ) -> None:
        if clear_previously_registered:
            self.unload_all_classes()
            self._models_modules.clear()

        self._models_modules.extend([_item for _item in modules if _item not in self._models_modules])

    def import_class(self, class_name: ClassNameType, module_type: ModuleType = ModuleType.USER) -> type[Model]:
        _loaded = self._loaded_classes[module_type]

        if class_name in _loaded:
            return _loaded[class_name][0]

        _requested_modules, _rest_modules = self._split_models_modules_by(module_type)

        for _index, (_module, _module_type) in enumerate(_requested_modules + _rest_modules):
            model_class_loader = ModelClassLoader(_module)
            _loaded_by_module_type = self._loaded_classes[_module_type]

            for _class in model_class_loader.load():
                if _class.__module_type__ != _module_type:
                    continue

                if _class.__name__ in _loaded_by_module_type:
                    continue

                _loaded_by_module_type[_class.__name__] = (_class, _module)

                _m2m_fields = getattr(_class, MANY_TO_MANY_FIELDS, None) or {}

                for _, m2m_model, _, _ in _m2m_fields.values():
                    _loaded_by_module_type[m2m_model.__name__] = (m2m_model, _module)

            if class_name in _loaded_by_module_type:
                return _loaded_by_module_type[class_name][0]

        msg = f'Cannot import model class "{class_name}"!'
        raise ImportError(msg)

    def teardown(self) -> None:
        self.unload_all_classes()
        self.__class__.invalidate()

    def unload_classes(self, class_name: ClassNameType, module_type: ModuleType = ModuleType.USER) -> None:
        if class_name in self._loaded_classes[module_type]:
            _, _module = self._loaded_classes[module_type][class_name]
            del self._loaded_classes[module_type][class_name]

            if _module:
                sys.modules.pop(_module, None)

    def unload_all_classes(self) -> None:
        for _module_type, _loaded_module_type in self._loaded_classes.items():
            for _class_name in list(_loaded_module_type.keys()):
                self.unload_classes(_class_name, _module_type)

    def _split_models_modules_by(
        self,
        module_type: ModuleType,
    ) -> tuple[list[tuple[ModulePathType, ModuleType]], list[tuple[ModulePathType, ModuleType]]]:
        _searching_modules = []
        _rest_modules = []

        for _module_path, _module_type in self._models_modules:
            if _module_type == module_type:
                _searching_modules.append((_module_path, _module_type))
            else:
                _rest_modules.append((_module_path, _module_type))

        return _searching_modules, _rest_modules
