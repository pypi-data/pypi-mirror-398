from typing import Any
from typing import ClassVar

from amsdal_models.builder.validators.dict_validators import validate_non_empty_keys
from amsdal_models.classes.model import TypeModel
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field
from pydantic.functional_validators import field_validator

from amsdal.models.core.option import *  # noqa: F403


class ClassProperty(TypeModel):
    __module_type__: ClassVar[ModuleType] = ModuleType.CORE
    title: str | None = Field(None, title='Title')
    type: str = Field(title='Type')
    default: Any | None = Field(None, title='Default')
    options: list['Option'] | None = Field(None, title='Options')  # noqa: F405
    items: dict[str, Any | None] | None = Field(None, title='Items')
    discriminator: str | None = Field(None, title='Discriminator')
    extra: dict[str, Any | None] = Field(default_factory=dict, title='Extra')

    @field_validator('items')
    @classmethod
    def _non_empty_keys_items(cls: type, value: Any) -> Any:  # type: ignore # noqa: A003
        return validate_non_empty_keys(value)
