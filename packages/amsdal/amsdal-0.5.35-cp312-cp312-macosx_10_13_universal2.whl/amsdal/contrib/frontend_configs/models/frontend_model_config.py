from typing import ClassVar
from typing import Optional

from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field

from amsdal.contrib.frontend_configs.models.frontend_control_config import *  # noqa: F403


class FrontendModelConfig(Model):
    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    class_name: str = Field(title='Class Name')
    control: Optional['FrontendControlConfig'] = Field(None, title='Control')  # noqa: F405
