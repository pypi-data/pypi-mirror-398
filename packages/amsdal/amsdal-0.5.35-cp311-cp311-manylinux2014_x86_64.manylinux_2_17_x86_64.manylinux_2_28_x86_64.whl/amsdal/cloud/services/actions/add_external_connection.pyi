from amsdal.cloud.models.base import AddExternalConnectionResponse as AddExternalConnectionResponse
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class AddExternalConnectionAction(CloudActionBase):
    """
    Action class for adding an external connection to an environment.
    """
    def action(self, connection_name: str, backend: str, credentials: dict[str, str], env_name: str, application_uuid: str | None = None, application_name: str | None = None) -> AddExternalConnectionResponse:
        """
        Executes the action to add an external connection to an environment.

        Args:
            connection_name (str): The name of the connection.
            backend (str): The backend type (e.g., 'postgres', 'mysql', 'redis').
            credentials (dict[str, str]): Dictionary of connection credentials.
            env_name (str): The name of the environment.
            application_uuid (str, optional): The UUID of the application. Defaults to None.
            application_name (str, optional): The name of the application. Defaults to None.

        Returns:
            AddExternalConnectionResponse: The response containing the added connection details.
        """
