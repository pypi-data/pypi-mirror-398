from typing import Any
from typing import ClassVar

from amsdal_models.classes.model import TypeModel
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class Validator(TypeModel):
    __module_type__: ClassVar[ModuleType] = ModuleType.CORE
    name: str = Field(title='Validator Name')
    data: Any = Field(title='Validator Data')
