from datetime import datetime
from typing import Any
from typing import ClassVar

from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field

from amsdal.contrib.auth.models.mfa_device import MFADevice
from amsdal.contrib.auth.utils.mfa import DeviceType


class EmailMFADevice(MFADevice):
    """
    Email-based MFA device model.

    This model represents an email-based MFA method where a temporary code is sent
    to the user's email address for authentication.

    Attributes:
        email (str): The email address to send codes to (could be same as user email or alternate).
        code (str | None): Temporary MFA code (stored temporarily, expires after use).
        code_expires_at (datetime | None): When the current code expires.
    """

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB

    email: str = Field(title='Email Address')
    code: str | None = Field(None, title='Current Code')
    code_expires_at: datetime | None = Field(None, title='Code Expiration')

    def post_init(self, *, is_new_object: bool, kwargs: dict[str, Any]) -> None:
        """
        Post-initializes an email MFA device by setting the device type.

        Args:
            is_new_object (bool): Indicates if the object is new.
            kwargs (dict[str, Any]): The keyword arguments containing device details.
        """
        super().post_init(is_new_object=is_new_object, kwargs=kwargs)
        self.device_type = DeviceType.EMAIL

        # Email devices are confirmed by default (verification happens through email ownership)
        if is_new_object:
            self.confirmed = True

    def generate_and_send_code(self) -> str:
        """
        Generate a new MFA code and send it via email.

        This method generates a random numeric code, sets its expiration time,
        and sends it to the configured email address.

        Returns:
            str: The generated code (for testing purposes).

        Note:
            In production, you should implement actual email sending logic here
            or call an email service.
        """
        from amsdal.contrib.auth.utils.mfa import generate_email_mfa_code
        from amsdal.contrib.auth.utils.mfa import get_email_code_expiration

        # Generate new code
        self.code = generate_email_mfa_code()
        self.code_expires_at = get_email_code_expiration()

        # TODO: Implement actual email sending
        # For now, we'll just store the code
        # In production, integrate with your email service:
        # send_email(
        #     to=self.email,
        #     subject='Your MFA Code',
        #     body=f'Your verification code is: {self.code}'
        # )

        return self.code

    def verify_code(self, code: str) -> bool:
        """
        Verify an email MFA code.

        Args:
            code (str): The code to verify.

        Returns:
            bool: True if the code is valid and not expired, False otherwise.
        """
        from amsdal.contrib.auth.utils.mfa import is_email_code_valid

        # Check if code matches
        if not self.code or self.code != code:
            return False

        # Check if code is expired
        if not self.code_expires_at or not is_email_code_valid(self.code_expires_at):
            return False

        return True

    def clear_code(self) -> None:
        """
        Clear the current code after successful use or expiration.
        """
        self.code = None
        self.code_expires_at = None

    def __str__(self) -> str:
        return f'EmailMFADevice(name={self.name}, email={self.email}, user={self.user_email})'
