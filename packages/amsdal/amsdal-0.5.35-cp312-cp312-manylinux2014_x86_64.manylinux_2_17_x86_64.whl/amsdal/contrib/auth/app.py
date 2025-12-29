from amsdal_utils.lifecycle.enum import LifecycleEvent
from amsdal_utils.lifecycle.producer import LifecycleProducer

from amsdal.contrib.app_config import AppConfig


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
        from amsdal.contrib.auth.lifecycle.consumer import AuthenticateUserConsumer
        from amsdal.contrib.auth.lifecycle.consumer import CheckAndCreateSuperUserConsumer
        from amsdal.contrib.auth.lifecycle.consumer import CheckPermissionConsumer

        LifecycleProducer.add_listener(LifecycleEvent.ON_SERVER_STARTUP, CheckAndCreateSuperUserConsumer)
        LifecycleProducer.add_listener(LifecycleEvent.ON_AUTHENTICATE, AuthenticateUserConsumer)
        LifecycleProducer.add_listener(LifecycleEvent.ON_PERMISSION_CHECK, CheckPermissionConsumer)
