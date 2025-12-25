from amsdal_utils.models.enums import ModuleType as ModuleType
from typing import TypeAlias

ModulePathType: TypeAlias = str
ClassNameType: TypeAlias = str

class ModelModuleInfo:
    _info: dict[ModuleType, dict[ClassNameType, ModulePathType]]
    def __init__(self, info: dict[ModuleType, dict[ClassNameType, ModulePathType]]) -> None: ...
    def get_by_type(self, module_type: ModuleType) -> dict[ClassNameType, ModulePathType]: ...
