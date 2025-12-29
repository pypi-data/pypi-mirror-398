"""MFA device transaction wrappers for API endpoints."""

from amsdal_data.transactions.decorators import async_transaction
from amsdal_data.transactions.decorators import transaction
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from amsdal.context.manager import AmsdalContextManager
from amsdal.contrib.auth.decorators import require_auth
from amsdal.contrib.auth.models.email_mfa_device import EmailMFADevice
from amsdal.contrib.auth.models.user import User
from amsdal.contrib.auth.services.mfa_device_service import MFADeviceService
from amsdal.contrib.auth.utils.mfa import DeviceType

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

TAGS = ['Auth', 'MFA']


class AddEmailDeviceRequest(BaseModel):
    """Request model for adding email MFA device."""

    target_user_email: str = Field(..., description='Email of user to add device for')
    device_name: str = Field(..., description='User-friendly name for the device')
    email: str | None = Field(None, description='Email for MFA codes (defaults to target_user_email)')


class EmailDeviceResponse(BaseModel):
    """Response model for email MFA device."""

    device_id: str = Field(..., description='Device ID')
    user_email: str = Field(..., description='User email')
    name: str = Field(..., description='Device name')
    email: str = Field(..., description='Email where MFA codes are sent')
    confirmed: bool = Field(..., description='Whether device is confirmed')

    @classmethod
    def from_device(cls, device: EmailMFADevice) -> 'EmailDeviceResponse':
        """Create response from EmailMFADevice model."""
        return cls(
            device_id=device._object_id,
            user_email=device.user_email,
            name=device.name,
            email=device.email,
            confirmed=device.confirmed,
        )


class AddBackupCodesRequest(BaseModel):
    """Request model for adding backup codes."""

    target_user_email: str = Field(..., description='Email of user to add codes for')
    device_name: str = Field('Backup Codes', description='Name for the backup code set')
    code_count: int | None = Field(None, description='Number of codes to generate (optional)', ge=1, le=20)


class AddBackupCodesResponse(BaseModel):
    """Response model for adding backup codes."""

    model_config = ConfigDict(
        json_schema_extra={
            'example': {
                'device_count': 10,
                'codes': ['ABC123DEF456', 'GHI789JKL012', '...'],
            },
        },
    )

    device_count: int = Field(..., description='Number of backup codes generated')
    codes: list[str] = Field(..., description='Plaintext backup codes (DISPLAY ONCE)')


class ListDevicesRequest(BaseModel):
    """Request model for listing MFA devices."""

    target_user_email: str = Field(..., description='Email of user to list devices for')
    include_unconfirmed: bool = Field(False, description='Whether to include unconfirmed devices')


class DeviceInfo(BaseModel):
    """Device information for list response."""

    device_id: str = Field(..., description='Device ID')
    name: str = Field(..., description='Device name')
    confirmed: bool = Field(..., description='Whether device is confirmed')
    device_type: str = Field(..., description='Type of device')


class ListDevicesResponse(BaseModel):
    """Response model for listing MFA devices."""

    totp_devices: list[DeviceInfo] = Field(default_factory=list, description='TOTP authenticator devices')
    email_devices: list[DeviceInfo] = Field(default_factory=list, description='Email MFA devices')
    sms_devices: list[DeviceInfo] = Field(default_factory=list, description='SMS MFA devices')
    backup_codes: list[DeviceInfo] = Field(default_factory=list, description='Backup code devices')
    total_count: int = Field(..., description='Total number of devices')

    @classmethod
    def from_device_dict(cls, devices_by_type: dict) -> 'ListDevicesResponse':  # type: ignore[type-arg]
        """Create response from service layer result."""
        totp_devices = [
            DeviceInfo(
                device_id=device._object_id,
                name=device.name,
                confirmed=device.confirmed,
                device_type='totp',
            )
            for device in devices_by_type.get(DeviceType.TOTP, [])
        ]

        email_devices = [
            DeviceInfo(
                device_id=device._object_id,
                name=device.name,
                confirmed=device.confirmed,
                device_type='email',
            )
            for device in devices_by_type.get(DeviceType.EMAIL, [])
        ]

        sms_devices = [
            DeviceInfo(
                device_id=device._object_id,
                name=device.name,
                confirmed=device.confirmed,
                device_type='sms',
            )
            for device in devices_by_type.get(DeviceType.SMS, [])
        ]

        backup_codes = [
            DeviceInfo(
                device_id=device._object_id,
                name=device.name,
                confirmed=device.confirmed,
                device_type='backup_code',
            )
            for device in devices_by_type.get(DeviceType.BACKUP_CODE, [])
        ]

        total = len(totp_devices) + len(email_devices) + len(sms_devices) + len(backup_codes)

        return cls(
            totp_devices=totp_devices,
            email_devices=email_devices,
            sms_devices=sms_devices,
            backup_codes=backup_codes,
            total_count=total,
        )


class RemoveDeviceRequest(BaseModel):
    """Request model for removing MFA device."""

    device_id: str = Field(..., description='ID of device to remove')
    hard_delete: bool = Field(False, description='If True, permanently delete; if False, soft delete')


class RemoveDeviceResponse(BaseModel):
    """Response model for removing MFA device."""

    device_id: str = Field(..., description='ID of removed device')
    deleted: bool = Field(..., description='Whether device was permanently deleted')


# ============================================================================
# TRANSACTION FUNCTIONS
# ============================================================================


def get_current_user() -> User:
    """Helper to get current authenticated user from context."""
    return AmsdalContextManager().get_context().get('request').user  # type: ignore[union-attr]


@require_auth
@transaction(tags=TAGS)  # type: ignore[call-arg]
def add_mfa_email_device_transaction(
    target_user_email: str,
    device_name: str,
    email: str | None = None,
) -> EmailDeviceResponse:
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

    device = MFADeviceService.add_email_device(  # type: ignore[call-arg]
        current_user=get_current_user(),
        target_user_email=target_user_email,
        device_name=device_name,
        email=email,
    )

    return EmailDeviceResponse.from_device(device)


@require_auth
@async_transaction(tags=TAGS)  # type: ignore[call-arg]
async def aadd_mfa_email_device_transaction(
    target_user_email: str,
    device_name: str,
    email: str | None = None,
) -> EmailDeviceResponse:
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

    device = await MFADeviceService.aadd_email_device(  # type: ignore[call-arg]
        current_user=get_current_user(),
        target_user_email=target_user_email,
        device_name=device_name,
        email=email,
    )

    return EmailDeviceResponse.from_device(device)


@require_auth
@transaction(tags=TAGS)  # type: ignore[call-arg]
def add_mfa_backup_codes_transaction(
    target_user_email: str,
    device_name: str,
    code_count: int | None = None,
) -> AddBackupCodesResponse:
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
    devices, plaintext_codes = MFADeviceService.add_backup_codes(  # type: ignore[call-arg]
        current_user=get_current_user(),
        target_user_email=target_user_email,
        device_name=device_name,
        code_count=code_count,
    )

    return AddBackupCodesResponse(
        device_count=len(devices),
        codes=plaintext_codes,
    )


@require_auth
@async_transaction(tags=TAGS)  # type: ignore[call-arg]
async def aadd_mfa_backup_codes_transaction(
    target_user_email: str,
    device_name: str,
    code_count: int | None = None,
) -> AddBackupCodesResponse:
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

    devices, plaintext_codes = await MFADeviceService.aadd_backup_codes(  # type: ignore[call-arg]
        current_user=get_current_user(),
        target_user_email=target_user_email,
        device_name=device_name,
        code_count=code_count,
    )

    return AddBackupCodesResponse(
        device_count=len(devices),
        codes=plaintext_codes,
    )


@require_auth
@transaction(tags=TAGS)  # type: ignore[call-arg]
def list_mfa_devices_transaction(
    target_user_email: str,
    include_unconfirmed: bool = False,  # noqa: FBT001, FBT002
) -> ListDevicesResponse:
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

    devices_by_type = MFADeviceService.list_devices(
        current_user=get_current_user(),
        target_user_email=target_user_email,
        include_unconfirmed=include_unconfirmed,
    )

    return ListDevicesResponse.from_device_dict(devices_by_type)


@require_auth
@async_transaction(tags=TAGS)  # type: ignore[call-arg]
async def alist_mfa_devices_transaction(
    target_user_email: str,
    include_unconfirmed: bool = False,  # noqa: FBT001, FBT002
) -> ListDevicesResponse:
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

    devices_by_type = await MFADeviceService.alist_devices(
        current_user=get_current_user(),
        target_user_email=target_user_email,
        include_unconfirmed=include_unconfirmed,
    )

    return ListDevicesResponse.from_device_dict(devices_by_type)


@require_auth
@transaction(tags=TAGS)  # type: ignore[call-arg]
def remove_mfa_device_transaction(
    device_id: str,
    hard_delete: bool = False,  # noqa: FBT001, FBT002
) -> RemoveDeviceResponse:
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

    MFADeviceService.remove_device(  # type: ignore[call-arg]
        current_user=get_current_user(),
        device_id=device_id,
        hard_delete=hard_delete,
    )

    return RemoveDeviceResponse(
        device_id=device_id,
        deleted=hard_delete,
    )


@require_auth
@async_transaction(tags=TAGS)  # type: ignore[call-arg]
async def aremove_mfa_device_transaction(
    device_id: str,
    hard_delete: bool = False,  # noqa: FBT001, FBT002
) -> RemoveDeviceResponse:
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

    await MFADeviceService.aremove_device(  # type: ignore[call-arg]
        current_user=get_current_user(),
        device_id=device_id,
        hard_delete=hard_delete,
    )

    return RemoveDeviceResponse(
        device_id=device_id,
        deleted=hard_delete,
    )
