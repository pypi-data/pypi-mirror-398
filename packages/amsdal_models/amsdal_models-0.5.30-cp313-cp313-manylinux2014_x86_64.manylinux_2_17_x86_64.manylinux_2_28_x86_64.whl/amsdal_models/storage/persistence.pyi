from amsdal_models.storage.base import Storage as Storage
from amsdal_models.storage.errors import StateError as StateError, StorageError as StorageError
from amsdal_models.storage.helpers import build_storage_address as build_storage_address
from amsdal_models.storage.types import FileProtocol as FileProtocol
from typing import BinaryIO

def persist_file(file: FileProtocol, storage: Storage) -> FileProtocol:
    """
    Persist a FileProtocol to the provided storage (sync) according to the design lifecycle.
    Updates storage_address, filename, size, clears payload if allowed, and marks as persisted.
    """
async def apersist_file(file: FileProtocol, storage: Storage) -> FileProtocol:
    """
    Persist a File to the provided storage (async) using asave() if implemented.
    Falls back to thread execution of sync save if async not available.
    """
def _content_stream(file: FileProtocol) -> BinaryIO: ...
