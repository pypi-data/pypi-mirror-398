from typing import ClassVar
from typing import Optional

from amsdal_models.classes.model import TypeModel
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class StorageMetadata(TypeModel):
    __module_type__: ClassVar[ModuleType] = ModuleType.CORE
    table_name: Optional[str] = Field(None, title='Table name')  # noqa: UP007
    db_fields: dict[str, list[str]] | None = Field(None, title='Database fields')
    primary_key: Optional[list[str]] = Field(None, title='Primary key fields')  # noqa: UP007
    indexed: Optional[list[list[str]]] = Field(None, title='Indexed')  # noqa: UP007
    unique: Optional[list[list[str]]] = Field(None, title='Unique Fields')  # noqa: UP007
