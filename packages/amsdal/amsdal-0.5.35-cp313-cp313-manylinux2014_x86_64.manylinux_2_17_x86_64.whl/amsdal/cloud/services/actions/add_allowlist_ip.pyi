from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class AddAllowlistIPAction(CloudActionBase):
    """
    Action class for adding an IP address to the allowlist.
    """
    def action(self, env_name: str, ip_address: str | None = None, application_name: str | None = None, application_uuid: str | None = None) -> bool:
        """
        Executes the action to add an IP address to the allowlist.

        Args:
            env_name (str): The name of the environment.
            ip_address (str, optional): The IP address to add to the allowlist. Defaults to None.
            application_name (str, optional): The name of the application. Defaults to None.
            application_uuid (str, optional): The UUID of the application. Defaults to None.

        Returns:
            bool: True if the action was executed successfully.
        """
