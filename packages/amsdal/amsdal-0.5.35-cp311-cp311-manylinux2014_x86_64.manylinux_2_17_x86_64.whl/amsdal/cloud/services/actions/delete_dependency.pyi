from amsdal.cloud.services.actions.base import CloudActionBase as CloudActionBase

class DeleteDepenencyAction(CloudActionBase):
    """
    Class to handle the deletion of an application dependency.

    This class provides functionality to remove a specified dependency for a given environment and application.
    """
    def action(self, dependency_name: str, env_name: str, application_name: str | None = None, application_uuid: str | None = None) -> bool:
        """
        Executes the application dependency deletion action with the given parameters.

        Args:
            dependency_name (str): The name of the dependency to remove.
            env_name (str): The name of the environment.
            application_name (str | None, optional): The name of the application. Defaults to None.
            application_uuid (str | None, optional): The UUID of the application. Defaults to None.

        Returns:
            bool: True if the application dependency deletion action was successful.
        """
