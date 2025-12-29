from typing import ClassVar

from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field

from amsdal.contrib.frontend_configs.models.frontend_config_skip_none_base import *  # noqa: F403


class FrontendConfigOption(FrontendConfigSkipNoneBase):  # noqa: F405
    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    label: str | None = Field(None, title='Label')
    value: str | None = Field(None, title='Value')
