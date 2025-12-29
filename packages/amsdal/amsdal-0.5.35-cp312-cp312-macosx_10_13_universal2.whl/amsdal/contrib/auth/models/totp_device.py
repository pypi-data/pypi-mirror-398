from typing import Any
from typing import ClassVar

from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field

from amsdal.contrib.auth.models.mfa_device import MFADevice
from amsdal.contrib.auth.utils.mfa import DeviceType


class TOTPDevice(MFADevice):
    """
    Time-based One-Time Password (TOTP) device model.

    This model represents an authenticator app device (e.g., Google Authenticator, Authy)
    that generates time-based one-time passwords following RFC 6238.

    Attributes:
        secret (str): The encrypted TOTP secret key shared with the authenticator app.
        qr_code_url (str | None): URL for the QR code used during device setup.
        digits (int): Number of digits in the generated code (default: 6).
        step (int): Time step in seconds for code generation (default: 30).
    """

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB

    secret: str = Field(title='TOTP Secret')
    qr_code_url: str | None = Field(None, title='QR Code URL')
    digits: int = Field(6, title='Code Digits')
    step: int = Field(30, title='Time Step (seconds)')

    def post_init(self, *, is_new_object: bool, kwargs: dict[str, Any]) -> None:
        """
        Post-initializes a TOTP device by setting the device type.

        Args:
            is_new_object (bool): Indicates if the object is new.
            kwargs (dict[str, Any]): The keyword arguments containing device details.
        """
        super().post_init(is_new_object=is_new_object, kwargs=kwargs)
        self.device_type = DeviceType.TOTP

    def verify_code(self, code: str) -> bool:
        """
        Verify a TOTP code against this device's secret.

        Args:
            code (str): The TOTP code to verify.

        Returns:
            bool: True if the code is valid, False otherwise.
        """
        from amsdal.contrib.auth.utils.mfa import verify_totp_code

        return verify_totp_code(self.secret, code, self.digits, self.step)

    def __str__(self) -> str:
        return f'TOTPDevice(name={self.name}, user={self.user_email})'
