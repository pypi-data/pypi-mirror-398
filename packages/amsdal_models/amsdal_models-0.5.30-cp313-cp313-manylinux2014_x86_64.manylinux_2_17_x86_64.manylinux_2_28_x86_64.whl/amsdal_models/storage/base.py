from __future__ import annotations

import importlib
from typing import IO
from typing import Any
from typing import BinaryIO
from typing import ClassVar

from amsdal_models.storage.errors import ConfigurationError
from amsdal_models.storage.types import FileProtocol


class Storage:
    """
    Base interface for storage backends.

    Every backend must implement save/open/delete/exists/url and a JSON-safe
    serialization protocol via to_storage_spec()/from_storage_spec().
    Async counterparts live on the same class and by default raise NotImplementedError.
    """

    # Whether backend retains a local copy after save. Influences whether File.data/_source
    # can be cleared safely after persistence. Backends should override if needed.
    keeps_local_copy: ClassVar[bool] = False

    def save(self, file: FileProtocol, content: BinaryIO) -> str:
        """Save the content stream for the given File. Return final canonical name."""
        msg = 'Sync save (save) is not implemented for this storage backend'
        raise NotImplementedError(msg)

    def open(self, file: FileProtocol, mode: str = 'rb') -> IO[Any]:
        """Open a binary stream for the given File (reading by default)."""
        msg = 'Sync open (open) is not implemented for this storage backend'
        raise NotImplementedError(msg)

    def delete(self, file: FileProtocol) -> None:
        """Delete the given File from storage if it exists."""
        msg = 'Sync delete (delete) is not implemented for this storage backend'
        raise NotImplementedError(msg)

    def exists(self, file: FileProtocol) -> bool:
        """Return True if the given File exists in storage."""
        msg = 'Sync exists (exists) is not implemented for this storage backend'
        raise NotImplementedError(msg)

    def url(self, file: FileProtocol) -> str:
        """Return a URL for public access (if configured) for the given File."""
        msg = 'Sync url (url) is not implemented for this storage backend'
        raise NotImplementedError(msg)

    # ---- Async counterparts (optional for backends) ----
    async def asave(self, file: FileProtocol, content: BinaryIO) -> str:  # pragma: no cover - default stub
        msg = 'Async save (asave) is not implemented for this storage backend'
        raise NotImplementedError(msg)

    async def aopen(self, file: FileProtocol, mode: str = 'rb') -> Any:  # pragma: no cover - default stub
        msg = 'Async open (aopen) is not implemented for this storage backend'
        raise NotImplementedError(msg)

    async def adelete(self, file: FileProtocol) -> None:  # pragma: no cover - default stub
        msg = 'Async delete (adelete) is not implemented for this storage backend'
        raise NotImplementedError(msg)

    async def aexists(self, file: FileProtocol) -> bool:  # pragma: no cover - default stub
        msg = 'Async exists (aexists) is not implemented for this storage backend'
        raise NotImplementedError(msg)

    async def aurl(self, file: FileProtocol) -> str:  # pragma: no cover - default stub
        msg = 'Async url (aurl) is not implemented for this storage backend'
        raise NotImplementedError(msg)

    def to_storage_spec(self) -> dict[str, Any]:
        """
        Return a JSON-safe StorageSpec representing this storage instance.

        Shape: {"storage_class": full_import_path, "storage_kwargs": {...}}
        """
        cls = self.__class__
        module_path = cls.__module__
        full_class_path = f'{module_path}.{cls.__name__}'
        kwargs = self._export_kwargs()

        return {'storage_class': full_class_path, 'storage_kwargs': kwargs}

    @classmethod
    def from_storage_spec(cls, spec: dict[str, Any]) -> Storage:
        """Construct a storage instance from a StorageSpec."""
        class_path = spec.get('storage_class')
        kwargs = spec.get('storage_kwargs', {}) or {}

        if not class_path:
            msg = "StorageSpec missing 'class'"
            raise ConfigurationError(msg)

        module_name, _, class_name = class_path.rpartition('.')

        try:
            module = importlib.import_module(module_name)
            storage_cls: type[Storage] = getattr(module, class_name)
        except Exception as e:
            msg = f"Cannot import storage class '{class_path}': {e}"
            raise ImportError(msg) from e

        return storage_cls(**kwargs)

    # Backend can override to customize exported kwargs
    def _export_kwargs(self) -> dict[str, Any]:
        return {}
