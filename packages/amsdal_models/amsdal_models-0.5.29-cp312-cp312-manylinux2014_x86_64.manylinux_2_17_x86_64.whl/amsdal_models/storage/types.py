from typing import TYPE_CHECKING
from typing import Optional
from typing import Protocol
from typing import runtime_checkable

from amsdal_utils.models.data_models.reference import Reference

if TYPE_CHECKING:
    from amsdal_models.storage.base import Storage


@runtime_checkable
class FileProtocol(Protocol):
    filename: str
    data: bytes | None
    size: float | None
    storage_address: Reference | None
    _storage: Optional['Storage']
