from typing import Any
from typing import ClassVar
from typing import Optional

from amsdal_models.builder.validators.dict_validators import validate_non_empty_keys
from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field
from pydantic.functional_validators import field_validator


class Object(Model):
    __module_type__: ClassVar[ModuleType] = ModuleType.TYPE
    title: str = Field(title='Title', default='')
    type: str = Field(title='Type', default='object')
    module_type: str = Field(title='Module Type', default=ModuleType.CORE.value)
    default: Optional[Any] = Field(None, title='Default')  # noqa: UP007
    properties: Optional[dict[str, Optional[Any]]] = Field(None, title='Properties')  # noqa: UP007
    required: Optional[list[str]] = Field(None, title='Required')  # noqa: UP007
    custom_code: Optional[str] = Field(None, title='Custom Code')  # noqa: UP007
    meta_class: Optional[str] = Field(None, title='Meta Class')  # noqa: UP007

    @field_validator('properties')
    @classmethod
    def _non_empty_keys_properties(cls: type, value: Any) -> Any:  # type: ignore # noqa: A003
        return validate_non_empty_keys(value)
