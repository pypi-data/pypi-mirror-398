from amsdal.cloud.models.base import ListExternalConnectionsResponse as ListExternalConnectionsResponse
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class ListExternalConnectionsAction(CloudActionBase):
    """
    Class to handle the listing of external connections.

    This class provides functionality to list external connections for a given environment.
    """
    def action(self, env_name: str, application_uuid: str | None = None, application_name: str | None = None) -> ListExternalConnectionsResponse:
        """
        Executes the action to list external connections with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            ListExternalConnectionsResponse: The response containing the list of external connections.
        """
