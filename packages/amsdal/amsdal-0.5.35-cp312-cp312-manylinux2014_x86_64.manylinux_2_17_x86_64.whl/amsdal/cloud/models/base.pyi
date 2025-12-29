from amsdal.cloud.enums import ResponseStatus as ResponseStatus
from pydantic import BaseModel
from typing import Any

class ResponseBaseModel(BaseModel):
    """
    Base model for responses.

    Attributes:
        status (ResponseStatus): The status of the response.
        errors (list[str] | None): A list of error messages, if any.
    """
    status: ResponseStatus
    errors: list[str] | None

class DeployResponse(BaseModel):
    """
    Model representing a deployment response.

    Attributes:
        status (str): The status of the deployment.
        client_id (str): The client ID associated with the deployment.
        deployment_id (str): The unique identifier for the deployment.
        created_at (float): The timestamp when the deployment was created.
        last_update_at (float): The timestamp of the last update to the deployment.
        environment_name (str | None): The name of the environment, if any.
        application_uuid (str | None): The UUID of the application, if any.
        application_name (str | None): The name of the application, if any.
        domain_url (str | None): The URL of the domain, if any.
    """
    status: str
    client_id: str
    deployment_id: str
    created_at: float
    last_update_at: float
    environment_name: str | None
    application_uuid: str | None
    application_name: str | None
    domain_url: str | None

class UpdateDeployStatusResponse(BaseModel):
    """
    Model representing an update to the deployment status.

    Attributes:
        status (str): The status of the deployment.
        deployment_id (str): The unique identifier for the deployment.
        created_at (float): The timestamp when the deployment was created.
        last_update_at (float): The timestamp of the last update to the deployment.
        updated (bool): Indicates whether the deployment status was updated.
    """
    status: str
    deployment_id: str
    created_at: float
    last_update_at: float
    updated: bool

class ListDeployResponse(BaseModel):
    """
    Model representing a list of deployment responses.

    Attributes:
        deployments (list[DeployResponse]): A list of deployment responses.
    """
    deployments: list[DeployResponse]

class DeployTransactionResponse(ResponseBaseModel):
    """
    Model representing a deployment transaction response.

    Attributes:
        details (DeployResponse | UpdateDeployStatusResponse | ListDeployResponse | None):
            The details of the deployment transaction response, which can be one of
            DeployResponse, UpdateDeployStatusResponse, ListDeployResponse, or None.
    """
    details: DeployResponse | UpdateDeployStatusResponse | ListDeployResponse | None

class ListSecretsDetails(BaseModel):
    """
    Model representing the details of listed secrets.

    Attributes:
        secrets (list[str]): A list of secret strings.
    """
    secrets: list[str]

class ListSecretsResponse(ResponseBaseModel):
    """
    Model representing a response containing the details of listed secrets.

    Attributes:
        details (ListSecretsDetails | None): The details of the listed secrets, if any.
    """
    details: ListSecretsDetails | None

class SignupReponseCredentials(BaseModel):
    """
    Model representing the credentials for a signup response.

    Attributes:
        amsdal_access_key_id (str): The access key ID for AMSDAL.
        amsdal_secret_access_key (str): The secret access key for AMSDAL.
    """
    amsdal_access_key_id: str
    amsdal_secret_access_key: str

class SignupResponse(ResponseBaseModel):
    """
    Model representing a signup response.

    Attributes:
        details (SignupReponseCredentials | None): The credentials for the signup response, if any.
    """
    details: SignupReponseCredentials | None

class CreateSessionDetails(BaseModel):
    """
    Model representing the details for creating a session.

    Attributes:
        token (str): The token for the session.
    """
    token: str

class CreateSessionResponse(ResponseBaseModel):
    """
    Model representing a response for creating a session.

    Attributes:
        details (CreateSessionDetails | None): The details for creating a session, if any.
    """
    details: CreateSessionDetails | None

class ListDependenciesDetails(BaseModel):
    """
    Model representing the details of listed dependencies.

    Attributes:
        dependencies (list[str]): A list of dependencies.
        all (list[str]): A list of all dependencies.
    """
    dependencies: list[str]
    all: list[str]

class ListApplicationDependenciesResponse(ResponseBaseModel):
    """
    Model representing a response containing the details of listed application dependencies.

    Attributes:
        details (ListDependenciesDetails | None): The details of the listed application dependencies, if any.
    """
    details: ListDependenciesDetails | None

class ExposeApplicationDBResponse(ResponseBaseModel):
    """
    Model representing a response for exposing an application database.

    Attributes:
        details (dict[str, Any] | None): The details of the exposed application database, if any.
    """
    details: dict[str, Any] | None

class MonitoringInfo(BaseModel):
    """
    Model representing monitoring information.

    Attributes:
        url (str): The URL for monitoring.
        username (str): The username for monitoring access.
        password (str): The password for monitoring access.
    """
    url: str
    username: str
    password: str

class GetMonitoringInfoResponse(ResponseBaseModel):
    """
    Model representing a response containing monitoring information.

    Attributes:
        details (MonitoringInfo | None): The monitoring information details, if any.
    """
    details: MonitoringInfo | None

class BasicAuthCredentials(BaseModel):
    """
    Model representing basic authentication credentials.

    Attributes:
        username (str): The username for basic authentication.
        password (str): The password for basic authentication.
    """
    username: str
    password: str

class AddBasicAuthResponse(ResponseBaseModel):
    """
    Model representing a response for adding basic authentication.

    Attributes:
        details (BasicAuthCredentials | None): The basic authentication credentials, if any.
    """
    details: BasicAuthCredentials | None

class ListEnvsDetails(BaseModel):
    """
    Model representing the details of listed environments.

    Attributes:
        application_uuid (str): The UUID of the application.
        application_name (str): The name of the application.
        environments (list[str]): A list of environment names.
    """
    application_uuid: str
    application_name: str
    environments: list[str]

class ListEnvsResponse(ResponseBaseModel):
    """
    Model representing a response containing the details of listed environments.

    Attributes:
        details (ListEnvsDetails | None): The details of the listed environments, if any.
    """
    details: ListEnvsDetails | None

class CreateEnvDetails(BaseModel):
    """
    Model representing the details for creating an environment.

    Attributes:
        environment_name (str): The name of the environment.
        application_uuid (str): The UUID of the application.
        application_name (str): The name of the application.
    """
    environment_name: str
    application_uuid: str
    application_name: str

class CreateEnvResponse(ResponseBaseModel):
    """
    Model representing a response for creating an environment.

    Attributes:
        details (CreateEnvDetails | None): The details for creating an environment, if any.
    """
    details: CreateEnvDetails | None

class ExternalConnectionDetails(BaseModel):
    """
    Model representing external connection details.

    Attributes:
        name (str): The name of the connection.
        backend (str): The backend type (e.g., 'postgres', 'mysql', 'redis').
        credentials (dict[str, str]): Dictionary of connection credentials.
    """
    name: str
    backend: str
    credentials: dict[str, str]

class AddExternalConnectionResponse(ResponseBaseModel):
    """
    Model representing a response for adding an external connection.

    Attributes:
        details (ExternalConnectionDetails | None): The external connection details, if any.
    """
    details: ExternalConnectionDetails | None

class RemoveExternalConnectionResponse(ResponseBaseModel):
    """
    Model representing a response for removing an external connection.

    Attributes:
        details (ExternalConnectionDetails | None): The removed connection details, if any.
    """
    details: ExternalConnectionDetails | None

class ListExternalConnectionsDetails(BaseModel):
    """
    Model representing the details of listed external connections.

    Attributes:
        environment_name (str): The name of the environment.
        application_uuid (str): The UUID of the application.
        connections (list[ExternalConnectionDetails]): A list of external connections.
    """
    environment_name: str
    application_uuid: str
    connections: list[ExternalConnectionDetails]

class ListExternalConnectionsResponse(ResponseBaseModel):
    """
    Model representing a response containing the details of listed external connections.

    Attributes:
        details (ListExternalConnectionsDetails | None): The details of the listed connections, if any.
    """
    details: ListExternalConnectionsDetails | None

class UpdateExternalConnectionResponse(ResponseBaseModel):
    """
    Model representing a response for updating an external connection.

    Attributes:
        details (ExternalConnectionDetails | None): The updated connection details, if any.
    """
    details: ExternalConnectionDetails | None
