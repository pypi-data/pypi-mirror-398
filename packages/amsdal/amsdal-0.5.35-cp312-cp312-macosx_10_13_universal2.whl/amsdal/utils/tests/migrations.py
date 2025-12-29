import contextlib
from asyncio import iscoroutine

from amsdal_data.connections.historical.schema_version_manager import AsyncHistoricalSchemaVersionManager
from amsdal_data.connections.historical.schema_version_manager import HistoricalSchemaVersionManager
from amsdal_models.migration import migrations
from amsdal_models.migration.executors.default_executor import DefaultAsyncMigrationExecutor
from amsdal_models.migration.executors.default_executor import DefaultMigrationExecutor
from amsdal_models.migration.file_migration_executor import AsyncFileMigrationExecutorManager
from amsdal_models.migration.file_migration_executor import FileMigrationExecutorManager
from amsdal_models.migration.file_migration_generator import SimpleFileMigrationGenerator
from amsdal_models.migration.file_migration_store import AsyncFileMigrationStore
from amsdal_models.migration.file_migration_store import FileMigrationStore
from amsdal_models.migration.file_migration_writer import FileMigrationWriter
from amsdal_models.migration.migrations import MigrationSchemas
from amsdal_models.migration.migrations_loader import MigrationsLoader
from amsdal_models.schemas.class_schema_loader import ClassSchemaLoader
from amsdal_utils.models.enums import ModuleType

from amsdal.configs.constants import CORE_MIGRATIONS_PATH
from amsdal.configs.main import settings


def migrate() -> None:
    schemas = MigrationSchemas()
    executor = DefaultMigrationExecutor(schemas, use_foreign_keys=True)
    store = FileMigrationStore(settings.migrations_root_path)
    store.init_migration_table()

    class UserMigrationsLoader(MigrationsLoader):
        def __init__(self):
            super().__init__(settings.migrations_root_path, ModuleType.USER)
            self._migrations_files = []

    with contextlib.suppress(Exception):
        HistoricalSchemaVersionManager().object_classes  # noqa: B018

    # migrate core and contrib due to applied migrations
    executor_manager = FileMigrationExecutorManager(
        core_migrations_path=CORE_MIGRATIONS_PATH,
        app_migrations_loader=UserMigrationsLoader(),
        executor=executor,
        store=store,
        contrib=settings.CONTRIBS,
    )
    executor_manager.execute()

    # always apply migrations for user models
    user_schema_loader = ClassSchemaLoader(
        settings.USER_MODELS_MODULE,
        class_filter=lambda cls: cls.__module_type__ == ModuleType.USER,
    )
    _schemas, _cycle_schemas = user_schema_loader.load_sorted()
    _schemas_map = {_schema.title: _schema for _schema in _schemas}

    for object_schema in _schemas:
        for _operation_data in SimpleFileMigrationGenerator.build_operations(
            ModuleType.USER,
            object_schema,
            None,
        ):
            _operation_name = FileMigrationWriter.operation_name_map[_operation_data.type]
            _operation = getattr(migrations, _operation_name)(
                module_type=ModuleType.USER,
                class_name=_operation_data.class_name,
                new_schema=_operation_data.new_schema.model_dump(),
            )

            _operation.forward(executor)

    for object_schema in _cycle_schemas:
        for _operation_data in SimpleFileMigrationGenerator.build_operations(
            ModuleType.USER,
            object_schema,
            _schemas_map[object_schema.title],
        ):
            _operation_name = FileMigrationWriter.operation_name_map[_operation_data.type]
            _operation = getattr(migrations, _operation_name)(
                module_type=ModuleType.USER,
                class_name=_operation_data.class_name,
                new_schema=_operation_data.new_schema.model_dump(),
            )

            _operation.forward(executor)

    executor.flush_buffer()


async def async_migrate() -> None:
    schemas = MigrationSchemas()
    executor = DefaultAsyncMigrationExecutor(schemas)
    store = AsyncFileMigrationStore(settings.migrations_root_path)
    await store.init_migration_table()

    class UserMigrationsLoader(MigrationsLoader):
        def __init__(self):
            super().__init__(settings.migrations_root_path, ModuleType.USER)
            self._migrations_files = []

    with contextlib.suppress(Exception):
        await AsyncHistoricalSchemaVersionManager().object_classes

    # migrate core and contrib due to applied migrations
    executor_manager = AsyncFileMigrationExecutorManager(
        core_migrations_path=CORE_MIGRATIONS_PATH,
        app_migrations_loader=UserMigrationsLoader(),
        executor=executor,
        store=store,
        contrib=settings.CONTRIBS,
    )
    await executor_manager.execute()

    # always apply migrations for user models
    user_schema_loader = ClassSchemaLoader(
        settings.USER_MODELS_MODULE,
        class_filter=lambda cls: cls.__module_type__ == ModuleType.USER,
    )
    _schemas, _cycle_schemas = user_schema_loader.load_sorted()
    _schemas_map = {_schema.title: _schema for _schema in _schemas}

    for object_schema in _schemas:
        for _operation_data in SimpleFileMigrationGenerator.build_operations(
            ModuleType.USER,
            object_schema,
            None,
        ):
            _operation_name = FileMigrationWriter.operation_name_map[_operation_data.type]
            _operation = getattr(migrations, _operation_name)(
                module_type=ModuleType.USER,
                class_name=_operation_data.class_name,
                new_schema=_operation_data.new_schema.model_dump(),
            )

            forward_result = _operation.forward(executor)

            if iscoroutine(forward_result):
                await forward_result

    for object_schema in _cycle_schemas:
        for _operation_data in SimpleFileMigrationGenerator.build_operations(
            ModuleType.USER,
            object_schema,
            _schemas_map[object_schema.title],
        ):
            _operation_name = FileMigrationWriter.operation_name_map[_operation_data.type]
            _operation = getattr(migrations, _operation_name)(
                module_type=ModuleType.USER,
                class_name=_operation_data.class_name,
                new_schema=_operation_data.new_schema.model_dump(),
            )

            forward_result = _operation.forward(executor)

            if iscoroutine(forward_result):
                await forward_result

    await executor.flush_buffer()
