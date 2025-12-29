from amsdal_models.migration import migrations
from amsdal_utils.models.enums import ModuleType


class Migration(migrations.Migration):
    operations: list[migrations.Operation] = [
        # Update LoginSession model to add mfa_code field
        migrations.UpdateClass(
            module_type=ModuleType.CONTRIB,
            class_name="LoginSession",
            old_schema={
                "title": "LoginSession",
                "required": ["email", "password"],
                "properties": {
                    "email": {"type": "string", "title": "Email"},
                    "password": {"type": "string", "title": "Password (hash)"},
                    "token": {"type": "string", "title": "Token"},
                },
                "custom_code": "from datetime import UTC\nfrom datetime import datetime\nfrom datetime import timedelta\nfrom typing import Any\n\nimport jwt\n\n\n@property\ndef display_name(self) -> str:\n    \"\"\"\n        Returns the display name of the user.\n\n        This method returns the email of the user as their display name.\n\n        Returns:\n            str: The email of the user.\n        \"\"\"\n    return self.email\n\nasync def apre_create(self) -> None:\n    import bcrypt\n\n    from amsdal.contrib.auth.errors import AuthenticationError\n    from amsdal.contrib.auth.models.user import User\n    user = await User.objects.filter(email=self.email).latest().first().aexecute()\n    if not user:\n        msg = 'User not found'\n        raise AuthenticationError(msg)\n    if not bcrypt.checkpw(self.password.encode(), user.password):\n        msg = 'Invalid password'\n        raise AuthenticationError(msg)\n    self.password = 'validated'\n\nasync def apre_update(self) -> None:\n    from amsdal.contrib.auth.errors import AuthenticationError\n    msg = 'Update not allowed'\n    raise AuthenticationError(msg)\n\ndef pre_create(self) -> None:\n    import bcrypt\n\n    from amsdal.contrib.auth.errors import AuthenticationError\n    from amsdal.contrib.auth.models.user import User\n    user = User.objects.filter(email=self.email).latest().first().execute()\n    if not user:\n        msg = 'User not found'\n        raise AuthenticationError(msg)\n    if not bcrypt.checkpw(self.password.encode(), user.password):\n        msg = 'Invalid password'\n        raise AuthenticationError(msg)\n    self.password = 'validated'\n\ndef pre_init(self, *, is_new_object: bool, kwargs: dict[str, Any]) -> None:\n    \"\"\"\n        Pre-initializes a user object by validating email and password, and generating a JWT token.\n\n        This method checks if the object is new and validates the provided email and password.\n        If the email and password are valid, it generates a JWT token and adds it to the kwargs.\n\n        Args:\n            is_new_object (bool): Indicates if the object is new.\n            kwargs (dict[str, Any]): The keyword arguments containing user details.\n\n        Raises:\n            AuthenticationError: If the email or password is invalid.\n        \"\"\"\n    if not is_new_object or '_metadata' in kwargs:\n        return\n    from amsdal.contrib.auth.errors import AuthenticationError\n    from amsdal.contrib.auth.settings import auth_settings\n    email = kwargs.get('email', None)\n    password = kwargs.get('password', None)\n    if not email:\n        msg = \"Email can't be empty\"\n        raise AuthenticationError(msg)\n    if not password:\n        msg = \"Password can't be empty\"\n        raise AuthenticationError(msg)\n    lowercased_email = email.lower()\n    kwargs['email'] = lowercased_email\n    if not auth_settings.AUTH_JWT_KEY:\n        msg = 'JWT key is not set'\n        raise AuthenticationError(msg)\n    expiration_time = datetime.now(tz=UTC) + timedelta(seconds=auth_settings.AUTH_TOKEN_EXPIRATION)\n    token = jwt.encode({'email': lowercased_email, 'exp': expiration_time}, key=auth_settings.AUTH_JWT_KEY, algorithm='HS256')\n    kwargs['token'] = token\n\ndef pre_update(self) -> None:\n    from amsdal.contrib.auth.errors import AuthenticationError\n    msg = 'Update not allowed'\n    raise AuthenticationError(msg)",
                "storage_metadata": {
                    "table_name": "LoginSession",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
            new_schema={
                "title": "LoginSession",
                "required": ["email", "password"],
                "properties": {
                    "email": {"type": "string", "title": "Email"},
                    "password": {"type": "string", "title": "Password (hash)"},
                    "token": {"type": "string", "title": "Token"},
                    "mfa_code": {"type": "string", "title": "MFA Code", "default": None},
                },
                "custom_code": "import typing as t\nfrom datetime import UTC\nfrom datetime import datetime\nfrom datetime import timedelta\nfrom typing import Any\n\nimport jwt\n\nif t.TYPE_CHECKING:\n    from amsdal.contrib.auth.models.mfa_device import MFADevice\n\n\n@property\ndef display_name(self) -> str:\n    \"\"\"\n    Returns the display name of the user.\n\n    This method returns the email of the user as their display name.\n\n    Returns:\n        str: The email of the user.\n    \"\"\"\n    return self.email\n\ndef pre_init(self, *, is_new_object: bool, kwargs: dict[str, Any]) -> None:\n    \"\"\"\n    Pre-initializes a user object by validating email and password, and generating a JWT token.\n\n    This method checks if the object is new and validates the provided email and password.\n    If the email and password are valid, it generates a JWT token and adds it to the kwargs.\n\n    Args:\n        is_new_object (bool): Indicates if the object is new.\n        kwargs (dict[str, Any]): The keyword arguments containing user details.\n\n    Raises:\n        AuthenticationError: If the email or password is invalid.\n    \"\"\"\n    if not is_new_object or '_metadata' in kwargs:\n        return\n    from amsdal.contrib.auth.errors import AuthenticationError\n    from amsdal.contrib.auth.settings import auth_settings\n\n    email = kwargs.get('email', None)\n    password = kwargs.get('password', None)\n    if not email:\n        msg = \"Email can't be empty\"\n        raise AuthenticationError(msg)\n    if not password:\n        msg = \"Password can't be empty\"\n        raise AuthenticationError(msg)\n    lowercased_email = email.lower()\n    kwargs['email'] = lowercased_email\n\n    if not auth_settings.AUTH_JWT_KEY:\n        msg = 'JWT key is not set'\n        raise AuthenticationError(msg)\n\n    expiration_time = datetime.now(tz=UTC) + timedelta(seconds=auth_settings.AUTH_TOKEN_EXPIRATION)\n    token = jwt.encode(\n        {'email': lowercased_email, 'exp': expiration_time},\n        key=auth_settings.AUTH_JWT_KEY,\n        algorithm='HS256',\n    )\n    kwargs['token'] = token\n\ndef pre_create(self) -> None:\n    import bcrypt\n\n    from amsdal.contrib.auth.errors import AuthenticationError\n    from amsdal.contrib.auth.errors import InvalidMFACodeError\n    from amsdal.contrib.auth.errors import MFARequiredError\n    from amsdal.contrib.auth.models.user import User\n    from amsdal.contrib.auth.utils.mfa import get_active_user_devices\n\n    user = User.objects.filter(email=self.email).latest().first().execute()\n\n    if not user:\n        msg = 'User not found'\n        raise AuthenticationError(msg)\n\n    if not bcrypt.checkpw(self.password.encode(), user.password):\n        msg = 'Invalid password'\n        raise AuthenticationError(msg)\n\n    devices = get_active_user_devices(user)\n    if any(devices.values()):\n        if not self.mfa_code:\n            msg = 'MFA verification is required. Please provide an MFA code.'\n            raise MFARequiredError(msg)\n\n        # Verify MFA code against user's devices\n        if not self._verify_mfa_code(devices, self.mfa_code):\n            msg = 'Invalid MFA code'\n            raise InvalidMFACodeError(msg)\n\n    self.password = 'validated'\n\ndef pre_update(self) -> None:\n    from amsdal.contrib.auth.errors import AuthenticationError\n\n    msg = 'Update not allowed'\n    raise AuthenticationError(msg)\n\nasync def apre_create(self) -> None:\n    import bcrypt\n\n    from amsdal.contrib.auth.errors import AuthenticationError\n    from amsdal.contrib.auth.errors import InvalidMFACodeError\n    from amsdal.contrib.auth.errors import MFARequiredError\n    from amsdal.contrib.auth.models.user import User\n    from amsdal.contrib.auth.utils.mfa import aget_active_user_devices\n\n    user = await User.objects.filter(email=self.email).latest().first().aexecute()\n\n    if not user:\n        msg = 'User not found'\n        raise AuthenticationError(msg)\n\n    if not bcrypt.checkpw(self.password.encode(), user.password):\n        msg = 'Invalid password'\n        raise AuthenticationError(msg)\n\n    devices = await aget_active_user_devices(user)\n    # Check if MFA is required for this user\n    if any(devices.values()):\n        if not self.mfa_code:\n            msg = 'MFA verification is required. Please provide an MFA code.'\n            raise MFARequiredError(msg)\n\n        # Verify MFA code against user's devices\n        if not await self._averify_mfa_code(devices, self.mfa_code):\n            msg = 'Invalid MFA code'\n            raise InvalidMFACodeError(msg)\n\n    self.password = 'validated'\n\nasync def apre_update(self) -> None:\n    from amsdal.contrib.auth.errors import AuthenticationError\n\n    msg = 'Update not allowed'\n    raise AuthenticationError(msg)\n\ndef _verify_mfa_code(self, devices, code: str) -> bool:\n    from datetime import UTC\n    from datetime import datetime\n    from amsdal.contrib.auth.utils.mfa import DeviceType\n\n    for device_type, specific_devices in devices.items():\n        try:\n            for device in specific_devices:\n                if device.verify_code(code):\n                    # Update last_used_at\n                    device.last_used_at = datetime.now(tz=UTC)\n\n                    # Special handling for backup codes (mark as used)\n                    if device_type == DeviceType.BACKUP_CODE:\n                        device.mark_as_used()\n                    # Special handling for email devices (clear code)\n                    elif device_type == DeviceType.EMAIL:\n                        device.clear_code()\n\n                    device.save()\n                    return True\n\n        except Exception:\n            # Continue to next device type if verification fails\n            continue\n\n    return False\n\nasync def _averify_mfa_code(self, devices, code: str) -> bool:\n    from datetime import UTC\n    from datetime import datetime\n    from amsdal.contrib.auth.utils.mfa import DeviceType\n\n    for device_type, specific_devices in devices.items():\n        try:\n            for device in specific_devices:\n                if device.verify_code(code):\n                    # Update last_used_at\n                    device.last_used_at = datetime.now(tz=UTC)\n\n                    # Special handling for backup codes (mark as used)\n                    if device_type == DeviceType.BACKUP_CODE:\n                        device.mark_as_used()\n                    # Special handling for email devices (clear code)\n                    elif device_type == DeviceType.EMAIL:\n                        device.clear_code()\n\n                    await device.asave()\n                    return True\n\n        except Exception:\n            # Continue to next device type if verification fails\n            continue\n\n    return False",
                "storage_metadata": {
                    "table_name": "LoginSession",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
        ),
        # Create MFADevice base model
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="MFADevice",
            new_schema={
                "title": "MFADevice",
                "type": "object",
                "required": ["user_email", "name"],
                "properties": {
                    "user_email": {"type": "string", "title": "User Email"},
                    "device_type": {"type": "string", "title": "Device Type", "default": None},
                    "name": {"type": "string", "title": "Device Name"},
                    "is_active": {"type": "boolean", "title": "Is Active", "default": True},
                    "confirmed": {"type": "boolean", "title": "Confirmed", "default": False},
                    "created_at": {"type": "datetime", "title": "Created At"},
                    "last_used_at": {"type": "datetime", "title": "Last Used At", "default": None},
                },
                "custom_code": "@property\ndef display_name(self) -> str:\n    \"\"\"\n    Returns the display name of the device.\n\n    Returns:\n        str: The device name and type.\n    \"\"\"\n    return f'{self.name} ({self.device_type})'\n\ndef __repr__(self) -> str:\n    return str(self)\n\ndef __str__(self) -> str:\n    return f'MFADevice(name={self.name}, type={self.device_type}, user={self.user_email})'\n\ndef has_object_permission(self, user, action: str) -> bool:\n    \"\"\"\n    Check if a user has permission to perform an action on this device.\n\n    Users can only manage their own devices. Admins with wildcard permissions\n    can manage all devices.\n\n    Args:\n        user: The user requesting the action.\n        action: The action being requested (read, update, delete, etc.).\n\n    Returns:\n        bool: True if the user has permission, False otherwise.\n    \"\"\"\n    # Users can only manage their own devices\n    if self.user_email == user.email:\n        return True\n\n    # Check if user has admin permissions (wildcard model permissions)\n    if user.permissions:\n        for permission in user.permissions:\n            if permission.model == '*' and permission.action in ('*', action):\n                return True\n            if permission.model == 'MFADevice' and permission.action in ('*', action):\n                return True\n\n    return False",
                "storage_metadata": {
                    "table_name": "MFADevice",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
        ),
        # Create TOTPDevice model
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="TOTPDevice",
            new_schema={
                "title": "TOTPDevice",
                "type": "MFADevice",
                "required": ["user_email", "name", "secret"],
                "properties": {
                    "user_email": {"type": "string", "title": "User Email"},
                    "device_type": {"type": "string", "title": "Device Type", "default": None},
                    "name": {"type": "string", "title": "Device Name"},
                    "is_active": {"type": "boolean", "title": "Is Active", "default": True},
                    "confirmed": {"type": "boolean", "title": "Confirmed", "default": False},
                    "created_at": {"type": "datetime", "title": "Created At"},
                    "last_used_at": {"type": "datetime", "title": "Last Used At", "default": None},
                    "secret": {"type": "string", "title": "TOTP Secret"},
                    "qr_code_url": {"type": "string", "title": "QR Code URL", "default": None},
                    "digits": {"type": "integer", "title": "Code Digits", "default": 6},
                    "step": {"type": "integer", "title": "Time Step (seconds)", "default": 30},
                },
                "custom_code": "from typing import Any\nfrom amsdal.contrib.auth.utils.mfa import DeviceType\n\n\ndef post_init(self, *, is_new_object: bool, kwargs: dict[str, Any]) -> None:\n    \"\"\"\n    Post-initializes a TOTP device by setting the device type.\n\n    Args:\n        is_new_object (bool): Indicates if the object is new.\n        kwargs (dict[str, Any]): The keyword arguments containing device details.\n    \"\"\"\n    super().post_init(is_new_object=is_new_object, kwargs=kwargs)\n    self.device_type = DeviceType.TOTP\n\ndef verify_code(self, code: str) -> bool:\n    \"\"\"\n    Verify a TOTP code against this device's secret.\n\n    Args:\n        code (str): The TOTP code to verify.\n\n    Returns:\n        bool: True if the code is valid, False otherwise.\n    \"\"\"\n    from amsdal.contrib.auth.utils.mfa import verify_totp_code\n\n    return verify_totp_code(self.secret, code, self.digits, self.step)\n\ndef __str__(self) -> str:\n    return f'TOTPDevice(name={self.name}, user={self.user_email})'",
                "storage_metadata": {
                    "table_name": "TOTPDevice",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
        ),
        # Create BackupCode model
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="BackupCode",
            new_schema={
                "title": "BackupCode",
                "type": "MFADevice",
                "required": ["user_email", "name", "code"],
                "properties": {
                    "user_email": {"type": "string", "title": "User Email"},
                    "device_type": {"type": "string", "title": "Device Type", "default": None},
                    "name": {"type": "string", "title": "Device Name"},
                    "is_active": {"type": "boolean", "title": "Is Active", "default": True},
                    "confirmed": {"type": "boolean", "title": "Confirmed", "default": False},
                    "created_at": {"type": "datetime", "title": "Created At"},
                    "last_used_at": {"type": "datetime", "title": "Last Used At", "default": None},
                    "code": {"type": "binary", "title": "Hashed Code"},
                    "used": {"type": "boolean", "title": "Used", "default": False},
                    "used_at": {"type": "datetime", "title": "Used At", "default": None},
                },
                "custom_code": "from typing import Any\nfrom datetime import UTC\nfrom datetime import datetime\nfrom amsdal.contrib.auth.utils.mfa import DeviceType\n\n\ndef post_init(self, *, is_new_object: bool, kwargs: dict[str, Any]) -> None:\n    \"\"\"\n    Post-initializes a backup code by setting the device type and hashing the code.\n\n    Args:\n        is_new_object (bool): Indicates if the object is new.\n        kwargs (dict[str, Any]): The keyword arguments containing device details.\n    \"\"\"\n    super().post_init(is_new_object=is_new_object, kwargs=kwargs)\n    self.device_type = DeviceType.BACKUP_CODE\n\n    # Hash the code if it's provided as a string (new object)\n    code_value = kwargs.get('code', None)\n    if is_new_object and isinstance(code_value, str):\n        from amsdal.contrib.auth.utils.mfa import hash_backup_code\n\n        self.code = hash_backup_code(code_value)\n\n    # Backup codes are confirmed by default (no verification needed)\n    if is_new_object:\n        self.confirmed = True\n\ndef verify_code(self, code: str) -> bool:\n    \"\"\"\n    Verify a backup code against this device's stored hash.\n\n    Args:\n        code (str): The code to verify.\n\n    Returns:\n        bool: True if the code is valid and not yet used, False otherwise.\n    \"\"\"\n    from amsdal.contrib.auth.utils.mfa import verify_backup_code\n\n    # Code must not have been used already\n    if self.used:\n        return False\n\n    return verify_backup_code(self.code, code)\n\ndef mark_as_used(self) -> None:\n    \"\"\"\n    Mark this backup code as used.\n\n    This should be called after successful authentication with this code.\n    \"\"\"\n    self.used = True\n    self.used_at = datetime.now(tz=UTC)\n    self.last_used_at = datetime.now(tz=UTC)\n\ndef __str__(self) -> str:\n    status = 'used' if self.used else 'available'\n    return f'BackupCode(name={self.name}, user={self.user_email}, status={status})'",
                "storage_metadata": {
                    "table_name": "BackupCode",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
        ),
        # Create EmailMFADevice model
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="EmailMFADevice",
            new_schema={
                "title": "EmailMFADevice",
                "type": "MFADevice",
                "required": ["user_email", "name", "email"],
                "properties": {
                    "user_email": {"type": "string", "title": "User Email"},
                    "device_type": {"type": "string", "title": "Device Type", "default": None},
                    "name": {"type": "string", "title": "Device Name"},
                    "is_active": {"type": "boolean", "title": "Is Active", "default": True},
                    "confirmed": {"type": "boolean", "title": "Confirmed", "default": False},
                    "created_at": {"type": "datetime", "title": "Created At"},
                    "last_used_at": {"type": "datetime", "title": "Last Used At", "default": None},
                    "email": {"type": "string", "title": "Email Address"},
                    "code": {"type": "string", "title": "Current Code", "default": None},
                    "code_expires_at": {"type": "datetime", "title": "Code Expiration", "default": None},
                },
                "custom_code": "from typing import Any\nfrom amsdal.contrib.auth.utils.mfa import DeviceType\n\n\ndef post_init(self, *, is_new_object: bool, kwargs: dict[str, Any]) -> None:\n    \"\"\"\n    Post-initializes an email MFA device by setting the device type.\n\n    Args:\n        is_new_object (bool): Indicates if the object is new.\n        kwargs (dict[str, Any]): The keyword arguments containing device details.\n    \"\"\"\n    super().post_init(is_new_object=is_new_object, kwargs=kwargs)\n    self.device_type = DeviceType.EMAIL\n\n    # Email devices are confirmed by default (verification happens through email ownership)\n    if is_new_object:\n        self.confirmed = True\n\ndef generate_and_send_code(self) -> str:\n    \"\"\"\n    Generate a new MFA code and send it via email.\n\n    This method generates a random numeric code, sets its expiration time,\n    and sends it to the configured email address.\n\n    Returns:\n        str: The generated code (for testing purposes).\n\n    Note:\n        In production, you should implement actual email sending logic here\n        or call an email service.\n    \"\"\"\n    from amsdal.contrib.auth.utils.mfa import generate_email_mfa_code\n    from amsdal.contrib.auth.utils.mfa import get_email_code_expiration\n\n    # Generate new code\n    self.code = generate_email_mfa_code()\n    self.code_expires_at = get_email_code_expiration()\n\n    return self.code\n\ndef verify_code(self, code: str) -> bool:\n    \"\"\"\n    Verify an email MFA code.\n\n    Args:\n        code (str): The code to verify.\n\n    Returns:\n        bool: True if the code is valid and not expired, False otherwise.\n    \"\"\"\n    from amsdal.contrib.auth.utils.mfa import is_email_code_valid\n\n    # Check if code matches\n    if not self.code or self.code != code:\n        return False\n\n    # Check if code is expired\n    if not self.code_expires_at or not is_email_code_valid(self.code_expires_at):\n        return False\n\n    return True\n\ndef clear_code(self) -> None:\n    \"\"\"\n    Clear the current code after successful use or expiration.\n    \"\"\"\n    self.code = None\n    self.code_expires_at = None\n\ndef __str__(self) -> str:\n    return f'EmailMFADevice(name={self.name}, email={self.email}, user={self.user_email})'",
                "storage_metadata": {
                    "table_name": "EmailMFADevice",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
        ),
        # Create SMSDevice model
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="SMSDevice",
            new_schema={
                "title": "SMSDevice",
                "type": "MFADevice",
                "required": ["user_email", "name", "phone_number"],
                "properties": {
                    "user_email": {"type": "string", "title": "User Email"},
                    "device_type": {"type": "string", "title": "Device Type", "default": None},
                    "name": {"type": "string", "title": "Device Name"},
                    "is_active": {"type": "boolean", "title": "Is Active", "default": True},
                    "confirmed": {"type": "boolean", "title": "Confirmed", "default": False},
                    "created_at": {"type": "datetime", "title": "Created At"},
                    "last_used_at": {"type": "datetime", "title": "Last Used At", "default": None},
                    "phone_number": {"type": "string", "title": "Phone Number"},
                    "code": {"type": "string", "title": "Current Code", "default": None},
                    "code_expires_at": {"type": "datetime", "title": "Code Expiration", "default": None},
                },
                "custom_code": "from typing import Any\nfrom amsdal.contrib.auth.utils.mfa import DeviceType\n\n\ndef post_init(self, *, is_new_object: bool, kwargs: dict[str, Any]) -> None:\n    \"\"\"\n    Post-initializes an SMS MFA device by setting the device type.\n\n    Args:\n        is_new_object (bool): Indicates if the object is new.\n        kwargs (dict[str, Any]): The keyword arguments containing device details.\n    \"\"\"\n    super().post_init(is_new_object=is_new_object, kwargs=kwargs)\n    self.device_type = DeviceType.SMS\n\ndef generate_and_send_code(self) -> str:\n    \"\"\"\n    Generate a new MFA code and send it via SMS.\n\n    This method generates a random numeric code, sets its expiration time,\n    and sends it to the configured phone number.\n\n    Returns:\n        str: The generated code (for testing purposes).\n\n    Raises:\n        NotImplementedError: This feature requires SMS service integration.\n\n    Note:\n        Full implementation requires integration with an SMS provider.\n        Example providers: Twilio, AWS SNS, MessageBird, etc.\n    \"\"\"\n    from amsdal.contrib.auth.utils.mfa import generate_email_mfa_code\n    from amsdal.contrib.auth.utils.mfa import get_email_code_expiration\n\n    # Generate new code\n    self.code = generate_email_mfa_code()\n    self.code_expires_at = get_email_code_expiration()\n\n    msg = 'SMS MFA is not yet implemented. Please integrate with an SMS service provider (e.g., Twilio, AWS SNS).'\n    raise NotImplementedError(msg)\n\ndef verify_code(self, code: str) -> bool:\n    \"\"\"\n    Verify an SMS MFA code.\n\n    Args:\n        code (str): The code to verify.\n\n    Returns:\n        bool: True if the code is valid and not expired, False otherwise.\n    \"\"\"\n    from amsdal.contrib.auth.utils.mfa import is_email_code_valid\n\n    # Check if code matches\n    if not self.code or self.code != code:\n        return False\n\n    # Check if code is expired\n    if not self.code_expires_at or not is_email_code_valid(self.code_expires_at):\n        return False\n\n    return True\n\ndef clear_code(self) -> None:\n    \"\"\"\n    Clear the current code after successful use or expiration.\n    \"\"\"\n    self.code = None\n    self.code_expires_at = None\n\ndef __str__(self) -> str:\n    return f'SMSDevice(name={self.name}, phone={self.phone_number}, user={self.user_email})'",
                "storage_metadata": {
                    "table_name": "SMSDevice",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
        ),
    ]
