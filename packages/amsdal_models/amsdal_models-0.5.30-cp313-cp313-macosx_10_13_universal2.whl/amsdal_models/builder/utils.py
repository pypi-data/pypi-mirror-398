from typing import TypeAlias

from amsdal_utils.models.enums import ModuleType

ModulePathType: TypeAlias = str
ClassNameType: TypeAlias = str


class ModelModuleInfo:
    _info: dict[ModuleType, dict[ClassNameType, ModulePathType]]

    def __init__(self, info: dict[ModuleType, dict[ClassNameType, ModulePathType]]) -> None:
        self._info = info

    def get_by_type(self, module_type: ModuleType) -> dict[ClassNameType, ModulePathType]:
        return self._info.get(module_type, {})
