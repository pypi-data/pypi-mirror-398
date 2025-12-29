from amsdal_models.migration import migrations
from amsdal_utils.models.enums import ModuleType


class Migration(migrations.Migration):
    operations: list[migrations.Operation] = [
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="LoginSession",
            new_schema={
                "title": "LoginSession",
                "required": ["email", "password"],
                "properties": {
                    "email": {"type": "string", "title": "Email"},
                    "password": {"type": "string", "title": "Password (hash)"},
                    "token": {"type": "string", "title": "Token"},
                },
                "custom_code": "from datetime import UTC\nfrom datetime import datetime\nfrom datetime import timedelta\nfrom typing import Any\n\nimport jwt\n\n\n@property\ndef display_name(self) -> str:\n    \"\"\"\n        Returns the display name of the user.\n\n        This method returns the email of the user as their display name.\n\n        Returns:\n            str: The email of the user.\n        \"\"\"\n    return self.email\n\nasync def apre_create(self) -> None:\n    import bcrypt\n\n    from amsdal.contrib.auth.errors import AuthenticationError\n    from amsdal.contrib.auth.models.user import User\n    user = await User.objects.filter(email=self.email).latest().first().aexecute()\n    if not user:\n        msg = 'User not found'\n        raise AuthenticationError(msg)\n    if not bcrypt.checkpw(self.password.encode(), user.password):\n        msg = 'Invalid password'\n        raise AuthenticationError(msg)\n    self.password = 'validated'\n\nasync def apre_update(self) -> None:\n    from amsdal.contrib.auth.errors import AuthenticationError\n    msg = 'Update not allowed'\n    raise AuthenticationError(msg)\n\ndef pre_create(self) -> None:\n    import bcrypt\n\n    from amsdal.contrib.auth.errors import AuthenticationError\n    from amsdal.contrib.auth.models.user import User\n    user = User.objects.filter(email=self.email).latest().first().execute()\n    if not user:\n        msg = 'User not found'\n        raise AuthenticationError(msg)\n    if not bcrypt.checkpw(self.password.encode(), user.password):\n        msg = 'Invalid password'\n        raise AuthenticationError(msg)\n    self.password = 'validated'\n\ndef pre_init(self, *, is_new_object: bool, kwargs: dict[str, Any]) -> None:\n    \"\"\"\n        Pre-initializes a user object by validating email and password, and generating a JWT token.\n\n        This method checks if the object is new and validates the provided email and password.\n        If the email and password are valid, it generates a JWT token and adds it to the kwargs.\n\n        Args:\n            is_new_object (bool): Indicates if the object is new.\n            kwargs (dict[str, Any]): The keyword arguments containing user details.\n\n        Raises:\n            AuthenticationError: If the email or password is invalid.\n        \"\"\"\n    if not is_new_object or '_metadata' in kwargs:\n        return\n    from amsdal.contrib.auth.errors import AuthenticationError\n    from amsdal.contrib.auth.settings import auth_settings\n    email = kwargs.get('email', None)\n    password = kwargs.get('password', None)\n    if not email:\n        msg = \"Email can't be empty\"\n        raise AuthenticationError(msg)\n    if not password:\n        msg = \"Password can't be empty\"\n        raise AuthenticationError(msg)\n    lowercased_email = email.lower()\n    if not auth_settings.AUTH_JWT_KEY:\n        msg = 'JWT key is not set'\n        raise AuthenticationError(msg)\n    expiration_time = datetime.now(tz=UTC) + timedelta(seconds=auth_settings.AUTH_TOKEN_EXPIRATION)\n    token = jwt.encode({'email': lowercased_email, 'exp': expiration_time}, key=auth_settings.AUTH_JWT_KEY, algorithm='HS256')\n    kwargs['token'] = token\n\ndef pre_update(self) -> None:\n    from amsdal.contrib.auth.errors import AuthenticationError\n    msg = 'Update not allowed'\n    raise AuthenticationError(msg)",
                "storage_metadata": {
                    "table_name": "LoginSession",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="Permission",
            new_schema={
                "title": "Permission",
                "required": ["model", "action"],
                "properties": {
                    "model": {"type": "string", "title": "Model"},
                    "action": {"type": "string", "title": "Action"},
                },
                "custom_code": '@property\ndef display_name(self) -> str:\n    """\n        Returns the display name of the user.\n\n        This method returns a formatted string combining the model and action of the user.\n\n        Returns:\n            str: The formatted display name in the format \'model:action\'.\n        """\n    return f\'{self.model}:{self.action}\'',
                "storage_metadata": {
                    "table_name": "Permission",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="User",
            new_schema={
                "title": "User",
                "required": ["email", "password"],
                "properties": {
                    "email": {"type": "string", "title": "Email"},
                    "password": {"type": "binary", "title": "Password (hash)"},
                    "permissions": {"type": "array", "items": {"type": "Permission"}, "title": "Permissions"},
                },
                "custom_code": "from typing import Any\n\nfrom amsdal.contrib.auth.models.permission import *\n\n\n@property\ndef display_name(self) -> str:\n    \"\"\"\n        Returns the display name of the user.\n\n        This method returns the email of the user as their display name.\n\n        Returns:\n            str: The email of the user.\n        \"\"\"\n    return self.email\n\nasync def apre_update(self) -> None:\n    import bcrypt\n    original_object = await self.arefetch_from_db()\n    password = self.password\n    if original_object.password and password is not None:\n        if isinstance(password, str):\n            password = password.encode('utf-8')\n        try:\n            if not bcrypt.checkpw(password, original_object.password):\n                self.password = password\n        except ValueError:\n            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())\n            self.password = hashed_password\n\ndef __repr__(self) -> str:\n    return str(self)\n\ndef __str__(self) -> str:\n    return f'User(email={self.email})'\n\ndef post_init(self, *, is_new_object: bool, kwargs: dict[str, Any]) -> None:\n    \"\"\"\n        Post-initializes a user object by validating email and password, and hashing the password.\n\n        This method checks if the email and password are provided and valid. If the object is new,\n        it hashes the password and sets the object ID to the lowercased email.\n\n        Args:\n            is_new_object (bool): Indicates if the object is new.\n            kwargs (dict[str, Any]): The keyword arguments containing user details.\n\n        Raises:\n            UserCreationError: If the email or password is invalid.\n        \"\"\"\n    import bcrypt\n\n    from amsdal.contrib.auth.errors import UserCreationError\n    email = kwargs.get('email', None)\n    password = kwargs.get('password', None)\n    if email is None or email == '':\n        msg = \"Email can't be empty\"\n        raise UserCreationError(msg)\n    if password is None or password == '':\n        msg = \"Password can't be empty\"\n        raise UserCreationError(msg)\n    kwargs['email'] = email.lower()\n    if is_new_object and '_metadata' not in kwargs:\n        if isinstance(password, str):\n            password = password.encode('utf-8')\n        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())\n        self.password = hashed_password\n        self._object_id = email.lower()\n\ndef pre_create(self) -> None:\n    \"\"\"\n        Pre-creates a user object.\n\n        This method is a placeholder for any pre-creation logic that needs to be executed\n        before a user object is created.\n        \"\"\"\n    pass\n\ndef pre_update(self) -> None:\n    import bcrypt\n    original_object = self.refetch_from_db()\n    password = self.password\n    if original_object.password and password is not None:\n        if isinstance(password, str):\n            password = password.encode('utf-8')\n        try:\n            if not bcrypt.checkpw(password, original_object.password):\n                self.password = password\n        except ValueError:\n            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())\n            self.password = hashed_password",
                "storage_metadata": {
                    "table_name": "User",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="UserPermission",
            new_schema={
                "title": "UserPermission",
                "required": ["user", "permission"],
                "properties": {
                    "user": {"type": "User", "title": "User"},
                    "permission": {"type": "Permission", "title": "Permission"},
                },
                "storage_metadata": {
                    "table_name": "UserPermission",
                    "db_fields": {"user": ["user_partition_key"], "permission": ["permission_partition_key"]},
                    "primary_key": ["user", "permission"],
                    "foreign_keys": {
                        "user": [{"user_partition_key": "string"}, "User", ["partition_key"]],
                        "permission": [{"permission_partition_key": "string"}, "Permission", ["partition_key"]],
                    },
                },
            },
        ),
    ]
