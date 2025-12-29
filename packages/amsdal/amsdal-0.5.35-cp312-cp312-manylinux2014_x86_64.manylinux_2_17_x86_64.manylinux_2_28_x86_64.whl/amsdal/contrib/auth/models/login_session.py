import typing as t
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import ClassVar

import jwt
from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field

from amsdal.contrib.auth.utils.mfa import DeviceType
from amsdal.contrib.auth.utils.mfa import aget_active_user_devices
from amsdal.contrib.auth.utils.mfa import get_active_user_devices

if t.TYPE_CHECKING:
    from amsdal.contrib.auth.models.mfa_device import MFADevice


class LoginSession(Model):
    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    email: str = Field(title='Email')
    password: str = Field(title='Password (hash)')
    token: str | None = Field(None, title='Token')
    mfa_code: str | None = Field(None, title='MFA Code')

    @property
    def display_name(self) -> str:
        """
        Returns the display name of the user.

        This method returns the email of the user as their display name.

        Returns:
            str: The email of the user.
        """
        return self.email

    def pre_init(self, *, is_new_object: bool, kwargs: dict[str, Any]) -> None:
        """
        Pre-initializes a user object by validating email and password, and generating a JWT token.

        This method checks if the object is new and validates the provided email and password.
        If the email and password are valid, it generates a JWT token and adds it to the kwargs.

        Args:
            is_new_object (bool): Indicates if the object is new.
            kwargs (dict[str, Any]): The keyword arguments containing user details.

        Raises:
            AuthenticationError: If the email or password is invalid.
        """
        if not is_new_object or '_metadata' in kwargs:
            return
        from amsdal.contrib.auth.errors import AuthenticationError
        from amsdal.contrib.auth.settings import auth_settings

        email = kwargs.get('email', None)
        password = kwargs.get('password', None)
        if not email:
            msg = "Email can't be empty"
            raise AuthenticationError(msg)
        if not password:
            msg = "Password can't be empty"
            raise AuthenticationError(msg)
        lowercased_email = email.lower()
        kwargs['email'] = lowercased_email

        if not auth_settings.AUTH_JWT_KEY:
            msg = 'JWT key is not set'
            raise AuthenticationError(msg)

        expiration_time = datetime.now(tz=UTC) + timedelta(seconds=auth_settings.AUTH_TOKEN_EXPIRATION)
        token = jwt.encode(
            {'email': lowercased_email, 'exp': expiration_time},
            key=auth_settings.AUTH_JWT_KEY,  # type: ignore[arg-type]
            algorithm='HS256',
        )
        kwargs['token'] = token

    def pre_create(self) -> None:
        import bcrypt

        from amsdal.contrib.auth.errors import AuthenticationError
        from amsdal.contrib.auth.errors import InvalidMFACodeError
        from amsdal.contrib.auth.errors import MFARequiredError
        from amsdal.contrib.auth.models.user import User

        user = User.objects.filter(email=self.email).latest().first().execute()

        if not user:
            msg = 'User not found'
            raise AuthenticationError(msg)

        if not bcrypt.checkpw(self.password.encode(), user.password):
            msg = 'Invalid password'
            raise AuthenticationError(msg)

        devices = get_active_user_devices(user)
        if any(devices.values()):
            if not self.mfa_code:
                msg = 'MFA verification is required. Please provide an MFA code.'
                raise MFARequiredError(msg)

            # Verify MFA code against user's devices
            if not self._verify_mfa_code(devices, self.mfa_code):
                msg = 'Invalid MFA code'
                raise InvalidMFACodeError(msg)

        self.password = 'validated'

    def pre_update(self) -> None:
        from amsdal.contrib.auth.errors import AuthenticationError

        msg = 'Update not allowed'
        raise AuthenticationError(msg)

    async def apre_create(self) -> None:
        import bcrypt

        from amsdal.contrib.auth.errors import AuthenticationError
        from amsdal.contrib.auth.errors import InvalidMFACodeError
        from amsdal.contrib.auth.errors import MFARequiredError
        from amsdal.contrib.auth.models.user import User

        user = await User.objects.filter(email=self.email).latest().first().aexecute()

        if not user:
            msg = 'User not found'
            raise AuthenticationError(msg)

        if not bcrypt.checkpw(self.password.encode(), user.password):
            msg = 'Invalid password'
            raise AuthenticationError(msg)

        devices = await aget_active_user_devices(user)
        # Check if MFA is required for this user
        if any(devices.values()):
            if not self.mfa_code:
                msg = 'MFA verification is required. Please provide an MFA code.'
                raise MFARequiredError(msg)

            # Verify MFA code against user's devices
            if not await self._averify_mfa_code(devices, self.mfa_code):
                msg = 'Invalid MFA code'
                raise InvalidMFACodeError(msg)

        self.password = 'validated'

    async def apre_update(self) -> None:
        from amsdal.contrib.auth.errors import AuthenticationError

        msg = 'Update not allowed'
        raise AuthenticationError(msg)

    def _verify_mfa_code(self, devices: dict[DeviceType, list['MFADevice']], code: str) -> bool:  # type: ignore # noqa: F821
        """
        Verify an MFA code against the user's active devices.

        This method checks all active and confirmed MFA devices for the user
        and attempts to verify the provided code against each one.

        Args:
            user: The user attempting to authenticate.
            code: The MFA code to verify.

        Returns:
            bool: True if the code is valid for any device, False otherwise.
        """
        from datetime import UTC
        from datetime import datetime

        for device_type, specific_devices in devices.items():
            try:
                for device in specific_devices:
                    if device.verify_code(code):  # type: ignore[attr-defined]
                        # Update last_used_at
                        device.last_used_at = datetime.now(tz=UTC)  # type: ignore[attr-defined]

                        # Special handling for backup codes (mark as used)
                        if device_type == DeviceType.BACKUP_CODE:
                            device.mark_as_used()  # type: ignore[attr-defined]
                        # Special handling for email devices (clear code)
                        elif device_type == DeviceType.EMAIL:
                            device.clear_code()  # type: ignore[attr-defined]

                        device.save()  # type: ignore[attr-defined]
                        return True

            except Exception:  # noqa: S112
                # Continue to next device type if verification fails
                continue

        return False

    async def _averify_mfa_code(self, devices: dict[DeviceType, list['MFADevice']], code: str) -> bool:  # type: ignore # noqa: F821
        """
        Verify an MFA code against the user's active devices (async version).

        This method checks all active and confirmed MFA devices for the user
        and attempts to verify the provided code against each one.

        Args:
            user: The user attempting to authenticate.
            code: The MFA code to verify.

        Returns:
            bool: True if the code is valid for any device, False otherwise.
        """
        from datetime import UTC
        from datetime import datetime

        for device_type, specific_devices in devices.items():
            try:
                for device in specific_devices:
                    if device.verify_code(code):  # type: ignore[attr-defined]
                        # Update last_used_at
                        device.last_used_at = datetime.now(tz=UTC)  # type: ignore[attr-defined]

                        # Special handling for backup codes (mark as used)
                        if device_type == DeviceType.BACKUP_CODE:
                            device.mark_as_used()  # type: ignore[attr-defined]
                        # Special handling for email devices (clear code)
                        elif device_type == DeviceType.EMAIL:
                            device.clear_code()  # type: ignore[attr-defined]

                        await device.asave()  # type: ignore[attr-defined]
                        return True

            except Exception:  # noqa: S112
                # Continue to next device type if verification fails
                continue

        return False
