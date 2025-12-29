from amsdal_utils.models.enums import ModuleType
from amsdal_utils.schemas.interfaces import BaseDependsSchemaLoader
from amsdal_utils.schemas.interfaces import BaseSchemaLoader
from amsdal_utils.schemas.schema import ObjectSchema

from amsdal.schemas.mixins.check_dependencies_mixin import CheckDependenciesMixin
from amsdal.schemas.mixins.verify_schemas_mixin import VerifySchemasMixin
from amsdal.schemas.utils import ModelModuleInfo


class SchemaRepository(VerifySchemasMixin, CheckDependenciesMixin):
    type_schemas: list[ObjectSchema]
    core_schemas: list[ObjectSchema]
    contrib_schemas: list[ObjectSchema]
    user_schemas: list[ObjectSchema]

    def __init__(
        self,
        type_schema_loader: BaseSchemaLoader,
        core_schema_loader: BaseSchemaLoader | BaseDependsSchemaLoader,
        contrib_schema_loader: BaseSchemaLoader | BaseDependsSchemaLoader,
        user_schema_loader: BaseSchemaLoader | BaseDependsSchemaLoader,
    ):
        self._type_schema_loader = type_schema_loader
        self._core_schema_loader = core_schema_loader
        self._contrib_schema_loader = contrib_schema_loader
        self._user_schema_loader = user_schema_loader

        self.type_schemas = type_schema_loader.load()
        self.core_schemas = self._load_schemas(core_schema_loader)
        self.contrib_schemas = self._load_schemas(contrib_schema_loader, self.core_schemas)
        self.user_schemas = self._load_schemas(user_schema_loader, self.core_schemas, self.contrib_schemas)

        self.verify_schemas(
            self.type_schemas,
            self.core_schemas,
            self.contrib_schemas,
            self.user_schemas,
        )
        self.check_dependencies(
            self.type_schemas,
            self.core_schemas,
            self.contrib_schemas,
            self.user_schemas,
        )

    @property
    def model_module_info(self) -> ModelModuleInfo:
        _type_info = self._prepare_info(self._type_schema_loader.schemas_per_module)
        _core_info = self._prepare_info(self._core_schema_loader.schemas_per_module)
        _contrib_info = self._prepare_info(self._contrib_schema_loader.schemas_per_module)
        _user_info = self._prepare_info(self._user_schema_loader.schemas_per_module)

        return ModelModuleInfo(
            info={
                ModuleType.TYPE: _type_info,
                ModuleType.CORE: _core_info,
                ModuleType.CONTRIB: _contrib_info,
                ModuleType.USER: _user_info,
            },
        )

    def _load_schemas(
        self,
        loader: BaseSchemaLoader | BaseDependsSchemaLoader,
        *extra_schemas: list[ObjectSchema],
    ) -> list[ObjectSchema]:

        if isinstance(loader, BaseDependsSchemaLoader):
            return loader.load(self.type_schemas, *extra_schemas)
        else:
            _schemas, _circular = loader.load_sorted()
            return _schemas + _circular

    @staticmethod
    def _prepare_info(schemas_per_module: dict[str, list[ObjectSchema]]) -> dict[str, str]:
        _info = {}

        for module_path, schemas in schemas_per_module.items():
            _info.update(
                {_schema.title: module_path for _schema in schemas},
            )

        return _info
