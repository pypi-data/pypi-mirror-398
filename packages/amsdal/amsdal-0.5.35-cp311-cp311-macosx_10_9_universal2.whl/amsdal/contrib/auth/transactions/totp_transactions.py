"""TOTP device transaction wrappers for API endpoints."""

from amsdal_data.transactions.decorators import async_transaction
from amsdal_data.transactions.decorators import transaction
from pydantic import BaseModel
from pydantic import Field

from amsdal.context.manager import AmsdalContextManager
from amsdal.contrib.auth.decorators import require_auth
from amsdal.contrib.auth.models.totp_device import TOTPDevice
from amsdal.contrib.auth.models.user import User
from amsdal.contrib.auth.services.totp_service import TOTPService

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

TAGS = ['Auth', 'MFA', 'TOTP']


class SetupTOTPDeviceRequest(BaseModel):
    """Request model for TOTP device setup."""

    target_user_email: str = Field(..., description='Email of user to setup device for')
    device_name: str = Field(..., description='User-friendly name for the device')
    issuer: str | None = Field(None, description='TOTP issuer name (optional)')


class SetupTOTPDeviceResponse(BaseModel):
    """Response model for TOTP device setup."""

    secret: str = Field(..., description='Base32 TOTP secret (show to user ONCE)')
    qr_code_url: str = Field(..., description='otpauth:// URL for QR code generation')
    device_id: str = Field(..., description='ID of unconfirmed device')


class ConfirmTOTPDeviceRequest(BaseModel):
    """Request model for TOTP device confirmation."""

    device_id: str = Field(..., description='ID of unconfirmed device from setup')
    verification_code: str = Field(..., description='6-digit code from authenticator app', min_length=6, max_length=6)


class ConfirmTOTPDeviceResponse(BaseModel):
    """Response model for TOTP device confirmation."""

    device_id: str = Field(..., description='ID of confirmed device')
    user_email: str = Field(..., description='User email')
    name: str = Field(..., description='Device name')
    confirmed: bool = Field(..., description='Confirmation status')

    @classmethod
    def from_device(cls, device: TOTPDevice) -> 'ConfirmTOTPDeviceResponse':
        """Create response from TOTPDevice model."""
        return cls(
            device_id=device._object_id,
            user_email=device.user_email,
            name=device.name,
            confirmed=device.confirmed,
        )


# ============================================================================
# TRANSACTION FUNCTIONS
# ============================================================================


def get_current_user() -> User:
    """Helper to get current authenticated user from context."""
    return AmsdalContextManager().get_context().get('request').user  # type: ignore[union-attr]


@require_auth
@transaction(tags=TAGS)  # type: ignore[call-arg]
def add_mfa_totp_device_transaction(
    target_user_email: str,
    device_name: str,
    issuer: str | None = None,
) -> SetupTOTPDeviceResponse:
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
    result = TOTPService.setup_totp_device(  # type: ignore[call-arg]
        current_user=get_current_user(),
        target_user_email=target_user_email,
        device_name=device_name,
        issuer=issuer,
    )

    return SetupTOTPDeviceResponse(**result)


@require_auth
@async_transaction(tags=TAGS)  # type: ignore[call-arg]
async def aadd_mfa_totp_device_transaction(
    target_user_email: str,
    device_name: str,
    issuer: str | None = None,
) -> SetupTOTPDeviceResponse:
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

    result = await TOTPService.asetup_totp_device(  # type: ignore[call-arg]
        current_user=get_current_user(),
        target_user_email=target_user_email,
        device_name=device_name,
        issuer=issuer,
    )

    return SetupTOTPDeviceResponse(**result)


@require_auth
@transaction(tags=TAGS)  # type: ignore[call-arg]
def confirm_mfa_totp_device_transaction(
    device_id: str,
    verification_code: str,
) -> ConfirmTOTPDeviceResponse:
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

    device = TOTPService.confirm_totp_device(  # type: ignore[call-arg]
        current_user=get_current_user(),
        device_id=device_id,
        verification_code=verification_code,
    )

    return ConfirmTOTPDeviceResponse.from_device(device)


@require_auth
@async_transaction(tags=TAGS)  # type: ignore[call-arg]
async def aconfirm_mfa_totp_device_transaction(
    device_id: str,
    verification_code: str,
) -> ConfirmTOTPDeviceResponse:
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

    device = await TOTPService.aconfirm_totp_device(  # type: ignore[call-arg]
        current_user=get_current_user(),
        device_id=device_id,
        verification_code=verification_code,
    )

    return ConfirmTOTPDeviceResponse.from_device(device)
