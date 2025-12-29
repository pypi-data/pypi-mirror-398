from amsdal_models.migration import migrations
from amsdal_utils.models.enums import ModuleType


class Migration(migrations.Migration):
    operations: list[migrations.Operation] = [
        migrations.CreateClass(
            module_type=ModuleType.CORE,
            class_name="File",
            new_schema={
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
        ),
        migrations.CreateClass(
            module_type=ModuleType.CORE,
            class_name="Fixture",
            new_schema={
                "title": "Fixture",
                "required": ["external_id", "data"],
                "properties": {
                    "class_name": {"type": "string", "title": "Class Name"},
                    "order": {"type": "number", "title": "Order"},
                    "external_id": {"type": "string", "title": "External ID"},
                    "data": {
                        "type": "dictionary",
                        "items": {"key": {"type": "string"}, "value": {"type": "anything"}},
                        "title": "Data",
                    },
                },
                "custom_code": "from typing import Any\n\nfrom amsdal_models.builder.validators.dict_validators import validate_non_empty_keys\nfrom pydantic.functional_validators import field_validator\n\n\n@field_validator('data')\n@classmethod\ndef _non_empty_keys_data(cls: type, value: Any) -> Any:\n    return validate_non_empty_keys(value)",
                "storage_metadata": {
                    "table_name": "Fixture",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "unique": [["external_id"]],
                    "foreign_keys": {},
                },
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CORE,
            class_name="Option",
            new_schema={
                "title": "Option",
                "required": ["key", "value"],
                "properties": {
                    "key": {"type": "string", "title": "Key"},
                    "value": {"type": "string", "title": "Value Type"},
                },
                "meta_class": "TypeMeta",
                "storage_metadata": {"table_name": "Option", "db_fields": {}, "foreign_keys": {}},
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CORE,
            class_name="StorageMetadata",
            new_schema={
                "title": "StorageMetadata",
                "properties": {
                    "table_name": {"type": "string", "title": "Table name"},
                    "db_fields": {
                        "type": "dictionary",
                        "items": {"key": {"type": "string"}, "value": {"type": "array", "items": {"type": "string"}}},
                        "title": "Database fields",
                    },
                    "primary_key": {"type": "array", "items": {"type": "string"}, "title": "Primary key fields"},
                    "indexed": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "string"}},
                        "title": "Indexed",
                    },
                    "unique": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "string"}},
                        "title": "Unique Fields",
                    },
                },
                "meta_class": "TypeMeta",
                "storage_metadata": {"table_name": "StorageMetadata", "db_fields": {}, "foreign_keys": {}},
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CORE,
            class_name="Validator",
            new_schema={
                "title": "Validator",
                "required": ["name", "data"],
                "properties": {
                    "name": {"type": "string", "title": "Validator Name"},
                    "data": {"type": "anything", "title": "Validator Data"},
                },
                "meta_class": "TypeMeta",
                "storage_metadata": {"table_name": "Validator", "db_fields": {}, "foreign_keys": {}},
            },
        ),
    ]
