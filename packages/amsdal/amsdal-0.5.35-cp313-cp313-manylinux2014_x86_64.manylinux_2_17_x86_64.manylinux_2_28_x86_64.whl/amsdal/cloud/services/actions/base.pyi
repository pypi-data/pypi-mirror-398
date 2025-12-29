import abc
from _typeshed import Incomplete
from abc import ABC, abstractmethod
from amsdal.cloud.client import AuthClientService as AuthClientService
from amsdal.cloud.constants import ENCRYPT_PUBLIC_KEY as ENCRYPT_PUBLIC_KEY
from amsdal.cloud.enums import ResponseStatus as ResponseStatus
from amsdal.cloud.models.base import ResponseBaseModel as ResponseBaseModel
from amsdal.configs.main import settings as settings
from amsdal.errors import AmsdalCloudAlreadyDeployedError as AmsdalCloudAlreadyDeployedError, AmsdalCloudError as AmsdalCloudError
from enum import Enum
from typing import Any

class AuthErrorCodes(str, Enum):
    """
    Enum for authentication error codes.

    Attributes:
        INVALID_EMAIL (str): Error code for invalid email.
        MISSING_CREDENTIALS (str): Error code for missing credentials.
        INVALID_CREDENTIALS (str): Error code for invalid credentials.
        INVALID_APPLICATION_UUID (str): Error code for invalid application UUID.
        CLIENT_IS_INACTIVE (str): Error code for inactive client.
        CLIENT_ALREADY_EXISTS (str): Error code for client already exists.
        DEPLOY_FAILED (str): Error code for deploy failed.
        DEPLOY_ALREADY_EXISTS (str): Error code for deploy already exists.
        DEPLOY_NOT_IN_DEPLOYED_STATUS (str): Error code for deploy not in deployed status.
        DESTROY_FAILED (str): Error code for destroy failed.
        DEPLOY_NOT_FOUND (str): Error code for deploy not found.
        INVALID_DEPENDENCY (str): Error code for invalid dependency.
        EXPOSE_DB_ACCESS_FAILED (str): Error code for expose DB access failed.
        APPLICATION_ALREADY_EXISTS (str): Error code for application already exists.
        MULTIPLE_APPLICATIONS_FOUND (str): Error code for multiple applications found.
        MAXIMUM_APPLICATIONS_REACHED (str): Error code for maximum applications reached.
        INTERNAL_SECRET (str): Error code for internal secret.
        BA_DOES_NOT_EXIST (str): Error code for basic authentication does not exist.
        INVALID_IP_ADDRESS (str): Error code for invalid IP address.
        MONITORING_NOT_FOUND (str): Error code for monitoring not found.
        INVALID_ENVIRONMENT_NAME (str): Error code for invalid environment name.
        SAME_ENVIRONMENT_NAME (str): Error code for same environment name.
        ENVIRONMENT_NOT_FOUND (str): Error code for environment not found.
        ENVIRONMENT_NOT_DEPLOYED (str): Error code for environment not deployed.
        MAXIMUM_DEPLOYS_PER_APPLICATION_REACHED (str): Error code for maximum deploys per application reached.
        CANNOT_DELETE_ENVIRONMENT (str): Error code for cannot delete environment.
    """
    INVALID_EMAIL = 'invalid_email'
    MISSING_CREDENTIALS = 'missing_credentials'
    INVALID_CREDENTIALS = 'invalid_credentials'
    INVALID_APPLICATION_UUID = 'invalid_application_uuid'
    CLIENT_IS_INACTIVE = 'client_is_inactive'
    CLIENT_ALREADY_EXISTS = 'client_already_exists'
    DEPLOY_FAILED = 'deploy_failed'
    DEPLOY_ALREADY_EXISTS = 'deploy_already_exists'
    DEPLOY_NOT_IN_DEPLOYED_STATUS = 'deploy_not_in_deployed_status'
    DESTROY_FAILED = 'destroy_failed'
    DEPLOY_NOT_FOUND = 'deploy_not_found'
    INVALID_DEPENDENCY = 'invalid_dependency'
    EXPOSE_DB_ACCESS_FAILED = 'expose_access_failed'
    APPLICATION_ALREADY_EXISTS = 'application_already_exists'
    MULTIPLE_APPLICATIONS_FOUND = 'multiple_applications_found'
    MAXIMUM_APPLICATIONS_REACHED = 'maximum_applications_reached'
    INTERNAL_SECRET = 'internal_secret'
    BA_DOES_NOT_EXIST = 'ba_does_not_exist'
    INVALID_IP_ADDRESS = 'invalid_ip_address'
    MONITORING_NOT_FOUND = 'monitoring_not_found'
    INVALID_ENVIRONMENT_NAME = 'invalid_environment_name'
    SAME_ENVIRONMENT_NAME = 'same_environment_name'
    ENVIRONMENT_NOT_FOUND = 'environment_not_found'
    ENVIRONMENT_NOT_DEPLOYED = 'environment_not_deployed'
    MAXIMUM_DEPLOYS_PER_APPLICATION_REACHED = 'maximum_deploys_per_application_reached'
    CANNOT_DELETE_ENVIRONMENT = 'cannot_delete_environment'
    INVALID_CONNECTION_NAME = 'invalid_connection_name'
    INVALID_BACKEND = 'invalid_backend'
    EXTERNAL_CONNECTION_ALREADY_EXISTS = 'external_connection_already_exists'
    EXTERNAL_CONNECTION_NOT_FOUND = 'external_connection_not_found'

FRIENDLY_ERROR_MESSAGES: Incomplete

class CloudActionBase(ABC, metaclass=abc.ABCMeta):
    """
    Abstract base class for cloud actions.
    """
    auth_client: Incomplete
    def __init__(self) -> None: ...
    @abstractmethod
    def action(self, *args: Any, **kwargs: Any) -> Any:
        """
        Abstract method to be implemented by subclasses to execute the action.

        Args:
            *args (Any): Variable length argument list.
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            Any: The result of the action.
        """
    def _credentials_data(self) -> bytes: ...
    @staticmethod
    def _input(msg: str) -> str: ...
    @staticmethod
    def _print(msg: str) -> None: ...
    def execute_transaction(self, transaction_name: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Executes a transaction with the given name and data.

        Args:
            transaction_name (str): The name of the transaction to execute.
            data (dict[str, Any]): The data to be sent with the transaction.

        Returns:
            dict[str, Any]: The response data from the transaction.

        Raises:
            AmsdalCloudError: If the transaction cannot be executed or if the transaction fails.
            AmsdalCloudAlreadyDeployedError: If the deploy already exists.
        """
    def process_errors(self, response: ResponseBaseModel) -> None:
        """
        Processes errors in the response and raises appropriate exceptions.

        Args:
            response (ResponseBaseModel): The response model containing the status and errors.

        Raises:
            AmsdalCloudAlreadyDeployedError: If the deploy already exists.
            AmsdalCloudError: If there are other errors in the response or if the transaction failed.
        """
