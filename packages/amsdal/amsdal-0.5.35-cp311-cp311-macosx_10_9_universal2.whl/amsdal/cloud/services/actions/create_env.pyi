from amsdal.cloud.models.base import CreateEnvResponse as CreateEnvResponse
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class CreateEnvAction(CloudActionBase):
    """
    Class to handle the creation of an environment action.
    """
    def action(self, *, env_name: str, application_name: str | None = None, application_uuid: str | None = None) -> CreateEnvResponse:
        """
        Executes the environment creation action with the given parameters.

        Args:
            env_name (str): The name of the environment to create.
            application_name (str | None, optional): The name of the application. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.

        Returns:
            CreateEnvResponse: The response model containing the details of the created environment.
        """
