from typing import ClassVar

from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field

from amsdal.contrib.frontend_configs.models.frontend_config_skip_none_base import *  # noqa: F403


class FrontendConfigTextMask(FrontendConfigSkipNoneBase):  # noqa: F405
    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    mask_string: str = Field(title='Mask String')
    prefix: str | None = Field(None, title='Prefix')
    suffix: str | None = Field(None, title='Suffix')
    thousands_separator: str | None = Field(None, title='Thousands Separator')
