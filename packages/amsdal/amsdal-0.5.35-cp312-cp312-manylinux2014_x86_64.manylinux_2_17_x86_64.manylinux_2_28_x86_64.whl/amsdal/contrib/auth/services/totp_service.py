"""TOTP device enrollment and confirmation service."""

from amsdal_data.transactions.decorators import async_transaction
from amsdal_data.transactions.decorators import transaction
from amsdal_utils.models.enums import Versions

from amsdal.contrib.auth.errors import InvalidMFACodeError
from amsdal.contrib.auth.errors import MFADeviceNotFoundError
from amsdal.contrib.auth.errors import MFASetupError
from amsdal.contrib.auth.errors import PermissionDeniedError
from amsdal.contrib.auth.errors import UserNotFoundError
from amsdal.contrib.auth.models.totp_device import TOTPDevice
from amsdal.contrib.auth.models.user import User
from amsdal.contrib.auth.settings import auth_settings
from amsdal.contrib.auth.utils.mfa import generate_qr_code_url
from amsdal.contrib.auth.utils.mfa import generate_totp_secret


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
        if not user.permissions:
            return False

        for permission in user.permissions:
            if permission.model == '*' and permission.action == '*':
                return True
            if permission.model == 'MFADevice' and permission.action in ('*', 'create', 'update'):
                return True

        return False

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
        # Same user can manage their own devices
        if current_user.email == target_user_email:
            return

        # Admin can manage any user's devices
        if cls._is_admin(current_user):
            return

        msg = f'User {current_user.email} does not have permission to {action} devices for {target_user_email}'
        raise PermissionDeniedError(msg)

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
        # Same implementation as sync version (no async DB calls needed)
        cls._check_permission(current_user, target_user_email, action)

    @classmethod
    @transaction
    def setup_totp_device(
        cls,
        current_user: User,
        target_user_email: str,
        device_name: str,
        issuer: str | None = None,
    ) -> dict[str, str]:
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
        # Verify target user exists FIRST
        target_user = (
            User.objects.filter(email=target_user_email, _address__object_version=Versions.LATEST)
            .get_or_none()
            .execute()
        )
        if target_user is None:
            msg = f'User with email {target_user_email} not found'
            raise UserNotFoundError(msg)

        # Check permissions AFTER verifying user exists
        cls._check_permission(current_user, target_user_email, 'create')

        # Generate TOTP secret
        secret = generate_totp_secret()

        # Generate QR code URL
        if issuer is None:
            issuer = auth_settings.MFA_TOTP_ISSUER

        qr_code_url = generate_qr_code_url(secret, target_user_email, issuer)

        # Create unconfirmed TOTP device
        device = TOTPDevice(  # type: ignore[call-arg]
            user_email=target_user_email,
            name=device_name,
            secret=secret,
            qr_code_url=qr_code_url,
            confirmed=False,  # Explicitly set as unconfirmed
        )
        device.save(force_insert=True)

        # Return secret, QR code URL, and device ID
        return {
            'secret': secret,
            'qr_code_url': qr_code_url,
            'device_id': device._object_id,
        }

    @classmethod
    @async_transaction
    async def asetup_totp_device(
        cls,
        current_user: User,
        target_user_email: str,
        device_name: str,
        issuer: str | None = None,
    ) -> dict[str, str]:
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
        # Verify target user exists FIRST
        target_user = (
            await User.objects.filter(email=target_user_email, _address__object_version=Versions.LATEST)
            .get_or_none()
            .aexecute()
        )
        if target_user is None:
            msg = f'User with email {target_user_email} not found'
            raise UserNotFoundError(msg)

        # Check permissions AFTER verifying user exists
        await cls._acheck_permission(current_user, target_user_email, 'create')

        # Generate TOTP secret
        secret = generate_totp_secret()

        # Generate QR code URL
        if issuer is None:
            issuer = auth_settings.MFA_TOTP_ISSUER

        qr_code_url = generate_qr_code_url(secret, target_user_email, issuer)

        # Create unconfirmed TOTP device
        device = TOTPDevice(  # type: ignore[call-arg]
            user_email=target_user_email,
            name=device_name,
            secret=secret,
            qr_code_url=qr_code_url,
            confirmed=False,  # Explicitly set as unconfirmed
        )
        await device.asave(force_insert=True)

        # Return secret, QR code URL, and device ID
        return {
            'secret': secret,
            'qr_code_url': qr_code_url,
            'device_id': device._object_id,
        }

    @classmethod
    @transaction
    def confirm_totp_device(
        cls,
        current_user: User,
        device_id: str,
        verification_code: str,
    ) -> TOTPDevice:
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
        # Retrieve device by ID
        device = (
            TOTPDevice.objects.filter(_object_id=device_id, _address__object_version=Versions.LATEST)
            .get_or_none()
            .execute()
        )

        if device is None:
            msg = f'TOTP device with ID {device_id} not found'
            raise MFADeviceNotFoundError(msg)

        # Check permissions (ownership or admin)
        if not device.has_object_permission(current_user, 'update'):
            msg = f'User {current_user.email} does not have permission to confirm device {device_id}'
            raise PermissionDeniedError(msg)

        # Verify device not already confirmed
        if device.confirmed:
            msg = f'Device {device_id} is already confirmed'
            raise MFASetupError(msg)

        # Verify code
        if not device.verify_code(verification_code):
            msg = 'Invalid verification code'
            raise InvalidMFACodeError(msg)

        # Mark as confirmed
        device.confirmed = True
        device.save()

        return device

    @classmethod
    @async_transaction
    async def aconfirm_totp_device(
        cls,
        current_user: User,
        device_id: str,
        verification_code: str,
    ) -> TOTPDevice:
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
        # Retrieve device by ID
        device = (
            await TOTPDevice.objects.filter(_object_id=device_id, _address__object_version=Versions.LATEST)
            .get_or_none()
            .aexecute()
        )

        if device is None:
            msg = f'TOTP device with ID {device_id} not found'
            raise MFADeviceNotFoundError(msg)

        # Check permissions (ownership or admin)
        if not device.has_object_permission(current_user, 'update'):
            msg = f'User {current_user.email} does not have permission to confirm device {device_id}'
            raise PermissionDeniedError(msg)

        # Verify device not already confirmed
        if device.confirmed:
            msg = f'Device {device_id} is already confirmed'
            raise MFASetupError(msg)

        # Verify code
        if not device.verify_code(verification_code):
            msg = 'Invalid verification code'
            raise InvalidMFACodeError(msg)

        # Mark as confirmed
        device.confirmed = True
        await device.asave()

        return device
