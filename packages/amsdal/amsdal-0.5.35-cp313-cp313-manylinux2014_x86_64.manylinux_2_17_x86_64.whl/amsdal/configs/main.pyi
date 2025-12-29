from _typeshed import Incomplete
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Any, TypeAlias

class Settings(BaseSettings):
    """
    Configuration settings for the application.

    This class defines the configuration settings for the application, including paths,
    environment variables, and other settings.

    Attributes:
        model_config (SettingsConfigDict): Configuration for the settings model.
        APP_PATH (Path): Path to the app directory where the generated models and other files will be placed.
        CONFIG_PATH (Path | None): Path to the config.yml file. If not specified, the default APP_PATH/config.yml
            file will be used.
        MODELS_MODULE_NAME (str): The models module name. The generated models will be placed in this module.
        SCHEMAS_MODULE_NAME (str): The schemas module name. The schemas will be placed in this module.
        FIXTURES_MODULE_NAME (str): The fixtures module name. The fixtures will be placed in this module.
        STATIC_MODULE_NAME (str): The static module name. The static files will be placed in this module.
        TRANSACTIONS_MODULE_NAME (str): The transactions module name. The transactions will be placed in this module.
        MIGRATIONS_DIRECTORY_NAME (str): The migrations directory name. The migration files will be placed in this
            folder.
        ACCESS_KEY_ID (str | None): The access key that you will get during registering process.
        SECRET_ACCESS_KEY (str | None): The secret access key that you will get during registering process.
        ACCESS_TOKEN (str | None): The access token that you will get during sign in process.
        SANDBOX_ENVIRONMENT (bool | None): If True, the sandbox environment will be used. If False,
            the cloud environment will be used.
        CONTRIBS (list[str]): List of contrib modules that will be loaded and used.
            Can be specified via environment variable AMSDAL_CONTRIBS as comma separated string.
    """
    model_config: Incomplete
    APP_PATH: Path
    CONFIG_PATH: Path | None
    TYPE_MODELS_MODULE: str
    CORE_MODELS_MODULE: str
    USER_MODELS_MODULE_PATH: Path | None
    USER_MODELS_MODULE: str
    FIXTURES_MODULE_PATH: Path | None
    FIXTURES_MODULE_NAME: str
    STATIC_MODULE_PATH: Path | None
    STATIC_MODULE_NAME: str
    TRANSACTIONS_MODULE_PATH: Path | None
    TRANSACTIONS_MODULE_NAME: str
    MIGRATIONS_MODULE_PATH: Path | None
    MIGRATIONS_DIRECTORY_NAME: str
    ACCESS_KEY_ID: str | None
    SECRET_ACCESS_KEY: str | None
    ACCESS_TOKEN: str | None
    SANDBOX_ENVIRONMENT: bool | None
    CONTRIBS: list[str] | str
    CONTRIB_MODELS_PACKAGE_NAME: str
    CONTRIB_MIGRATIONS_DIRECTORY_NAME: str
    MEDIA_ROOT: Path
    MEDIA_URL: str
    DEFAULT_FILE_STORAGE: str
    def load_contrib_modules(cls, value: list[str]) -> list[str]:
        """
        Loads and initializes contrib modules.

        This method takes a list of contrib module paths, imports each module, and calls the `on_ready` method
        of the `AppConfig` class within each module.

        Args:
            value (list[str]): A list of contrib module paths in the format 'package.module.ClassName'.

        Returns:
            list[str]: The same list of contrib module paths after loading and initializing the modules.
        """
    @property
    def user_models_path(self) -> Path:
        """
        Returns the root path for models.

        This property constructs and returns the path to the models directory
        based on the `APP_PATH` and `MODELS_MODULE_NAME` attributes.

        Returns:
            Path: The root path for the models directory.
        """
    @property
    def fixtures_root_path(self) -> Path:
        """
        Returns the root path for fixtures.

        This property constructs and returns the path to the fixtures directory
        based on the `APP_PATH` and `FIXTURES_MODULE_NAME` attributes.

        Returns:
            Path: The root path for the fixtures directory.
        """
    @property
    def static_root_path(self) -> Path:
        """
        Returns the root path for static files.

        This property constructs and returns the path to the static files directory
        based on the `APP_PATH` and `STATIC_MODULE_NAME` attributes.

        Returns:
            Path: The root path for the static files directory.
        """
    @property
    def transactions_root_path(self) -> Path:
        """
        Returns the root path for transactions.

        This property constructs and returns the path to the transactions directory
        based on the `models_root_path` and `TRANSACTIONS_MODULE_NAME` attributes.

        Returns:
            Path: The root path for the transactions directory.
        """
    @property
    def migrations_root_path(self) -> Path:
        """
        Returns the root path for migrations.

        This property constructs and returns the path to the migrations directory
        based on the `models_root_path` and `MIGRATIONS_DIRECTORY_NAME` attributes.

        Returns:
            Path: The root path for the migrations directory.
        """
    def check_config_path_set(self) -> Settings:
        """
        Ensures the configuration path is set.

        This method checks if the `CONFIG_PATH` attribute is set. If it is not set,
        it assigns a default path based on the `APP_PATH` attribute.

        Returns:
            Settings: The updated settings instance with the `CONFIG_PATH` attribute set.
        """
    @classmethod
    def normalize_complex_values(cls, data: Any) -> Any: ...
base: TypeAlias = Settings

class SettingsProxy(base):
    """
    Proxy class for accessing and modifying settings.

    This class acts as a proxy for the `Settings` class, allowing for dynamic
    overriding and accessing of settings attributes.
    """
    _settings: Incomplete
    def __init__(self) -> None: ...
    def override(self, **kwargs: Any) -> None:
        """
        Overrides settings with provided keyword arguments.

        This method updates the current settings with the provided keyword arguments.

        Args:
            **kwargs: Keyword arguments representing settings to override.

        Returns:
            None
        """
    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Dumps the current settings model to a dictionary.

        This method returns the current settings as a dictionary.

        Args:
            *args: Additional positional arguments to pass to the underlying model dump method.
            **kwargs: Additional keyword arguments to pass to the underlying model dump method.

        Returns:
            dict[str, Any]: The current settings as a dictionary.
        """
    def __getattr__(self, name: str) -> Any: ...
    def __delattr__(self, name: str) -> None: ...
    def __setattr__(self, name: str, value: Any) -> None: ...

settings: SettingsProxy
