from _typeshed import Incomplete
from amsdal.context.manager import AmsdalContextManager as AmsdalContextManager
from amsdal.contrib.auth.decorators import require_auth as require_auth
from amsdal.contrib.auth.models.totp_device import TOTPDevice as TOTPDevice
from amsdal.contrib.auth.models.user import User as User
from amsdal.contrib.auth.services.totp_service import TOTPService as TOTPService
from pydantic import BaseModel

TAGS: Incomplete

class SetupTOTPDeviceRequest(BaseModel):
    """Request model for TOTP device setup."""
    target_user_email: str
    device_name: str
    issuer: str | None

class SetupTOTPDeviceResponse(BaseModel):
    """Response model for TOTP device setup."""
    secret: str
    qr_code_url: str
    device_id: str

class ConfirmTOTPDeviceRequest(BaseModel):
    """Request model for TOTP device confirmation."""
    device_id: str
    verification_code: str

class ConfirmTOTPDeviceResponse(BaseModel):
    """Response model for TOTP device confirmation."""
    device_id: str
    user_email: str
    name: str
    confirmed: bool
    @classmethod
    def from_device(cls, device: TOTPDevice) -> ConfirmTOTPDeviceResponse:
        """Create response from TOTPDevice model."""

def get_current_user() -> User:
    """Helper to get current authenticated user from context."""
@require_auth
def add_mfa_totp_device_transaction(target_user_email: str, device_name: str, issuer: str | None = None) -> SetupTOTPDeviceResponse:
    """
    Setup TOTP device (Step 1 of 2).

    Creates an unconfirmed TOTP device and returns the secret and QR code URL.
    The secret is only returned once and cannot be retrieved later.

    Args:
        request: Setup request containing target user and device details.

    Returns:
        SetupTOTPDeviceResponse: Contains secret, QR code URL, and device ID.

    Raises:
        UserNotFoundError: If target user doesn't exist.
        PermissionDeniedError: If user lacks permission.
    """
@require_auth
async def aadd_mfa_totp_device_transaction(target_user_email: str, device_name: str, issuer: str | None = None) -> SetupTOTPDeviceResponse:
    """
    Async version of setup_totp_device_transaction.

    Setup TOTP device (Step 1 of 2).

    Args:
        request: Setup request containing target user and device details.

    Returns:
        SetupTOTPDeviceResponse: Contains secret, QR code URL, and device ID.

    Raises:
        UserNotFoundError: If target user doesn't exist.
        PermissionDeniedError: If user lacks permission.
    """
@require_auth
def confirm_mfa_totp_device_transaction(device_id: str, verification_code: str) -> ConfirmTOTPDeviceResponse:
    """
    Confirm TOTP device by verifying code (Step 2 of 2).

    Validates the verification code from the authenticator app and marks
    the device as confirmed if successful.

    Args:
        request: Confirmation request containing device ID and verification code.

    Returns:
        ConfirmTOTPDeviceResponse: Confirmed device details.

    Raises:
        MFADeviceNotFoundError: If device doesn't exist.
        PermissionDeniedError: If user lacks permission.
        InvalidMFACodeError: If verification code is incorrect.
        MFASetupError: If device already confirmed.
    """
@require_auth
async def aconfirm_mfa_totp_device_transaction(device_id: str, verification_code: str) -> ConfirmTOTPDeviceResponse:
    """
    Async version of confirm_totp_device_transaction.

    Confirm TOTP device by verifying code (Step 2 of 2).

    Args:
        request: Confirmation request containing device ID and verification code.

    Returns:
        ConfirmTOTPDeviceResponse: Confirmed device details.

    Raises:
        MFADeviceNotFoundError: If device doesn't exist.
        PermissionDeniedError: If user lacks permission.
        InvalidMFACodeError: If verification code is incorrect.
        MFASetupError: If device already confirmed.
    """
