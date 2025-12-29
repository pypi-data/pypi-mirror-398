from amsdal.cloud.constants import AMSDAL_ENV_SUBDOMAIN as AMSDAL_ENV_SUBDOMAIN
from amsdal.cloud.models.base import DeployResponse as DeployResponse
from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase
from amsdal.errors import AmsdalCloudAlreadyDeployedError as AmsdalCloudAlreadyDeployedError
from typing import Any

class CreateDeployAction(CloudActionBase):
    """
    Class to handle the creation of a deploy action.
    """
    def want_deploy_input(self) -> str:
        """
        Prompts the user to confirm if they want to deploy the app.

        Returns:
            str: The user's input, stripped of leading and trailing whitespace.
        """
    def want_redeploy_input(self) -> str:
        """
        Prompts the user to confirm if they want to redeploy the app.

        Returns:
            str: The user's input, stripped of leading and trailing whitespace.
        """
    def action(self, deploy_type: str, lakehouse_type: str, env_name: str, from_env: str | None = None, application_uuid: str | None = None, application_name: str | None = None, *, no_input: bool = False) -> bool:
        """
        Executes the deploy action with the given parameters.

        Args:
            deploy_type (str): The type of deploy to perform.
            lakehouse_type (str): The type of lakehouse to deploy.
            env_name (str): The name of the environment to deploy to.
            from_env (str | None, optional): The environment to deploy from. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.
            no_input (bool, optional): If True, skips user input prompts. Defaults to False.

        Returns:
            bool: True if the deploy action was successful, False otherwise.
        """
    def _redeploy(self, deploy_data: dict[str, Any]) -> bool: ...
