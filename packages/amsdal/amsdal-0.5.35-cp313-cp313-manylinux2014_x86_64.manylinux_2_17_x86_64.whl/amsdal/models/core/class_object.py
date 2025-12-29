from typing import Any
from typing import ClassVar
from typing import Optional

from amsdal_models.builder.validators.dict_validators import validate_non_empty_keys
from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field
from pydantic.functional_validators import field_validator

from amsdal.models.core.class_property import *  # noqa: F403
from amsdal.models.core.storage_metadata import *  # noqa: F403


class ClassObject(Model):
    __module_type__: ClassVar[ModuleType] = ModuleType.CORE
    title: str = Field(title='Title')
    type: str = Field(title='Type')
    module_type: str = Field(title='Module Type')
    properties: Optional[dict[str, Optional['ClassProperty']]] = Field(None, title='Properties')  # noqa: F405, UP007
    required: Optional[list[str]] = Field(None, title='Required')  # noqa: UP007
    custom_code: str | None = Field(None, title='Custom Code')
    storage_metadata: Optional['StorageMetadata'] = Field(None, title='Storage metadata')  # noqa: F405

    @field_validator('properties')
    @classmethod
    def _non_empty_keys_properties(cls: type, value: Any) -> Any:  # type: ignore # noqa: A003
        return validate_non_empty_keys(value)

    @property
    def display_name(self) -> str:
        """
        Returns the display name of the object.

        Returns:
            str: The display name, which is the title of the object.
        """
        return self.title
