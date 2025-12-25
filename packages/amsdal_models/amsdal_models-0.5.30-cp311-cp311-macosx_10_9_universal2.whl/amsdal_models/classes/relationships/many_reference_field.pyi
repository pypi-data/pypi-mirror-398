from _typeshed import Incomplete
from amsdal_models.classes.model import Model as Model
from amsdal_models.managers.base_manager import BaseManager as BaseManager
from collections.abc import Generator
from pydantic.fields import FieldInfo, _FromFieldInfoInputs
from typing import Any, Self
from typing_extensions import Unpack

def ManyReferenceField(through_fields: tuple[str, str], *args, through: Model | None = None, **kwargs) -> Any: ...

class _ManyReferenceFromFieldInfoInputs(_FromFieldInfoInputs):
    through: Model | None
    through_fields: tuple[str, str] | None

class _ManyReferenceFieldInfoInputs(_ManyReferenceFromFieldInfoInputs, total=False):
    default: Any

class ManyReferenceFieldInfo(FieldInfo):
    through: Model | None
    through_fields: tuple[str, str]
    __slots__: Incomplete
    def __init__(self, default: Any, **kwargs: Unpack[_ManyReferenceFieldInfoInputs]) -> None: ...
    @staticmethod
    def from_field(default: Any = ..., **kwargs: Unpack[_ManyReferenceFromFieldInfoInputs]) -> FieldInfo: ...

class ManyList(list):
    m2m: Incomplete
    obj: Incomplete
    manager: Incomplete
    def __init__(self, m2m: str, obj: Model, manager: BaseManager, *args: Any, **kwargs: Any) -> None: ...
    def append(self, obj: Model) -> None: ...
    def insert(self, idx: int, obj: Model) -> None: ...
    def remove(self, obj: Model) -> None: ...
    def extend(self, obj_list: list['Model']) -> None: ...
    def _mark_as_changed(self) -> None: ...
    def __await__(self) -> Generator[None, None, Self]: ...
