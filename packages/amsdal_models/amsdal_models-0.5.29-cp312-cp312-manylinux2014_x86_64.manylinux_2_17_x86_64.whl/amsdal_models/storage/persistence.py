from __future__ import annotations

import io
from contextlib import suppress
from typing import BinaryIO

from amsdal_models.storage.base import Storage
from amsdal_models.storage.errors import StateError
from amsdal_models.storage.errors import StorageError
from amsdal_models.storage.helpers import build_storage_address
from amsdal_models.storage.types import FileProtocol


def persist_file(file: FileProtocol, storage: Storage) -> FileProtocol:
    """
    Persist a FileProtocol to the provided storage (sync) according to the design lifecycle.
    Updates storage_address, filename, size, clears payload if allowed, and marks as persisted.
    """
    content = _content_stream(file)
    final_name = storage.save(file, content)

    # Update filename if storage normalized/collided
    if final_name and final_name != file.filename:
        file.filename = final_name

    # Set size if not known
    if file.size is None:
        # Best-effort size detection without raising errors
        with suppress(Exception):
            # Try to get size from content if it's a BytesIO
            if hasattr(content, 'getbuffer'):
                file.size = len(content.getbuffer())
            elif hasattr(content, 'seek') and hasattr(content, 'tell'):
                pos = content.tell()
                with suppress(Exception):
                    content.seek(0, io.SEEK_END)
                    file.size = content.tell()
                    content.seek(pos)

    # Build and set storage address
    file.storage_address = build_storage_address(storage, file.filename)

    # Clear local payload if backend doesn't keep local copy
    if not storage.keeps_local_copy:
        file.data = None
        file._source = None  # type: ignore[attr-defined]

    # Mark as persisted
    file._needs_persist = False  # type: ignore[attr-defined]

    return file


async def apersist_file(file: FileProtocol, storage: Storage) -> FileProtocol:
    """
    Persist a File to the provided storage (async) using asave() if implemented.
    Falls back to thread execution of sync save if async not available.
    """
    content = _content_stream(file)

    # Prefer async save if implemented
    try:
        final_name = await storage.asave(file, content)
    except NotImplementedError:
        # Fallback: call sync save in the same thread (callers should run in a thread if needed)
        final_name = storage.save(file, content)
    except Exception as e:  # pragma: no cover - error path
        raise StorageError(str(e)) from e

    if final_name and final_name != file.filename:
        file.filename = final_name

    if file.size is None:
        with suppress(Exception):
            if hasattr(content, 'getbuffer'):
                file.size = len(content.getbuffer())

    file.storage_address = build_storage_address(storage, file.filename)

    if not storage.keeps_local_copy:
        file.data = None
        file._source = None  # type: ignore[attr-defined]

    file._needs_persist = False  # type: ignore[attr-defined]

    return file


def _content_stream(file: FileProtocol) -> BinaryIO:
    if file._source is not None:  # type: ignore[attr-defined]
        # Try to rewind to the beginning if possible
        with suppress(Exception):
            if hasattr(file._source, 'seek'):  # type: ignore[attr-defined]
                file._source.seek(0)  # type: ignore[attr-defined]
        return file._source  # type: ignore[attr-defined]
    if file.data is not None:
        return io.BytesIO(file.data)
    msg = f"No content to persist for file '{file.filename}'"
    raise StateError(msg)
