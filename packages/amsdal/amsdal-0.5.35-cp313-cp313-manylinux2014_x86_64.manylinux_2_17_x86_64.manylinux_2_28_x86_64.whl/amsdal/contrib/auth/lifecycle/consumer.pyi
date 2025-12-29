from _typeshed import Incomplete
from amsdal.contrib.auth.errors import AuthenticationError as AuthenticationError
from amsdal_data.transactions.decorators import async_transaction, transaction
from amsdal_models.classes.model import Model
from amsdal_utils.lifecycle.consumer import LifecycleConsumer
from typing import Any

logger: Incomplete

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
    @async_transaction
    async def on_event_async(self) -> None:
        """
        Checks for the existence of a super user and creates one if necessary.

        This method ensures that a super user exists by checking the email and password
        in the authentication settings. If the super user does not exist, it creates one
        with the necessary permissions.
        """

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

class CheckPermissionConsumer(LifecycleConsumer):
    """
    Checks and manages permissions for a given user and object.

    This consumer prepopulates default permissions, checks class-level permissions,
    and object-level permissions for a given user and object.
    """
    def _prepopulate_default_permissions(self, object_class: type[Model], permissions_info: Any) -> None: ...
    async def _async_prepopulate_default_permissions(self, object_class: type[Model], permissions_info: Any) -> None: ...
    def _check_class_permissions(self, object_class: type[Model], user: Any, permissions_info: Any) -> None: ...
    async def _async_check_class_permissions(self, object_class: type[Model], user: Any, permissions_info: Any) -> None: ...
    def _check_object_permissions(self, obj: Model, user: Any, permissions_info: Any) -> None: ...
    def on_event(self, object_class: type[Model], user: Any, access_types: list[Any], permissions_info: Any, obj: Model | None = None) -> None:
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
    async def on_event_async(self, object_class: type[Model], user: Any, access_types: list[Any], permissions_info: Any, obj: Model | None = None) -> None:
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
