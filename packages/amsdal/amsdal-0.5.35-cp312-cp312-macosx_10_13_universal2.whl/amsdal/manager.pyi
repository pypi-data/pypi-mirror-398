from _typeshed import Incomplete
from amsdal.cloud.services.actions.manager import CloudActionsManager as CloudActionsManager
from amsdal.cloud.services.auth.signup_service import SignupService as SignupService
from amsdal.configs.main import settings as settings
from amsdal.errors import AmsdalAuthenticationError as AmsdalAuthenticationError, AmsdalMissingCredentialsError as AmsdalMissingCredentialsError, AmsdalRuntimeError as AmsdalRuntimeError, AmsdalSignupError as AmsdalSignupError
from amsdal.fixtures.manager import AsyncFixturesManager as AsyncFixturesManager, FixturesManager as FixturesManager
from amsdal.mixins.class_versions_mixin import ClassVersionsMixin as ClassVersionsMixin
from amsdal_data.transactions.decorators import async_transaction, transaction
from amsdal_models.classes.class_manager import ClassManager
from amsdal_utils.config.data_models.amsdal_config import AmsdalConfig as AmsdalConfig
from amsdal_utils.utils.singleton import Singleton

class AmsdalManager(ClassVersionsMixin, metaclass=Singleton):
    """
    Manages the AMSDAL framework components and operations.

    This class is responsible for initializing, setting up, and managing various components
    of the AMSDAL framework, including connections, data management, schema management,
    and authentication. It also provides methods for building and tearing down the framework.
    """
    _class_manager: ClassManager
    _config_manager: Incomplete
    _config: Incomplete
    _data_application: Incomplete
    _is_setup: bool
    __is_authenticated: bool
    _metadata_manager: Incomplete
    _auth_manager: Incomplete
    def __init__(self, *, raise_on_new_signup: bool = False) -> None:
        """
        Initializes all sub managers. Reads the configuration.

        Returns:
            None
        """
    @property
    def is_setup(self) -> bool: ...
    @property
    def is_authenticated(self) -> bool:
        """
        Indicates if the AMSDAL license authentication process has been passed.

        This property returns a boolean value indicating whether the AMSDAL license
        authentication process has been successfully completed.

        Returns:
            bool: True if authenticated, False otherwise.
        """
    def pre_setup(self) -> None:
        """
        Initiates models root path and adds it into sys.path.

        This method initializes the class manager models modules and sets up the models root path
        as specified in the settings. It ensures that the models root path is added
        to the system path for proper module resolution.

        Returns:
            None
        """
    def setup(self) -> None:
        """
        Initiates models root path and the connections.

        This method sets up the AMSDAL framework by initializing the models root path and
        establishing connections. It ensures that the setup process is only performed once.

        Raises:
            AmsdalRuntimeError: If the AMSDAL manager is already set up.

        Returns:
            None
        """
    @transaction
    def post_setup(self) -> None:
        """
        Registers internal classes and prepares connections (creates internal tables).
        """
    def _check_auth(self) -> None: ...
    @property
    def cloud_actions_manager(self) -> CloudActionsManager:
        """
        Provides access to the CloudActionsManager.

        This property checks if the AMSDAL manager is authenticated and then returns
        an instance of the CloudActionsManager.

        Returns:
            CloudActionsManager: An instance of the CloudActionsManager.

        Raises:
            AmsdalAuthenticationError: If the AMSDAL manager is not authenticated.
        """
    def authenticate(self) -> None:
        """
        Run AMSDAL license authentication process.

        This method runs the AMSDAL license authentication process and sets the
        authentication status accordingly.

        Returns:
            None
        """
    @transaction
    def apply_fixtures(self) -> None:
        """
        Loads and applies fixtures defined in your application.

        This method loads the fixtures from the specified path and applies them to the
        AMSDAL framework. It uses the `FixturesManager` to manage the loading and application
        of the fixtures.

        Returns:
            None
        """
    def init_classes(self) -> None:
        """
        Initializes and imports classes based on the schema manager's class schemas.

        This method iterates over the class schemas provided by the schema manager and imports
        the classes into the class manager, excluding those of type `SchemaTypes.TYPE`.

        Returns:
            None
        """
    def teardown(self) -> None:
        """
        Clean up everything on the application exit.

        This method performs a cleanup of all components managed by the AMSDAL framework
        when the application exits. It disconnects and invalidates connections, clears caches,
        and resets the setup status.

        Raises:
            AmsdalRuntimeError: If the AMSDAL manager is not set up.

        Returns:
            None
        """

class AsyncAmsdalManager(ClassVersionsMixin, metaclass=Singleton):
    """
    Manages the AMSDAL framework components and operations.

    This class is responsible for initializing, setting up, and managing various components
    of the AMSDAL framework, including connections, data management, schema management,
    and authentication. It also provides methods for building and tearing down the framework.
    """
    _class_manager: ClassManager
    _config_manager: Incomplete
    _config: Incomplete
    _data_application: Incomplete
    _is_setup: bool
    __is_authenticated: bool
    _metadata_manager: Incomplete
    _auth_manager: Incomplete
    def __init__(self, *, raise_on_new_signup: bool = False) -> None:
        """
        Initializes all sub managers. Reads the configuration.

        Returns:
            None
        """
    @property
    def is_setup(self) -> bool: ...
    @property
    def is_authenticated(self) -> bool:
        """
        Indicates if the AMSDAL license authentication process has been passed.

        This property returns a boolean value indicating whether the AMSDAL license
        authentication process has been successfully completed.

        Returns:
            bool: True if authenticated, False otherwise.
        """
    def pre_setup(self) -> None:
        """
        Initiates models root path and adds it into sys.path.

        This method initializes the class manager and sets up the models root path
        as specified in the settings. It ensures that the models root path is added
        to the system path for proper module resolution.

        Returns:
            None
        """
    async def setup(self) -> None:
        """
        Initiates models root path and the connections.

        This method sets up the AMSDAL framework by initializing the models root path and
        establishing connections. It ensures that the setup process is only performed once.

        Raises:
            AmsdalRuntimeError: If the AMSDAL manager is already set up.

        Returns:
            None
        """
    @async_transaction
    async def post_setup(self) -> None:
        """
        Registers internal classes and prepares connections (creates internal tables).
        """
    def _check_auth(self) -> None: ...
    @property
    def cloud_actions_manager(self) -> CloudActionsManager:
        """
        Provides access to the CloudActionsManager.

        This property checks if the AMSDAL manager is authenticated and then returns
        an instance of the CloudActionsManager.

        Returns:
            CloudActionsManager: An instance of the CloudActionsManager.

        Raises:
            AmsdalAuthenticationError: If the AMSDAL manager is not authenticated.
        """
    def authenticate(self) -> None:
        """
        Run AMSDAL license authentication process.

        This method runs the AMSDAL license authentication process and sets the
        authentication status accordingly.

        Returns:
            None
        """
    @async_transaction
    async def apply_fixtures(self) -> None:
        """
        Loads and applies fixtures defined in your application.

        This method loads the fixtures from the specified path and applies them to the
        AMSDAL framework. It uses the `FixturesManager` to manage the loading and application
        of the fixtures.

        Returns:
            None
        """
    def init_classes(self) -> None:
        """
        Initializes and imports classes based on the schema manager's class schemas.

        This method iterates over the class schemas provided by the schema manager and imports
        the classes into the class manager, excluding those of type `SchemaTypes.TYPE`.

        Returns:
            None
        """
    async def teardown(self) -> None:
        """
        Clean up everything on the application exit.

        This method performs a cleanup of all components managed by the AMSDAL framework
        when the application exits. It disconnects and invalidates connections, clears caches,
        and resets the setup status.

        Raises:
            AmsdalRuntimeError: If the AMSDAL manager is not set up.

        Returns:
            None
        """
