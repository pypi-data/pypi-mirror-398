from typing import ClassVar

from amsdal_models.classes.model import TypeModel
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class Option(TypeModel):
    __module_type__: ClassVar[ModuleType] = ModuleType.CORE
    key: str = Field(title='Key')
    value: str = Field(title='Value Type')
