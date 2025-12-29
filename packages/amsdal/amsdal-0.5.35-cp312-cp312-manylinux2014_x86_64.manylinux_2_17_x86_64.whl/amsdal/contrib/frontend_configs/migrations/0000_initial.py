from amsdal_models.migration import migrations
from amsdal_utils.models.enums import ModuleType


class Migration(migrations.Migration):
    operations: list[migrations.Operation] = [
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="FrontendConfigSkipNoneBase",
            new_schema={
                "title": "FrontendConfigSkipNoneBase",
                "properties": {},
                "meta_class": "TypeMeta",
                "custom_code": "from typing import Any\n\n\ndef model_dump(self, **kwargs: Any) -> dict[str, Any]:\n    kwargs['exclude_none'] = True\n    return super().model_dump(**kwargs)\n\ndef model_dump_json(self, **kwargs: Any) -> str:\n    kwargs['exclude_none'] = True\n    return super().model_dump_json(**kwargs)",
                "storage_metadata": {"table_name": "FrontendConfigSkipNoneBase", "db_fields": {}, "foreign_keys": {}},
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="FrontendConfigAsyncValidator",
            new_schema={
                "title": "FrontendConfigAsyncValidator",
                "type": "FrontendConfigSkipNoneBase",
                "properties": {"endpoint": {"type": "string", "title": "Endpoint"}},
                "meta_class": "TypeMeta",
                "custom_code": "from typing import Any\n\nfrom amsdal.contrib.frontend_configs.models.frontend_config_skip_none_base import *\n\n\ndef model_dump(self, **kwargs: Any) -> dict[str, Any]:\n    kwargs['exclude_none'] = True\n    return super().model_dump(**kwargs)\n\ndef model_dump_json(self, **kwargs: Any) -> str:\n    kwargs['exclude_none'] = True\n    return super().model_dump_json(**kwargs)",
                "storage_metadata": {"table_name": "FrontendConfigAsyncValidator", "db_fields": {}, "foreign_keys": {}},
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="FrontendConfigControlAction",
            new_schema={
                "title": "FrontendConfigControlAction",
                "type": "FrontendConfigSkipNoneBase",
                "required": ["action", "text", "type"],
                "properties": {
                    "action": {"type": "string", "title": "Action"},
                    "text": {"type": "string", "title": "Text"},
                    "type": {"type": "string", "title": "Type"},
                    "dataLayerEvent": {"type": "string", "title": "Data Layer Event"},
                    "activator": {"type": "string", "title": "Activator"},
                    "icon": {"type": "string", "title": "Icon"},
                },
                "meta_class": "TypeMeta",
                "custom_code": "from typing import Any\n\nfrom amsdal_models.builder.validators.options_validators import validate_options\nfrom pydantic import field_validator\n\nfrom amsdal.contrib.frontend_configs.models.frontend_config_skip_none_base import *\n\n\n@field_validator('action', mode='after')\n@classmethod\ndef validate_action(cls, v: str) -> str:\n    \"\"\"\n        Validates the action string to ensure it is one of the allowed values.\n\n        This method checks if the action string starts with 'navigate::' or is one of the predefined\n        actions. If the action string is invalid, it raises a ValueError.\n\n        Args:\n            cls: The class this method is attached to.\n            v (str): The action string to validate.\n\n        Returns:\n            str: The validated action string.\n\n        Raises:\n            ValueError: If the action string is not valid.\n        \"\"\"\n    if not v.startswith('navigate::') and v not in ['goPrev', 'goNext', 'goNextWithSubmit', 'submit', 'submitWithDataLayer']:\n        msg = 'Action must be one of: goPrev, goNext, goNextWithSubmit, submit, submitWithDataLayer, navigate::{string}'\n        raise ValueError(msg)\n    return v\n\n@field_validator('type')\n@classmethod\ndef validate_value_in_options_type(cls: type, value: Any) -> Any:\n    return validate_options(value, options=['action-button', 'arrow-next', 'arrow-prev', 'text-next', 'text-prev'])\n\ndef model_dump(self, **kwargs: Any) -> dict[str, Any]:\n    kwargs['exclude_none'] = True\n    return super().model_dump(**kwargs)\n\ndef model_dump_json(self, **kwargs: Any) -> str:\n    kwargs['exclude_none'] = True\n    return super().model_dump_json(**kwargs)",
                "storage_metadata": {"table_name": "FrontendConfigControlAction", "db_fields": {}, "foreign_keys": {}},
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="FrontendConfigGroupValidator",
            new_schema={
                "title": "FrontendConfigGroupValidator",
                "type": "FrontendConfigSkipNoneBase",
                "properties": {
                    "mainControl": {"type": "string", "title": "Main Control"},
                    "dependentControls": {"type": "array", "items": {"type": "string"}, "title": "Dependent Controls"},
                    "condition": {"type": "string", "title": "Condition"},
                },
                "meta_class": "TypeMeta",
                "custom_code": "from typing import Any\n\nfrom amsdal_models.builder.validators.options_validators import validate_options\nfrom pydantic.functional_validators import field_validator\n\nfrom amsdal.contrib.frontend_configs.models.frontend_config_skip_none_base import *\n\n\n@field_validator('condition')\n@classmethod\ndef validate_value_in_options_condition(cls: type, value: Any) -> Any:\n    return validate_options(value, options=['eq', 'exist', 'gt', 'gte', 'lt', 'lte', 'neq'])\n\ndef model_dump(self, **kwargs: Any) -> dict[str, Any]:\n    kwargs['exclude_none'] = True\n    return super().model_dump(**kwargs)\n\ndef model_dump_json(self, **kwargs: Any) -> str:\n    kwargs['exclude_none'] = True\n    return super().model_dump_json(**kwargs)",
                "storage_metadata": {"table_name": "FrontendConfigGroupValidator", "db_fields": {}, "foreign_keys": {}},
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="FrontendConfigOption",
            new_schema={
                "title": "FrontendConfigOption",
                "type": "FrontendConfigSkipNoneBase",
                "properties": {
                    "label": {"type": "string", "title": "Label"},
                    "value": {"type": "string", "title": "Value"},
                },
                "meta_class": "TypeMeta",
                "custom_code": "from typing import Any\n\nfrom amsdal.contrib.frontend_configs.models.frontend_config_skip_none_base import *\n\n\ndef model_dump(self, **kwargs: Any) -> dict[str, Any]:\n    kwargs['exclude_none'] = True\n    return super().model_dump(**kwargs)\n\ndef model_dump_json(self, **kwargs: Any) -> str:\n    kwargs['exclude_none'] = True\n    return super().model_dump_json(**kwargs)",
                "storage_metadata": {"table_name": "FrontendConfigOption", "db_fields": {}, "foreign_keys": {}},
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="FrontendConfigSliderOption",
            new_schema={
                "title": "FrontendConfigSliderOption",
                "type": "FrontendConfigSkipNoneBase",
                "properties": {
                    "min": {"type": "number", "title": "Minimum"},
                    "max": {"type": "number", "title": "Maximum"},
                    "range": {"type": "boolean", "title": "Range"},
                },
                "meta_class": "TypeMeta",
                "custom_code": "from typing import Any\n\nfrom amsdal.contrib.frontend_configs.models.frontend_config_skip_none_base import *\n\n\ndef model_dump(self, **kwargs: Any) -> dict[str, Any]:\n    kwargs['exclude_none'] = True\n    return super().model_dump(**kwargs)\n\ndef model_dump_json(self, **kwargs: Any) -> str:\n    kwargs['exclude_none'] = True\n    return super().model_dump_json(**kwargs)",
                "storage_metadata": {"table_name": "FrontendConfigSliderOption", "db_fields": {}, "foreign_keys": {}},
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="FrontendConfigTextMask",
            new_schema={
                "title": "FrontendConfigTextMask",
                "type": "FrontendConfigSkipNoneBase",
                "required": ["mask_string"],
                "properties": {
                    "mask_string": {"type": "string", "title": "Mask String"},
                    "prefix": {"type": "string", "title": "Prefix"},
                    "suffix": {"type": "string", "title": "Suffix"},
                    "thousands_separator": {"type": "string", "title": "Thousands Separator"},
                },
                "meta_class": "TypeMeta",
                "custom_code": "from typing import Any\n\nfrom amsdal.contrib.frontend_configs.models.frontend_config_skip_none_base import *\n\n\ndef model_dump(self, **kwargs: Any) -> dict[str, Any]:\n    kwargs['exclude_none'] = True\n    return super().model_dump(**kwargs)\n\ndef model_dump_json(self, **kwargs: Any) -> str:\n    kwargs['exclude_none'] = True\n    return super().model_dump_json(**kwargs)",
                "storage_metadata": {"table_name": "FrontendConfigTextMask", "db_fields": {}, "foreign_keys": {}},
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="FrontendActivatorConfig",
            new_schema={
                "title": "FrontendActivatorConfig",
                "type": "FrontendConfigGroupValidator",
                "properties": {
                    "mainControl": {"type": "string", "title": "Main Control"},
                    "dependentControls": {"type": "array", "items": {"type": "string"}, "title": "Dependent Controls"},
                    "condition": {"type": "string", "title": "Condition"},
                    "value": {"type": "anything", "title": "Value"},
                },
                "meta_class": "TypeMeta",
                "custom_code": "from typing import Any\n\nfrom amsdal_models.builder.validators.options_validators import validate_options\nfrom pydantic.functional_validators import field_validator\n\nfrom amsdal.contrib.frontend_configs.models.frontend_config_group_validator import *\nfrom amsdal.contrib.frontend_configs.models.frontend_config_skip_none_base import *\n\n\n@field_validator('condition')\n@classmethod\ndef validate_value_in_options_condition(cls: type, value: Any) -> Any:\n    return validate_options(value, options=['eq', 'exist', 'gt', 'gte', 'lt', 'lte', 'neq'])\n\ndef model_dump(self, **kwargs: Any) -> dict[str, Any]:\n    kwargs['exclude_none'] = True\n    return super().model_dump(**kwargs)\n\ndef model_dump_json(self, **kwargs: Any) -> str:\n    kwargs['exclude_none'] = True\n    return super().model_dump_json(**kwargs)",
                "storage_metadata": {"table_name": "FrontendActivatorConfig", "db_fields": {}, "foreign_keys": {}},
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="FrontendConfigValidator",
            new_schema={
                "title": "FrontendConfigValidator",
                "type": "FrontendConfigGroupValidator",
                "properties": {
                    "mainControl": {"type": "string", "title": "Main Control"},
                    "dependentControls": {"type": "array", "items": {"type": "string"}, "title": "Dependent Controls"},
                    "condition": {"type": "string", "title": "Condition"},
                    "function": {"type": "string", "title": "Function"},
                    "value": {"type": "string", "title": "Value"},
                },
                "meta_class": "TypeMeta",
                "custom_code": "from typing import Any\n\nfrom amsdal_models.builder.validators.options_validators import validate_options\nfrom pydantic.functional_validators import field_validator\n\nfrom amsdal.contrib.frontend_configs.models.frontend_config_group_validator import *\nfrom amsdal.contrib.frontend_configs.models.frontend_config_skip_none_base import *\n\n\n@field_validator('condition')\n@classmethod\ndef validate_value_in_options_condition(cls: type, value: Any) -> Any:\n    return validate_options(value, options=['eq', 'exist', 'gt', 'gte', 'lt', 'lte', 'neq'])\n\n@field_validator('function')\n@classmethod\ndef validate_value_in_options_function(cls: type, value: Any) -> Any:\n    return validate_options(value, options=['max', 'maxLength', 'min', 'minLength', 'pattern', 'required'])\n\ndef model_dump(self, **kwargs: Any) -> dict[str, Any]:\n    kwargs['exclude_none'] = True\n    return super().model_dump(**kwargs)\n\ndef model_dump_json(self, **kwargs: Any) -> str:\n    kwargs['exclude_none'] = True\n    return super().model_dump_json(**kwargs)",
                "storage_metadata": {"table_name": "FrontendConfigValidator", "db_fields": {}, "foreign_keys": {}},
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="FrontendControlConfig",
            new_schema={
                "title": "FrontendControlConfig",
                "type": "FrontendConfigSkipNoneBase",
                "required": ["type", "name"],
                "properties": {
                    "type": {"type": "string", "title": "Type"},
                    "name": {"type": "string", "title": "Name"},
                    "label": {"type": "string", "title": "Label"},
                    "required": {"type": "boolean", "title": "Required"},
                    "hideLabel": {"type": "boolean", "title": "Hide Label"},
                    "actions": {
                        "type": "array",
                        "items": {"type": "FrontendConfigControlAction", "title": "FrontendConfigControlAction"},
                        "title": "Actions",
                    },
                    "validators": {
                        "type": "array",
                        "items": {"type": "FrontendConfigValidator", "title": "FrontendConfigValidator"},
                        "title": "Validators",
                    },
                    "asyncValidators": {
                        "type": "array",
                        "items": {"type": "FrontendConfigAsyncValidator", "title": "FrontendConfigAsyncValidator"},
                        "title": "Async Validators",
                    },
                    "activators": {
                        "type": "array",
                        "items": {"type": "FrontendActivatorConfig", "title": "FrontendActivatorConfig"},
                        "title": "Activators",
                    },
                    "additionalText": {"type": "string", "title": "Additional Text"},
                    "value": {"type": "anything", "title": "Value"},
                    "placeholder": {"type": "string", "title": "Placeholder"},
                    "options": {
                        "type": "array",
                        "items": {"type": "FrontendConfigOption", "title": "FrontendConfigOption"},
                        "title": "Options",
                    },
                    "mask": {"type": "FrontendConfigTextMask", "title": "Mask"},
                    "controls": {
                        "type": "array",
                        "items": {"type": "FrontendControlConfig", "title": "FrontendControlConfig"},
                        "title": "Controls",
                    },
                    "showSearch": {"type": "boolean", "title": "Show Search"},
                    "sliderOptions": {"type": "FrontendConfigSliderOption", "title": "Slider Option"},
                    "customLabel": {"type": "array", "items": {"type": "string"}, "title": "Custom Label"},
                    "control": {"type": "FrontendControlConfig", "title": "Control"},
                    "entityType": {"type": "string", "title": "Entity Type"},
                },
                "meta_class": "TypeMeta",
                "custom_code": "from typing import Any\n\nfrom amsdal_models.builder.validators.options_validators import validate_options\nfrom pydantic.functional_validators import field_validator\n\nfrom amsdal.contrib.frontend_configs.models.frontend_activator_config import *\nfrom amsdal.contrib.frontend_configs.models.frontend_config_async_validator import *\nfrom amsdal.contrib.frontend_configs.models.frontend_config_control_action import *\nfrom amsdal.contrib.frontend_configs.models.frontend_config_option import *\nfrom amsdal.contrib.frontend_configs.models.frontend_config_skip_none_base import *\nfrom amsdal.contrib.frontend_configs.models.frontend_config_slider_option import *\nfrom amsdal.contrib.frontend_configs.models.frontend_config_text_mask import *\nfrom amsdal.contrib.frontend_configs.models.frontend_config_validator import *\n\n\n@field_validator('type')\n@classmethod\ndef validate_value_in_options_type(cls: type, value: Any) -> Any:\n    return validate_options(value, options=['Bytes', 'array', 'checkbox', 'date', 'dateTriplet', 'datetime', 'dict', 'dropzone', 'email', 'file', 'group', 'group_switch', 'group_toggle', 'info-group', 'infoscreen', 'multiselect', 'number', 'number-operations', 'number-slider', 'number_equals', 'number_initial', 'number_minus', 'number_plus', 'object', 'object_group', 'object_latest', 'password', 'phone', 'radio', 'select', 'text', 'textarea', 'time', 'toggle'])\n\ndef model_dump(self, **kwargs: Any) -> dict[str, Any]:\n    kwargs['exclude_none'] = True\n    return super().model_dump(**kwargs)\n\ndef model_dump_json(self, **kwargs: Any) -> str:\n    kwargs['exclude_none'] = True\n    return super().model_dump_json(**kwargs)",
                "storage_metadata": {"table_name": "FrontendControlConfig", "db_fields": {}, "foreign_keys": {}},
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="FrontendModelConfig",
            new_schema={
                "title": "FrontendModelConfig",
                "required": ["class_name"],
                "properties": {
                    "class_name": {"type": "string", "title": "Class Name"},
                    "control": {"type": "FrontendControlConfig", "title": "Control"},
                },
                "custom_code": "from amsdal.contrib.frontend_configs.models.frontend_control_config import *",
                "storage_metadata": {
                    "table_name": "FrontendModelConfig",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
        ),
    ]
