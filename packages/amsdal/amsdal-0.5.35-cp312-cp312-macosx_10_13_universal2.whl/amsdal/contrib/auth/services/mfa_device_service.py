"""MFA device management service for email, backup codes, listing, and removal."""

from amsdal_data.transactions.decorators import async_transaction
from amsdal_data.transactions.decorators import transaction
from amsdal_utils.models.enums import Versions

from amsdal.contrib.auth.errors import MFADeviceNotFoundError
from amsdal.contrib.auth.errors import PermissionDeniedError
from amsdal.contrib.auth.errors import UserNotFoundError
from amsdal.contrib.auth.models.backup_code import BackupCode
from amsdal.contrib.auth.models.email_mfa_device import EmailMFADevice
from amsdal.contrib.auth.models.mfa_device import MFADevice
from amsdal.contrib.auth.models.user import User
from amsdal.contrib.auth.settings import auth_settings
from amsdal.contrib.auth.utils.mfa import DeviceType
from amsdal.contrib.auth.utils.mfa import generate_backup_codes


class MFADeviceService:
    """Service for general MFA device management operations."""

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
            if permission.model == 'MFADevice' and permission.action in ('*', 'create', 'read', 'delete'):
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
    def add_email_device(
        cls,
        current_user: User,
        target_user_email: str,
        device_name: str,
        email: str | None = None,
    ) -> EmailMFADevice:
        """
        Add email MFA device for a user.

        Args:
            current_user: The authenticated user making the request.
            target_user_email: Email of user to add device for.
            device_name: User-friendly name for the device.
            email: Email for MFA codes (defaults to target_user_email).

        Returns:
            EmailMFADevice: The created device.

        Raises:
            UserNotFoundError: If target user doesn't exist.
            PermissionDeniedError: If user lacks permission.
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

        # Default email to target user's email
        if email is None:
            email = target_user_email

        # Create email MFA device (auto-confirmed)
        device = EmailMFADevice(  # type: ignore[call-arg]
            user_email=target_user_email,
            name=device_name,
            email=email,
        )
        device.save(force_insert=True)

        return device

    @classmethod
    @async_transaction
    async def aadd_email_device(
        cls,
        current_user: User,
        target_user_email: str,
        device_name: str,
        email: str | None = None,
    ) -> EmailMFADevice:
        """
        Async version of add_email_device.

        Add email MFA device for a user.

        Args:
            current_user: The authenticated user making the request.
            target_user_email: Email of user to add device for.
            device_name: User-friendly name for the device.
            email: Email for MFA codes (defaults to target_user_email).

        Returns:
            EmailMFADevice: The created device.

        Raises:
            UserNotFoundError: If target user doesn't exist.
            PermissionDeniedError: If user lacks permission.
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

        # Default email to target user's email
        if email is None:
            email = target_user_email

        # Create email MFA device (auto-confirmed)
        device = EmailMFADevice(  # type: ignore[call-arg]
            user_email=target_user_email,
            name=device_name,
            email=email,
        )
        await device.asave(force_insert=True)

        return device

    @classmethod
    @transaction
    def add_backup_codes(
        cls,
        current_user: User,
        target_user_email: str,
        device_name: str = 'Backup Codes',
        code_count: int | None = None,
    ) -> tuple[list[BackupCode], list[str]]:
        """
        Add backup codes for a user.

        Args:
            current_user: The authenticated user making the request.
            target_user_email: Email of user to add codes for.
            device_name: Name for the backup code set.
            code_count: Number of codes (defaults to MFA_BACKUP_CODES_COUNT setting).

        Returns:
            tuple[list[BackupCode], list[str]]: Device instances and plaintext codes.

        Raises:
            UserNotFoundError: If target user doesn't exist.
            PermissionDeniedError: If user lacks permission.

        Security Note:
            Plaintext codes are returned ONLY during creation.
            Caller must display/send these to user immediately.
            Codes cannot be retrieved later.
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

        # Get code count from parameter or settings
        if code_count is None:
            code_count = auth_settings.MFA_BACKUP_CODES_COUNT

        # Generate plaintext codes
        plaintext_codes = generate_backup_codes(code_count)

        # Create BackupCode instances for each code
        devices = []
        for code in plaintext_codes:
            device = BackupCode(  # type: ignore[call-arg]
                user_email=target_user_email,
                name=device_name,
                code=code,  # type: ignore[arg-type]  # Will be hashed in post_init
            )
            device.save(force_insert=True)
            devices.append(device)

        return devices, plaintext_codes

    @classmethod
    @async_transaction
    async def aadd_backup_codes(
        cls,
        current_user: User,
        target_user_email: str,
        device_name: str = 'Backup Codes',
        code_count: int | None = None,
    ) -> tuple[list[BackupCode], list[str]]:
        """
        Async version of add_backup_codes.

        Add backup codes for a user.

        Args:
            current_user: The authenticated user making the request.
            target_user_email: Email of user to add codes for.
            device_name: Name for the backup code set.
            code_count: Number of codes (defaults to MFA_BACKUP_CODES_COUNT setting).

        Returns:
            tuple[list[BackupCode], list[str]]: Device instances and plaintext codes.

        Raises:
            UserNotFoundError: If target user doesn't exist.
            PermissionDeniedError: If user lacks permission.

        Security Note:
            Plaintext codes are returned ONLY during creation.
            Caller must display/send these to user immediately.
            Codes cannot be retrieved later.
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

        # Get code count from parameter or settings
        if code_count is None:
            code_count = auth_settings.MFA_BACKUP_CODES_COUNT

        # Generate plaintext codes
        plaintext_codes = generate_backup_codes(code_count)

        # Create BackupCode instances for each code
        devices = []
        for code in plaintext_codes:
            device = BackupCode(  # type: ignore[call-arg]
                user_email=target_user_email,
                name=device_name,
                code=code,  # type: ignore[arg-type]  # Will be hashed in post_init
            )
            await device.asave(force_insert=True)
            devices.append(device)

        return devices, plaintext_codes

    @classmethod
    def list_devices(
        cls,
        current_user: User,
        target_user_email: str,
        *,
        include_unconfirmed: bool = False,
    ) -> dict[DeviceType, list[MFADevice]]:
        """
        List all MFA devices for a user.

        Args:
            current_user: The authenticated user making the request.
            target_user_email: Email of user to list devices for.
            include_unconfirmed: Whether to include unconfirmed devices.

        Returns:
            dict[DeviceType, list[MFADevice]]: Devices grouped by type.

        Raises:
            PermissionDeniedError: If user lacks permission.

        Note: Read-only operation, no transaction needed.
        """
        from amsdal.contrib.auth.models.sms_device import SMSDevice
        from amsdal.contrib.auth.models.totp_device import TOTPDevice

        # Check permissions
        cls._check_permission(current_user, target_user_email, 'read')

        # Query each device type separately (ORM pattern for inheritance)
        result: dict[DeviceType, list[MFADevice]] = {}

        for device_class, device_type in [
            (TOTPDevice, DeviceType.TOTP),
            (BackupCode, DeviceType.BACKUP_CODE),
            (EmailMFADevice, DeviceType.EMAIL),
            (SMSDevice, DeviceType.SMS),
        ]:
            # Build query for this device type
            query = device_class.objects.filter(  # type: ignore[attr-defined]
                user_email=target_user_email,
                is_active=True,
                _address__object_version=Versions.LATEST,
            )

            # Add confirmed filter unless include_unconfirmed is True
            if not include_unconfirmed:
                query = query.filter(confirmed=True)

            # Execute and store
            result[device_type] = query.execute()

        return result

    @classmethod
    async def alist_devices(
        cls,
        current_user: User,
        target_user_email: str,
        *,
        include_unconfirmed: bool = False,
    ) -> dict[DeviceType, list[MFADevice]]:
        """
        Async version of list_devices.

        List all MFA devices for a user.

        Args:
            current_user: The authenticated user making the request.
            target_user_email: Email of user to list devices for.
            include_unconfirmed: Whether to include unconfirmed devices.

        Returns:
            dict[DeviceType, list[MFADevice]]: Devices grouped by type.

        Raises:
            PermissionDeniedError: If user lacks permission.

        Note: Read-only operation, no transaction needed.
        """
        from amsdal.contrib.auth.models.sms_device import SMSDevice
        from amsdal.contrib.auth.models.totp_device import TOTPDevice

        # Check permissions
        await cls._acheck_permission(current_user, target_user_email, 'read')

        # Query each device type separately (ORM pattern for inheritance)
        result: dict[DeviceType, list[MFADevice]] = {}

        for device_class, device_type in [
            (TOTPDevice, DeviceType.TOTP),
            (BackupCode, DeviceType.BACKUP_CODE),
            (EmailMFADevice, DeviceType.EMAIL),
            (SMSDevice, DeviceType.SMS),
        ]:
            # Build query for this device type
            query = device_class.objects.filter(  # type: ignore[attr-defined]
                user_email=target_user_email,
                is_active=True,
                _address__object_version=Versions.LATEST,
            )

            # Add confirmed filter unless include_unconfirmed is True
            if not include_unconfirmed:
                query = query.filter(confirmed=True)

            # Execute and store
            result[device_type] = await query.aexecute()

        return result

    @classmethod
    @transaction
    def remove_device(
        cls,
        current_user: User,
        device_id: str,
        *,
        hard_delete: bool = False,
    ) -> None:
        """
        Remove (deactivate or delete) an MFA device.

        Args:
            current_user: The authenticated user making the request.
            device_id: ID of the device to remove.
            hard_delete: If True, permanently delete; if False, soft delete (mark inactive).

        Raises:
            PermissionDeniedError: If user lacks permission.
            MFADeviceNotFoundError: If device doesn't exist.

        Security Note:
            Soft delete (default) preserves audit trail.
            Hard delete permanently removes device.
        """
        from amsdal.contrib.auth.models.sms_device import SMSDevice
        from amsdal.contrib.auth.models.totp_device import TOTPDevice

        # Try to find device in each device type class
        device = None
        for device_class in [TOTPDevice, BackupCode, EmailMFADevice, SMSDevice]:
            device = (
                device_class.objects.filter(  # type: ignore[attr-defined]
                    _object_id=device_id, _address__object_version=Versions.LATEST
                )
                .get_or_none()
                .execute()
            )
            if device is not None:
                break

        if device is None:
            msg = f'MFA device with ID {device_id} not found'
            raise MFADeviceNotFoundError(msg)

        # Check permission using object-level permission
        if not device.has_object_permission(current_user, 'delete'):
            msg = f'User {current_user.email} does not have permission to remove device {device_id}'
            raise PermissionDeniedError(msg)

        # Hard delete or soft delete
        if hard_delete:
            device.delete()
        else:
            device.is_active = False
            device.save()

    @classmethod
    @async_transaction
    async def aremove_device(
        cls,
        current_user: User,
        device_id: str,
        *,
        hard_delete: bool = False,
    ) -> None:
        """
        Async version of remove_device.

        Remove (deactivate or delete) an MFA device.

        Args:
            current_user: The authenticated user making the request.
            device_id: ID of the device to remove.
            hard_delete: If True, permanently delete; if False, soft delete (mark inactive).

        Raises:
            PermissionDeniedError: If user lacks permission.
            MFADeviceNotFoundError: If device doesn't exist.

        Security Note:
            Soft delete (default) preserves audit trail.
            Hard delete permanently removes device.
        """
        from amsdal.contrib.auth.models.sms_device import SMSDevice
        from amsdal.contrib.auth.models.totp_device import TOTPDevice

        # Try to find device in each device type class
        device = None
        for device_class in [TOTPDevice, BackupCode, EmailMFADevice, SMSDevice]:
            device = (
                await device_class.objects.filter(  # type: ignore[attr-defined]
                    _object_id=device_id, _address__object_version=Versions.LATEST
                )
                .get_or_none()
                .aexecute()
            )
            if device is not None:
                break

        if device is None:
            msg = f'MFA device with ID {device_id} not found'
            raise MFADeviceNotFoundError(msg)

        # Check permission using object-level permission
        if not device.has_object_permission(current_user, 'delete'):
            msg = f'User {current_user.email} does not have permission to remove device {device_id}'
            raise PermissionDeniedError(msg)

        # Hard delete or soft delete
        if hard_delete:
            await device.adelete()
        else:
            device.is_active = False
            await device.asave()
