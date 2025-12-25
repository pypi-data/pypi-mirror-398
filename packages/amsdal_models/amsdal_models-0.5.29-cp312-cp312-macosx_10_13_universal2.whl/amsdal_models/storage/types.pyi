from amsdal_models.storage.base import Storage as Storage
from amsdal_utils.models.data_models.reference import Reference as Reference
from typing import Protocol

class FileProtocol(Protocol):
    filename: str
    data: bytes | None
    size: float | None
    storage_address: Reference | None
    _storage: Storage | None
