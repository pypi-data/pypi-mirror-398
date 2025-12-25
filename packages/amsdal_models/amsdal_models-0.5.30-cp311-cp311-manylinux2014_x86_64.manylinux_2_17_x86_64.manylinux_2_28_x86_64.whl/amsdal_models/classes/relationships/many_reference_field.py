from collections.abc import Generator
from typing import TYPE_CHECKING
from typing import Any
from typing import Optional
from typing import Self

from pydantic.fields import FieldInfo
from pydantic.fields import _FromFieldInfoInputs
from pydantic_core import PydanticUndefined
from typing_extensions import Unpack

from amsdal_models.managers.base_manager import BaseManager

if TYPE_CHECKING:
    from amsdal_models.classes.model import Model


def ManyReferenceField(  # type: ignore[no-untyped-def] # noqa: N802
    through_fields: tuple[str, str],
    *args,
    through: Optional['Model'] = None,
    **kwargs,
) -> Any:
    return ManyReferenceFieldInfo.from_field(*args, through=through, through_fields=through_fields, **kwargs)


class _ManyReferenceFromFieldInfoInputs(_FromFieldInfoInputs):
    through: Optional['Model']
    through_fields: tuple[str, str] | None


class _ManyReferenceFieldInfoInputs(_ManyReferenceFromFieldInfoInputs, total=False):
    default: Any


class ManyReferenceFieldInfo(FieldInfo):  # type: ignore[misc]
    through: Optional['Model']
    through_fields: tuple[str, str]

    __slots__ = (*FieldInfo.__slots__, 'through', 'through_fields')

    def __init__(self, default: Any, **kwargs: Unpack[_ManyReferenceFieldInfoInputs]) -> None:  # type: ignore[misc]
        self.through = kwargs['through']
        self.through_fields = kwargs['through_fields']
        super().__init__(default=default, **kwargs)

    @staticmethod
    def from_field(  # type: ignore[override]
        default: Any = PydanticUndefined,
        **kwargs: Unpack[_ManyReferenceFromFieldInfoInputs],
    ) -> FieldInfo:
        return ManyReferenceFieldInfo(default=default, **kwargs)


class ManyList(list):  # type: ignore[type-arg]
    def __init__(self, m2m: str, obj: 'Model', manager: BaseManager, *args: Any, **kwargs: Any) -> None:  # type: ignore[type-arg]
        self.m2m = m2m
        self.obj = obj
        self.manager = manager
        super().__init__(*args, **kwargs)

    def append(self, obj: 'Model') -> None:
        super().append(obj)
        self._mark_as_changed()

    def insert(self, idx: int, obj: 'Model') -> None:  # type: ignore[override]
        super().insert(idx, obj)
        self._mark_as_changed()

    def remove(self, obj: 'Model') -> None:
        super().remove(obj)
        self._mark_as_changed()

    def extend(self, obj_list: list['Model']) -> None:  # type: ignore[override]
        super().extend(obj_list)
        self._mark_as_changed()

    def _mark_as_changed(self) -> None:
        from amsdal_models.classes.relationships.meta.many_to_many import build_m2m_value_property

        setattr(self.obj, build_m2m_value_property(self.m2m), self)

    def __await__(self) -> Generator[None, None, Self]:
        async def _self() -> Self:
            return self

        return _self().__await__()
