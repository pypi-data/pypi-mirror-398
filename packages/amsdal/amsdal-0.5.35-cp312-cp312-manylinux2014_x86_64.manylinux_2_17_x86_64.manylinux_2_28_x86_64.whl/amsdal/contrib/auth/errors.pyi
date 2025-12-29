from amsdal_utils.errors import AmsdalError

class UserCreationError(AmsdalError): ...
class AuthenticationError(AmsdalError): ...
class MFARequiredError(AuthenticationError):
    """Raised when MFA verification is required but not provided."""
class InvalidMFACodeError(AuthenticationError):
    """Raised when the provided MFA code is invalid."""
class MFADeviceNotFoundError(AmsdalError):
    """Raised when no valid MFA device is found for the user."""
class MFASetupError(AmsdalError):
    """Raised when there's an error during MFA device setup."""
class PermissionDeniedError(AmsdalError):
    """Raised when a user lacks permission for an operation."""
class UserNotFoundError(AmsdalError):
    """Raised when a target user cannot be found."""
