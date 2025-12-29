from datetime import datetime
from typing import Any
from typing import ClassVar

from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field

from amsdal.contrib.auth.models.mfa_device import MFADevice
from amsdal.contrib.auth.utils.mfa import DeviceType


class SMSDevice(MFADevice):
    """
    SMS-based MFA device model (future implementation).

    This model represents an SMS-based MFA method where a temporary code is sent
    to the user's phone number for authentication.

    Note:
        This is a placeholder for future SMS support. Full implementation requires
        integration with an SMS service provider (e.g., Twilio, AWS SNS).

    Attributes:
        phone_number (str): The phone number to send codes to.
        code (str | None): Temporary MFA code (stored temporarily, expires after use).
        code_expires_at (datetime | None): When the current code expires.
    """

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB

    phone_number: str = Field(title='Phone Number')
    code: str | None = Field(None, title='Current Code')
    code_expires_at: datetime | None = Field(None, title='Code Expiration')

    def post_init(self, *, is_new_object: bool, kwargs: dict[str, Any]) -> None:
        """
        Post-initializes an SMS MFA device by setting the device type.

        Args:
            is_new_object (bool): Indicates if the object is new.
            kwargs (dict[str, Any]): The keyword arguments containing device details.
        """
        super().post_init(is_new_object=is_new_object, kwargs=kwargs)
        self.device_type = DeviceType.SMS

    def generate_and_send_code(self) -> str:
        """
        Generate a new MFA code and send it via SMS.

        This method generates a random numeric code, sets its expiration time,
        and sends it to the configured phone number.

        Returns:
            str: The generated code (for testing purposes).

        Raises:
            NotImplementedError: This feature requires SMS service integration.

        Note:
            Full implementation requires integration with an SMS provider.
            Example providers: Twilio, AWS SNS, MessageBird, etc.
        """
        from amsdal.contrib.auth.utils.mfa import generate_email_mfa_code
        from amsdal.contrib.auth.utils.mfa import get_email_code_expiration

        # Generate new code
        self.code = generate_email_mfa_code()
        self.code_expires_at = get_email_code_expiration()

        # TODO: Implement SMS sending with your SMS provider
        # Example with Twilio:
        # from twilio.rest import Client
        # client = Client(account_sid, auth_token)
        # client.messages.create(
        #     to=self.phone_number,
        #     from_=your_twilio_number,
        #     body=f'Your MFA code is: {self.code}'
        # )

        msg = 'SMS MFA is not yet implemented. Please integrate with an SMS service provider (e.g., Twilio, AWS SNS).'
        raise NotImplementedError(msg)

    def verify_code(self, code: str) -> bool:
        """
        Verify an SMS MFA code.

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
        return f'SMSDevice(name={self.name}, phone={self.phone_number}, user={self.user_email})'
