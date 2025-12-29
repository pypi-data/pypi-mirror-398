from datetime import UTC
from datetime import datetime
from typing import ClassVar

from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field

from amsdal.contrib.auth.utils.mfa import DeviceType


def _now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(tz=UTC)


class MFADevice(Model):
    """
    Base model for Multi-Factor Authentication devices.

    This model serves as the base class for all MFA device types (TOTP, Backup Codes, Email, SMS).
    Each device is associated with a user and must be confirmed before it can be used for authentication.

    Attributes:
        user_email (str): Email of the user who owns this device (reference to User).
        device_type (str): Type of MFA device ('totp', 'backup_code', 'email', 'sms').
        name (str): User-friendly name for the device.
        is_active (bool): Whether the device is currently active and can be used.
        confirmed (bool): Whether the device has been verified during setup.
        created_at (datetime): When the device was created.
        last_used_at (datetime | None): When the device was last used for authentication.
    """

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB

    user_email: str = Field(title='User Email')
    device_type: DeviceType | None = Field(default=None, title='Device Type')
    name: str = Field(title='Device Name')
    is_active: bool = Field(True, title='Is Active')
    confirmed: bool = Field(False, title='Confirmed')
    created_at: datetime = Field(default_factory=_now_utc, title='Created At')
    last_used_at: datetime | None = Field(None, title='Last Used At')

    @property
    def display_name(self) -> str:
        """
        Returns the display name of the device.

        Returns:
            str: The device name and type.
        """
        return f'{self.name} ({self.device_type})'

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f'MFADevice(name={self.name}, type={self.device_type}, user={self.user_email})'

    def has_object_permission(self, user: 'User', action: str) -> bool:  # type: ignore # noqa: F821
        """
        Check if a user has permission to perform an action on this device.

        Users can only manage their own devices. Admins with wildcard permissions
        can manage all devices.

        Args:
            user: The user requesting the action.
            action: The action being requested (read, update, delete, etc.).

        Returns:
            bool: True if the user has permission, False otherwise.
        """
        # Users can only manage their own devices
        if self.user_email == user.email:
            return True

        # Check if user has admin permissions (wildcard model permissions)
        if user.permissions:
            for permission in user.permissions:
                if permission.model == '*' and permission.action in ('*', action):
                    return True
                if permission.model == 'MFADevice' and permission.action in ('*', action):
                    return True

        return False
