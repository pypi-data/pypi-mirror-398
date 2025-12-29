from _typeshed import Incomplete
from amsdal.schemas.mixins.check_dependencies_mixin import CheckDependenciesMixin as CheckDependenciesMixin
from amsdal.schemas.mixins.verify_schemas_mixin import VerifySchemasMixin as VerifySchemasMixin
from amsdal.schemas.utils import ModelModuleInfo as ModelModuleInfo
from amsdal_utils.schemas.interfaces import BaseDependsSchemaLoader, BaseSchemaLoader as BaseSchemaLoader
from amsdal_utils.schemas.schema import ObjectSchema as ObjectSchema

class SchemaRepository(VerifySchemasMixin, CheckDependenciesMixin):
    type_schemas: list[ObjectSchema]
    core_schemas: list[ObjectSchema]
    contrib_schemas: list[ObjectSchema]
    user_schemas: list[ObjectSchema]
    _type_schema_loader: Incomplete
    _core_schema_loader: Incomplete
    _contrib_schema_loader: Incomplete
    _user_schema_loader: Incomplete
    def __init__(self, type_schema_loader: BaseSchemaLoader, core_schema_loader: BaseSchemaLoader | BaseDependsSchemaLoader, contrib_schema_loader: BaseSchemaLoader | BaseDependsSchemaLoader, user_schema_loader: BaseSchemaLoader | BaseDependsSchemaLoader) -> None: ...
    @property
    def model_module_info(self) -> ModelModuleInfo: ...
    def _load_schemas(self, loader: BaseSchemaLoader | BaseDependsSchemaLoader, *extra_schemas: list[ObjectSchema]) -> list[ObjectSchema]: ...
    @staticmethod
    def _prepare_info(schemas_per_module: dict[str, list[ObjectSchema]]) -> dict[str, str]: ...
