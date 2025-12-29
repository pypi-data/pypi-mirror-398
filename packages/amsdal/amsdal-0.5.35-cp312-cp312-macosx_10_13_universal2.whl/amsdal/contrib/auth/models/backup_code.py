from datetime import datetime
from typing import Any
from typing import ClassVar

from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field

from amsdal.contrib.auth.models.mfa_device import MFADevice
from amsdal.contrib.auth.utils.mfa import DeviceType


class BackupCode(MFADevice):
    """
    Backup/Recovery code model for MFA.

    This model represents a one-time use backup code that can be used for authentication
    when the primary MFA device is unavailable. Each code can only be used once.

    Attributes:
        code (bytes): The hashed backup code.
        used (bool): Whether the code has been used.
        used_at (datetime | None): When the code was used.
    """

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB

    code: bytes = Field(title='Hashed Code')
    used: bool = Field(False, title='Used')
    used_at: datetime | None = Field(None, title='Used At')

    def post_init(self, *, is_new_object: bool, kwargs: dict[str, Any]) -> None:
        """
        Post-initializes a backup code by setting the device type and hashing the code.

        Args:
            is_new_object (bool): Indicates if the object is new.
            kwargs (dict[str, Any]): The keyword arguments containing device details.
        """
        super().post_init(is_new_object=is_new_object, kwargs=kwargs)
        self.device_type = DeviceType.BACKUP_CODE

        # Hash the code if it's provided as a string (new object)
        code_value = kwargs.get('code', None)
        if is_new_object and isinstance(code_value, str):
            from amsdal.contrib.auth.utils.mfa import hash_backup_code

            self.code = hash_backup_code(code_value)

        # Backup codes are confirmed by default (no verification needed)
        if is_new_object:
            self.confirmed = True

    def verify_code(self, code: str) -> bool:
        """
        Verify a backup code against this device's stored hash.

        Args:
            code (str): The code to verify.

        Returns:
            bool: True if the code is valid and not yet used, False otherwise.
        """
        from amsdal.contrib.auth.utils.mfa import verify_backup_code

        # Code must not have been used already
        if self.used:
            return False

        return verify_backup_code(self.code, code)

    def mark_as_used(self) -> None:
        """
        Mark this backup code as used.

        This should be called after successful authentication with this code.
        """
        from datetime import UTC

        self.used = True
        self.used_at = datetime.now(tz=UTC)
        self.last_used_at = datetime.now(tz=UTC)

    def __str__(self) -> str:
        status = 'used' if self.used else 'available'
        return f'BackupCode(name={self.name}, user={self.user_email}, status={status})'
