from amsdal.cloud.models.base import AddBasicAuthResponse as AddBasicAuthResponse
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class AddBasicAuthAction(CloudActionBase):
    """
    Action class for adding basic authentication.
    """
    def action(self, env_name: str, username: str | None = None, password: str | None = None, application_name: str | None = None, application_uuid: str | None = None) -> AddBasicAuthResponse:
        """
        Executes the action to add basic authentication.

        Args:
            env_name (str): The name of the environment.
            username (str, optional): The username for basic authentication. Defaults to None.
            password (str, optional): The password for basic authentication. Defaults to None.
            application_name (str, optional): The name of the application. Defaults to None.
            application_uuid (str, optional): The UUID of the application. Defaults to None.

        Returns:
            AddBasicAuthResponse: The response containing the basic authentication details.
        """
