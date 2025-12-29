from amsdal.contrib.auth.errors import InvalidMFACodeError as InvalidMFACodeError, MFADeviceNotFoundError as MFADeviceNotFoundError, MFASetupError as MFASetupError, PermissionDeniedError as PermissionDeniedError, UserNotFoundError as UserNotFoundError
from amsdal.contrib.auth.models.totp_device import TOTPDevice as TOTPDevice
from amsdal.contrib.auth.models.user import User as User
from amsdal.contrib.auth.settings import auth_settings as auth_settings
from amsdal.contrib.auth.utils.mfa import generate_qr_code_url as generate_qr_code_url, generate_totp_secret as generate_totp_secret
from amsdal_data.transactions.decorators import async_transaction, transaction

class TOTPService:
    """Service for TOTP device two-step enrollment flow."""
    @classmethod
    def _is_admin(cls, user: User) -> bool:
        """
        Check if user has admin permissions (wildcard or MFADevice-specific).

        Args:
            user: The user to check.

        Returns:
            bool: True if user has admin permissions, False otherwise.
        """
    @classmethod
    def _check_permission(cls, current_user: User, target_user_email: str, action: str) -> None:
        """
        Check if current_user has permission for action on target_user.

        Args:
            current_user: The authenticated user making the request.
            target_user_email: Email of the user being targeted.
            action: The action being performed.

        Raises:
            PermissionDeniedError: If user lacks permission.
        """
    @classmethod
    async def _acheck_permission(cls, current_user: User, target_user_email: str, action: str) -> None:
        """
        Async version of _check_permission.

        Args:
            current_user: The authenticated user making the request.
            target_user_email: Email of the user being targeted.
            action: The action being performed.

        Raises:
            PermissionDeniedError: If user lacks permission.
        """
    @classmethod
    @transaction
    def setup_totp_device(cls, current_user: User, target_user_email: str, device_name: str, issuer: str | None = None) -> dict[str, str]:
        """
        Step 1: Setup TOTP device (generate secret, create unconfirmed device).

        Args:
            current_user: The authenticated user making the request.
            target_user_email: Email of user to setup device for.
            device_name: User-friendly name for the device.
            issuer: TOTP issuer name (defaults to MFA_TOTP_ISSUER setting).

        Returns:
            dict with keys:
                - secret: Base32 secret (show to user ONCE)
                - qr_code_url: otpauth:// URL for QR code generation
                - device_id: ID of unconfirmed device

        Raises:
            UserNotFoundError: If target user doesn't exist.
            PermissionDeniedError: If user lacks permission.

        Security Note:
            Secret is returned ONLY during setup.
            User must scan QR or manually enter secret.
            Device is created with confirmed=False.
        """
    @classmethod
    @async_transaction
    async def asetup_totp_device(cls, current_user: User, target_user_email: str, device_name: str, issuer: str | None = None) -> dict[str, str]:
        """
        Async version of setup_totp_device.

        Step 1: Setup TOTP device (generate secret, create unconfirmed device).

        Args:
            current_user: The authenticated user making the request.
            target_user_email: Email of user to setup device for.
            device_name: User-friendly name for the device.
            issuer: TOTP issuer name (defaults to MFA_TOTP_ISSUER setting).

        Returns:
            dict with keys:
                - secret: Base32 secret (show to user ONCE)
                - qr_code_url: otpauth:// URL for QR code generation
                - device_id: ID of unconfirmed device

        Raises:
            UserNotFoundError: If target user doesn't exist.
            PermissionDeniedError: If user lacks permission.

        Security Note:
            Secret is returned ONLY during setup.
            User must scan QR or manually enter secret.
            Device is created with confirmed=False.
        """
    @classmethod
    @transaction
    def confirm_totp_device(cls, current_user: User, device_id: str, verification_code: str) -> TOTPDevice:
        """
        Step 2: Confirm TOTP device by verifying code.

        Args:
            current_user: The authenticated user making the request.
            device_id: ID of unconfirmed device from setup step.
            verification_code: 6-digit code from authenticator app.

        Returns:
            TOTPDevice: The confirmed device.

        Raises:
            PermissionDeniedError: If user lacks permission.
            MFADeviceNotFoundError: If device doesn't exist.
            InvalidMFACodeError: If verification code is incorrect.
            MFASetupError: If device already confirmed.

        Flow:
            1. Retrieve unconfirmed device
            2. Check ownership/permissions
            3. Verify code using device.verify_code()
            4. Mark device as confirmed=True
            5. Save and return
        """
    @classmethod
    @async_transaction
    async def aconfirm_totp_device(cls, current_user: User, device_id: str, verification_code: str) -> TOTPDevice:
        """
        Async version of confirm_totp_device.

        Step 2: Confirm TOTP device by verifying code.

        Args:
            current_user: The authenticated user making the request.
            device_id: ID of unconfirmed device from setup step.
            verification_code: 6-digit code from authenticator app.

        Returns:
            TOTPDevice: The confirmed device.

        Raises:
            PermissionDeniedError: If user lacks permission.
            MFADeviceNotFoundError: If device doesn't exist.
            InvalidMFACodeError: If verification code is incorrect.
            MFASetupError: If device already confirmed.

        Flow:
            1. Retrieve unconfirmed device
            2. Check ownership/permissions
            3. Verify code using device.verify_code()
            4. Mark device as confirmed=True
            5. Save and return
        """
