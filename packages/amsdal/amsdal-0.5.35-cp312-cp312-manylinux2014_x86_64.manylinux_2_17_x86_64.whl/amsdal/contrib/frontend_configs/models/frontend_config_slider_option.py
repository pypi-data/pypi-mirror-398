from typing import ClassVar

from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field

from amsdal.contrib.frontend_configs.models.frontend_config_skip_none_base import *  # noqa: F403


class FrontendConfigSliderOption(FrontendConfigSkipNoneBase):  # noqa: F405
    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    min: float | None = Field(None, title='Minimum')
    max: float | None = Field(None, title='Maximum')
    range: bool | None = Field(None, title='Range')
