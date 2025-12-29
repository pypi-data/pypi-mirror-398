from amsdal.contrib.auth.errors import MFADeviceNotFoundError as MFADeviceNotFoundError, PermissionDeniedError as PermissionDeniedError, UserNotFoundError as UserNotFoundError
from amsdal.contrib.auth.models.backup_code import BackupCode as BackupCode
from amsdal.contrib.auth.models.email_mfa_device import EmailMFADevice as EmailMFADevice
from amsdal.contrib.auth.models.mfa_device import MFADevice as MFADevice
from amsdal.contrib.auth.models.user import User as User
from amsdal.contrib.auth.settings import auth_settings as auth_settings
from amsdal.contrib.auth.utils.mfa import DeviceType as DeviceType, generate_backup_codes as generate_backup_codes
from amsdal_data.transactions.decorators import async_transaction, transaction

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
    def add_email_device(cls, current_user: User, target_user_email: str, device_name: str, email: str | None = None) -> EmailMFADevice:
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
    @classmethod
    @async_transaction
    async def aadd_email_device(cls, current_user: User, target_user_email: str, device_name: str, email: str | None = None) -> EmailMFADevice:
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
    @classmethod
    @transaction
    def add_backup_codes(cls, current_user: User, target_user_email: str, device_name: str = 'Backup Codes', code_count: int | None = None) -> tuple[list[BackupCode], list[str]]:
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
    @classmethod
    @async_transaction
    async def aadd_backup_codes(cls, current_user: User, target_user_email: str, device_name: str = 'Backup Codes', code_count: int | None = None) -> tuple[list[BackupCode], list[str]]:
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
    @classmethod
    def list_devices(cls, current_user: User, target_user_email: str, *, include_unconfirmed: bool = False) -> dict[DeviceType, list[MFADevice]]:
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
    @classmethod
    async def alist_devices(cls, current_user: User, target_user_email: str, *, include_unconfirmed: bool = False) -> dict[DeviceType, list[MFADevice]]:
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
    @classmethod
    @transaction
    def remove_device(cls, current_user: User, device_id: str, *, hard_delete: bool = False) -> None:
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
    @classmethod
    @async_transaction
    async def aremove_device(cls, current_user: User, device_id: str, *, hard_delete: bool = False) -> None:
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
