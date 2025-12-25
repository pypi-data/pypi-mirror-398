from amsdal_models.storage.errors import ConfigurationError as ConfigurationError
from amsdal_models.storage.types import FileProtocol as FileProtocol
from typing import Any, BinaryIO, ClassVar, IO

class Storage:
    """
    Base interface for storage backends.

    Every backend must implement save/open/delete/exists/url and a JSON-safe
    serialization protocol via to_storage_spec()/from_storage_spec().
    Async counterparts live on the same class and by default raise NotImplementedError.
    """
    keeps_local_copy: ClassVar[bool]
    def save(self, file: FileProtocol, content: BinaryIO) -> str:
        """Save the content stream for the given File. Return final canonical name."""
    def open(self, file: FileProtocol, mode: str = 'rb') -> IO[Any]:
        """Open a binary stream for the given File (reading by default)."""
    def delete(self, file: FileProtocol) -> None:
        """Delete the given File from storage if it exists."""
    def exists(self, file: FileProtocol) -> bool:
        """Return True if the given File exists in storage."""
    def url(self, file: FileProtocol) -> str:
        """Return a URL for public access (if configured) for the given File."""
    async def asave(self, file: FileProtocol, content: BinaryIO) -> str: ...
    async def aopen(self, file: FileProtocol, mode: str = 'rb') -> Any: ...
    async def adelete(self, file: FileProtocol) -> None: ...
    async def aexists(self, file: FileProtocol) -> bool: ...
    async def aurl(self, file: FileProtocol) -> str: ...
    def to_storage_spec(self) -> dict[str, Any]:
        '''
        Return a JSON-safe StorageSpec representing this storage instance.

        Shape: {"storage_class": full_import_path, "storage_kwargs": {...}}
        '''
    @classmethod
    def from_storage_spec(cls, spec: dict[str, Any]) -> Storage:
        """Construct a storage instance from a StorageSpec."""
    def _export_kwargs(self) -> dict[str, Any]: ...
