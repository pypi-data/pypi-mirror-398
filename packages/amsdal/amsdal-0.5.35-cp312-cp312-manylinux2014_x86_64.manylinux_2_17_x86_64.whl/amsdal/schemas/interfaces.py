from abc import ABC
from abc import abstractmethod
from typing import TypeAlias

from amsdal_utils.schemas.schema import ObjectSchema

ModulePathType: TypeAlias = str


class BaseSchemaLoader(ABC):
    @property
    @abstractmethod
    def schemas_per_module(self) -> dict[ModulePathType, list[ObjectSchema]]: ...

    @abstractmethod
    def load(self) -> list[ObjectSchema]: ...


class BaseDependsSchemaLoader(ABC):
    @property
    @abstractmethod
    def schemas_per_module(self) -> dict[ModulePathType, list[ObjectSchema]]: ...

    @abstractmethod
    def load(self, type_schemas: list[ObjectSchema], *extra_schemas: list[ObjectSchema]) -> list[ObjectSchema]: ...
