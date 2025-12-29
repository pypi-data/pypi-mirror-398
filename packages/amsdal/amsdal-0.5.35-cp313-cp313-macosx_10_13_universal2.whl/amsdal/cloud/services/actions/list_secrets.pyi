from amsdal.cloud.models.base import ListSecretsDetails as ListSecretsDetails
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class ListSecretsAction(CloudActionBase):
    """
    Class to handle the listing of secrets.

    This class provides functionality to list secrets for a given environment and application.
    """
    def action(self, env_name: str, application_uuid: str | None = None, application_name: str | None = None, *, with_values: bool = False) -> ListSecretsDetails:
        """
        Executes the action to list secrets with the given parameters.

        Args:
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.
            with_values (bool, optional): Whether to include secret values. Defaults to False.

        Returns:
            ListSecretsDetails: The response containing the list of secrets.
        """
