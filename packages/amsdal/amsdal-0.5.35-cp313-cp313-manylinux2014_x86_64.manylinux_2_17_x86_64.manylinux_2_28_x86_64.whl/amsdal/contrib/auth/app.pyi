from amsdal.contrib.app_config import AppConfig as AppConfig

class AuthAppConfig(AppConfig):
    """
    Configuration class for the authentication application.

    This class sets up the necessary listeners for various lifecycle events
    related to authentication and permission checks.
    """
    def on_ready(self) -> None:
        """
        Sets up listeners for various lifecycle events.

        This method adds listeners for server startup, user authentication, and permission checks.
        """
