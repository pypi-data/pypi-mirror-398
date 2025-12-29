import abc
from abc import ABC, abstractmethod
from amsdal_utils.schemas.schema import ObjectSchema as ObjectSchema
from typing import TypeAlias

ModulePathType: TypeAlias = str

class BaseSchemaLoader(ABC, metaclass=abc.ABCMeta):
    @property
    @abstractmethod
    def schemas_per_module(self) -> dict[ModulePathType, list[ObjectSchema]]: ...
    @abstractmethod
    def load(self) -> list[ObjectSchema]: ...

class BaseDependsSchemaLoader(ABC, metaclass=abc.ABCMeta):
    @property
    @abstractmethod
    def schemas_per_module(self) -> dict[ModulePathType, list[ObjectSchema]]: ...
    @abstractmethod
    def load(self, type_schemas: list[ObjectSchema], *extra_schemas: list[ObjectSchema]) -> list[ObjectSchema]: ...
