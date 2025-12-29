from amsdal_models.migration import migrations
from amsdal_utils.models.enums import ModuleType


class Migration(migrations.Migration):
    operations: list[migrations.Operation] = [
        migrations.UpdateClass(
            module_type=ModuleType.CORE,
            class_name="File",
            old_schema={
                "title": "File",
                "required": ["filename", "data"],
                "properties": {
                    "filename": {"type": "string", "title": "Filename"},
                    "data": {"type": "binary", "title": "Data"},
                    "size": {"type": "number", "title": "Size"},
                },
                "custom_code": 'import base64\nfrom pathlib import Path\nfrom typing import BinaryIO\n\nfrom pydantic import field_validator\n\n\n@classmethod\ndef from_file(cls, file_or_path: Path | BinaryIO) -> \'File\':\n    """\n        Creates a `File` object from a file path or a binary file object.\n\n        Args:\n            file_or_path (Path | BinaryIO): The file path or binary file object.\n\n        Returns:\n            File: The created `File` object.\n\n        Raises:\n            ValueError: If the provided path is a directory.\n        """\n    if isinstance(file_or_path, Path):\n        if file_or_path.is_dir():\n            msg = f\'{file_or_path} is a directory\'\n            raise ValueError(msg)\n        data = file_or_path.read_bytes()\n        filename = file_or_path.name\n    else:\n        file_or_path.seek(0)\n        data = file_or_path.read()\n        filename = Path(file_or_path.name).name\n    return cls(data=data, filename=filename)\n\n@field_validator(\'data\')\n@classmethod\ndef data_base64_decode(cls, v: bytes) -> bytes:\n    """\n        Decodes a base64-encoded byte string if it is base64-encoded.\n\n        This method checks if the provided byte string is base64-encoded and decodes it if true.\n        If the byte string is not base64-encoded, it returns the original byte string.\n\n        Args:\n            cls: The class this method belongs to.\n            v (bytes): The byte string to be checked and potentially decoded.\n\n        Returns:\n            bytes: The decoded byte string if it was base64-encoded, otherwise the original byte string.\n        """\n    is_base64: bool = False\n    try:\n        is_base64 = base64.b64encode(base64.b64decode(v)) == v\n    except Exception:\n        ...\n    if is_base64:\n        return base64.b64decode(v)\n    return v\n\n@property\ndef mimetype(self) -> str | None:\n    """\n        Returns the MIME type of the file based on its filename.\n\n        This method uses the `mimetypes` module to guess the MIME type of the file.\n\n        Returns:\n            str | None: The guessed MIME type of the file, or None if it cannot be determined.\n        """\n    import mimetypes\n    return mimetypes.guess_type(self.filename)[0]\n\nasync def apre_create(self) -> None:\n    """\n        Prepares the object for creation by setting its size attribute.\n\n        This method calculates the size of the object\'s data and assigns it to the size attribute.\n        If the data is None, it defaults to an empty byte string.\n\n        Args:\n            None\n        """\n    self.size = len(self.data or b\'\')\n\nasync def apre_update(self) -> None:\n    """\n        Prepares the object for update by setting its size attribute.\n\n        This method calculates the size of the object\'s data and assigns it to the size attribute.\n        If the data is None, it defaults to an empty byte string.\n\n        Args:\n            None\n        """\n    self.size = len(self.data or b\'\')\n\ndef __repr__(self) -> str:\n    return f\'File<{self.filename}>({self.size or len(self.data) or 0} bytes)\'\n\ndef __str__(self) -> str:\n    return repr(self)\n\ndef pre_create(self) -> None:\n    """\n        Prepares the object for creation by setting its size attribute.\n\n        This method calculates the size of the object\'s data and assigns it to the size attribute.\n        If the data is None, it defaults to an empty byte string.\n\n        Args:\n            None\n        """\n    self.size = len(self.data or b\'\')\n\ndef pre_update(self) -> None:\n    """\n        Prepares the object for update by setting its size attribute.\n\n        This method calculates the size of the object\'s data and assigns it to the size attribute.\n        If the data is None, it defaults to an empty byte string.\n\n        Args:\n            None\n        """\n    self.size = len(self.data or b\'\')\n\ndef to_file(self, file_or_path: Path | BinaryIO) -> None:\n    """\n        Writes the object\'s data to a file path or a binary file object.\n\n        Args:\n            file_or_path (Path | BinaryIO): The file path or binary file object where the data will be written.\n\n        Returns:\n            None\n\n        Raises:\n            ValueError: If the provided path is a directory.\n        """\n    if isinstance(file_or_path, Path):\n        if file_or_path.is_dir():\n            file_or_path = file_or_path / self.name\n        file_or_path.write_bytes(self.data)\n    else:\n        file_or_path.write(self.data)\n        file_or_path.seek(0)',
                "storage_metadata": {
                    "table_name": "File",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
            new_schema={
                "title": "File",
                "required": ["filename"],
                "properties": {
                    "filename": {"type": "string", "title": "Filename"},
                    "data": {"type": "binary", "title": "Data"},
                    "size": {"type": "number", "title": "Size"},
                    "storage_address": {"type": "anything", "title": "Storage Reference"},
                },
                "custom_code": 'import base64\nimport io\nfrom contextlib import suppress\nfrom pathlib import Path\nfrom typing import IO\nfrom typing import Any\nfrom typing import BinaryIO\n\nfrom amsdal_models.storage.backends.db import DBStorage\nfrom amsdal_models.storage.base import Storage\nfrom pydantic import model_validator\n\n\n@classmethod\ndef data_base64_decode(cls, data: Any) -> bytes:\n    if isinstance(data, str):\n        data = data.encode(\'utf-8\')\n    is_base64: bool = False\n    with suppress(Exception):\n        is_base64 = base64.b64encode(base64.b64decode(data)) == data\n    if is_base64:\n        return base64.b64decode(data)\n    return data\n\n@classmethod\ndef from_bytes(cls, filename: str, data: bytes) -> \'File\':\n    """\n        Creates a `File` object from a byte string.\n\n        Args:\n            filename (str): The filename of the file.\n            data (bytes): The byte string containing the file data.:\n\n        Returns:\n            File: The created `File` object.\n        """\n    obj = cls(filename=filename, data=data, size=len(data))\n    obj._needs_persist = True\n    return obj\n\n@classmethod\ndef from_file(cls, file_or_path: Path | BinaryIO) -> \'File\':\n    """\n        Creates a `File` object from a file path or a binary file object.\n\n        Args:\n            file_or_path (Path | BinaryIO): The file path or binary file object.\n\n        Returns:\n            File: The created `File` object.\n\n        Raises:\n            ValueError: If the provided path is a directory.\n        """\n    f: BinaryIO | io.BufferedReader\n    if isinstance(file_or_path, Path):\n        if file_or_path.is_dir():\n            msg = f\'{file_or_path} is a directory\'\n            raise ValueError(msg)\n        f = file_or_path.open(\'rb\')\n        filename = file_or_path.name\n        size = file_or_path.stat().st_size\n    else:\n        f = file_or_path\n        filename = Path(getattr(f, \'name\', \'unnamed\')).name\n        try:\n            if f.seekable():\n                f.seek(0, io.SEEK_END)\n                size = f.tell()\n                f.seek(0)\n            else:\n                size = None\n        except (OSError, AttributeError):\n            size = None\n    obj = cls(filename=filename, size=size)\n    obj._source = f\n    obj._needs_persist = True\n    return obj\n\n@model_validator(mode=\'before\')\n@classmethod\ndef validate_model_data(cls, data: Any) -> Any:\n    if isinstance(data, dict):\n        if \'data\' in data:\n            if data[\'data\']:\n                data[\'data\'] = cls.data_base64_decode(data[\'data\'])\n                data[\'size\'] = len(data[\'data\'])\n            else:\n                data[\'size\'] = 0\n    return data\n\n@property\ndef mimetype(self) -> str | None:\n    """\n        Returns the MIME type of the file based on its filename.\n\n        This method uses the `mimetypes` module to guess the MIME type of the file.\n\n        Returns:\n            str | None: The guessed MIME type of the file, or None if it cannot be determined.\n        """\n    import mimetypes\n    return mimetypes.guess_type(self.filename)[0]\n\n@property\ndef storage(self) -> Storage:\n    from amsdal.storages import default_storage\n    if self._storage:\n        return self._storage\n    if self.storage_address:\n        return Storage.from_storage_spec({\'storage_class\': self.storage_address.ref.resource})\n    return default_storage()\n\nasync def aopen(self, mode: str=\'rb\') -> Any:\n    """\n        Async variant of open().\n\n        Uses the resolved storage to call aopen(); if the backend does not implement\n        async, falls back to the sync open().\n        """\n    try:\n        return await self.storage.aopen(self, mode)\n    except NotImplementedError:\n        return self.storage.open(self, mode)\n\nasync def apre_create(self) -> None:\n    if self._needs_persist:\n        from amsdal_models.storage.persistence import apersist_file\n        await apersist_file(self, storage=self.storage)\n\nasync def apre_update(self) -> None:\n    if self._needs_persist:\n        from amsdal_models.storage.persistence import apersist_file\n        await apersist_file(self, storage=self.storage)\n\nasync def aread_bytes(self) -> bytes:\n    async with await self.aopen() as f:\n        return await f.read()\n\nasync def aurl(self) -> str:\n    """\n        Async variant of url().\n\n        Uses the resolved storage to call aurl(); if the backend does not implement\n        async, falls back to the sync url().\n        """\n    try:\n        return await self.storage.aurl(self)\n    except NotImplementedError:\n        return self.storage.url(self)\n\ndef __repr__(self) -> str:\n    return f"File<{self.filename}>({self.size or len(self.data or \'\') or 0} bytes)"\n\ndef __str__(self) -> str:\n    return repr(self)\n\ndef open(self, mode: str=\'rb\') -> IO[Any]:\n    """\n        Open a binary stream for reading (or other modes if supported) using storage_address.\n\n        Raises StateError if storage_address is missing.\n        """\n    return self.storage.open(self, mode)\n\ndef pre_create(self) -> None:\n    if self._needs_persist:\n        from amsdal_models.storage.persistence import persist_file\n        persist_file(self, storage=self.storage)\n\ndef pre_update(self) -> None:\n    if self._needs_persist:\n        from amsdal_models.storage.persistence import persist_file\n        persist_file(self, storage=self.storage)\n\ndef read_bytes(self) -> bytes:\n    with self.open() as f:\n        return f.read()\n\ndef set_data(self, data: bytes | str) -> None:\n    if not isinstance(self.storage, DBStorage):\n        msg = \'Cannot set data on a file that is not stored in a database. Use `File.from_bytes` instead.\'\n        raise ValueError(msg)\n    self.data = self.data_base64_decode(data)\n    self.size = len(self.data)\n    self._needs_persist = True\n\ndef to_file(self, file_or_path: Path | BinaryIO) -> None:\n    """\n        Writes the object\'s data to a file path or a binary file object.\n\n        Args:\n            file_or_path (Path | BinaryIO): The file path or binary file object where the data will be written.\n\n        Returns:\n            None\n\n        Raises:\n            ValueError: If the provided path is a directory.\n        """\n    with self.open() as f:\n        if isinstance(file_or_path, Path):\n            if file_or_path.is_dir():\n                file_or_path = file_or_path / self.name\n            file_or_path.write_bytes(f.read())\n        else:\n            file_or_path.write(f.read())\n            file_or_path.seek(0)\n\ndef url(self) -> str:\n    """\n        Return a URL for this file using its storage_address.\n\n        Raises StateError if storage_address is missing.\n        """\n    return self.storage.url(self)',
                "storage_metadata": {
                    "table_name": "File",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
        ),
        migrations.UpdateClass(
            module_type=ModuleType.CORE,
            class_name="ClassProperty",
            old_schema={
                "title": "ClassProperty",
                "required": ["type"],
                "properties": {
                    "title": {"type": "string", "title": "Title"},
                    "type": {"type": "string", "title": "Type"},
                    "default": {"type": "anything", "title": "Default"},
                    "options": {"type": "array", "items": {"type": "Option", "title": "Option"}, "title": "Options"},
                    "items": {
                        "type": "dictionary",
                        "items": {"key": {"type": "string"}, "value": {"type": "anything"}},
                        "title": "Items",
                    },
                    "discriminator": {"type": "string", "title": "Discriminator"},
                },
                "meta_class": "TypeMeta",
                "custom_code": "from typing import Any\n\nfrom amsdal_models.builder.validators.dict_validators import validate_non_empty_keys\nfrom pydantic.functional_validators import field_validator\n\nfrom amsdal.models.core.option import *\n\n\n@field_validator('items')\n@classmethod\ndef _non_empty_keys_items(cls: type, value: Any) -> Any:\n    return validate_non_empty_keys(value)",
                "storage_metadata": {"table_name": "ClassProperty", "db_fields": {}, "foreign_keys": {}},
            },
            new_schema={
                "title": "ClassProperty",
                "required": ["type"],
                "properties": {
                    "title": {"type": "string", "title": "Title"},
                    "type": {"type": "string", "title": "Type"},
                    "default": {"type": "anything", "title": "Default"},
                    "options": {"type": "array", "items": {"type": "Option", "title": "Option"}, "title": "Options"},
                    "items": {
                        "type": "dictionary",
                        "items": {"key": {"type": "string"}, "value": {"type": "anything"}},
                        "title": "Items",
                    },
                    "discriminator": {"type": "string", "title": "Discriminator"},
                    "extra": {
                        "type": "dictionary",
                        "items": {"key": {"type": "string"}, "value": {"type": "anything"}},
                        "title": "Extra",
                    },
                },
                "meta_class": "TypeMeta",
                "custom_code": "from typing import Any\n\nfrom amsdal_models.builder.validators.dict_validators import validate_non_empty_keys\nfrom pydantic.functional_validators import field_validator\n\nfrom amsdal.models.core.option import *\n\n\n@field_validator('items')\n@classmethod\ndef _non_empty_keys_items(cls: type, value: Any) -> Any:\n    return validate_non_empty_keys(value)",
                "storage_metadata": {"table_name": "ClassProperty", "db_fields": {}, "foreign_keys": {}},
            },
        ),
    ]
