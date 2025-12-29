import asyncio
import os
from contextlib import suppress
from pathlib import Path
from typing import IO
from typing import Any
from typing import BinaryIO

from amsdal_models.storage.base import Storage
from amsdal_models.storage.errors import StorageError
from amsdal_models.storage.helpers import build_storage_address
from amsdal_models.storage.types import FileProtocol
from amsdal_utils.config.manager import AmsdalConfigManager

CHUNK_SIZE = 8 * 1024


class FileSystemStorage(Storage):
    """
    Simple filesystem-based storage backend.

    - base_dir: root directory for stored files
    - base_url: URL prefix for building public URLs (optional)
    """

    keeps_local_copy = False

    def __init__(
        self,
        base_dir: str | os.PathLike[Any] | None = None,
        base_url: str | None = None,
        *,
        serialize_base_dir: bool = True,
        serialize_base_url: bool = True,
    ) -> None:
        from amsdal.configs.main import settings

        # If AMSDAL is configured to run in async mode, ensure aiofiles is installed.
        if AmsdalConfigManager().get_config().async_mode:
            try:
                import aiofiles  # noqa: F401
            except ImportError as e:
                msg = (
                    "AMSDAL is configured to run in async mode, but the 'aiofiles' package is not installed.\n"
                    'Please install it to enable async file operations.\n\n'
                    'Example:\n'
                    '    pip install aiofiles\n\n'
                    f'Original error: {e}'
                )
                raise ImportError(msg) from e

        _base_dir = base_dir or settings.MEDIA_ROOT
        _base_url = base_url or settings.MEDIA_URL

        self.base_dir = Path(_base_dir).resolve()
        self.base_url = _base_url
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.serialize_base_dir = serialize_base_dir
        self.serialize_base_url = serialize_base_url

    def save(self, file: FileProtocol, content: BinaryIO) -> str:
        suggested = file.filename
        final_name = self._get_available_name(suggested)
        full_path = self._full_path(final_name)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with full_path.open('wb') as f:
            # Ensure reading from start
            with suppress(Exception):
                if hasattr(content, 'seek'):
                    content.seek(0)

            chunk = content.read(CHUNK_SIZE)

            while chunk:
                f.write(chunk)
                chunk = content.read(CHUNK_SIZE)

        file.storage_address = build_storage_address(self, final_name)
        return final_name

    def open(self, file: FileProtocol, mode: str = 'rb') -> IO[Any]:
        name = self._name_for(file)
        full_path = self._full_path(name)

        if not full_path.exists():
            msg = f'File not found: {name}'
            raise StorageError(msg)
        return full_path.open(mode)

    def delete(self, file: FileProtocol) -> None:
        name = self._name_for(file)
        try:
            self._full_path(name).unlink(missing_ok=True)
        except Exception as e:
            msg = f"Failed to delete '{name}': {e}"
            raise StorageError(msg) from e

    def exists(self, file: FileProtocol) -> bool:
        name = self._name_for(file)
        return self._full_path(name).exists()

    def url(self, file: FileProtocol) -> str:
        name = self._name_for(file)
        if not self.base_url:
            # Return file path as fallback
            return self._full_path(name).as_uri()

        prefix = self.base_url.rstrip('/')
        name_posix = Path(name).as_posix().lstrip('/')

        return f'{prefix}/{name_posix}'

    # ---- async counterparts ----
    async def asave(self, file: FileProtocol, content: BinaryIO) -> str:
        import aiofiles.os

        suggested = file.filename
        final_name = self._get_available_name(suggested)
        full_path = self._full_path(final_name)
        # Ensure directory exists
        await aiofiles.os.makedirs(str(full_path.parent), exist_ok=True)

        # Ensure reading from start
        with suppress(Exception):
            if hasattr(content, 'seek'):
                with suppress(Exception):
                    await asyncio.to_thread(content.seek, 0)

        async with aiofiles.open(str(full_path), 'wb') as f:  # type: ignore[call-arg]
            while True:
                chunk = await asyncio.to_thread(content.read, CHUNK_SIZE)
                if not chunk:
                    break
                await f.write(chunk)

        file.storage_address = build_storage_address(self, final_name)

        return final_name

    async def aopen(self, file: FileProtocol, mode: str = 'rb') -> Any:
        import aiofiles.ospath

        name = self._name_for(file)
        full_path = self._full_path(name)

        if not await aiofiles.ospath.exists(str(full_path)):
            msg = f'File not found: {name}'
            raise StorageError(msg)

        return aiofiles.open(str(full_path), mode)  # type: ignore[call-overload]

    async def adelete(self, file: FileProtocol) -> None:
        import aiofiles.os
        import aiofiles.ospath

        name = self._name_for(file)
        full_path = self._full_path(name)

        if await aiofiles.ospath.exists(str(full_path)):
            try:
                await aiofiles.os.remove(str(full_path))
            except Exception as e:  # pragma: no cover - error path
                msg = f"Failed to delete '{name}': {e}"
                raise StorageError(msg) from e

    async def aexists(self, file: FileProtocol) -> bool:
        import aiofiles.ospath

        name = self._name_for(file)
        return await aiofiles.ospath.exists(str(self._full_path(name)))

    async def aurl(self, file: FileProtocol) -> str:
        # Pure computation; no disk I/O.
        return self.url(file)

    def _full_path(self, name: str) -> Path:
        # Sanitize name to avoid path traversal
        norm = Path(name).as_posix().lstrip('/')

        return (self.base_dir / norm).resolve()

    def _get_available_name(self, name: str) -> str:
        # If file exists, add suffixes to avoid collision
        candidate = Path(name)
        base = candidate.stem
        suffix = candidate.suffix
        parent = candidate.parent.as_posix()
        i = 0
        final = candidate.as_posix()

        # Check filesystem directly to avoid relying on public exists signature
        while self._full_path(final).exists():
            i += 1
            new_name = f'{base}_{i}{suffix}'
            final = str(Path(parent) / new_name) if parent and parent != '.' else new_name
        return final

    def _name_for(self, file: FileProtocol) -> str:
        if getattr(file, 'storage_address', None) and getattr(file.storage_address, 'ref', None) is not None:
            if getattr(file.storage_address.ref, 'object_id', None) is not None:  # type: ignore[union-attr]
                return str(file.storage_address.ref.object_id)  # type: ignore[union-attr]
        return file.filename

    def _export_kwargs(self) -> dict[str, Any]:
        kwargs = {}

        if self.serialize_base_dir:
            kwargs['base_dir'] = str(self.base_dir)

        if self.serialize_base_url:
            kwargs['base_url'] = self.base_url

        return kwargs
