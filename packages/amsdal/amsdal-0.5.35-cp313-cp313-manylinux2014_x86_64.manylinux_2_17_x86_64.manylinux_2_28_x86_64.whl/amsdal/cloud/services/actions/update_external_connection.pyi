from amsdal.cloud.models.base import UpdateExternalConnectionResponse as UpdateExternalConnectionResponse
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase
from typing import Any

class UpdateExternalConnectionAction(CloudActionBase):
    """
    Class to handle the update of an external connection.

    This class provides functionality to update an external connection's backend or credentials
    for a given environment.
    """
    def action(self, connection_name: str, env_name: str, backend: str | None = None, credentials: dict[str, Any] | None = None, application_uuid: str | None = None, application_name: str | None = None) -> UpdateExternalConnectionResponse:
        """
        Executes the action to update an external connection with the given parameters.

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
