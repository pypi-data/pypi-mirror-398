import random
import string
from collections.abc import AsyncGenerator
from collections.abc import AsyncIterator
from collections.abc import Generator
from collections.abc import Iterator
from contextlib import ExitStack
from contextlib import asynccontextmanager
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from typing import Any

from amsdal_data.aliases.db import POSTGRES_HISTORICAL_ALIAS
from amsdal_data.aliases.db import POSTGRES_HISTORICAL_ASYNC_ALIAS
from amsdal_data.aliases.db import POSTGRES_STATE_ALIAS
from amsdal_data.aliases.db import POSTGRES_STATE_ASYNC_ALIAS
from amsdal_data.aliases.db import SQLITE_ALIAS
from amsdal_data.aliases.db import SQLITE_ASYNC_ALIAS
from amsdal_data.aliases.db import SQLITE_HISTORICAL_ALIAS
from amsdal_data.aliases.db import SQLITE_HISTORICAL_ASYNC_ALIAS
from amsdal_data.application import AsyncDataApplication
from amsdal_data.connections.db_alias_map import CONNECTION_BACKEND_ALIASES
from amsdal_data.connections.historical.schema_version_manager import AsyncHistoricalSchemaVersionManager
from amsdal_data.connections.historical.schema_version_manager import HistoricalSchemaVersionManager
from amsdal_data.test_utils.common import temp_dir
from amsdal_data.test_utils.config import build_config
from amsdal_data.test_utils.config import postgres_async_config
from amsdal_data.test_utils.config import postgres_async_lakehouse_only_config
from amsdal_data.test_utils.config import postgres_config
from amsdal_data.test_utils.config import postgres_lakehouse_only_config
from amsdal_data.test_utils.config import sqlite_async_config
from amsdal_data.test_utils.config import sqlite_async_lakehouse_only_config
from amsdal_data.test_utils.config import sqlite_config
from amsdal_data.test_utils.config import sqlite_lakehouse_only_config
from amsdal_data.test_utils.constants import PG_TEST_HOST
from amsdal_data.test_utils.constants import PG_TEST_PASSWORD
from amsdal_data.test_utils.constants import PG_TEST_PORT
from amsdal_data.test_utils.constants import PG_TEST_USER
from amsdal_data.test_utils.db import create_postgres_database
from amsdal_data.test_utils.db import create_postgres_extension
from amsdal_data.test_utils.db import drop_postgres_database
from amsdal_utils.config.data_models.amsdal_config import AmsdalConfig
from amsdal_utils.config.manager import AmsdalConfigManager

from amsdal.manager import AmsdalManager
from amsdal.manager import AsyncAmsdalManager
from amsdal.utils.tests.enums import DbExecutionType
from amsdal.utils.tests.enums import LakehouseOption
from amsdal.utils.tests.enums import StateOption
from amsdal.utils.tests.migrations import async_migrate
from amsdal.utils.tests.migrations import migrate


@contextmanager
def override_settings(**kwargs: Any) -> Iterator[None]:
    """
    A context manager that temporarily overrides settings.

    This is a copy of django.test.utils.override_settings, but with the
    ability to override settings with None.
    """
    from amsdal.configs.main import settings

    original_settings = settings.model_dump()

    settings.override(**kwargs)

    try:
        yield
    finally:
        settings.override(**original_settings)


@contextmanager
def init_config(
    db_execution_type: DbExecutionType,
    lakehouse_option: LakehouseOption,
    state_option: StateOption,
    *,
    is_async: bool = False,
    db_name_prefix: str | None = None,
    db_path: Path | None = None,
    drop_database: bool = False,
) -> Iterator[AmsdalConfig]:
    if db_name_prefix:
        lakehouse_database = f'{db_name_prefix}_lakehouse'
        state_database = f'{db_name_prefix}_state'
    else:
        lakehouse_database = ''.join(random.sample(string.ascii_letters, 16))
        state_database = ''.join(random.sample(string.ascii_letters, 16))

    if db_execution_type == DbExecutionType.lakehouse_only:
        ctx_managers = {
            LakehouseOption.sqlite: (
                partial(sqlite_async_lakehouse_only_config, db_path)
                if is_async
                else partial(sqlite_lakehouse_only_config, db_path)
            ),
            LakehouseOption.postgres: (
                partial(postgres_async_lakehouse_only_config, lakehouse_database, drop_database=drop_database)
                if is_async
                else partial(postgres_lakehouse_only_config, lakehouse_database, drop_database=drop_database)
            ),
        }
        with ctx_managers[lakehouse_option]() as _amsdal_config:
            yield _amsdal_config
        return

    if lakehouse_option.value == state_option.value:
        ctx_managers = {
            LakehouseOption.sqlite: (
                partial(
                    sqlite_async_config,
                    db_path=db_path,
                )
                if is_async
                else partial(sqlite_config, db_path)
            ),
            LakehouseOption.postgres: (
                partial(
                    postgres_async_config,
                    lakehouse_database=lakehouse_database,
                    state_database=state_database,
                    drop_database=drop_database,
                )
                if is_async
                else partial(
                    postgres_config,
                    lakehouse_database=lakehouse_database,
                    state_database=state_database,
                    drop_database=drop_database,
                )
            ),
        }

        with ctx_managers[lakehouse_option]() as _amsdal_config:
            yield _amsdal_config
        return

    with ExitStack() as stack:
        db_path = db_path if db_path else stack.enter_context(temp_dir())

        if lakehouse_option == LakehouseOption.postgres:
            config = build_config(
                lakehouse_backend=CONNECTION_BACKEND_ALIASES[
                    POSTGRES_HISTORICAL_ASYNC_ALIAS if is_async else POSTGRES_HISTORICAL_ALIAS
                ],
                lakehouse_credentials={
                    'dsn': f'postgresql://{PG_TEST_USER}:{PG_TEST_PASSWORD}@{PG_TEST_HOST}:{PG_TEST_PORT}/{lakehouse_database}',
                },
                state_backend=CONNECTION_BACKEND_ALIASES[SQLITE_ASYNC_ALIAS if is_async else SQLITE_ALIAS],
                state_credentials={
                    'db_path': f'{db_path}/amsdal_state.sqlite3',
                },
                is_async_mode=is_async,
            )
            AmsdalConfigManager().set_config(config)
            create_postgres_database(lakehouse_database)
            create_postgres_extension(lakehouse_database, 'vector')
            try:
                yield config
            finally:
                AmsdalConfigManager.invalidate()

                if drop_database:
                    drop_postgres_database(lakehouse_database)
            return

        config = build_config(
            lakehouse_backend=CONNECTION_BACKEND_ALIASES[
                SQLITE_HISTORICAL_ASYNC_ALIAS if is_async else SQLITE_HISTORICAL_ALIAS
            ],
            lakehouse_credentials={
                'db_path': f'{db_path}/amsdal_historical.sqlite3',
            },
            state_backend=CONNECTION_BACKEND_ALIASES[POSTGRES_STATE_ASYNC_ALIAS if is_async else POSTGRES_STATE_ALIAS],
            state_credentials={
                'dsn': f'postgresql://{PG_TEST_USER}:{PG_TEST_PASSWORD}@{PG_TEST_HOST}:{PG_TEST_PORT}/{state_database}',
            },
            is_async_mode=True,
        )
        AmsdalConfigManager().set_config(config)
        create_postgres_database(state_database)
        create_postgres_extension(state_database, 'vector')

        try:
            yield config
        finally:
            AmsdalConfigManager.invalidate()

            if drop_database:
                drop_postgres_database(state_database)


@contextmanager
def init_manager(
    src_dir_path: Path,
    db_execution_type: DbExecutionType,
    lakehouse_option: LakehouseOption,
    state_option: StateOption,
    app_models_path: Path | None = None,
    app_transactions_path: Path | None = None,
    app_fixtures_path: Path | None = None,
    **settings_options: Any,
) -> Iterator[AmsdalManager]:
    app_models_path = app_models_path or src_dir_path / 'models'
    app_transactions_path = app_transactions_path or src_dir_path / 'transactions'
    app_fixtures_path = app_fixtures_path or src_dir_path / 'fixtures'

    with ExitStack() as stack:
        tmp_dir = stack.enter_context(temp_dir())
        stack.enter_context(init_config(db_execution_type, lakehouse_option, state_option))
        stack.enter_context(
            override_settings(
                APP_PATH=tmp_dir,
                USER_MODELS_MODULE_PATH=app_models_path,
                TRANSACTIONS_MODULE_PATH=app_transactions_path,
                FIXTURES_MODULE_PATH=app_fixtures_path,
                **settings_options,
            ),
        )

        manager = AmsdalManager()
        manager.setup()
        manager.post_setup()  # type: ignore[call-arg]

        try:
            yield manager
        finally:
            manager.teardown()
            AmsdalManager.invalidate()
            AsyncDataApplication.invalidate()


@asynccontextmanager
async def async_init_manager(
    src_dir_path: Path,
    db_execution_type: DbExecutionType,
    lakehouse_option: LakehouseOption,
    state_option: StateOption,
    app_models_path: Path | None = None,
    app_transactions_path: Path | None = None,
    app_fixtures_path: Path | None = None,
    **settings_options: Any,
) -> AsyncIterator[AsyncAmsdalManager]:
    app_models_path = app_models_path or src_dir_path / 'models'
    app_transactions_path = app_transactions_path or src_dir_path / 'transactions'
    app_fixtures_path = app_fixtures_path or src_dir_path / 'fixtures'

    with ExitStack() as stack:
        tmp_dir = stack.enter_context(temp_dir())
        stack.enter_context(init_config(db_execution_type, lakehouse_option, state_option, is_async=True))
        stack.enter_context(
            override_settings(
                APP_PATH=tmp_dir,
                USER_MODELS_MODULE_PATH=app_models_path,
                TRANSACTIONS_MODULE_PATH=app_transactions_path,
                FIXTURES_MODULE_PATH=app_fixtures_path,
                **settings_options,
            )
        )
        manager = AsyncAmsdalManager()
        await manager.setup()
        await manager.post_setup()  # type: ignore[call-arg,misc]

        try:
            yield manager
        finally:
            await manager.teardown()
            await AsyncDataApplication().teardown()
            AsyncAmsdalManager.invalidate()
            AsyncDataApplication.invalidate()


@contextmanager
def init_manager_and_migrate(
    src_dir_path: Path,
    db_execution_type: DbExecutionType,
    lakehouse_option: LakehouseOption,
    state_option: StateOption,
    app_models_path: Path | None = None,
    app_transactions_path: Path | None = None,
    app_fixtures_path: Path | None = None,
    **settings_options: Any,
) -> Generator[AmsdalManager, Any, None]:
    with init_manager(
        src_dir_path=src_dir_path,
        db_execution_type=db_execution_type,
        lakehouse_option=lakehouse_option,
        state_option=state_option,
        app_models_path=app_models_path,
        app_transactions_path=app_transactions_path,
        app_fixtures_path=app_fixtures_path,
        **settings_options,
    ) as manager:
        migrate()
        manager.authenticate()
        manager.init_classes()
        HistoricalSchemaVersionManager()._cache_object_classes.clear()

        yield manager


@asynccontextmanager
async def async_init_manager_and_migrate(
    src_dir_path: Path,
    db_execution_type: DbExecutionType,
    lakehouse_option: LakehouseOption,
    state_option: StateOption,
    app_models_path: Path | None = None,
    app_transactions_path: Path | None = None,
    app_fixtures_path: Path | None = None,
    **settings_options: Any,
) -> AsyncGenerator[AsyncAmsdalManager, Any]:
    async with async_init_manager(
        src_dir_path=src_dir_path,
        db_execution_type=db_execution_type,
        lakehouse_option=lakehouse_option,
        state_option=state_option,
        app_models_path=app_models_path,
        app_transactions_path=app_transactions_path,
        app_fixtures_path=app_fixtures_path,
        **settings_options,
    ) as manager:
        await async_migrate()
        manager.authenticate()
        manager.init_classes()
        AsyncHistoricalSchemaVersionManager()._cache_object_classes.clear()

        yield manager
