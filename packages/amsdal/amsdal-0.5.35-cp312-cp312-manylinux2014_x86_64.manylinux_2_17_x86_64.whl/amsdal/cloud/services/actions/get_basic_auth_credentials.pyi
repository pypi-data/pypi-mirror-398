from amsdal.cloud.models.base import AddBasicAuthResponse as AddBasicAuthResponse
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class GetBasicAuthCredentialsAction(CloudActionBase):
    """
    Class to handle the retrieval of basic authentication credentials.

    This class provides functionality to get basic authentication credentials for a given environment and application.
    """
    def action(self, env_name: str, application_name: str | None = None, application_uuid: str | None = None) -> AddBasicAuthResponse:
        """
        Executes the action to retrieve basic authentication credentials with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_name (str | None, optional): The name of the application. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.

        Returns:
            AddBasicAuthResponse: The response containing the basic authentication credentials.
        """
