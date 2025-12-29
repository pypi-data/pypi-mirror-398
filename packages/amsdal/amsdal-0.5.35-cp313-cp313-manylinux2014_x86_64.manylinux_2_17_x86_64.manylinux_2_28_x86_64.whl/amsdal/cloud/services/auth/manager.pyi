from amsdal.cloud.enums import AuthType as AuthType
from amsdal.cloud.services.auth.base import AuthHandlerBase as AuthHandlerBase
from amsdal.cloud.services.auth.credentials import CredentialsAuthHandler as CredentialsAuthHandler
from amsdal.cloud.services.auth.token import TokenAuthHandler as TokenAuthHandler
from amsdal.configs.main import settings as settings
from amsdal.errors import AmsdalAuthenticationError as AmsdalAuthenticationError, AmsdalMissingCredentialsError as AmsdalMissingCredentialsError
from amsdal_utils.utils.singleton import Singleton

class AuthManager(metaclass=Singleton):
    """
    Manages authentication for the application.

    This class handles the initialization and validation of authentication credentials based on
        the provided authentication type.
    """
    _auth_handler: AuthHandlerBase
    def __init__(self, auth_type: AuthType | None = None) -> None: ...
    def authenticate(self) -> None:
        """
        Authenticates the user by validating the provided credentials.

        This method uses the authentication handler to validate the credentials based on the authentication type.

        Raises:
            AmsdalAuthenticationError: If the authentication fails.
        """
