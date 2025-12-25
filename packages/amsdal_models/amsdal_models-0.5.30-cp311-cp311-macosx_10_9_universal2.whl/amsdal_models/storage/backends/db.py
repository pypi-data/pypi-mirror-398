import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextlib import suppress
from io import BytesIO
from types import TracebackType
from typing import IO
from typing import Any
from typing import BinaryIO
from typing import Self

from amsdal_models.storage.base import Storage
from amsdal_models.storage.errors import StorageError
from amsdal_models.storage.helpers import build_storage_address
from amsdal_models.storage.types import FileProtocol


class AsyncFileWrapper:
    def __init__(self, bio: IO[Any]):
        self._bio = bio

    # Async context manager
    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._bio.close()

    # Async methods mirroring common IO API
    async def read(self, n: int = -1) -> bytes:
        return self._bio.read(n)

    async def close(self) -> None:
        self._bio.close()

    async def seek(self, offset: int, whence: int = 0) -> int:
        return self._bio.seek(offset, whence)

    async def tell(self) -> int:
        return self._bio.tell()


class DBStorage(Storage):
    """
    In-database storage backend.

    This backend "stores" file bytes within the File model's `data` field itself.
    - save(): reads bytes from the provided content stream and assigns to file.data.
    - open(): returns a BytesIO stream over file.data.
    - url(): returns a non-public placeholder URL (db://<filename>).

    Since bytes are kept on the model, this backend keeps a local copy to prevent
    persistence layer from clearing payload.
    """

    keeps_local_copy = True

    def save(self, file: FileProtocol, content: BinaryIO) -> str:
        data = self._ensure_bytes(content)
        file.data = data
        file.storage_address = build_storage_address(self, file.filename)
        # Do not change the provided filename; collisions are irrelevant for DB storage
        return file.filename

    def open(self, file: FileProtocol, mode: str = 'rb') -> IO[Any]:
        self._validate_mode(mode)
        if file.data is None:
            msg = f"No data present in FileProtocol '{file.filename}' to open"
            raise StorageError(msg)
        # Return a new BytesIO each time to emulate a fresh stream
        return BytesIO(file.data)

    def delete(self, file: FileProtocol) -> None:
        file.data = None

    def exists(self, file: FileProtocol) -> bool:
        return file.data is not None

    def url(self, file: FileProtocol) -> str:
        return f'db://{file.filename}'

    async def asave(self, file: FileProtocol, content: BinaryIO) -> str:
        return self.save(file, content)

    async def aopen(self, file: FileProtocol, mode: str = 'rb') -> AsyncFileWrapper:
        return AsyncFileWrapper(self.open(file, mode))

    async def adelete(self, file: FileProtocol) -> None:
        self.delete(file)

    async def aexists(self, file: FileProtocol) -> bool:
        return self.exists(file)

    async def aurl(self, file: FileProtocol) -> str:
        return self.url(file)

    @staticmethod
    @contextmanager
    def _ensure_open(binary: BinaryIO, mode: str = 'rb') -> Iterator[IO[Any]]:
        if getattr(binary, 'closed', False):
            name = getattr(binary, 'name', None)
            if isinstance(name, (str | bytes | os.PathLike)):
                with open(name, mode) as f:
                    yield f
                return
            msg = 'Could not open binary stream for reading'
            raise ValueError(msg)
        yield binary

    def _ensure_bytes(self, content: BinaryIO) -> bytes:
        with self._ensure_open(content) as _content:
            # Try to reset to beginning if possible
            if hasattr(_content, 'seek'):
                with suppress(Exception):
                    _content.seek(0)

            data = _content.read()

            if not isinstance(data, bytes | bytearray):
                msg = 'DBStorage.save expected a binary stream returning bytes'
                raise StorageError(msg)
            return bytes(data)

    def _validate_mode(self, mode: str) -> None:
        # We only support reading modes from in-memory bytes
        if 'w' in mode or 'a' in mode or '+' in mode:
            msg = f"DBStorage.open does not support write/append modes: '{mode}'"
            raise StorageError(msg)
