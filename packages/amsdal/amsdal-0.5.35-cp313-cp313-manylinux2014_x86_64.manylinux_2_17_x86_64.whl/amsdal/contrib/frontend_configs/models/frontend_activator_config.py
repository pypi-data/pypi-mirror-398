from typing import Any
from typing import ClassVar

from amsdal_models.builder.validators.options_validators import validate_options
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field
from pydantic.functional_validators import field_validator

from amsdal.contrib.frontend_configs.models.frontend_config_group_validator import *  # noqa: F403


class FrontendActivatorConfig(FrontendConfigGroupValidator):  # noqa: F405
    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    mainControl: str | None = Field(None, title='Main Control')  # noqa: N815
    dependentControls: list[str] | None = Field(None, title='Dependent Controls')  # noqa: N815
    condition: str | None = Field(None, title='Condition')
    value: Any | None = Field(None, title='Value')

    @field_validator('condition')
    @classmethod
    def validate_value_in_options_condition(cls: type, value: Any) -> Any:
        return validate_options(value, options=['eq', 'exist', 'gt', 'gte', 'lt', 'lte', 'neq'])
