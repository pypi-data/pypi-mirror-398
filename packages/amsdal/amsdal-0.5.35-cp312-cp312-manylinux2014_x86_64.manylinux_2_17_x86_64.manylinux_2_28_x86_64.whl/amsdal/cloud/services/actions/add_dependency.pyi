from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class AddDepenencyAction(CloudActionBase):
    """
    Action class for adding a dependency to an application.
    """
    def action(self, dependency_name: str, env_name: str, application_name: str | None = None, application_uuid: str | None = None) -> bool:
        """
        Executes the action to add a dependency to an application.

        Args:
            dependency_name (str): The name of the dependency.
            env_name (str): The name of the environment.
            application_name (str, optional): The name of the application. Defaults to None.
            application_uuid (str, optional): The UUID of the application. Defaults to None.

        Returns:
            bool: True if the action was executed successfully.
        """
