from _typeshed import Incomplete
from amsdal.__about__ import __version__ as __version__
from amsdal.cloud.client import AuthClientService as AuthClientService
from amsdal.cloud.constants import ENCRYPT_PUBLIC_KEY as ENCRYPT_PUBLIC_KEY, SYNC_KEY as SYNC_KEY
from amsdal.cloud.services.actions.create_session import CreateSessionAction as CreateSessionAction
from amsdal.cloud.services.auth.base import AuthHandlerBase as AuthHandlerBase
from amsdal.cloud.services.auth.token import TokenAuthHandler as TokenAuthHandler
from amsdal.errors import AmsdalAuthenticationError as AmsdalAuthenticationError

class CredentialsAuthHandler(AuthHandlerBase):
    """
    Handles authentication using credentials.

    This class provides functionality to authenticate using an access key ID and a secret access key.
    """
    __access_key_id: Incomplete
    __secret_access_key: Incomplete
    __fernet: Incomplete
    auth_client: Incomplete
    def __init__(self, access_key_id: str | None, secret_access_key: str | None) -> None: ...
    def _create_session(self) -> str: ...
    def _get_public_key(self) -> str: ...
    def _decode_public_key(self, key: str) -> str: ...
    def validate_credentials(self) -> None:
        """
        Validates the provided credentials by creating a session and decoding the public key.

        Raises:
            AmsdalAuthenticationError: If the credentials are invalid.
        """
