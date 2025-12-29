from amsdal_models.migration import migrations
from amsdal_utils.models.enums import ModuleType


class Migration(migrations.Migration):
    operations: list[migrations.Operation] = [
        migrations.CreateClass(
            module_type=ModuleType.CORE,
            class_name="ClassProperty",
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
                },
                "meta_class": "TypeMeta",
                "custom_code": "from typing import Any\n\nfrom amsdal_models.builder.validators.dict_validators import validate_non_empty_keys\nfrom pydantic.functional_validators import field_validator\n\nfrom amsdal.models.core.option import *\n\n\n@field_validator('items')\n@classmethod\ndef _non_empty_keys_items(cls: type, value: Any) -> Any:\n    return validate_non_empty_keys(value)",
                "storage_metadata": {"table_name": "ClassProperty", "db_fields": {}, "foreign_keys": {}},
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CORE,
            class_name="ClassObject",
            new_schema={
                "title": "ClassObject",
                "required": ["title", "type", "module_type"],
                "properties": {
                    "title": {"type": "string", "title": "Title"},
                    "type": {"type": "string", "title": "Type"},
                    "module_type": {"type": "string", "title": "Module Type"},
                    "properties": {
                        "type": "dictionary",
                        "items": {
                            "key": {"type": "string"},
                            "value": {"type": "ClassProperty", "title": "ClassProperty"},
                        },
                        "title": "Properties",
                    },
                    "required": {"type": "array", "items": {"type": "string"}, "title": "Required"},
                    "custom_code": {"type": "string", "title": "Custom Code"},
                    "storage_metadata": {"type": "StorageMetadata", "title": "Storage metadata"},
                },
                "custom_code": 'from typing import Any\n\nfrom amsdal_models.builder.validators.dict_validators import validate_non_empty_keys\nfrom pydantic.functional_validators import field_validator\n\nfrom amsdal.models.core.class_property import *\nfrom amsdal.models.core.storage_metadata import *\n\n\n@field_validator(\'properties\')\n@classmethod\ndef _non_empty_keys_properties(cls: type, value: Any) -> Any:\n    return validate_non_empty_keys(value)\n\n@property\ndef display_name(self) -> str:\n    """\n        Returns the display name of the object.\n\n        Returns:\n            str: The display name, which is the title of the object.\n        """\n    return self.title',
                "storage_metadata": {
                    "table_name": "ClassObject",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
        ),
    ]
