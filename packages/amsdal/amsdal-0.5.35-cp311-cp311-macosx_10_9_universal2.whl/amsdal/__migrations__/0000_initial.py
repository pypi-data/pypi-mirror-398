from amsdal_models.migration import migrations
from amsdal_utils.models.enums import ModuleType


class Migration(migrations.Migration):
    operations: list[migrations.Operation] = [
        migrations.CreateClass(
            module_type=ModuleType.TYPE,
            class_name='Object',
            new_schema={
                "title": "Object",
                "required": ["title", "type", "module_type"],
                "properties": {
                    "title": {"type": "string", "title": "Title"},
                    "type": {"type": "string", "title": "Type"},
                    "module_type": {"type": "string", "title": "Module Type"},
                    "default": {"type": "anything", "title": "Default"},
                    "properties": {
                        "type": "dictionary",
                        "items": {"key": {"type": "string"}, "value": {"type": "anything"}},
                        "title": "Properties",
                    },
                    "required": {"type": "array", "items": {"type": "string"}, "title": "Required"},
                    "custom_code": {"type": "string", "title": "Custom Code"},
                    "meta_class": {"type": "string", "title": "Meta Class"},
                },
                "custom_code": "from typing import Any\n\nfrom amsdal_models.builder.validators.dict_validators import validate_non_empty_keys\nfrom pydantic.functional_validators import field_validator\n\n\n@field_validator('properties')\n@classmethod\ndef _non_empty_keys_properties(cls: type, value: Any) -> Any:\n    return validate_non_empty_keys(value)",
                "storage_metadata": {
                    "table_name": "Object",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
        ),
    ]
