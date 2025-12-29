from amsdal.cloud.models.base import RemoveExternalConnectionResponse as RemoveExternalConnectionResponse
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class RemoveExternalConnectionAction(CloudActionBase):
    """
    Class to handle the removal of an external connection.

    This class provides functionality to remove a specified external connection
    from a given environment.
    """
    def action(self, connection_name: str, env_name: str, application_uuid: str | None = None, application_name: str | None = None) -> RemoveExternalConnectionResponse:
        """
        Executes the external connection removal action with the given parameters.

        Args:
            connection_name (str): The name of the connection to remove.
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            RemoveExternalConnectionResponse: The response containing the removed connection details.
        """
