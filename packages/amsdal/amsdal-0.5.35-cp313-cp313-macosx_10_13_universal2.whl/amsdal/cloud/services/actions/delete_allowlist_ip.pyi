from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class DeleteAllowlistIPAction(CloudActionBase):
    """
    Class to handle the deletion of an allowlist IP action.
    """
    def action(self, env_name: str, ip_address: str | None = None, application_name: str | None = None, application_uuid: str | None = None) -> bool:
        """
        Executes the allowlist IP deletion action with the given parameters.

        Args:
            env_name (str): The name of the environment.
            ip_address (str | None, optional): The IP address to remove from the allowlist. Defaults to None.
            application_name (str | None, optional): The name of the application. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.

        Returns:
            bool: True if the allowlist IP deletion action was successful.
        """
