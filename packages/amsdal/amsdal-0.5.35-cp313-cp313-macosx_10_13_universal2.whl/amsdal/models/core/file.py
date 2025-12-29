import base64
import io
from contextlib import suppress
from pathlib import Path
from typing import IO
from typing import Any
from typing import BinaryIO
from typing import ClassVar

from amsdal_models.classes.model import Model
from amsdal_models.storage.backends.db import AsyncFileWrapper
from amsdal_models.storage.backends.db import DBStorage
from amsdal_models.storage.base import Storage
from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.models.enums import ModuleType
from pydantic import PrivateAttr
from pydantic import model_validator
from pydantic.fields import Field


class File(Model):
    __module_type__: ClassVar[ModuleType] = ModuleType.CORE
    filename: str = Field(title='Filename')
    data: bytes | None = Field(default=None, title='Data')
    size: float | None = Field(default=None, title='Size')
    storage_address: Reference | None = Field(default=None, title='Storage Reference')

    _source: BinaryIO | None = PrivateAttr(default=None)
    _storage: Storage | None = PrivateAttr(default=None)

    @property
    def storage(self) -> Storage:
        from amsdal.storages import default_storage

        if self._storage:
            return self._storage

        if self.storage_address:
            return Storage.from_storage_spec({'storage_class': self.storage_address.ref.resource})

        return default_storage()

    def __repr__(self) -> str:
        return f'File<{self.filename}>({self.size or len(self.data or "") or 0} bytes)'

    def __str__(self) -> str:
        return repr(self)

    def pre_create(self) -> None:
        from amsdal_models.storage.persistence import persist_file

        persist_file(self, storage=self.storage)

    def pre_update(self) -> None:
        from amsdal_models.storage.persistence import persist_file

        persist_file(self, storage=self.storage)

    async def apre_create(self) -> None:
        from amsdal_models.storage.persistence import apersist_file

        await apersist_file(self, storage=self.storage)

    async def apre_update(self) -> None:
        from amsdal_models.storage.persistence import apersist_file

        await apersist_file(self, storage=self.storage)

    @model_validator(mode='before')
    @classmethod
    def validate_model_data(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if 'data' in data:
                if data['data']:
                    data['data'] = cls.data_base64_decode(data['data'])
                    data['size'] = len(data['data'])
                else:
                    data['size'] = 0
        return data

    @classmethod
    def data_base64_decode(cls, data: Any) -> bytes:
        if isinstance(data, str):
            data = data.encode('utf-8')

        is_base64: bool = False

        with suppress(Exception):
            is_base64 = base64.b64encode(base64.b64decode(data)) == data

        if is_base64:
            return base64.b64decode(data)

        return data

    @classmethod
    def from_file(cls, file_or_path: Path | BinaryIO) -> 'File':
        """
        Creates a `File` object from a file path or a binary file object.

        Args:
            file_or_path (Path | BinaryIO): The file path or binary file object.

        Returns:
            File: The created `File` object.

        Raises:
            ValueError: If the provided path is a directory.
        """
        f: BinaryIO | io.BufferedReader

        if isinstance(file_or_path, Path):
            if file_or_path.is_dir():
                msg = f'{file_or_path} is a directory'
                raise ValueError(msg)
            f = file_or_path.open('rb')
            filename = file_or_path.name
            size = file_or_path.stat().st_size

        else:
            f = file_or_path
            filename = Path(getattr(f, 'name', 'unnamed')).name

            try:
                if f.seekable():
                    f.seek(0, io.SEEK_END)
                    size = f.tell()
                    f.seek(0)
                else:
                    size = None
            except (OSError, AttributeError):
                size = None

        obj = cls(filename=filename, size=size)
        obj._source = f
        return obj

    @classmethod
    def from_bytes(cls, filename: str, data: bytes) -> 'File':
        """
        Creates a `File` object from a byte string.

        Args:
            filename (str): The filename of the file.
            data (bytes): The byte string containing the file data.:

        Returns:
            File: The created `File` object.
        """
        obj = cls(filename=filename, data=data, size=len(data))
        return obj

    def to_file(self, file_or_path: Path | BinaryIO) -> None:
        """
        Writes the object's data to a file path or a binary file object.

        Args:
            file_or_path (Path | BinaryIO): The file path or binary file object where the data will be written.

        Returns:
            None

        Raises:
            ValueError: If the provided path is a directory.
        """
        with self.open() as f:
            if isinstance(file_or_path, Path):
                if file_or_path.is_dir():
                    file_or_path = file_or_path / self.name
                file_or_path.write_bytes(f.read())  # type: ignore[union-attr]
            else:
                file_or_path.write(f.read())
                file_or_path.seek(0)

    def url(self) -> str:
        """
        Return a URL for this file using its storage_address.

        Raises StateError if storage_address is missing.
        """
        return self.storage.url(self)

    def open(self, mode: str = 'rb') -> IO[Any]:
        """
        Open a binary stream for reading (or other modes if supported) using storage_address.

        Raises StateError if storage_address is missing.
        """
        return self.storage.open(self, mode)

    async def aurl(self) -> str:
        """
        Async variant of url().

        Uses the resolved storage to call aurl(); if the backend does not implement
        async, falls back to the sync url().
        """
        try:
            return await self.storage.aurl(self)  # type: ignore[attr-defined]
        except NotImplementedError:
            return self.storage.url(self)

    async def aopen(self, mode: str = 'rb') -> Any:
        """
        Async variant of open().

        Uses the resolved storage to call aopen(); if the backend does not implement
        async, falls back to the sync open().
        """
        try:
            return await self.storage.aopen(self, mode)
        except NotImplementedError:
            return AsyncFileWrapper(self.storage.open(self, mode))

    @property
    def mimetype(self) -> str | None:
        """
        Returns the MIME type of the file based on its filename.

        This method uses the `mimetypes` module to guess the MIME type of the file.

        Returns:
            str | None: The guessed MIME type of the file, or None if it cannot be determined.
        """
        import mimetypes

        return mimetypes.guess_type(self.filename)[0]

    def read_bytes(self) -> bytes:
        with self.open() as f:
            return f.read()

    async def aread_bytes(self) -> bytes:
        async with await self.aopen() as f:
            return await f.read()

    def set_data(self, data: bytes | str) -> None:
        if not isinstance(self.storage, DBStorage):
            msg = 'Cannot set data on a file that is not stored in a database. Use `File.from_bytes` instead.'
            raise ValueError(msg)

        self.data = self.data_base64_decode(data)
        self.size = len(self.data)
