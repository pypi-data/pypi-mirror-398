from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from typing import Literal
from typing import Optional

from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field

from amsdal.contrib.frontend_configs.models.frontend_activator_config import *  # noqa: F403
from amsdal.contrib.frontend_configs.models.frontend_config_async_validator import *  # noqa: F403
from amsdal.contrib.frontend_configs.models.frontend_config_control_action import *  # noqa: F403
from amsdal.contrib.frontend_configs.models.frontend_config_option import *  # noqa: F403
from amsdal.contrib.frontend_configs.models.frontend_config_skip_none_base import *  # noqa: F403
from amsdal.contrib.frontend_configs.models.frontend_config_slider_option import *  # noqa: F403
from amsdal.contrib.frontend_configs.models.frontend_config_text_mask import *  # noqa: F403
from amsdal.contrib.frontend_configs.models.frontend_config_validator import *  # noqa: F403

if TYPE_CHECKING:
    from amsdal.contrib.frontend_configs.models.frontend_config_control_action import ActionType

ConfigType = Literal[
    'Bytes',
    'array',
    'attachment',
    'wizard',
    'button',
    'chat',
    'checkbox',
    'date',
    'dateTriplet',
    'datetime',
    'dict',
    'dropzone',
    'email',
    'file',
    'group',
    'group_switch',
    'group_toggle',
    'info-group',
    'infoscreen',
    'multiselect',
    'number',
    'number-operations',
    'number-slider',
    'number_equals',
    'number_initial',
    'number_minus',
    'number_plus',
    'object',
    'object_group',
    'object_latest',
    'password',
    'phone',
    'radio',
    'select',
    'text',
    'textarea',
    'time',
    'toggle',
    'sections',
    'section',
]


class ConditionItem(FrontendConfigSkipNoneBase):  # noqa: F405
    path: str = Field(title='Path')
    condition: str = Field(title='Condition')
    value: Any = Field(default=None, title='Value')


class Condition(FrontendConfigSkipNoneBase):  # noqa: F405
    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    operation: Literal['and', 'or', 'not'] = Field(title='Operation')
    conditions: list[ConditionItem] = Field(title='Conditions')  # noqa: F405


Condition.model_rebuild()


class FrontendControlConfig(FrontendConfigSkipNoneBase):  # noqa: F405
    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    id: str | None = Field(None, title='ID')
    type: ConfigType = Field(title='Type')
    name: str = Field(title='Name')
    label: str | None = Field(None, title='Label')
    required: bool | None = Field(None, title='Required')
    hideLabel: bool | None = Field(None, title='Hide Label')  # noqa: N815
    actions: list[ActionType] | None = Field(None, title='Actions')  # noqa: F405
    validators: list['FrontendConfigValidator'] | None = Field(None, title='Validators')  # noqa: F405
    asyncValidators: list['FrontendConfigAsyncValidator'] | None = Field(  # noqa: F405, N815
        None,
        title='Async Validators',
    )
    activators: list['FrontendActivatorConfig'] | None = Field(None, title='Activators')  # noqa: F405
    additionalText: str | None = Field(None, title='Additional Text')  # noqa: N815
    value: Any | None = Field(None, title='Value')
    placeholder: str | None = Field(None, title='Placeholder')
    options: list['FrontendConfigOption'] | None = Field(None, title='Options')  # noqa: F405
    mask: Optional['FrontendConfigTextMask'] = Field(None, title='Mask')  # noqa: F405
    controls: list['FrontendControlConfig'] | None = Field(None, title='Controls')
    showSearch: bool | None = Field(None, title='Show Search')  # noqa: N815
    sliderOptions: Optional['FrontendConfigSliderOption'] = Field(None, title='Slider Option')  # noqa: F405, N815
    customLabel: list[str] | None = Field(None, title='Custom Label')  # noqa: N815
    control: Optional['FrontendControlConfig'] = Field(None, title='Control')
    entityType: str | None = Field(None, title='Entity Type')  # noqa: N815
    condition: Condition | None = Field(None, title='Condition')  # noqa: F405


FrontendControlConfig.model_rebuild()
