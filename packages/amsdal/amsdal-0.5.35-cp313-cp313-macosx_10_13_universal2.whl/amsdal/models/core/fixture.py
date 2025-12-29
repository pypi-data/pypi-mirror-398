from typing import Any
from typing import ClassVar

from amsdal_models.builder.validators.dict_validators import validate_non_empty_keys
from amsdal_models.classes.data_models.constraints import UniqueConstraint
from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field
from pydantic.functional_validators import field_validator


class Fixture(Model):
    __module_type__: ClassVar[ModuleType] = ModuleType.CORE
    __constraints__: ClassVar[list[UniqueConstraint]] = [
        UniqueConstraint(name='unq_fixture_external_id', fields=['external_id'])
    ]
    class_name: str | None = Field(None, title='Class Name')
    order: float | None = Field(None, title='Order')
    external_id: str = Field(title='External ID')
    data: dict[str, Any | None] = Field(title='Data')

    @field_validator('data')
    @classmethod
    def _non_empty_keys_data(cls: type, value: Any) -> Any:
        return validate_non_empty_keys(value)
