from _typeshed import Incomplete
from amsdal.context.manager import AmsdalContextManager as AmsdalContextManager
from amsdal.contrib.auth.decorators import require_auth as require_auth
from amsdal.contrib.auth.models.email_mfa_device import EmailMFADevice as EmailMFADevice
from amsdal.contrib.auth.models.user import User as User
from amsdal.contrib.auth.services.mfa_device_service import MFADeviceService as MFADeviceService
from amsdal.contrib.auth.utils.mfa import DeviceType as DeviceType
from pydantic import BaseModel

TAGS: Incomplete

class AddEmailDeviceRequest(BaseModel):
    """Request model for adding email MFA device."""
    target_user_email: str
    device_name: str
    email: str | None

class EmailDeviceResponse(BaseModel):
    """Response model for email MFA device."""
    device_id: str
    user_email: str
    name: str
    email: str
    confirmed: bool
    @classmethod
    def from_device(cls, device: EmailMFADevice) -> EmailDeviceResponse:
        """Create response from EmailMFADevice model."""

class AddBackupCodesRequest(BaseModel):
    """Request model for adding backup codes."""
    target_user_email: str
    device_name: str
    code_count: int | None

class AddBackupCodesResponse(BaseModel):
    """Response model for adding backup codes."""
    model_config: Incomplete
    device_count: int
    codes: list[str]

class ListDevicesRequest(BaseModel):
    """Request model for listing MFA devices."""
    target_user_email: str
    include_unconfirmed: bool

class DeviceInfo(BaseModel):
    """Device information for list response."""
    device_id: str
    name: str
    confirmed: bool
    device_type: str

class ListDevicesResponse(BaseModel):
    """Response model for listing MFA devices."""
    totp_devices: list[DeviceInfo]
    email_devices: list[DeviceInfo]
    sms_devices: list[DeviceInfo]
    backup_codes: list[DeviceInfo]
    total_count: int
    @classmethod
    def from_device_dict(cls, devices_by_type: dict) -> ListDevicesResponse:
        """Create response from service layer result."""

class RemoveDeviceRequest(BaseModel):
    """Request model for removing MFA device."""
    device_id: str
    hard_delete: bool

class RemoveDeviceResponse(BaseModel):
    """Response model for removing MFA device."""
    device_id: str
    deleted: bool

def get_current_user() -> User:
    """Helper to get current authenticated user from context."""
@require_auth
def add_mfa_email_device_transaction(target_user_email: str, device_name: str, email: str | None = None) -> EmailDeviceResponse:
    """
    Add email MFA device for a user.

    Email devices are automatically confirmed and can be used immediately.

    Args:
        current_user: The authenticated user making the request.
        request: Email device creation request.

    Returns:
        EmailDeviceResponse: Created device details.

    Raises:
        UserNotFoundError: If target user doesn't exist.
        PermissionDeniedError: If user lacks permission.
    """
@require_auth
async def aadd_mfa_email_device_transaction(target_user_email: str, device_name: str, email: str | None = None) -> EmailDeviceResponse:
    """
    Async version of add_email_device_transaction.

    Add email MFA device for a user.

    Args:
        current_user: The authenticated user making the request.
        request: Email device creation request.

    Returns:
        EmailDeviceResponse: Created device details.

    Raises:
        UserNotFoundError: If target user doesn't exist.
        PermissionDeniedError: If user lacks permission.
    """
@require_auth
def add_mfa_backup_codes_transaction(target_user_email: str, device_name: str, code_count: int | None = None) -> AddBackupCodesResponse:
    """
    Add backup codes for a user.

    Backup codes are one-time use codes that can be used if primary
    MFA methods are unavailable.

    Security Note:
        Plaintext codes are returned ONLY during creation.
        Caller must display/send these to user immediately.
        Codes cannot be retrieved later.

    Args:
        current_user: The authenticated user making the request.
        request: Backup codes creation request.

    Returns:
        AddBackupCodesResponse: Contains plaintext backup codes.

    Raises:
        UserNotFoundError: If target user doesn't exist.
        PermissionDeniedError: If user lacks permission.
    """
@require_auth
async def aadd_mfa_backup_codes_transaction(target_user_email: str, device_name: str, code_count: int | None = None) -> AddBackupCodesResponse:
    """
    Async version of add_backup_codes_transaction.

    Add backup codes for a user.

    Args:
        current_user: The authenticated user making the request.
        request: Backup codes creation request.

    Returns:
        AddBackupCodesResponse: Contains plaintext backup codes.

    Raises:
        UserNotFoundError: If target user doesn't exist.
        PermissionDeniedError: If user lacks permission.
    """
@require_auth
def list_mfa_devices_transaction(target_user_email: str, include_unconfirmed: bool = False) -> ListDevicesResponse:
    """
    List all MFA devices for a user.

    Returns devices grouped by type (TOTP, Email, SMS, Backup Codes).

    Note: Read-only operation, no @transaction decorator needed.

    Args:
        current_user: The authenticated user making the request.
        request: List devices request.

    Returns:
        ListDevicesResponse: Devices grouped by type.

    Raises:
        PermissionDeniedError: If user lacks permission.
    """
@require_auth
async def alist_mfa_devices_transaction(target_user_email: str, include_unconfirmed: bool = False) -> ListDevicesResponse:
    """
    Async version of list_devices_transaction.

    List all MFA devices for a user.

    Args:
        current_user: The authenticated user making the request.
        request: List devices request.

    Returns:
        ListDevicesResponse: Devices grouped by type.

    Raises:
        PermissionDeniedError: If user lacks permission.
    """
@require_auth
def remove_mfa_device_transaction(device_id: str, hard_delete: bool = False) -> RemoveDeviceResponse:
    """
    Remove (deactivate or delete) an MFA device.

    By default performs soft delete (marks inactive) to preserve audit trail.
    Use hard_delete=True to permanently remove the device.

    Args:
        current_user: The authenticated user making the request.
        request: Remove device request.

    Returns:
        RemoveDeviceResponse: Removal confirmation.

    Raises:
        PermissionDeniedError: If user lacks permission.
        MFADeviceNotFoundError: If device doesn't exist.
    """
@require_auth
async def aremove_mfa_device_transaction(device_id: str, hard_delete: bool = False) -> RemoveDeviceResponse:
    """
    Async version of remove_device_transaction.

    Remove (deactivate or delete) an MFA device.

    Args:
        current_user: The authenticated user making the request.
        request: Remove device request.

    Returns:
        RemoveDeviceResponse: Removal confirmation.

    Raises:
        PermissionDeniedError: If user lacks permission.
        MFADeviceNotFoundError: If device doesn't exist.
    """
