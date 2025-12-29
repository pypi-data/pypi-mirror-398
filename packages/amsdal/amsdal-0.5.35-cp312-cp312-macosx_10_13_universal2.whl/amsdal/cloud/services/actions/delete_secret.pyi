from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class DeleteSecretAction(CloudActionBase):
    """
    Class to handle the deletion of a secret.

    This class provides functionality to remove a specified secret for a given environment and application.
    """
    def action(self, secret_name: str, env_name: str, application_uuid: str | None = None, application_name: str | None = None) -> bool:
        """
        Executes the secret deletion action with the given parameters.

        Args:
            secret_name (str): The name of the secret to remove.
            env_name (str): The name of the environment.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.

        Returns:
            bool: True if the secret deletion action was successful.
        """
