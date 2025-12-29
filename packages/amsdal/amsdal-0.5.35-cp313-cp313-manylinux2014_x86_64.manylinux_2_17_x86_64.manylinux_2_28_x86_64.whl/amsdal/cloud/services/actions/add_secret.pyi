from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class AddSecretAction(CloudActionBase):
    """
    Action class for adding a secret to an application.
    """
    def action(self, secret_name: str, secret_value: str, env_name: str, application_uuid: str | None = None, application_name: str | None = None) -> bool:
        """
        Executes the action to add a secret to an application.

        Args:
            secret_name (str): The name of the secret.
            secret_value (str): The value of the secret.
            env_name (str): The name of the environment.
            application_uuid (str, optional): The UUID of the application. Defaults to None.
            application_name (str, optional): The name of the application. Defaults to None.

        Returns:
            bool: True if the action was executed successfully.
        """
