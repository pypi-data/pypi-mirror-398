from amsdal.cloud.models.base import AddBasicAuthResponse as AddBasicAuthResponse, AddExternalConnectionResponse as AddExternalConnectionResponse, CreateEnvResponse as CreateEnvResponse, GetMonitoringInfoResponse as GetMonitoringInfoResponse, ListDependenciesDetails as ListDependenciesDetails, ListDeployResponse as ListDeployResponse, ListEnvsResponse as ListEnvsResponse, ListExternalConnectionsResponse as ListExternalConnectionsResponse, ListSecretsDetails as ListSecretsDetails, RemoveExternalConnectionResponse as RemoveExternalConnectionResponse, UpdateDeployStatusResponse as UpdateDeployStatusResponse, UpdateExternalConnectionResponse as UpdateExternalConnectionResponse
from amsdal.cloud.services.actions.add_allowlist_ip import AddAllowlistIPAction as AddAllowlistIPAction
from amsdal.cloud.services.actions.add_basic_auth import AddBasicAuthAction as AddBasicAuthAction
from amsdal.cloud.services.actions.add_dependency import AddDepenencyAction as AddDepenencyAction
from amsdal.cloud.services.actions.add_external_connection import AddExternalConnectionAction as AddExternalConnectionAction
from amsdal.cloud.services.actions.add_secret import AddSecretAction as AddSecretAction
from amsdal.cloud.services.actions.create_deploy import CreateDeployAction as CreateDeployAction
from amsdal.cloud.services.actions.create_env import CreateEnvAction as CreateEnvAction
from amsdal.cloud.services.actions.delete_allowlist_ip import DeleteAllowlistIPAction as DeleteAllowlistIPAction
from amsdal.cloud.services.actions.delete_basic_auth import DeleteBasicAuthAction as DeleteBasicAuthAction
from amsdal.cloud.services.actions.delete_dependency import DeleteDepenencyAction as DeleteDepenencyAction
from amsdal.cloud.services.actions.delete_env import DeleteEnvAction as DeleteEnvAction
from amsdal.cloud.services.actions.delete_secret import DeleteSecretAction as DeleteSecretAction
from amsdal.cloud.services.actions.destroy_deploy import DestroyDeployAction as DestroyDeployAction
from amsdal.cloud.services.actions.expose_db import ExposeDBAction as ExposeDBAction
from amsdal.cloud.services.actions.get_basic_auth_credentials import GetBasicAuthCredentialsAction as GetBasicAuthCredentialsAction
from amsdal.cloud.services.actions.get_monitoring_info import GetMonitoringInfoAction as GetMonitoringInfoAction
from amsdal.cloud.services.actions.list_dependencies import ListDependenciesAction as ListDependenciesAction
from amsdal.cloud.services.actions.list_deploys import ListDeploysAction as ListDeploysAction
from amsdal.cloud.services.actions.list_envs import ListEnvsAction as ListEnvsAction
from amsdal.cloud.services.actions.list_external_connections import ListExternalConnectionsAction as ListExternalConnectionsAction
from amsdal.cloud.services.actions.list_secrets import ListSecretsAction as ListSecretsAction
from amsdal.cloud.services.actions.remove_external_connection import RemoveExternalConnectionAction as RemoveExternalConnectionAction
from amsdal.cloud.services.actions.update_deploy import UpdateDeployAction as UpdateDeployAction
from amsdal.cloud.services.actions.update_external_connection import UpdateExternalConnectionAction as UpdateExternalConnectionAction
from typing import Any

class CloudActionsManager:
    """
    Manager class to handle various cloud actions.

    This class provides methods to perform actions such as creating, listing, and deleting deployments,
        environments, secrets, and dependencies.
    """
    def create_deploy(self, deploy_type: str, lakehouse_type: str, env_name: str, from_env: str | None = None, application_uuid: str | None = None, application_name: str | None = None, *, no_input: bool = False) -> bool:
        """
        Creates a new deployment with the given parameters.

        Args:
            deploy_type (str): The type of deployment.
            lakehouse_type (str): The type of lakehouse.
            env_name (str): The name of the environment.
            from_env (str | None, optional): The source environment. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.
            no_input (bool, optional): Whether to disable input prompts. Defaults to False.

        Returns:
            bool: True if the deployment was created successfully, False otherwise.
        """
    def list_deploys(self, *, list_all: bool = True) -> ListDeployResponse:
        """
        Lists deployments with the given parameters.

        Args:
            list_all (bool, optional): Whether to list all deployments. Defaults to True.

        Returns:
            ListDeployResponse: The response containing the list of deployments.
        """
    def destroy_deploy(self, deployment_id: str) -> bool:
        """
        Destroys a deployment with the given deployment ID.

        Args:
            deployment_id (str): The ID of the deployment to be destroyed.

        Returns:
            bool: True if the deployment was destroyed successfully, False otherwise.
        """
    def update_deploy(self, deployment_id: str) -> UpdateDeployStatusResponse:
        """
        Updates the status of a deployment with the given deployment ID.

        Args:
            deployment_id (str): The ID of the deployment to be updated.

        Returns:
            UpdateDeployStatusResponse: The response containing the updated deployment status.
        """
    def add_secret(self, secret_name: str, secret_value: str, env_name: str, application_uuid: str | None = None, application_name: str | None = None) -> bool:
        """
        Adds a secret with the given parameters.

        Args:
            secret_name (str): The name of the secret.
            secret_value (str): The value of the secret.
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            bool: True if the secret was added successfully, False otherwise.
        """
    def list_secrets(self, env_name: str, application_uuid: str | None = None, application_name: str | None = None, *, with_values: bool = False) -> ListSecretsDetails:
        """
        Lists secrets with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.
            with_values (bool, optional): Whether to include secret values. Defaults to False.

        Returns:
            ListSecretsDetails: The response containing the list of secrets.
        """
    def delete_secret(self, secret_name: str, env_name: str, application_uuid: str | None = None, application_name: str | None = None) -> bool:
        """
        Deletes a secret with the given parameters.

        Args:
            secret_name (str): The name of the secret.
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            bool: True if the secret was deleted successfully, False otherwise.
        """
    def add_dependency(self, dependency_name: str, env_name: str, application_uuid: str | None = None, application_name: str | None = None) -> bool:
        """
        Adds a dependency with the given parameters.

        Args:
            dependency_name (str): The name of the dependency.
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            bool: True if the dependency was added successfully, False otherwise.
        """
    def delete_dependency(self, dependency_name: str, env_name: str, application_uuid: str | None = None, application_name: str | None = None) -> bool:
        """
        Deletes a dependency with the given parameters.

        Args:
            dependency_name (str): The name of the dependency.
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            bool: True if the dependency was deleted successfully, False otherwise.
        """
    def list_dependencies(self, env_name: str, application_uuid: str | None = None, application_name: str | None = None) -> ListDependenciesDetails:
        """
        Lists dependencies with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            ListDependenciesDetails: The response containing the list of dependencies.
        """
    def expose_db(self, env_name: str, application_uuid: str | None = None, application_name: str | None = None, ip_address: str | None = None) -> dict[str, Any]:
        """
        Exposes the database with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.
            ip_address (str | None, optional): The IP address to expose the database to. Defaults to None.

        Returns:
            dict[str, Any]: The response containing the database exposure details.
        """
    def get_monitoring_info(self, env_name: str, application_uuid: str | None = None, application_name: str | None = None) -> GetMonitoringInfoResponse:
        """
        Gets monitoring information with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            GetMonitoringInfoResponse: The response containing the monitoring information.
        """
    def add_allowlist_ip(self, env_name: str, ip_address: str | None = None, application_uuid: str | None = None, application_name: str | None = None) -> bool:
        """
        Adds an IP address to the allowlist with the given parameters.

        Args:
            env_name (str): The name of the environment.
            ip_address (str | None, optional): The IP address to be added to the allowlist. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            bool: True if the IP address was added to the allowlist successfully, False otherwise.
        """
    def delete_allowlist_ip(self, env_name: str, ip_address: str | None = None, application_uuid: str | None = None, application_name: str | None = None) -> bool:
        """
        Deletes an IP address from the allowlist with the given parameters.

        Args:
            env_name (str): The name of the environment.
            ip_address (str | None, optional): The IP address to be deleted from the allowlist. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            bool: True if the IP address was deleted from the allowlist successfully, False otherwise.
        """
    def add_basic_auth(self, env_name: str, username: str | None = None, password: str | None = None, application_uuid: str | None = None, application_name: str | None = None) -> AddBasicAuthResponse:
        """
        Adds basic authentication credentials with the given parameters.

        Args:
            env_name (str): The name of the environment.
            username (str | None, optional): The username for basic authentication. Defaults to None.
            password (str | None, optional): The password for basic authentication. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            AddBasicAuthResponse: The response containing the added basic authentication credentials.
        """
    def delete_basic_auth(self, env_name: str, application_uuid: str | None = None, application_name: str | None = None) -> bool:
        """
        Deletes basic authentication credentials with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            bool: True if the basic authentication credentials were deleted successfully, False otherwise.
        """
    def get_basic_auth_credentials(self, env_name: str, application_uuid: str | None = None, application_name: str | None = None) -> AddBasicAuthResponse:
        """
        Gets basic authentication credentials with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            AddBasicAuthResponse: The response containing the basic authentication credentials.
        """
    def list_envs(self, application_uuid: str | None = None, application_name: str | None = None) -> ListEnvsResponse:
        """
        Lists environments with the given parameters.

        Args:
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            ListEnvsResponse: The response containing the list of environments.
        """
    def create_env(self, env_name: str, application_name: str | None = None, application_uuid: str | None = None) -> CreateEnvResponse:
        """
        Creates an environment with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_name (str | None, optional): The name of the application. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.

        Returns:
            CreateEnvResponse: The response containing the created environment details.
        """
    def delete_env(self, env_name: str, application_name: str | None = None, application_uuid: str | None = None) -> CreateEnvResponse:
        """
        Deletes an environment with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_name (str | None, optional): The name of the application. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.

        Returns:
            CreateEnvResponse: The response containing the deleted environment details.
        """
    def add_external_connection(self, connection_name: str, backend: str, credentials: dict[str, str], env_name: str, application_uuid: str | None = None, application_name: str | None = None) -> AddExternalConnectionResponse:
        """
        Adds an external connection to an environment with the given parameters.

        Args:
            connection_name (str): The name of the connection.
            backend (str): The backend type (e.g., 'postgres', 'mysql', 'redis').
            credentials (dict[str, str]): Dictionary of connection credentials.
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            AddExternalConnectionResponse: The response containing the added connection details.
        """
    def list_external_connections(self, env_name: str, application_uuid: str | None = None, application_name: str | None = None) -> ListExternalConnectionsResponse:
        """
        Lists external connections for an environment with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            ListExternalConnectionsResponse: The response containing the list of external connections.
        """
    def update_external_connection(self, connection_name: str, env_name: str, backend: str | None = None, credentials: dict[str, Any] | None = None, application_uuid: str | None = None, application_name: str | None = None) -> UpdateExternalConnectionResponse:
        """
        Updates an external connection in an environment with the given parameters.

        Args:
            connection_name (str): The name of the connection to update.
            env_name (str): The name of the environment.
            backend (str | None, optional): New backend type. Defaults to None (keeps existing).
            credentials (dict[str, Any] | None, optional): New credentials dict. Defaults to None (keeps existing).
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            UpdateExternalConnectionResponse: The response containing the updated connection details.
        """
    def remove_external_connection(self, connection_name: str, env_name: str, application_uuid: str | None = None, application_name: str | None = None) -> RemoveExternalConnectionResponse:
        """
        Removes an external connection from an environment with the given parameters.

        Args:
            connection_name (str): The name of the connection to remove.
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            RemoveExternalConnectionResponse: The response containing the removed connection details.
        """
