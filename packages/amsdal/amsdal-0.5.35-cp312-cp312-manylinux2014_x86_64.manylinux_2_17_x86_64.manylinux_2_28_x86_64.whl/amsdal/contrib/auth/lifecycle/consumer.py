import logging
from typing import Any

import jwt
from amsdal_data.transactions.decorators import async_transaction
from amsdal_data.transactions.decorators import transaction
from amsdal_models.classes.helpers.reference_loader import ReferenceLoader
from amsdal_models.classes.model import Model
from amsdal_utils.lifecycle.consumer import LifecycleConsumer
from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.models.enums import Versions

from amsdal.contrib.auth.errors import AuthenticationError

logger = logging.getLogger(__name__)


class CheckAndCreateSuperUserConsumer(LifecycleConsumer):
    """
    Ensures the existence of a super user in the system.

    This consumer checks if a super user exists based on the provided email and password
    in the authentication settings. If the super user does not exist, it creates one.
    """

    @transaction
    def on_event(self) -> None:
        """
        Checks for the existence of a super user and creates one if necessary.

        This method ensures that a super user exists by checking the email and password
        in the authentication settings. If the super user does not exist, it creates one
        with the necessary permissions.
        """
        from amsdal.contrib.auth.models.permission import Permission
        from amsdal.contrib.auth.models.user import User
        from amsdal.contrib.auth.settings import auth_settings

        logger.info('Ensure super user exists')

        if not (auth_settings.ADMIN_USER_EMAIL and auth_settings.ADMIN_USER_PASSWORD):
            logger.info('Email / password missing for super user - skipping')
            return

        user = (
            User.objects.filter(email=auth_settings.ADMIN_USER_EMAIL, _address__object_version=Versions.LATEST)
            .get_or_none()
            .execute()
        )
        if user is not None:
            logger.info('Super user already exists - skipping')
            return

        logger.info("Super user doesn't exist - creating now")

        access_all_permission = (
            Permission.objects.filter(
                model='*',
                action='*',
                _address__object_version=Versions.LATEST,
            )
            .get()
            .execute()
        )

        instance = User(  # type: ignore[call-arg]
            email=auth_settings.ADMIN_USER_EMAIL,
            password=auth_settings.ADMIN_USER_PASSWORD.encode(),
            permissions=[access_all_permission],
        )
        instance.save(force_insert=True)
        logger.info('Super user created successfully')

    @async_transaction
    async def on_event_async(self) -> None:  # type: ignore[override]
        """
        Checks for the existence of a super user and creates one if necessary.

        This method ensures that a super user exists by checking the email and password
        in the authentication settings. If the super user does not exist, it creates one
        with the necessary permissions.
        """
        from amsdal.contrib.auth.models.permission import Permission  # type: ignore[import-not-found]
        from amsdal.contrib.auth.models.user import User  # type: ignore[import-not-found]
        from amsdal.contrib.auth.settings import auth_settings

        logger.info('Ensure super user exists')

        if not (auth_settings.ADMIN_USER_EMAIL and auth_settings.ADMIN_USER_PASSWORD):
            logger.info('Email / password missing for super user - skipping')
            return

        user = (
            await User.objects.filter(email=auth_settings.ADMIN_USER_EMAIL, _address__object_version=Versions.LATEST)
            .get_or_none()
            .aexecute()
        )
        if user is not None:
            logger.info('Super user already exists - skipping')
            return

        logger.info("Super user doesn't exist - creating now")

        access_all_permission = (
            await Permission.objects.filter(
                model='*',
                action='*',
                _address__object_version=Versions.LATEST,
            )
            .get()
            .aexecute()
        )

        instance = User(  # type: ignore[call-arg]
            email=auth_settings.ADMIN_USER_EMAIL,
            password=auth_settings.ADMIN_USER_PASSWORD.encode(),
            permissions=[access_all_permission],
        )
        await instance.asave(force_insert=True)  # type: ignore[misc]
        logger.info('Super user created successfully')


class AuthenticateUserConsumer(LifecycleConsumer):
    """
    Authenticates a user based on a provided JWT token.

    This consumer decodes the JWT token from the authorization header and retrieves
    the corresponding user from the database. If the token is invalid or expired,
    it raises an `AuthenticationError`.
    """

    def on_event(self, auth_header: str, authentication_info: Any) -> None:
        """
        Authenticates the user using the provided JWT token.

        This method decodes the JWT token from the authorization header and retrieves
        the corresponding user from the database. If the token is invalid or expired,
        it raises an `AuthenticationError`.

        Args:
            auth_header (str): The JWT token from the authorization header.
            authentication_info (Any): The authentication information object to update with the user.
        """
        from amsdal.contrib.auth.models.user import User  # type: ignore[import-not-found]
        from amsdal.contrib.auth.settings import auth_settings

        authentication_info.user = None
        email: str | None

        try:
            jwt_payload = jwt.decode(
                auth_header,
                auth_settings.AUTH_JWT_KEY,  # type: ignore[arg-type]
                algorithms=['HS256'],
            )
            email = jwt_payload['email']
        except jwt.ExpiredSignatureError as exc:
            logger.error('Auth token expired. Defaulting to anonymous user.')

            msg = 'Auth token has expired.'
            raise AuthenticationError(msg) from exc
        except Exception as exc:
            logger.error('Auth token decode failure. Defaulting to anonymous user.')

            msg = 'Failed to decode auth token.'
            raise AuthenticationError(msg) from exc

        user = User.objects.filter(email=email, _address__object_version=Versions.LATEST).get_or_none().execute()

        authentication_info.user = user

    async def on_event_async(self, auth_header: str, authentication_info: Any) -> None:
        """
        Authenticates the user using the provided JWT token.

        This method decodes the JWT token from the authorization header and retrieves
        the corresponding user from the database. If the token is invalid or expired,
        it raises an `AuthenticationError`.

        Args:
            auth_header (str): The JWT token from the authorization header.
            authentication_info (Any): The authentication information object to update with the user.
        """
        from amsdal.contrib.auth.models.user import User  # type: ignore[import-not-found]
        from amsdal.contrib.auth.settings import auth_settings

        authentication_info.user = None
        email: str | None

        try:
            jwt_payload = jwt.decode(
                auth_header,
                auth_settings.AUTH_JWT_KEY,  # type: ignore[arg-type]
                algorithms=['HS256'],
            )
            email = jwt_payload['email']
        except jwt.ExpiredSignatureError as exc:
            logger.error('Auth token expired. Defaulting to anonymous user.')

            msg = 'Auth token has expired.'
            raise AuthenticationError(msg) from exc
        except Exception as exc:
            logger.error('Auth token decode failure. Defaulting to anonymous user.')

            msg = 'Failed to decode auth token.'
            raise AuthenticationError(msg) from exc

        user = await User.objects.filter(email=email, _address__object_version=Versions.LATEST).get_or_none().aexecute()

        authentication_info.user = user


class CheckPermissionConsumer(LifecycleConsumer):
    """
    Checks and manages permissions for a given user and object.

    This consumer prepopulates default permissions, checks class-level permissions,
    and object-level permissions for a given user and object.
    """

    def _prepopulate_default_permissions(self, object_class: type[Model], permissions_info: Any) -> None:
        from amsdal.contrib.auth.models.permission import Permission
        from amsdal.contrib.auth.settings import auth_settings

        permissions_info.has_read_permission = not auth_settings.REQUIRE_DEFAULT_AUTHORIZATION
        permissions_info.has_create_permission = (
            (not auth_settings.REQUIRE_DEFAULT_AUTHORIZATION) if object_class.__name__ != 'LoginSession' else True
        )
        permissions_info.has_update_permission = not auth_settings.REQUIRE_DEFAULT_AUTHORIZATION
        permissions_info.has_delete_permission = not auth_settings.REQUIRE_DEFAULT_AUTHORIZATION

        required_permissions = Permission.objects.filter(
            model=object_class.__name__,
            _address__object_version=Versions.LATEST,
        ).execute()

        for required_permission in required_permissions:
            if required_permission.action == 'read':
                permissions_info.has_read_permission = False
            elif required_permission.action == 'create':
                permissions_info.has_create_permission = False
            elif required_permission.action == 'update':
                permissions_info.has_update_permission = False
            elif required_permission.action == 'delete':
                permissions_info.has_delete_permission = False

    async def _async_prepopulate_default_permissions(self, object_class: type[Model], permissions_info: Any) -> None:
        from amsdal.contrib.auth.models.permission import Permission  # type: ignore[import-not-found]
        from amsdal.contrib.auth.settings import auth_settings

        permissions_info.has_read_permission = not auth_settings.REQUIRE_DEFAULT_AUTHORIZATION
        permissions_info.has_create_permission = (
            (not auth_settings.REQUIRE_DEFAULT_AUTHORIZATION) if object_class.__name__ != 'LoginSession' else True
        )
        permissions_info.has_update_permission = not auth_settings.REQUIRE_DEFAULT_AUTHORIZATION
        permissions_info.has_delete_permission = not auth_settings.REQUIRE_DEFAULT_AUTHORIZATION

        required_permissions = await Permission.objects.filter(
            model=object_class.__name__,
            _address__object_version=Versions.LATEST,
        ).aexecute()

        for required_permission in required_permissions:
            if required_permission.action == 'read':
                permissions_info.has_read_permission = False
            elif required_permission.action == 'create':
                permissions_info.has_create_permission = False
            elif required_permission.action == 'update':
                permissions_info.has_update_permission = False
            elif required_permission.action == 'delete':
                permissions_info.has_delete_permission = False

    def _check_class_permissions(self, object_class: type[Model], user: Any, permissions_info: Any) -> None:
        if hasattr(object_class, 'has_permission'):
            for action in ['read', 'create', 'update', 'delete']:
                setattr(permissions_info, f'has_{action}_permission', object_class.has_permission(user, action))

        if not user or not getattr(user, 'permissions', None):
            return

        user_permissions = [
            ReferenceLoader(p).load_reference() if isinstance(p, Reference) else p for p in user.permissions
        ]

        for user_permission in user_permissions:
            if user_permission.model not in [object_class.__name__, '*']:
                continue

            if user_permission.action == 'read':
                permissions_info.has_read_permission = True
            elif user_permission.action == 'create':
                permissions_info.has_create_permission = True
            elif user_permission.action == 'update':
                permissions_info.has_update_permission = True
            elif user_permission.action == 'delete':
                permissions_info.has_delete_permission = True
            elif user_permission.action == '*':
                permissions_info.has_read_permission = True
                permissions_info.has_create_permission = True
                permissions_info.has_update_permission = True
                permissions_info.has_delete_permission = True

    async def _async_check_class_permissions(self, object_class: type[Model], user: Any, permissions_info: Any) -> None:
        if hasattr(object_class, 'has_permission'):
            for action in ['read', 'create', 'update', 'delete']:
                setattr(permissions_info, f'has_{action}_permission', object_class.has_permission(user, action))

        if not user or not getattr(user, 'permissions', None):
            return

        user_permissions = [
            await ReferenceLoader(p).aload_reference() if isinstance(p, Reference) else p for p in user.permissions
        ]

        for user_permission in user_permissions:
            if user_permission.model not in [object_class.__name__, '*']:
                continue

            if user_permission.action == 'read':
                permissions_info.has_read_permission = True
            elif user_permission.action == 'create':
                permissions_info.has_create_permission = True
            elif user_permission.action == 'update':
                permissions_info.has_update_permission = True
            elif user_permission.action == 'delete':
                permissions_info.has_delete_permission = True
            elif user_permission.action == '*':
                permissions_info.has_read_permission = True
                permissions_info.has_create_permission = True
                permissions_info.has_update_permission = True
                permissions_info.has_delete_permission = True

    def _check_object_permissions(self, obj: Model, user: Any, permissions_info: Any) -> None:
        if hasattr(obj, 'has_object_permission'):
            for action in ['read', 'update', 'delete']:
                setattr(
                    permissions_info,
                    f'has_{action}_permission',
                    getattr(permissions_info, f'has_{action}_permission') and obj.has_object_permission(user, action),
                )

    def on_event(
        self,
        object_class: type[Model],
        user: Any,
        access_types: list[Any],  # noqa: ARG002
        permissions_info: Any,
        obj: Model | None = None,
    ) -> None:
        """
        Main method to check permissions for a given user and object.

        This method prepopulates default permissions, checks class-level permissions,
        and object-level permissions for the given user and object.

        Args:
            object_class (type[Model]): The class of the object to check permissions for.
            user (Any): The user to check permissions for.
            access_types (list[Any]): The list of access types to check.
            permissions_info (Any): The permissions information object to update.
            obj (Model | None): The object to check permissions for, if any.
        """
        self._prepopulate_default_permissions(object_class, permissions_info)
        self._check_class_permissions(object_class, user, permissions_info)

        if obj:
            self._check_object_permissions(obj, user, permissions_info)

    async def on_event_async(
        self,
        object_class: type[Model],
        user: Any,
        access_types: list[Any],  # noqa: ARG002
        permissions_info: Any,
        obj: Model | None = None,
    ) -> None:
        """
        Main method to check permissions for a given user and object.

        This method prepopulates default permissions, checks class-level permissions,
        and object-level permissions for the given user and object.

        Args:
            object_class (type[Model]): The class of the object to check permissions for.
            user (Any): The user to check permissions for.
            access_types (list[Any]): The list of access types to check.
            permissions_info (Any): The permissions information object to update.
            obj (Model | None): The object to check permissions for, if any.
        """
        await self._async_prepopulate_default_permissions(object_class, permissions_info)
        await self._async_check_class_permissions(object_class, user, permissions_info)

        if obj:
            self._check_object_permissions(obj, user, permissions_info)
