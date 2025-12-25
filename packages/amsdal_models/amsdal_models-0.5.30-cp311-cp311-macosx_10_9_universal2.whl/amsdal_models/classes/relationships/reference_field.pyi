from _typeshed import Incomplete
from amsdal_models.classes.model import Model as Model
from amsdal_models.classes.relationships.constants import PRIMARY_KEY as PRIMARY_KEY
from amsdal_models.classes.relationships.enum import ReferenceMode as ReferenceMode
from collections.abc import Callable as Callable, Iterable
from pydantic.fields import FieldInfo, _FromFieldInfoInputs
from typing import Any
from typing_extensions import Unpack

def build_reference_db_field(field_name: str, suffix: str = '_id') -> str: ...
def default_db_field(field_name: str, field_type: type['Model']) -> str | Iterable[str]: ...
def ReferenceField(*args, db_field: str | Iterable[str] | Callable[[str, type['Model']], str | Iterable[str]] = ..., **kwargs) -> Any: ...

class _ReferenceFromFieldInfoInputs(_FromFieldInfoInputs):
    db_field: str | Iterable[str] | Callable[[str, type['Model']], str | Iterable[str]]
    on_delete: ReferenceMode | Callable[[Any], None]

class _ReferenceFieldInfoInputs(_ReferenceFromFieldInfoInputs, total=False):
    default: Any

class ReferenceFieldInfo(FieldInfo):
    db_field: str | Iterable[str] | Callable[[str, type['Model']], str | Iterable[str]]
    __slots__: Incomplete
    def __init__(self, **kwargs: Unpack[_ReferenceFieldInfoInputs]) -> None: ...
    @staticmethod
    def from_field(default: Any = ..., **kwargs: Unpack[_ReferenceFromFieldInfoInputs]) -> FieldInfo: ...
    @staticmethod
    def merge_field_infos(*field_infos: FieldInfo | ReferenceFieldInfo, **overrides: Any) -> ReferenceFieldInfo:
        """Merge `FieldInfo | ReferenceFieldInfo` instances keeping only explicitly set attributes.

        Later `FieldInfo | ReferenceFieldInfo` instances override earlier ones.

        Returns:
            ReferenceFieldInfo: A merged FieldInfo | ReferenceFieldInfo instance.
        """
