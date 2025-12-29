from _typeshed import Incomplete
from amsdal.cloud.constants import JWT_PUBLIC_KEY as JWT_PUBLIC_KEY
from amsdal.cloud.services.auth.base import AuthHandlerBase as AuthHandlerBase
from amsdal.errors import AmsdalAuthenticationError as AmsdalAuthenticationError

HMAC_KEY: bytes

class TokenAuthHandler(AuthHandlerBase):
    """
    Handles authentication using a token.

    This class provides functionality to authenticate using a JWT token and validate its checksum.
    """
    __token: Incomplete
    public_key: Incomplete
    def __init__(self, token: str | None, public_key: str = ...) -> None: ...
    def _validate_checksum(self, expected_checksum: str) -> None: ...
    def validate_credentials(self) -> None:
        """
        Validates the provided JWT token.

        This method decodes the token and validates its checksum or expiration date.

        Raises:
            AmsdalAuthenticationError: If the token is expired, has an invalid signature, is invalid, or is missing
                an expiration date.
        """
