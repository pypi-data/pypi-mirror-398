from amsdal.cloud.models.base import CreateEnvResponse as CreateEnvResponse
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class DeleteEnvAction(CloudActionBase):
    """
    Class to handle the deletion of an environment.

    This class provides functionality to remove an environment for a given application.
    """
    def action(self, *, env_name: str, application_name: str | None = None, application_uuid: str | None = None) -> CreateEnvResponse:
        """
        Executes the environment deletion action with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_name (str | None, optional): The name of the application. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.

        Returns:
            CreateEnvResponse: The response data after the environment deletion action.
        """
